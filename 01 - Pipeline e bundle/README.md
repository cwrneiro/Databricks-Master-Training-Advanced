# 01 - Pipeline e bundle

Neste módulo você recebe um **bundle** pronto: um `databricks.yml` que declara, em código, o seu schema, um pipeline e um job. Você faz deploy em `dev`, vê o job falhar, corrige o pipeline, confirma em `dev` e promove para `prod`. O resto do dia acontece em cima do que sobe aqui.

## Objetivo
- Conhecer a estrutura de um bundle e a UI de bundles do workspace
- Entender o pipeline (Lakeflow Spark Declarative Pipelines): Auto Loader, expectations, `AUTO CDC`, materialized view e sink
- Fazer deploy em `dev`, corrigir um bug e promover para `prod`

## O que está no bundle

```
01 - Pipeline e bundle/
├── databricks.yml                      # nome do bundle, variáveis e targets dev/prod
├── resources/
│   ├── aluno.schema.yml                # o seu schema: academydb.<aluno>
│   ├── autorizacoes.pipeline.yml       # o pipeline (serverless)
│   └── autorizacoes.job.yml            # o job: pipeline → validar, a cada 10 min
└── src/
    ├── pipeline/
    │   ├── bronze.py                   # bronze_autorizacao_eventos (Auto Loader)
    │   ├── silver.py                   # eventos_validos + silver_autorizacao_status
    │   ├── gold.py                     # gold_kpi_autorizacoes (materialized view)
    │   └── notificacoes.py             # notif_autorizacao_negada (foreach_batch_sink)
    └── validar.py                      # notebook com os asserts da segunda task do job
```

O gerador do instrutor escreve um lote de eventos a cada 10 min em `/Volumes/academydb/shared/raw/autorizacao_eventos/`, o dia inteiro. Os eventos chegam com duplicatas, fora de ordem e com alguns inválidos, como num sistema real.

---

## Passo 1: Clonar o repo como Git folder
No menu lateral, clique em **Workspace** → **Create** → **Git folder** e cole a URL do repo que o instrutor passar (a versão pública é `https://github.com/cwrneiro/Databricks-Master-Training-Advanced`).

## Passo 2: Abrir o bundle
Na Git folder, abra a pasta `01 - Pipeline e bundle` e clique em `databricks.yml`. O workspace reconhece que a pasta é um bundle e mostra o painel de bundles (**Deployments**) ao lado do editor.

## Passo 3: Explorar a estrutura
Abra os arquivos da árvore acima. Em cada bloco do pipeline há um comentário `# --- Equivalente em Structured Streaming ---`: é o código que você escreveria "na mão" para fazer o mesmo. Ele não roda; serve para mostrar o que o pipeline faz por você.

## Passo 4: Preencher o seu nome de aluno
Em `databricks.yml`, troque `troque_pelo_seu_nome` pelo seu nome de aluno: primeira letra do nome + sobrenome, sem acento (ex.: Augusto Carneiro → `acarneiro`).

```yaml
  aluno:
    ...
    default: acarneiro
```

## Passo 5: Deploy em `dev`
No painel **Deployments**, deixe o target `dev` selecionado e clique em **Deploy**. O diálogo lista o que vai ser criado:
- o schema `dev_<usuario>_<aluno>`;
- o pipeline e o job, com o prefixo `[dev <usuario>]`.

O `mode: development` do target `dev` faz esses prefixos, para que o seu teste nunca esbarre no de outra pessoa, e pausa o schedule do job.

## Passo 6: Rodar o job
Na lista **Bundle resources**, clique em **Run job** no job `autorizacoes_<aluno>`. Ele roda duas tasks: `pipeline` e, se ela passar, `validar`. O primeiro run leva ~2 min (o serverless está subindo).

## Passo 7: Ver a falha
A task `validar` fica vermelha:

```
AssertionError: A silver tem 1390 linhas para 554 autorizações: uma linha por evento, não por autorização. ...
```

