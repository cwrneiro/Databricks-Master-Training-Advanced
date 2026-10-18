# ADR-0001: SDP como pipeline principal, Structured Streaming como "por baixo do capô"

Status: aceito (2026-10-15), revisto em 2026-10-16

## Contexto
O doc original pede Delta, CDF, Structured Streaming, `foreachBatch` e MERGE, com ETLs que aceitam retry sem duplicar. O público são devs que nunca usaram Spark.

## Decisão
O módulo 1 é construído em Lakeflow Spark Declarative Pipelines (Python): Auto Loader, expectations, `AUTO CDC` (SCD1 no lugar do MERGE, SCD2 como desafio), materialized view e `@dp.foreach_batch_sink`. O equivalente em Structured Streaming de cada peça fica como comentário logo abaixo do bloco SDP correspondente, no próprio código do pipeline.

Revisão (2026-10-16): os 2 blocos executáveis em SS (restart pelo checkpoint e `foreachBatch` + MERGE) saíram. Isso tirou do workshop o único motivo para ter um cluster all-purpose.

## Consequências
- Menos código para o aluno. Checkpoints e idempotência ficam por conta da plataforma, e os fundamentos continuam visíveis, lado a lado com o código que roda.
- `foreach_batch_sink` é Public Preview e só existe em Python, por isso o SDP é todo em Python.
- Tudo roda em serverless (pipeline, jobs e notebooks). Não há cluster all-purpose.
