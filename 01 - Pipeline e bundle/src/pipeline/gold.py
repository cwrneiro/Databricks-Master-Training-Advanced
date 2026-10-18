from pyspark import pipelines as dp
from pyspark.sql import functions as F

VALIDO = "autorizacao_id IS NOT NULL AND status IN ('solicitada', 'em_analise', 'aprovada', 'negada')"


@dp.materialized_view(comment="KPIs por procedimento e prestador: volume, taxa de negativa e tempo médio de aprovação.")
def gold_kpi_autorizacoes():
    por_autorizacao = (
        spark.read.table("bronze_autorizacao_eventos")
        .where(VALIDO)
        .groupBy("autorizacao_id", "procedimento", "prestador_id")
        .agg(
            F.max_by("status", "event_ts").alias("status"),
            F.min(F.when(F.col("status") == "solicitada", F.col("event_ts"))).alias("solicitada_em"),
            F.max(F.when(F.col("status") == "aprovada", F.col("event_ts"))).alias("aprovada_em"),
        )
    )
    return por_autorizacao.groupBy("procedimento", "prestador_id").agg(
        F.count("*").alias("autorizacoes"),
        F.sum((F.col("status") == "aprovada").cast("int")).alias("aprovadas"),
        F.sum((F.col("status") == "negada").cast("int")).alias("negadas"),
        F.round(F.avg((F.col("status") == "negada").cast("int")), 4).alias("taxa_negativa"),
        F.round(
            F.avg((F.unix_timestamp("aprovada_em") - F.unix_timestamp("solicitada_em")) / 3600), 1
        ).alias("tempo_medio_aprovacao_horas"),
    )

# --- Equivalente em Structured Streaming ---
# Não há um equivalente direto: um agregado sobre a base inteira, refeito a cada lote, é um
# job batch. Na mão, você recalcula e sobrescreve a tabela a cada execução:
#
# kpis.write.mode("overwrite").saveAsTable("academydb.<aluno>.gold_kpi_autorizacoes")
#
# A materialized view faz isso por você e, quando consegue, atualiza só o que mudou.