Os números dependem de quantos lotes já chegaram. Abra o pipeline (link na lista **Bundle resources**) e veja o grafo: a `silver_autorizacao_status` está em **append**, então recebe uma linha por evento, duplicatas incluídas. Ela deveria ter uma linha por autorização, com o status atual.

Aproveite e clique em `bronze_autorizacao_eventos` → **Expectations**: as duas regras registram quantos eventos inválidos chegaram. Na bronze elas só avisam (warn); na view `eventos_validos`, descartam (drop).

## Passo 8: TODO — trocar a silver por `AUTO CDC`
Em `src/pipeline/silver.py`, troque o bloco `@dp.table(...) def silver_autorizacao_status()` por um `AUTO CDC` SCD1: chave `autorizacao_id`, ordem por `event_ts`, origem `eventos_validos`. Mantenha o `delta.enableChangeDataFeed`, que o módulo 2 usa.

Como validar: no passo 9, a task `validar` fica verde.

<details markdown="1">
<summary>👉 Solução</summary>

```python
dp.create_streaming_table(
    name="silver_autorizacao_status",
    comment="Status atual de cada autorização.",
    table_properties={"delta.enableChangeDataFeed": "true"},
)
dp.create_auto_cdc_flow(
    target="silver_autorizacao_status",
    source="eventos_validos",
    keys=["autorizacao_id"],
    sequence_by="event_ts",
    stored_as_scd_type=1,
)
```

O `AUTO CDC` faz o MERGE de cada lote por você: deduplica, aplica os eventos na ordem de `event_ts` (mesmo os que chegam atrasados) e mantém uma linha por `autorizacao_id`.

</details>

## Passo 9: Rodar de novo em `dev`, com full refresh
Salve o arquivo. **Não precisa de novo deploy**: em `dev`, o pipeline e o job leem o código direto da sua Git folder. Novo deploy em `dev` só quando você muda um YAML.

A silver ainda guarda as linhas do run anterior, e trocar o tipo de flow (de append para `AUTO CDC`) exige recalcular a tabela do zero. Por isso:
1. Abra o pipeline, clique na seta ao lado de **Run pipeline** → **Run pipeline with full table refresh** → **Start full refresh**. Leva ~1 min.
2. Volte ao bundle e clique em **Run job**. A task `validar` fica verde:

```
✅ 554 autorizações, uma linha cada, todas com status válido.
```

Se você rodar o job sem o full refresh, o pipeline termina sem erro, mas a silver continua com as linhas antigas e a `validar` falha de novo.

## Passo 10: Deploy em `prod`
No painel **Deployments**, troque o target para `prod` e clique em **Deploy**. Agora os nomes vêm sem prefixo: o schema é `academydb.<aluno>`, e o job e o pipeline se chamam `autorizacoes_<aluno>`. Se o deploy disser que o schema já existe, outra pessoa escolheu o mesmo nome: troque o `aluno` (ex.: `acarneiro2`) e faça deploy de novo.

> ⚠️ Em `prod`, o deploy **copia** o código para `.bundle/vida_saude/prod/files`, e o job roda essa cópia. Qualquer mudança de código depois disso só vale em `prod` depois de um novo deploy em `prod`. Em `dev`, como vimos, o código é lido direto da Git folder.

## Passo 11: Rodar o job em `prod`
Na lista **Bundle resources**, clique em **Run job** no job de `prod`. Ele passa de primeira, porque o código já está corrigido. Em `prod`, o schedule está ligado: o job roda sozinho a cada 10 min, 2 min depois de cada lote do gerador, e a silver acompanha os dados que chegam ao longo do dia.

Daqui em diante, o workshop inteiro segue em `prod`, para economizar tempo. No dia a dia, o recomendado é desenvolver sempre em `dev` e só promover para `prod` depois de confirmar que funciona.

---

## Fila de runs
No `autorizacoes.job.yml`, o job tem `max_concurrent_runs: 1` e `queue.enabled: true`. Clique em **Run now** duas vezes seguidas na página do job: o segundo run fica **Queued** até o primeiro terminar, em vez de rodar junto ou ser descartado.

