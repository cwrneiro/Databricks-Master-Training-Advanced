# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Teardown do workshop (líder)
# MAGIC
# MAGIC Remove o que a preparação e os alunos criaram. **Idempotente**: o que já não existe é ignorado, então é seguro rodar de novo. Rode como **administrador de conta**.
# MAGIC
# MAGIC Os alunos são descobertos pelos schemas que o bundle criou (comentário `Schema do aluno <aluno> no workshop Vida+ Saúde`), tanto `dev_<usuario>_<aluno>` quanto `<aluno>`. Nada fora disso é tocado.
# MAGIC
# MAGIC | Alternador | Remove | Padrão |
# MAGIC |---|---|---|
# MAGIC | 1. Recursos dos alunos | apps do módulo 4 `vida-saude-<aluno>`, apps do agente `agent-bricks-<aluno>` (Runtime Store antes do app, depois as lojas de memória e sessões e o experimento de tracing), pipelines e jobs de dev e prod, synced table do módulo 2, schemas de dev e prod com `CASCADE` (tabelas, streaming tables órfãs, model service) | `true` |
# MAGIC | 2. Recursos compartilhados | job do gerador, endpoints de AI Search (com todos os índices), projeto Lakebase (com purge), schema `shared` | `true` |
# MAGIC | 3. Grupo | grupo `edia_alunos` (e os grants dele) e o `USE CATALOG` de `account users` | `true` |
# MAGIC | 4. Catálogo | `DROP CATALOG academydb CASCADE` | **`false`** |
# MAGIC
# MAGIC ⚠️ **REMOVER CATÁLOGO** apaga tudo o que está em `academydb`, inclusive o que não é do workshop. Ligue só se o catálogo foi criado para o workshop.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Parâmetros

# COMMAND ----------

dbutils.widgets.dropdown("delete_alunos", "true", ["true", "false"], "1. Excluir recursos dos alunos")
dbutils.widgets.dropdown("delete_compartilhados", "true", ["true", "false"], "2. Excluir recursos compartilhados")
dbutils.widgets.dropdown("delete_group", "true", ["true", "false"], "3. Excluir grupo do workshop")
dbutils.widgets.dropdown("delete_catalog", "false", ["true", "false"], "4. REMOVER CATÁLOGO (DESTRUTIVO)")

# COMMAND ----------

import re

import yaml
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Mesmos nomes da preparação.
CATALOG = "academydb"
SHARED = f"{CATALOG}.shared"
GROUP = "edia_alunos"
JOB_GERADOR = "edia_gerador_eventos"
LAKEBASE = "edia-workshop"
VS_PREFIX = "edia-ai-search-"

DELETE_ALUNOS = dbutils.widgets.get("delete_alunos") == "true"
DELETE_COMPARTILHADOS = dbutils.widgets.get("delete_compartilhados") == "true"
DELETE_GROUP = dbutils.widgets.get("delete_group") == "true"
DELETE_CATALOG = dbutils.widgets.get("delete_catalog") == "true"

OK, NO, ERR, NA = "✅", "❌", "⚠️", "➖"


def api(method, path, **kw):
    return w.api_client.do(method, path, **kw)


def ausente(e):
    return "NotFound" in type(e).__name__ or "404" in str(e) or "does not exist" in str(e).lower()


def api_get_or_none(path, **kw):
    try:
        return api("GET", path, **kw)
    except Exception as e:
        if ausente(e):
            return None
        raise


def delete(path, label, method="DELETE", **kw):
    """Apaga e reporta; recurso já ausente conta como removido."""
    try:
        api(method, path, **kw)
        print(f"{OK} {label} excluído.")
    except Exception as e:
        print(f"{OK} {label} já ausente." if ausente(e) else f"{NO} {label}: {str(e)[:200]}")


def acct_scim(method, path, **kw):
    return api(method, f"/api/2.0/account/scim/v2{path}", **kw)


def paginate(path, key, **query):
    tok = None
    while True:
        r = api("GET", path, query={**query, **({"page_token": tok} if tok else {})})
        yield from r.get(key, [])
        tok = r.get("next_page_token")
        if not tok:
            return


