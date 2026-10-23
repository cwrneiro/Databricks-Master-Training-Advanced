from pyspark import pipelines as dp
from pyspark.sql import functions as F

# Eventos inválidos não param o pipeline: na bronze, as expectations só registram as violações (warn).
REGRAS = {
    "autorizacao_id_presente": "autorizacao_id IS NOT NULL",
    "status_no_dominio": "status IN ('solicitada', 'em_analise', 'aprovada', 'negada')",
}


@dp.table(comment="Eventos de autorização como chegaram do gerador, um por linha, inválidos incluídos.")
@dp.expect_all(REGRAS)
def bronze_autorizacao_eventos():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .schema(
            "event_id STRING, autorizacao_id STRING, beneficiario_id STRING, prestador_id STRING, "
            "procedimento STRING, status STRING, event_ts TIMESTAMP"
        )
        .load(spark.conf.get("eventos_path"))
        .withColumn("arquivo", F.col("_metadata.file_path"))
        .withColumn("ingerido_em", F.current_timestamp())
    )

# --- Equivalente em Structured Streaming ---
# O Auto Loader lembra quais arquivos já leu num checkpoint. Na mão, você escolhe onde fica o
# checkpoint e dispara o stream; as expectations viram contagens que você mesmo calcula.
#
# (spark.readStream.format("cloudFiles")
#     .option("cloudFiles.format", "json")
#     .schema(...)
#     .load("/Volumes/academydb/shared/raw/autorizacao_eventos")
#     .writeStream
#     .option("checkpointLocation", "/Volumes/academydb/<aluno>/checkpoints/bronze")
#     .trigger(availableNow=True)
#     .toTable("academydb.<aluno>.bronze_autorizacao_eventos"))
