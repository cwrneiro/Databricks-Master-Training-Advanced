from pyspark import pipelines as dp

# Na silver, as mesmas regras da bronze descartam as linhas inválidas (drop).
REGRAS = {
    "autorizacao_id_presente": "autorizacao_id IS NOT NULL",
    "status_no_dominio": "status IN ('solicitada', 'em_analise', 'aprovada', 'negada')",
}


@dp.temporary_view(comment="Só os eventos válidos. Não é publicada no catálogo.")
@dp.expect_all_or_drop(REGRAS)
def eventos_validos():
    return spark.readStream.table("bronze_autorizacao_eventos").select(
        "event_id", "autorizacao_id", "beneficiario_id", "prestador_id", "procedimento", "status", "event_ts"
    )

# --- Equivalente em Structured Streaming ---
# Uma view temporária não grava nada: é só um DataFrame reaproveitado pelas tabelas abaixo.
#
# eventos_validos = (spark.readStream.table("academydb.<aluno>.bronze_autorizacao_eventos")
#     .where("autorizacao_id IS NOT NULL AND status IN ('solicitada', 'em_analise', 'aprovada', 'negada')"))


# TODO (passo 9): esta tabela deveria ter uma linha por autorização, com o status atual.
# Em append, ela recebe uma linha por evento, duplicatas incluídas, e a task validar falha.
# Troque o bloco abaixo por AUTO CDC (SCD1). A solução está no README do módulo.
@dp.table(
    comment="Status atual de cada autorização.",
    table_properties={"delta.enableChangeDataFeed": "true"},
)
def silver_autorizacao_status():
    return spark.readStream.table("eventos_validos")

# --- Equivalente em Structured Streaming ---
# O AUTO CDC faz por você o MERGE de cada micro-batch: deduplica, ignora eventos que chegam
# atrasados com event_ts menor que o já gravado e atualiza o status da autorização.
#
# def upsert(df, batch_id):
#     ultimo = (df.withColumn("n", F.row_number().over(
#                   Window.partitionBy("autorizacao_id").orderBy(F.col("event_ts").desc())))
#               .where("n = 1").drop("n"))
#     (DeltaTable.forName(df.sparkSession, "academydb.<aluno>.silver_autorizacao_status").alias("t")
#         .merge(ultimo.alias("s"), "t.autorizacao_id = s.autorizacao_id")
#         .whenMatchedUpdateAll(condition="s.event_ts > t.event_ts")
#         .whenNotMatchedInsertAll()
#         .execute())
#
# (eventos_validos.writeStream
#     .foreachBatch(upsert)
#     .option("checkpointLocation", "/Volumes/academydb/<aluno>/checkpoints/silver")
#     .trigger(availableNow=True)
#     .start())
