# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # 03 - Agente
# MAGIC
# MAGIC Este notebook acompanha o guia do módulo. Rode **uma seção por vez**, no passo que o guia indicar:
# MAGIC 1. **Seção 1** (passo 2): confere os trechos dos documentos e o índice de AI Search, e faz uma busca nele.
# MAGIC 2. **Seção 2** (passo 6): mostra os comandos de deploy do agente, já com o seu caminho e o seu nome.
# MAGIC 3. **Seção 3** (passo 7): mostra o application ID do service principal do app do agente.
# MAGIC 4. **Checkpoint** (passo 7, depois do deploy do bundle): confere os grants do SP.
# MAGIC
# MAGIC Rode no **serverless**. O web terminal do passo 6 é aberto a partir deste notebook.

# COMMAND ----------

dbutils.widgets.text("aluno", "troque_pelo_seu_nome")
aluno = dbutils.widgets.get("aluno")  # o mesmo var.aluno do databricks.yml
assert aluno != "troque_pelo_seu_nome", "Preencha o widget 'aluno' no topo do notebook com o seu nome de aluno."

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
CATALOG = "academydb"
SCHEMA = f"{CATALOG}.{aluno}"
INDICE = f"{SCHEMA}.documentos_idx"
APP = f"agent-bricks-{aluno}"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Trechos e índice
# MAGIC O pipeline gravou um trecho por bloco de texto dos PDFs na `documentos_chunks`. O índice de AI Search calcula o embedding de cada trecho e encontra os mais parecidos com uma pergunta. É exatamente essa busca que o agente faz antes de responder sobre regras e prazos.

# COMMAND ----------

trechos = spark.table(f"{SCHEMA}.documentos_chunks")
display(trechos.groupBy("documento").count().orderBy("documento"))

status = w.api_client.do("GET", f"/api/2.0/vector-search/indexes/{INDICE}")["status"]
assert status.get("ready"), f"O índice {INDICE} ainda não está pronto ({status.get('message')}). Espere 1 min e rode de novo."
print(f"Índice pronto, com {status.get('indexed_row_count')} trechos.")

# COMMAND ----------

pergunta = "Qual é o prazo máximo para realização de uma ressonância magnética?"
r = w.vector_search_indexes.query_index(INDICE, columns=["documento", "texto"], query_text=pergunta, num_results=3)
for documento, texto, score in r.result.data_array:
    print(f"{score:.2f}  {documento}\n      {texto[:200]}\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Comandos para o web terminal
# MAGIC Copie os comandos abaixo e cole no web terminal (painel inferior do notebook → **Terminal**). Troque `<id do Genie space>` pelo ID que você copiou no passo 3.

# COMMAND ----------

notebook = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
projeto = "/Workspace" + notebook.rsplit("/", 1)[0] + "/agente"
print(f"""pip install databricks-agentbricks==0.5.1
cd "{projeto}"
sed -i 's/troque_pelo_seu_nome/{aluno}/g' agent.toml agent/agent.py
agentbricks tools add genie-agent <id do Genie space>
agentbricks deploy {aluno}""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. O service principal do app
# MAGIC Todo app do Databricks roda com um service principal (SP) próprio, criado junto com o app. É com essa identidade que o agente chama o model service e o índice, e ela ainda não tem acesso a nada no seu schema.

# COMMAND ----------

app = w.apps.get(APP)
sp = app.service_principal_client_id
print(f"App {APP}: {app.url}")
print(f"Application ID do SP (cole em var.agent_sp): {sp}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Checkpoint de validação
# MAGIC Rode depois do deploy do bundle com os `grants` (TODO do passo 7).

# COMMAND ----------

def privilegios(tipo, nome):
    acl = w.api_client.do("GET", f"/api/2.1/unity-catalog/permissions/{tipo}/{nome}").get("privilege_assignments", [])
    return {p for a in acl if a["principal"] == sp for p in a["privileges"]}


no_schema = privilegios("schema", SCHEMA)
no_llm = privilegios("model-service", f"{SCHEMA}.llm")
assert {"USE_SCHEMA", "SELECT"} <= no_schema, (
    f"O SP {sp} tem {sorted(no_schema) or 'nada'} no schema {SCHEMA}. Confira var.agent_sp e o grants do schema, e faça deploy em prod."
)
assert "EXECUTE" in no_llm, (
    f"O SP {sp} tem {sorted(no_llm) or 'nada'} no model service {SCHEMA}.llm. Confira o grants do model service e faça deploy em prod."
)
print(f"✅ O app {APP} pode usar o índice e o model service. Abra {app.url} e converse com o agente.")
