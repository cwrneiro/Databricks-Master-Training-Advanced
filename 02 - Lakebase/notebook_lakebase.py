# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # 02 - Lakebase
# MAGIC
# MAGIC A synced table do seu bundle copia a `silver_autorizacao_status` para o Postgres do Lakebase a cada run do job. Neste notebook você:
# MAGIC 1. conecta no Postgres com o seu usuário do Databricks (token OAuth, sem senha);
# MAGIC 2. confere que a cópia no Postgres acompanha a silver;
# MAGIC 3. cria a tabela `observacao_atendente`, onde o app do módulo 4 grava as observações.
# MAGIC
# MAGIC Rode no **serverless**, depois de fazer o passo 4 do guia (deploy em `prod` e um **Run job** verde).

# COMMAND ----------

dbutils.widgets.text("aluno", "troque_pelo_seu_nome")
aluno = dbutils.widgets.get("aluno")  # o mesmo var.aluno do databricks.yml (em dev: dev_<usuario>_<aluno>)
assert aluno != "troque_pelo_seu_nome", "Preencha o widget 'aluno' no topo do notebook com o seu nome de aluno."

CATALOG = "academydb"
ENDPOINT = "projects/edia-workshop/branches/production/endpoints/primary"  # projeto Lakebase do instrutor

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Conectar no Postgres
# MAGIC O Lakebase não tem senha fixa: o Databricks gera um token OAuth de 1 h para o seu usuário, e ele é a senha. O app do módulo 4 faz o mesmo com o service principal dele.

# COMMAND ----------

import psycopg2
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
host = w.api_client.do("GET", f"/api/2.0/postgres/{ENDPOINT}")["status"]["hosts"]["host"]
token = w.api_client.do("POST", "/api/2.0/postgres/credentials", body={"endpoint": ENDPOINT})["token"]
user = w.current_user.me().user_name

conn = psycopg2.connect(host=host, dbname="databricks_postgres", user=user, password=token, sslmode="require")
conn.autocommit = True
print(f"Conectado em {host} como {user}.")


def sql(query, params=None):
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall() if cur.description else None

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. A synced table no Postgres
# MAGIC No Postgres, o seu schema do Unity Catalog virou um schema Postgres com o mesmo nome, e a synced table virou a tabela `autorizacao_status`, com chave primária em `autorizacao_id`. É uma cópia **só leitura**: quem escreve nela é o sync.

# COMMAND ----------

pg_linhas, pg_ultimo = sql(f'SELECT count(*), max(event_ts) FROM "{aluno}".autorizacao_status')[0]
silver = spark.sql(f"SELECT count(*) AS n, max(event_ts) AS ultimo FROM {CATALOG}.{aluno}.silver_autorizacao_status").first()
print(f"Postgres: {pg_linhas} autorizações (último evento {pg_ultimo})")
print(f"Silver:   {silver.n} autorizações (último evento {silver.ultimo})")

# COMMAND ----------

# MAGIC %md
# MAGIC Os números podem diferir por alguns minutos: o job atualiza a silver primeiro e só depois a task `sync_lakebase` copia as mudanças. Se o Postgres estiver atrás, espere o run do job terminar e rode a célula de novo.
# MAGIC
# MAGIC A consulta que o app faz é por chave, uma autorização por vez. No Postgres, isso leva milissegundos:

# COMMAND ----------

import time

exemplo = sql(f'SELECT autorizacao_id FROM "{aluno}".autorizacao_status ORDER BY event_ts DESC LIMIT 1')[0][0]
t0 = time.perf_counter()
print(sql(f'SELECT autorizacao_id, procedimento, status, event_ts FROM "{aluno}".autorizacao_status '
          "WHERE autorizacao_id = %s", (exemplo,)))
print(f"{(time.perf_counter() - t0) * 1000:.0f} ms")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. A tabela de escrita: `observacao_atendente`
# MAGIC A synced table só vai do Lakehouse para o Postgres. O que o atendente escreve no app nasce no Postgres, numa tabela comum, criada aqui no seu schema. O app do módulo 4 grava nela.

# COMMAND ----------

sql(f"""
CREATE TABLE IF NOT EXISTS "{aluno}".observacao_atendente (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    autorizacao_id TEXT        NOT NULL,
    texto          TEXT        NOT NULL,
    autor          TEXT        NOT NULL,
    criado_em      TIMESTAMPTZ NOT NULL DEFAULT now()
)""")
novo_id = sql(f'INSERT INTO "{aluno}".observacao_atendente (autorizacao_id, texto, autor) '
              "VALUES (%s, %s, %s) RETURNING id", (exemplo, "Beneficiário ligou pedindo prazo.", user))[0][0]
print(sql(f'SELECT * FROM "{aluno}".observacao_atendente ORDER BY id DESC LIMIT 5'))

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Checkpoint de validação

# COMMAND ----------

assert pg_linhas > 0, (
    "A autorizacao_status do Postgres está vazia. Confira se o job rodou depois do deploy em prod "
    "e se a task sync_lakebase ficou verde (passo 4 do guia).")
assert pg_linhas <= silver.n, f"O Postgres tem {pg_linhas} autorizações e a silver só {silver.n}: algo está errado no sync."
assert sql(f'SELECT count(*) FROM "{aluno}".observacao_atendente WHERE id = %s', (novo_id,))[0][0] == 1
print(f"✅ Postgres com {pg_linhas} autorizações e observacao_atendente pronta.")
