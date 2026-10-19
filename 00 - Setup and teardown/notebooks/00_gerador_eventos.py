# Databricks notebook source
# MAGIC %md
# MAGIC # Gerador de eventos de autorização (líder)
# MAGIC
# MAGIC Task do job do gerador, criado pelo setup: cron a cada 10 min, um lote por run. Escreve eventos JSON (um por linha) em `academydb.shared.raw/autorizacao_eventos/`. Seed fixa: os números são sempre os mesmos.
# MAGIC
# MAGIC - Cada run escreve o próximo dos 42 lotes, sempre em **modo caos** (duplicatas e eventos atrasados) e com alguns eventos inválidos para as expectations.
# MAGIC - Depois do lote 42, o notebook pausa o schedule do próprio job (widget `job_id = {{job.id}}`). Rodado à mão, sem `job_id`, só escreve o lote.

# COMMAND ----------

dbutils.widgets.text("catalog", "academydb")
dbutils.widgets.text("schema", "shared")
dbutils.widgets.text("volume", "raw")
dbutils.widgets.text("job_id", "")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
volume = dbutils.widgets.get("volume")
job_id = dbutils.widgets.get("job_id")

# COMMAND ----------

import json
import os
import sys

sys.path.append(os.path.abspath("../data/src"))
from generator import N_BATCHES, batches, generate_events

path = f"/Volumes/{catalog}/{schema}/{volume}/autorizacao_eventos"
os.makedirs(path, exist_ok=True)

lotes = batches(generate_events())
k = len([f for f in os.listdir(path) if f.startswith("lote_") and f.endswith(".json")]) + 1

if k <= N_BATCHES:
    with open(f"{path}/lote_{k:03d}.json", "w") as f:
        f.writelines(json.dumps(e) + "\n" for e in lotes[k - 1])
    print(f"lote {k}/{N_BATCHES}: {len(lotes[k - 1])} eventos")
else:
    print(f"Os {N_BATCHES} lotes já foram escritos em {path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Checkpoint de validação

# COMMAND ----------

if k <= N_BATCHES:
    with open(f"{path}/lote_{k:03d}.json") as f:
        assert sum(1 for _ in f) == len(lotes[k - 1]), f"lote {k} incompleto"
    print("✅ Lote escrito e conferido em", path)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pausa o schedule depois do último lote

# COMMAND ----------

if job_id and k >= N_BATCHES:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.jobs import JobSettings, PauseStatus

    w = WorkspaceClient()
    schedule = w.jobs.get(int(job_id)).settings.schedule
    schedule.pause_status = PauseStatus.PAUSED
    w.jobs.update(int(job_id), new_settings=JobSettings(schedule=schedule))
    print("Schedule pausado:", w.jobs.get(int(job_id)).settings.schedule.pause_status)
