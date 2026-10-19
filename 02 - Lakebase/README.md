# 02 - Lakebase

O app do módulo 4 precisa responder em milissegundos "qual o status da autorização AUT-00058?" e gravar a observação que o atendente escreve. Isso é trabalho de banco transacional (OLTP), não de lakehouse. Neste módulo você leva a `silver_autorizacao_status` para o **Lakebase**, o Postgres gerenciado do Databricks, com uma **synced table**, e cria no Postgres a tabela onde o app vai escrever.

## Objetivo
- Adicionar ao bundle uma synced table *Triggered* e a task que a sincroniza depois de cada run do pipeline
- Conectar no Postgres com o seu usuário do Databricks e conferir que a cópia acompanha a silver
- Criar a tabela de escrita `observacao_atendente`

## Como fica

```
gerador → Volume → pipeline → silver_autorizacao_status ──sync_lakebase──▶ Postgres: <aluno>.autorizacao_status (só leitura)
                                                                           Postgres: <aluno>.observacao_atendente (o app escreve)
```

O projeto Lakebase `edia-workshop` já existe: o instrutor criou um para a turma. Cada aluno tem o próprio schema Postgres, com o mesmo nome do schema do Unity Catalog.

---

## Passo 1: Declarar a synced table no bundle
> Lakebase: Synced tables · Delta: Change Data Feed · Bundles

Na pasta `01 - Pipeline e bundle/resources/`, crie o arquivo `autorizacao_status.synced_table.yml` (**Create → File**) e cole:

```yaml
resources:
  postgres_synced_tables:
    autorizacao_status:
      # Nome no Unity Catalog. No Postgres, vira a tabela autorizacao_status no schema <aluno>.
      synced_table_id: ${var.catalog}.${resources.schemas.aluno.name}.autorizacao_status
      source_table_full_name: ${var.catalog}.${resources.schemas.aluno.name}.silver_autorizacao_status
      primary_key_columns:
        - autorizacao_id
      # Triggered: sincroniza só quando alguém dispara (a task sync_lakebase do job).
      scheduling_policy: TRIGGERED
      branch: projects/edia-workshop/branches/production # projeto Lakebase do instrutor; não mude
      postgres_database: databricks_postgres
      create_database_objects_if_missing: true
      new_pipeline_spec:
        storage_catalog: ${var.catalog}
        storage_schema: ${resources.schemas.aluno.name}
```

O que cada parte faz:

- `source_table_full_name`: a origem, a sua silver. O sync incremental lê o *Change Data Feed* dela, que o `delta.enableChangeDataFeed` do módulo 1 ligou.
- `primary_key_columns`: a chave da tabela no Postgres. A silver tem uma linha por `autorizacao_id` desde o `AUTO CDC`.
- `create_database_objects_if_missing`: cria o schema Postgres `<aluno>` no primeiro sync.
- `new_pipeline_spec`: o sync roda num pipeline gerenciado, criado junto com a synced table.

O `databricks.yml` inclui `resources/*.yml`, então o arquivo novo já faz parte do bundle.

## Passo 2: TODO — sincronizar a cada run do job
> Jobs: Pipeline task

A synced table *Triggered* só copia as mudanças quando alguém dispara o pipeline dela. Em `resources/autorizacoes.job.yml`, adicione uma terceira task, `sync_lakebase`, que roda **depois da `validar`** e dispara esse pipeline. O ID dele está em `${resources.postgres_synced_tables.autorizacao_status.status.pipeline_id}`.

Como validar: no passo 4, o job mostra três tasks, e as três ficam verdes.

<details markdown="1">
<summary>👉 Solução</summary>

No fim da lista `tasks:` do job:

```yaml
        - task_key: sync_lakebase
          depends_on:
            - task_key: validar
          pipeline_task:
            pipeline_id: ${resources.postgres_synced_tables.autorizacao_status.status.pipeline_id}
```

Depender da `validar`, e não só do `pipeline`, faz o app nunca receber dados que falharam nos `assert`s: se a validação ficar vermelha, o sync não roda.

</details>

## Passo 3: Deploy em `prod`
> Bundles

No painel **Deployments**, com o target `prod`, clique em **Deploy**. Sobem a synced table nova e a mudança no job (~20 s).

> Você mudou só YAML, mas em `prod` qualquer mudança (YAML ou código) só vale depois de um deploy em `prod`.

O deploy cria a synced table e faz a primeira carga, que leva menos de 1 min.

## Passo 4: Rodar o job
> Jobs · Lakebase: Synced tables

Na lista **Bundle resources**, clique em **Run job**. Agora são três tasks: `pipeline` → `validar` → `sync_lakebase`. O run leva ~3 min. Daqui em diante, o schedule faz isso sozinho a cada 10 min, e o Postgres acompanha os lotes que chegam.

No **Catalog**, a synced table aparece em `academydb` → `<aluno>` → `autorizacao_status`, ao lado da silver.

## Passo 5: Ver os dados no Postgres
> Lakebase · Notebooks

Abra `02 - Lakebase/notebook_lakebase.py`, conecte no **serverless**, preencha o widget `aluno` com o seu nome de aluno e clique em **Run all**. O notebook:

1. conecta no Postgres com o seu usuário (o token OAuth faz o papel da senha);
2. compara a `autorizacao_status` do Postgres com a silver;
3. faz a consulta por chave que o app vai fazer;
4. cria `observacao_atendente` e grava uma observação de teste.

O checkpoint no fim fica verde:

```
✅ Postgres com <n> autorizações e observacao_atendente pronta.
```

---

## OLAP vs OLTP
- **OLAP** (lakehouse: Delta, SQL warehouse): lê muitas linhas de uma vez. Serve ao pipeline, à gold e à Genie.
- **OLTP** (Postgres, no Lakebase): lê e grava poucas linhas por chave, em milissegundos, com transações. Serve ao app.

A synced table liga os dois sem um ETL de volta: o lakehouse continua a fonte da verdade, e o Postgres serve o app.

## Triggered, Continuous ou Snapshot
- **Snapshot**: copia a tabela inteira a cada sync. Serve para tabelas pequenas ou que mudam quase toda a cada carga.
- **Triggered** (o que você usou): copia só as mudanças, quando alguém dispara. Aqui, a task do job, logo depois de cada lote.
- **Continuous**: um pipeline sempre ligado copia as mudanças em segundos. É o que você usaria se o app precisasse do status quase em tempo real, mas ele fica ligado (e cobrando) o tempo todo.