## Por que o schedule, e não "quando chegar arquivo"
O job poderia disparar com o trigger **file arrival**, a cada arquivo novo no Volume. Para isso, o external location precisa de *file events*, que dependem de permissões de IAM na cloud. Sem eles, o workspace aceita no máximo 50 jobs com esse trigger. Com uma turma inteira, o schedule a cada 10 min é o caminho seguro.

## Por que SDP é o padrão
Em Structured Streaming "na mão" (os comentários abaixo de cada bloco), você escolhe e guarda os checkpoints, escreve o MERGE, cuida da idempotência, ordena as dependências entre tabelas e reprocessa tudo quando algo muda. No pipeline declarativo, você descreve **o que** cada tabela é, e a plataforma cuida do **como**: checkpoints, ordem de execução, retries, qualidade de dados (expectations) e full refresh. O código fica menor, e o que sobra é regra de negócio. Structured Streaming continua por baixo, e você recorre a ele quando precisa de algo que o pipeline não oferece.

## O mesmo pelo CLI, e num CI
Cada botão do painel **Deployments** tem um comando equivalente no CLI do Databricks. É o que roda num pipeline de CI/CD, onde ninguém clica em **Deploy**:

```bash
cd "01 - Pipeline e bundle"
databricks bundle validate -t prod             # confere o YAML e resolve as variáveis, sem criar nada
databricks bundle deploy -t dev                # o Deploy do painel, no target dev
databricks bundle run -t dev autorizacoes_job  # o Run job
databricks bundle deploy -t prod --var aluno=acarneiro  # --var troca uma variável sem editar o YAML
```

O nome depois de `run` é a chave do recurso no YAML (`autorizacoes_job`), não o nome que aparece no workspace.

Em `prod`, o job e o pipeline rodam como quem fez o deploy: hoje, você. No dia a dia, isso quebra no primeiro dia de férias. Por isso, o target `prod` de um projeto real declara um service principal (SP), uma identidade que não é de nenhuma pessoa:

```yaml
  prod:
    mode: production
    run_as:
      service_principal_name: 00000000-0000-0000-0000-000000000000 # application ID do SP
```

E o deploy sai das mãos das pessoas: um merge na branch principal dispara o CI, que se autentica como o SP e roda o mesmo `deploy -t prod`. Um exemplo com GitHub Actions:

```yaml
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
      DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}         # application ID do SP
      DATABRICKS_CLIENT_SECRET: ${{ secrets.DATABRICKS_CLIENT_SECRET }} # secret OAuth do SP
    defaults:
      run:
        working-directory: 01 - Pipeline e bundle
    steps:
      - uses: actions/checkout@v4
      - uses: databricks/setup-cli@main
      - run: databricks bundle validate -t prod
      - run: databricks bundle deploy -t prod
```

No workshop, cada aluno faz o próprio deploy pela UI, para ver cada passo acontecer.

## 🎯 Desafio: histórico de status (SCD2)
Crie a `silver_autorizacao_historico`, com uma linha por mudança de status de cada autorização (`__START_AT` e `__END_AT` marcam a vigência). Dica: é o mesmo `AUTO CDC`, com `stored_as_scd_type=2`. Como é uma tabela nova, basta um **Run job**, sem full refresh.

<details markdown="1">
<summary>👉 Solução</summary>

No fim de `src/pipeline/silver.py`:

```python
dp.create_streaming_table(
    name="silver_autorizacao_historico",
    comment="Histórico de status de cada autorização (SCD2).",
)
dp.create_auto_cdc_flow(
    target="silver_autorizacao_historico",
    source="eventos_validos",
    keys=["autorizacao_id"],
    sequence_by="event_ts",
    stored_as_scd_type=2,
    track_history_column_list=["status"],
)
```

Para conferir, o status atual de cada autorização é a linha com `__END_AT IS NULL`:

```sql
SELECT count(*) AS linhas, count_if(__END_AT IS NULL) AS atuais
FROM academydb.<aluno>.silver_autorizacao_historico;
```

`atuais` é igual ao número de linhas da `silver_autorizacao_status`.

</details>
