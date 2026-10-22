# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # 04 - App
# MAGIC
# MAGIC Este notebook acompanha o guia do módulo. Rode **uma seção por vez**, no passo que o guia indicar:
# MAGIC 1. **Seção 1** (passo 3): mostra o app e o service principal (SP) dele, e conecta no Postgres.
# MAGIC 2. **Seção 2** (passo 3): o TODO, os GRANTs no Postgres para o SP do app, e o checkpoint.
# MAGIC 3. **Seção 3** (passo 4): mostra as observações que o app gravou.
# MAGIC
# MAGIC Rode no **serverless**, depois do passo 2 do guia (deploy em `prod` e **Run** do app).

# COMMAND ----------

# MAGIC %md
# MAGIC > ⚠️ Rode **só a primeira célula** abaixo e pare: o widget `aluno` aparece no topo do notebook. Preencha com o seu nome de aluno e só então use **Run all** (ou rode as células seguintes).

# COMMAND ----------

dbutils.widgets.text("aluno", "troque_pelo_seu_nome")

# COMMAND ----------

aluno = dbutils.widgets.get("aluno")  # o mesmo var.aluno do databricks.yml
assert aluno != "troque_pelo_seu_nome", "Preencha o widget 'aluno' no topo do notebook com o seu nome de aluno."

APP = f"vida-saude-{aluno}"
SCHEMA = aluno  # em prod, o schema do Postgres tem o nome do aluno (módulo 2)
ENDPOINT = "projects/edia-workshop/branches/production/endpoints/primary"  # projeto Lakebase do instrutor

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. O app e o service principal dele
# MAGIC O app tem duas identidades. Para o Postgres, ele usa o próprio SP, criado junto com o app. Para conversar com o agente, ele usa o token de quem está logado. O recurso `postgres` do bundle criou um role com o application ID do SP no Postgres, mas esse role ainda não enxerga o seu schema.

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
app = w.apps.get(APP)
sp = app.service_principal_client_id
implantado = app.active_deployment and app.active_deployment.status.state.value == "SUCCEEDED"
print(f"App {APP}: {app.url}")
print(f"Application ID do SP: {sp}")
assert implantado, (
    f"O app {APP} existe, mas o código ainda não subiu. Em Bundle resources, clique em Run no app (passo 2 do guia).")

# COMMAND ----------

import psycopg2

host = w.api_client.do("GET", f"/api/2.0/postgres/{ENDPOINT}")["status"]["hosts"]["host"]
token = w.api_client.do("POST", "/api/2.0/postgres/credentials", body={"endpoint": ENDPOINT})["token"]
user = w.current_user.me().user_name

conn = psycopg2.connect(host=host, dbname="databricks_postgres", user=user, password=token, sslmode="require")
conn.autocommit = True


def sql(query, params=None):
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall() if cur.description else None


assert sql("SELECT 1 FROM pg_roles WHERE rolname = %s", (sp,)), (
    f"O Postgres ainda não tem o role {sp}. Confira o recurso postgres do app no bundle e faça deploy em prod.")
print(f"Conectado como {user}. O role {sp} existe no Postgres.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. TODO: dar ao SP do app acesso ao seu schema
# MAGIC Você é dono do schema `<aluno>` e da `observacao_atendente`, e tem `SELECT` com grant option na `autorizacao_status`. Então é você quem concede ao SP o que o app usa.

# COMMAND ----------

# TODO: conceda ao SP do app (a variável sp) o que ele usa no seu schema do Postgres (a variável SCHEMA):
#   - USAGE no schema
#   - SELECT na autorizacao_status (o app lê o status)
#   - SELECT e INSERT na observacao_atendente (o app lê e grava as observações)
# Use a função sql(...), como no módulo 2. No Postgres, o schema e o role vão entre aspas duplas: "{SCHEMA}" e "{sp}".

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Checkpoint de validação

# COMMAND ----------

pode = {
    "USAGE no schema": sql("SELECT has_schema_privilege(%s, %s, 'USAGE')", (sp, SCHEMA))[0][0],
    "SELECT na autorizacao_status": sql("SELECT has_table_privilege(%s, %s, 'SELECT')", (sp, f'"{SCHEMA}".autorizacao_status'))[0][0],
    "SELECT na observacao_atendente": sql("SELECT has_table_privilege(%s, %s, 'SELECT')", (sp, f'"{SCHEMA}".observacao_atendente'))[0][0],
    "INSERT na observacao_atendente": sql("SELECT has_table_privilege(%s, %s, 'INSERT')", (sp, f'"{SCHEMA}".observacao_atendente'))[0][0],
}
falta = [k for k, v in pode.items() if not v]
assert not falta, f"O SP {sp} ainda não tem: {', '.join(falta)}. Complete o TODO acima e rode de novo."
print(f"✅ O app {APP} pode ler e gravar no schema {SCHEMA}. Recarregue {app.url}.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. As observações que o app gravou
# MAGIC Rode depois de salvar uma observação no app (passo 4). Quem grava é o SP do app, mas o `autor` é o seu e-mail: o app lê quem está logado e grava junto.

# COMMAND ----------

display(spark.createDataFrame(
    sql(f'SELECT id, autorizacao_id, texto, autor, criado_em FROM "{SCHEMA}".observacao_atendente ORDER BY id DESC LIMIT 10'),
    "id long, autorizacao_id string, texto string, autor string, criado_em timestamp"))
