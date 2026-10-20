# Databricks notebook source
# MAGIC %md
# MAGIC # Validar
# MAGIC
# MAGIC Segunda task do job, depois do pipeline. Confere a `silver_autorizacao_status` contra a bronze. Se algum `assert` falhar, a task fica vermelha e a mensagem diz o que corrigir.

# COMMAND ----------

dbutils.widgets.text("catalog", "academydb")
dbutils.widgets.text("schema", "")

schema = f"{dbutils.widgets.get('catalog')}.{dbutils.widgets.get('schema')}"
DOMINIO = "('solicitada', 'em_analise', 'aprovada', 'negada')"

silver = spark.table(f"{schema}.silver_autorizacao_status")
bronze = spark.table(f"{schema}.bronze_autorizacao_eventos")

linhas = silver.count()
autorizacoes = silver.select("autorizacao_id").distinct().count()
validas = (
    bronze.where(f"autorizacao_id IS NOT NULL AND status IN {DOMINIO}")
    .select("autorizacao_id").distinct().count()
)
fora_do_dominio = silver.where(f"autorizacao_id IS NULL OR status NOT IN {DOMINIO}").count()
print(f"silver: {linhas} linhas, {autorizacoes} autorizações; bronze: {validas} autorizações válidas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Checkpoint de validação

# COMMAND ----------

assert linhas == autorizacoes, (
    f"A silver tem {linhas} linhas para {autorizacoes} autorizações: uma linha por evento, não por autorização. "
    "Troque a silver por AUTO CDC (passo 9 do guia). Se já trocou, rode o pipeline com full refresh (passo 10)."
)
assert linhas == validas, f"A silver tem {linhas} autorizações, mas a bronze tem {validas} válidas."
assert fora_do_dominio == 0, f"{fora_do_dominio} linhas da silver têm autorizacao_id nulo ou status fora do domínio."
print(f"✅ {linhas} autorizações, uma linha cada, todas com status válido.")