# Schemas criados pelos bundles dos alunos: {schema: aluno}.
_COMMENT = re.compile(r"^Schema do aluno (\S+) no workshop")
SCHEMAS_ALUNOS = {}
if api_get_or_none(f"/api/2.1/unity-catalog/catalogs/{CATALOG}"):
    for s in w.schemas.list(catalog_name=CATALOG):
        m = _COMMENT.match(s.comment or "")
        if m:
            SCHEMAS_ALUNOS[s.name] = m.group(1)
ALUNOS = sorted(set(SCHEMAS_ALUNOS.values()))
# Nome dos jobs e pipelines do bundle: autorizacoes_<aluno>, com o prefixo [dev <usuario>] em dev.
_RECURSO_ALUNO = re.compile(r"^(\[dev [^\]]+\] )?autorizacoes_(?P<aluno>.+)$")


def do_aluno(name):
    m = _RECURSO_ALUNO.match(name or "")
    return bool(m) and m.group("aluno") in ALUNOS


def vs_endpoints():
    return [e["name"] for e in paginate("/api/2.0/vector-search/endpoints", "endpoints") if e["name"].startswith(VS_PREFIX)]


print(f"Alunos encontrados ({len(ALUNOS)}): {', '.join(ALUNOS) or '—'}")
print(f"Schemas de aluno: {', '.join(sorted(SCHEMAS_ALUNOS)) or '—'}")
print(f"1. alunos={DELETE_ALUNOS}  2. compartilhados={DELETE_COMPARTILHADOS}  3. grupo={DELETE_GROUP}  "
      f"4. CATÁLOGO={DELETE_CATALOG}{'  ⚠️ DESTRUTIVO' if DELETE_CATALOG else ''}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Teardown (idempotente)

# COMMAND ----------

# --- 2a. Apps do agente (ADR-0006) -------------------------------------------
# Mesma ordem do `agentbricks deployments delete`: o Runtime Store sai antes do app, porque apagar o store
# depende do SP do app. O agentbricks não apaga as lojas nem o experimento, e chama o CLI `databricks`, que
# não roda num notebook; por isso a sequência é feita aqui pela API. Os IDs vêm do app.yaml do deploy.
def delete_agent_app(name):
    app = api_get_or_none(f"/api/2.0/apps/{name}")
    if not app:
        print(f"{OK} App '{name}' já ausente.")
        return
    env = {}
    src = (app.get("active_deployment") or {}).get("source_code_path")
    try:
        with open(f"{src if src.startswith('/Workspace') else '/Workspace' + src}/app.yaml") as f:
            env = {e["name"]: e.get("value") for e in (yaml.safe_load(f).get("env") or [])}
    except Exception as e:
        print(f"  {ERR} app.yaml de '{name}' ilegível ({type(e).__name__}); lojas e experimento ficam.")
    delete(f"/api/2.0/agents/runtime-stores/{name}", f"Runtime Store '{name}'")
    delete(f"/api/2.0/apps/{name}", f"App '{name}'")
    if env.get("AGENT_MEMORY_STORE"):
        delete(f"/api/2.0/agents/memory-stores/{env['AGENT_MEMORY_STORE']}", f"  loja de memória '{env['AGENT_MEMORY_STORE']}'")
    if env.get("AGENT_SESSION_STORE"):
        delete(f"/api/2.0/agents/session-stores/{env['AGENT_SESSION_STORE']}", f"  loja de sessões '{env['AGENT_SESSION_STORE']}'")
    if env.get("MLFLOW_EXPERIMENT_ID"):
        delete("/api/2.0/mlflow/experiments/delete", f"  experimento {env['MLFLOW_EXPERIMENT_ID']}", method="POST",
               body={"experiment_id": env["MLFLOW_EXPERIMENT_ID"]})


if DELETE_ALUNOS:
    for _aluno in ALUNOS:
        # O app do módulo 4 sai antes: ele chama o app do agente.
        delete(f"/api/2.0/apps/vida-saude-{_aluno}", f"App 'vida-saude-{_aluno}'")
        delete_agent_app(f"agent-bricks-{_aluno}")

    # --- 2b. Pipelines e jobs de dev e prod de cada aluno ---------------------
    for _p in paginate("/api/2.0/pipelines", "statuses", filter="name LIKE '%autorizacoes_%'"):
        if do_aluno(_p.get("name")):
            delete(f"/api/2.0/pipelines/{_p['pipeline_id']}", f"Pipeline '{_p['name']}'")
    for _j in w.jobs.list():
        if do_aluno(_j.settings.name):
            delete("/api/2.2/jobs/delete", f"Job '{_j.settings.name}'", method="POST", body={"job_id": _j.job_id})
    # Synced table do módulo 2: apagá-la apaga também o pipeline de sync dela.
    for _s in sorted(SCHEMAS_ALUNOS):
        delete(f"/api/2.0/postgres/synced_tables/{CATALOG}.{_s}.autorizacao_status",
               f"Synced table '{CATALOG}.{_s}.autorizacao_status'")
else:
    print(f"{NA} Recursos dos alunos mantidos.")

# COMMAND ----------

# --- 2c. AI Search: índices (dos alunos e de aquecimento) e endpoints ---------
if DELETE_COMPARTILHADOS:
    for _ep in vs_endpoints():
        for _idx in paginate("/api/2.0/vector-search/indexes", "vector_indexes", endpoint_name=_ep):
            delete(f"/api/2.0/vector-search/indexes/{_idx['name']}", f"Índice '{_idx['name']}'")
        delete(f"/api/2.0/vector-search/endpoints/{_ep}", f"Endpoint de AI Search '{_ep}'")
else:
    print(f"{NA} Endpoints de AI Search mantidos.")

# --- 2d. Schemas dos alunos (CASCADE: apagar o pipeline não apaga as streaming tables) ---
if DELETE_ALUNOS:
    for _s in sorted(SCHEMAS_ALUNOS):
        try:
            spark.sql(f"DROP SCHEMA IF EXISTS {CATALOG}.`{_s}` CASCADE")
            print(f"{OK} Schema '{CATALOG}.{_s}' removido (CASCADE).")
        except Exception as e:
            print(f"{NO} Schema '{CATALOG}.{_s}': {str(e)[:200]}")

# --- 2e. Gerador, Lakebase e schema compartilhado ----------------------------
if DELETE_COMPARTILHADOS:
    for _j in w.jobs.list(name=JOB_GERADOR):
        delete("/api/2.2/jobs/delete", f"Job '{JOB_GERADOR}'", method="POST", body={"job_id": _j.job_id})
    # purge: sem ele o projeto fica 7 dias em soft delete e bloqueia o nome na próxima preparação.
    delete(f"/api/2.0/postgres/projects/{LAKEBASE}", f"Projeto Lakebase '{LAKEBASE}'", query={"purge": "true"})
    try:
        spark.sql(f"DROP SCHEMA IF EXISTS {SHARED} CASCADE")
        print(f"{OK} Schema '{SHARED}' removido (CASCADE: Volume raw, eventos e PDFs).")
    except Exception as e:
        print(f"{NO} Schema '{SHARED}': {str(e)[:200]}")

# COMMAND ----------

# --- 2f. Grupo (apagar o grupo revoga os grants dele) -------------------------
if DELETE_GROUP:
    if not DELETE_CATALOG:
        try:
            spark.sql(f"REVOKE USE CATALOG ON CATALOG {CATALOG} FROM `account users`")
            print(f"{OK} USE CATALOG de account users revogado.")
        except Exception:
            print(f"{NA} Revogação de account users omitida (catálogo ou grant já ausente).")
    _found = acct_scim("GET", "/Groups", query={"filter": f'displayName eq "{GROUP}"'}).get("Resources") or []
    if _found:
        try:
            api("DELETE", f"/api/2.0/preview/permissionassignments/principals/{_found[0]['id']}")
        except Exception:
            pass  # a atribuição pode já ter saído
        delete(f"/api/2.0/account/scim/v2/Groups/{_found[0]['id']}", f"Grupo de conta '{GROUP}'")
    else:
        print(f"{OK} Grupo de conta '{GROUP}' já ausente.")
else:
    print(f"{NA} Grupo '{GROUP}' mantido. Os grants dele continuam.")

# --- 2g. Catálogo (DESTRUTIVO, opt-in) ---------------------------------------
if DELETE_CATALOG:
    try:
        spark.sql(f"DROP CATALOG IF EXISTS {CATALOG} CASCADE")
        print(f"{OK} Catálogo '{CATALOG}' removido (CASCADE).")
    except Exception as e:
        print(f"{NO} Catálogo '{CATALOG}': {str(e)[:200]}")
else:
    print(f"{NA} Catálogo '{CATALOG}' mantido (REMOVER=false).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Relatório final
# MAGIC ✅ = removido · ➖ = mantido por escolha · ❌ = ainda presente · ⚠️ = não deu para verificar.

# COMMAND ----------

import time

import pandas as pd


def _row(label, requested, fn, wait_s=0):
    """`wait_s`: apps e projetos Lakebase somem alguns minutos depois do DELETE."""
    if not requested:
        return {"Item": label, "Status": NA, "Nota": "mantido"}
    try:
        left = fn()
        deadline = time.time() + wait_s
        while left and time.time() < deadline:
            time.sleep(15)
            left = fn()
    except Exception as e:
        return {"Item": label, "Status": ERR, "Nota": f"{type(e).__name__}: {str(e)[:100]}"}
    return {"Item": label, "Status": NO if left else OK, "Nota": ", ".join(map(str, left)) if left else "removido"}


_catalog = bool(api_get_or_none(f"/api/2.1/unity-catalog/catalogs/{CATALOG}"))
_schemas = {s.name for s in w.schemas.list(catalog_name=CATALOG)} if _catalog else set()
_group = acct_scim("GET", "/Groups", query={"filter": f'displayName eq "{GROUP}"'}).get("Resources") or []

report = [
    _row("Apps do módulo 4 dos alunos", DELETE_ALUNOS,
         lambda: [a for a in (f"vida-saude-{x}" for x in ALUNOS) if api_get_or_none(f"/api/2.0/apps/{a}")], 300),
    _row("Apps do agente dos alunos", DELETE_ALUNOS,
         lambda: [a for a in (f"agent-bricks-{x}" for x in ALUNOS) if api_get_or_none(f"/api/2.0/apps/{a}")], 300),
    _row("Pipelines dos alunos", DELETE_ALUNOS,
         lambda: [p["name"] for p in paginate("/api/2.0/pipelines", "statuses", filter="name LIKE '%autorizacoes_%'")
                  if do_aluno(p.get("name"))]),
    _row("Jobs dos alunos", DELETE_ALUNOS, lambda: [j.settings.name for j in w.jobs.list() if do_aluno(j.settings.name)]),
    _row("Schemas dos alunos", DELETE_ALUNOS, lambda: sorted(_schemas & set(SCHEMAS_ALUNOS))),
    _row(f"Job '{JOB_GERADOR}'", DELETE_COMPARTILHADOS, lambda: [j.job_id for j in w.jobs.list(name=JOB_GERADOR)]),
    _row("Endpoints de AI Search", DELETE_COMPARTILHADOS, vs_endpoints),
    _row(f"Projeto Lakebase '{LAKEBASE}'", DELETE_COMPARTILHADOS,
         lambda: [LAKEBASE] if api_get_or_none(f"/api/2.0/postgres/projects/{LAKEBASE}") else [], 300),
    _row(f"Schema '{SHARED}'", DELETE_COMPARTILHADOS, lambda: ["shared"] if "shared" in _schemas else []),
    _row(f"Grupo '{GROUP}'", DELETE_GROUP, lambda: [GROUP] if _group else []),
    _row(f"Catálogo '{CATALOG}'", DELETE_CATALOG, lambda: [CATALOG] if _catalog else []),
]

_done = all(r["Status"] in (OK, NA) for r in report)
print("GERAL:", "✅ Teardown concluído: tudo o que foi pedido foi removido." if _done
      else "❌ Alguns itens ainda estão presentes: veja abaixo.")
display(pd.DataFrame(report, columns=["Item", "Status", "Nota"]))
