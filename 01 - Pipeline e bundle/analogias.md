# 01 - Pipeline e bundle: analogias

Para quem já trabalha com Kafka, Kubernetes e Helm: o que cada peça deste módulo lembra, e onde a comparação deixa de valer.

## Pipeline: Kafka → Lakeflow Spark Declarative Pipelines

| De (Kafka) | Para (Databricks) | Onde aparece no módulo |
|---|---|---|
| Producer | O gerador do instrutor, que escreve um lote de JSON a cada 10 min | Passo 1 |
| Tópico | A pasta `raw/autorizacao_eventos` no Volume e, depois do pipeline, cada tabela Delta com Change Data Feed (CDF) | Passo 1; `delta.enableChangeDataFeed` na silver |
| Consumer | A streaming table que lê a origem: a bronze (Auto Loader) e a silver | `bronze.py`, `silver.py` |
| Offset do consumer group | O checkpoint de cada streaming table, que o pipeline guarda por você | Comentários `Equivalente em Structured Streaming` |
| Tópico compactado (último valor por chave) | A silver com `AUTO CDC` SCD1: uma linha por `autorizacao_id`, com o status atual | Passo 9 |
| Consumer que deduplica e reordena por timestamp | `AUTO CDC` com `sequence_by="event_ts"` | Passo 9 |
| Consumer que chama um sistema externo | `foreach_batch_sink`, com MERGE idempotente pelo `batch_id` | `notificacoes.py` |
| Reprocessar do offset zero (`--reset-offsets --to-earliest`) | Full refresh do pipeline | Passo 10 |
| Validação de schema no Schema Registry | Expectations: na bronze só registram (warn), na `eventos_validos` descartam (drop) | Passo 8 |

## Job: Kubernetes → Lakeflow Jobs

| De (Kubernetes) | Para (Databricks) | Onde aparece no módulo |
|---|---|---|
| CronJob | Job com `schedule` (`quartz_cron_expression`) | `autorizacoes.job.yml` |
| `concurrencyPolicy: Forbid` | `max_concurrent_runs: 1` | `autorizacoes.job.yml` |
| Init container + container principal (um depois do outro) | Tasks com `depends_on`: `pipeline` → `validar` | Passo 7 |
| Deployment sempre ligado | Pipeline em modo Continuous (o módulo 2 compara os modos) | Módulo 2 |
| Pod que sobe, roda e some | Serverless: o compute sobe para o run e desliga depois | Passo 7 |

## Bundle: Helm → Declarative Automation Bundles

| De (Helm) | Para (Databricks) | Onde aparece no módulo |
|---|---|---|
| Chart | O bundle: `databricks.yml` + `resources/` + `src/` | Passo 4 |
| `values.yaml` | `variables` do `databricks.yml` | Passo 5 |
| `values-dev.yaml` / `values-prod.yaml` | Targets `dev` e `prod` | Passos 6 e 11 |
| `--set chave=valor` | `--var aluno=acarneiro` | **O mesmo pelo CLI, e num CI** |
| `helm lint` / `helm template` | `databricks bundle validate` | **O mesmo pelo CLI, e num CI** |
| `helm upgrade --install` | `databricks bundle deploy` (o **Deploy** do painel) | Passos 6 e 11 |
| Namespace por ambiente | Prefixos do `mode: development` (`dev_<usuario>_`, `[dev <usuario>]`) | Passo 6 |
| ServiceAccount do pipeline de CD | `run_as` com um service principal | **O mesmo pelo CLI, e num CI** |

## Onde a analogia quebra

- **Não há partições nem consumer groups para escalar.** O paralelismo é do Spark e do serverless, não do número de partições do tópico.
- **O "tópico" é uma tabela.** Dá para consultar com SQL, fazer time travel e juntar com outras tabelas. Não há retenção por tempo como no Kafka: o histórico vive no log do Delta.
- **A latência é de minutos, não de milissegundos.** Aqui o job roda a cada 10 min. Mesmo o modo Continuous fica na casa dos segundos.
- **Fila não é `Forbid`.** O `concurrencyPolicy: Forbid` descarta o run que chega com outro em andamento. O `queue.enabled: true` guarda esse run e roda depois.
- **Não há `helm rollback`.** Voltar uma versão é reverter o código no Git e fazer deploy de novo.
- **O `mode: development` não isola como um namespace.** Ele só muda nomes e pausa schedules. As permissões continuam as do Unity Catalog.
