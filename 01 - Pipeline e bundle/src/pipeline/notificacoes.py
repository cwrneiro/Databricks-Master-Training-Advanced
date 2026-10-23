from pyspark import pipelines as dp
from pyspark.sql import functions as F

# Tabela comum (fora do pipeline) que um sistema de notificação leria: uma linha por autorização negada.
TABELA = f"{spark.conf.get('catalog')}.{spark.conf.get('schema')}.notif_autorizacao_negada"


@dp.foreach_batch_sink(name="notif_autorizacao_negada_sink")
def notif_autorizacao_negada_sink(df, batch_id):
    # Dentro do sink, use df.sparkSession, não o spark global.
    s = df.sparkSession
    s.sql(
        f"CREATE TABLE IF NOT EXISTS {TABELA} "
        "(autorizacao_id STRING, prestador_id STRING, procedimento STRING, negada_em TIMESTAMP, batch_id BIGINT)"
    )
    # batch_id registra em que micro-batch a notificação saiu. Se o mesmo batch rodar de novo
    # (retry), o MERGE encontra as autorizações já gravadas e não insere nada: idempotente.
    (
        df.dropDuplicates(["autorizacao_id"])
        .withColumn("batch_id", F.lit(batch_id))
        .createOrReplaceTempView("negadas")
    )
    s.sql(
        f"MERGE INTO {TABELA} t USING negadas s ON t.autorizacao_id = s.autorizacao_id "
        "WHEN NOT MATCHED THEN INSERT *"
    )


@dp.append_flow(target="notif_autorizacao_negada_sink")
def autorizacoes_negadas():
    return (
        spark.readStream.table("silver_autorizacao_eventos")
        .where("status = 'negada'")
        .select("autorizacao_id", "prestador_id", "procedimento", F.col("event_ts").alias("negada_em"))
    )

# --- Equivalente em Structured Streaming ---
# O sink é o próprio foreachBatch. A diferença é que, na mão, você cuida do checkpoint:
#
# (eventos_validos.where("status = 'negada'")
#     .writeStream
#     .foreachBatch(notif_autorizacao_negada_sink)
#     .option("checkpointLocation", "/Volumes/academydb/<aluno>/checkpoints/notif")
#     .trigger(availableNow=True)
#     .start())
