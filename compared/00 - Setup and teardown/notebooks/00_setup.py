# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # Setup e checagem do workshop (líder)
# MAGIC Rode como **administrador de conta**, no **serverless**, a partir da Git folder do repo (o notebook lê `data/` e cria o job do gerador apontando para `00_gerador_eventos`). Faz tudo de uma vez:
# MAGIC 1. **Prepara**: grupo `edia_alunos`, catálogo `academydb`, schema `academydb.shared` com o Volume `raw` (PDFs em `docs/`), job do gerador (pausado), projeto Lakebase, `ceil(N/40)` endpoints de AI Search aquecidos e os grants (ADR-0002).
# MAGIC 2. **Checa**: relatório ✅/❌ com tudo o que o dia usa (serverless, Lakebase, AI Search, Genie, Apps, Agent Runtime, model service, grants do `system.ai`, web terminal).
# MAGIC
# MAGIC **É idempotente**: seguro rodar de novo. Não cria schemas de aluno (o bundle de cada aluno cria o dele) nem cluster.
# MAGIC
# MAGIC > ⚠️ Rode as **duas primeiras células** para exibir os widgets, escolha os alunos e use **Run all**. O veredito fica na seção **5. Relatório final**. O aquecimento dos endpoints de AI Search leva ~15 min: se só ele estiver ❌, rode o notebook de novo depois disso.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Parâmetros

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

_PICK = "(escolha os alunos)"
_users = sorted({u.user_name for u in w.users.list(attributes="userName") if u.user_name})
muitos_usuarios = len(_users) + 1 > 1024
if muitos_usuarios:
    print("⚠️  Mais usuários do que o widget suporta: preencha alunos_manual na célula seguinte.")
print(f"{len(_users)} usuário(s) no workspace.")

# COMMAND ----------

dbutils.widgets.dropdown("create_catalog", "true", ["true", "false"], "1. Criar catálogo")
if not muitos_usuarios:
    dbutils.widgets.multiselect("alunos", _PICK, [_PICK] + _users, "2. Alunos (usuários do workspace)")
alunos_manual = [
    # preencha com os e-mails dos alunos só se a célula acima pedir
]

# COMMAND ----------

import math

CATALOG = "academydb"
SHARED = f"{CATALOG}.shared"
VOLUME = f"{SHARED}.raw"
VOLUME_PATH = f"/Volumes/{CATALOG}/shared/raw"
GROUP = "edia_alunos"
JOB_GERADOR = "edia_gerador_eventos"
LAKEBASE = "edia-workshop"
LAKEBASE_ROLES = f"/api/2.0/postgres/projects/{LAKEBASE}/branches/production/roles"
VS_PREFIX = "edia-ai-search-"
ALUNOS_POR_ENDPOINT = 40  # limite de 50 índices por endpoint, com folga
EMBEDDING = "databricks-qwen3-embedding-0-6b"
MODELO = "system.ai.claude-sonnet-4-5"
AGENTBRICKS = "databricks-agentbricks==0.5.1"

CREATE_CATALOG = dbutils.widgets.get("create_catalog") == "true"
ALUNOS = alunos_manual if muitos_usuarios else [
    a.strip() for a in dbutils.widgets.get("alunos").split(",") if a.strip() and a.strip() != _PICK]
if not ALUNOS:
    dbutils.notebook.exit("⏳ Escolha pelo menos um aluno no widget e rode 'Run all'.")

N_ENDPOINTS = math.ceil(len(ALUNOS) / ALUNOS_POR_ENDPOINT)
VS_ENDPOINTS = [f"{VS_PREFIX}{i}" for i in range(1, N_ENDPOINTS + 1)]

_notebook = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
DATA = "/Workspace" + _notebook.rsplit("/", 2)[0] + "/data"  # 00 - Setup and teardown/data na Git folder
GERADOR_NOTEBOOK = _notebook.rsplit("/", 1)[0] + "/00_gerador_eventos"

print(f"Catálogo: {CATALOG} (criar={CREATE_CATALOG})  ·  Compartilhado: {VOLUME}")
print(f"Grupo: {GROUP}  ·  Job do gerador: {JOB_GERADOR}  ·  Lakebase: {LAKEBASE}")
print(f"AI Search: {', '.join(VS_ENDPOINTS)}  ·  Dados: {DATA}")
print(f"Alunos ({len(ALUNOS)}):", *[f"  - {a}" for a in ALUNOS], sep="\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Funções auxiliares

# COMMAND ----------

import re
import time
from urllib.parse import quote

OK, NO, ERR = "✅", "❌", "⚠️"


def sym(v):
    return OK if v is True else (NO if v is False else ERR)


def api(method, path, **kw):
    return w.api_client.do(method, path, **kw)


def api_get_or_none(path, **kw):
    """GET que devolve None em 404 (recurso ausente) e propaga o resto."""
    try:
        return api("GET", path, **kw)
    except Exception as e:
        if "NotFound" in type(e).__name__ or "404" in str(e) or "does not exist" in str(e).lower():
            return None
        raise


def acct_scim(method, path, **kw):
    return api(method, f"/api/2.0/account/scim/v2{path}", **kw)


def grant_with_retry(sql, attempts=5, delay=3):
    """Repete o grant enquanto o UC ainda não enxerga um grupo recém-criado."""
    for i in range(attempts):
        try:
            return spark.sql(sql)
        except Exception as e:
            if i < attempts - 1 and ("PRINCIPAL_DOES_NOT_EXIST" in str(e) or "Could not find principal" in str(e)):
                time.sleep(delay)
                continue
            raise


def uc_privs(kind, name, principal, effective=False):
    """Privilégios de um principal num securable do UC (diretos ou efetivos); None se ilegível."""
    path = "effective-permissions" if effective else "permissions"
    try:
        r = api("GET", f"/api/2.1/unity-catalog/{path}/{kind}/{quote(name, safe='')}", query={"principal": principal})
    except Exception:
        return None
    return {p["privilege"] if isinstance(p, dict) else p
            for pa in (r.get("privilege_assignments") or []) for p in (pa.get("privileges") or [])}


def uc_has(kind, name, principal, needed, effective=False):
    privs = uc_privs(kind, name, principal, effective)
    return None if privs is None else ("ALL_PRIVILEGES" in privs or set(needed) <= privs)


def acl_level(object_type, object_id, group):
    """Nível de permissão do grupo (ou de `users`) no ACL de um objeto do workspace."""
    try:
        acl = api("GET", f"/api/2.0/permissions/{object_type}/{object_id}").get("access_control_list") or []
    except Exception:
        return None
    return {p["permission_level"] for e in acl if e.get("group_name") in (group, "users")
            for p in (e.get("all_permissions") or [])}


def give_group(object_type, object_id, level):
    api("PATCH", f"/api/2.0/permissions/{object_type}/{object_id}",
        body={"access_control_list": [{"group_name": GROUP, "permission_level": level}]})


print("Funções auxiliares definidas.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Setup (idempotente)

# COMMAND ----------

# --- 3a. Grupo de CONTA (o UC só aceita grupos de conta nos grants) ----------
try:
    for _g in w.groups.list(filter=f'displayName eq "{GROUP}"'):
        _meta = w.groups.get(_g.id).meta
        if _meta and _meta.resource_type == "WorkspaceGroup":
            w.groups.delete(_g.id)
            print(f"  removido grupo local de workspace '{GROUP}' (id {_g.id}).")

    _found = acct_scim("GET", "/Groups", query={"filter": f'displayName eq "{GROUP}"'}).get("Resources") or []
    if _found:
        GROUP_ID = _found[0]["id"]
        print(f"{OK} Grupo de conta '{GROUP}' existe (id {GROUP_ID}).")
    else:
        GROUP_ID = acct_scim("POST", "/Groups", body={
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"], "displayName": GROUP})["id"]
        print(f"{OK} Grupo de conta '{GROUP}' criado (id {GROUP_ID}).")

    api("PUT", f"/api/2.0/preview/permissionassignments/principals/{GROUP_ID}", body={"permissions": ["USER"]})
    print(f"{OK} Grupo atribuído a este workspace.")

    _members = {m["value"] for m in (acct_scim("GET", f"/Groups/{GROUP_ID}").get("members") or [])}
    _to_add, ALUNOS_SEM_CONTA = [], []
    for _email in ALUNOS:
        _res = acct_scim("GET", "/Users", query={"filter": f'userName eq "{_email}"'}).get("Resources") or []
        if not _res:
            ALUNOS_SEM_CONTA.append(_email)
            print(f"  {ERR} não é usuário de conta, não dá para adicionar: {_email}")
        elif _res[0]["id"] not in _members:
            _to_add.append(_res[0]["id"])
    if _to_add:
        acct_scim("PATCH", f"/Groups/{GROUP_ID}", body={
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "add", "path": "members", "value": [{"value": u} for u in _to_add]}]})
    print(f"{OK} Membros: {len(_members)} já estavam, {len(_to_add)} adicionados.")

    # Direitos de workspace no grupo (a Genie precisa de Databricks SQL).
    _ws_gid = None
    for _ in range(6):
        _wsg = list(w.groups.list(filter=f'displayName eq "{GROUP}"', attributes="id"))
        if _wsg:
            _ws_gid = _wsg[0].id
            break
        time.sleep(3)
    if _ws_gid:
        api("PATCH", f"/api/2.0/preview/scim/v2/Groups/{_ws_gid}", body={
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [{"op": "add", "path": "entitlements",
                            "value": [{"value": "workspace-access"}, {"value": "databricks-sql-access"}]}]})
        print(f"{OK} Direitos do grupo: workspace-access, databricks-sql-access.")
    else:
        print(f"{ERR} Grupo ainda não visível no SCIM do workspace; rode de novo para aplicar os direitos.")
except Exception as e:
    if any(k in str(e) for k in ("403", "PERMISSION_DENIED")) or "not authorized" in str(e).lower():
        raise RuntimeError(
            "Criar o grupo de conta exige ADMIN DE CONTA. Rode como admin de conta, ou crie o grupo "
            f"'{GROUP}' no console da conta, atribua ao workspace, adicione os alunos e rode de novo.") from e
    raise

# COMMAND ----------

# --- 3b. Catálogo, schema compartilhado e Volume ----------------------------
try:
    w.catalogs.get(CATALOG)
    print(f"{OK} Catálogo '{CATALOG}' existe.")
except Exception as _e:
    if "NotFound" not in type(_e).__name__ and "404" not in str(_e):
        raise
    if not CREATE_CATALOG:
        raise RuntimeError(f"Catálogo '{CATALOG}' não existe e 'Criar catálogo' = false.")
    try:
        spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
        print(f"{OK} Catálogo '{CATALOG}' criado.")
    except Exception as e:
        if any(k in str(e).lower() for k in ("managed location", "storage location", "default storage",
                                              "location is required", "storage root")):
            raise RuntimeError(
                f"O metastore não tem storage padrão. Crie o catálogo à mão (Catalog → Create catalog), ou:\n"
                f"    CREATE CATALOG {CATALOG} MANAGED LOCATION 's3://<bucket>/<path>';\n"
                f"e rode de novo com 'Criar catálogo' = false.") from e
        raise

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SHARED} COMMENT 'Workshop Vida+ Saúde: dados compartilhados (só leitura para os alunos)'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {VOLUME} COMMENT 'Eventos do gerador (autorizacao_eventos/) e PDFs (docs/)'")
print(f"{OK} {SHARED} e Volume {VOLUME} prontos.")

# PDFs da operadora (versionados em data/docs/) → Volume.
import os
import shutil

os.makedirs(f"{VOLUME_PATH}/docs", exist_ok=True)
os.makedirs(f"{VOLUME_PATH}/autorizacao_eventos", exist_ok=True)
PDFS = sorted(f for f in os.listdir(f"{DATA}/docs") if f.endswith(".pdf"))
for _pdf in PDFS:
    shutil.copyfile(f"{DATA}/docs/{_pdf}", f"{VOLUME_PATH}/docs/{_pdf}")
print(f"{OK} {len(PDFS)} PDFs copiados para {VOLUME_PATH}/docs/.")

# COMMAND ----------

# --- 3c. Grants (ADR-0002) ----------------------------------------------------
GRANTS = [
    f"GRANT USE CATALOG, CREATE SCHEMA ON CATALOG {CATALOG} TO `{GROUP}`",
    f"GRANT USE SCHEMA, READ VOLUME ON SCHEMA {SHARED} TO `{GROUP}`",
    f"GRANT USE SCHEMA, EXECUTE ON SCHEMA system.ai TO `{GROUP}`",
    # Os SPs dos apps nascem fora do grupo; sozinho, USE CATALOG não dá acesso a nada.
    f"GRANT USE CATALOG ON CATALOG {CATALOG} TO `account users`",
]
for _sql in GRANTS:
    try:
        grant_with_retry(_sql)
        print(f"{OK} {_sql}")
    except Exception as e:
        print(f"{NO} {_sql}\n     {str(e)[:200]}")

# COMMAND ----------

# --- 3d. Job do gerador (criado PAUSADO: o líder liga na abertura) -----------
JOB_SETTINGS = {
    "name": JOB_GERADOR,
    "description": "Gerador do workshop Vida+ Saúde: um lote de eventos a cada 10 min, 42 lotes. Pausa sozinho no fim.",
    "max_concurrent_runs": 1,
    "schedule": {"quartz_cron_expression": "0 0/10 * * * ?", "timezone_id": "America/Sao_Paulo",
                 "pause_status": "PAUSED"},
    "tasks": [{"task_key": "gerador", "notebook_task": {
        "notebook_path": GERADOR_NOTEBOOK, "source": "WORKSPACE",
        "base_parameters": {"catalog": CATALOG, "schema": "shared", "volume": "raw", "job_id": "{{job.id}}"}}}],
}
_job = next(iter(w.jobs.list(name=JOB_GERADOR)), None)
if _job:
    # Mantém o estado do schedule (o líder pode já ter ligado).
    JOB_SETTINGS["schedule"]["pause_status"] = api("GET", "/api/2.2/jobs/get", query={"job_id": _job.job_id}
                                                   )["settings"]["schedule"]["pause_status"]
    api("POST", "/api/2.2/jobs/reset", body={"job_id": _job.job_id, "new_settings": JOB_SETTINGS})
    JOB_ID = _job.job_id
    print(f"{OK} Job '{JOB_GERADOR}' atualizado (id {JOB_ID}, schedule {JOB_SETTINGS['schedule']['pause_status']}).")
else:
    JOB_ID = api("POST", "/api/2.2/jobs/create", body=JOB_SETTINGS)["job_id"]
    print(f"{OK} Job '{JOB_GERADOR}' criado (id {JOB_ID}), schedule PAUSADO.")

# COMMAND ----------

# --- 3e. Projeto Lakebase (um para a turma, um schema Postgres por aluno) ----
_proj = api_get_or_none(f"/api/2.0/postgres/projects/{LAKEBASE}")
if _proj and _proj.get("delete_time"):
    # Apagado sem purge: o nome fica preso até o purge_time e não dá para criar outro.
    print(f"{NO} Projeto Lakebase '{LAKEBASE}' está em soft delete (purge em {_proj.get('purge_time')}). "
          f"Restaure com `databricks postgres undelete-project projects/{LAKEBASE}` ou apague de vez com "
          f"`databricks postgres delete-project projects/{LAKEBASE} --purge` e rode de novo.")
    _proj = None
elif _proj:
    print(f"{OK} Projeto Lakebase '{LAKEBASE}' existe.")
else:
    api("POST", "/api/2.0/postgres/projects", query={"project_id": LAKEBASE},
        body={"spec": {"display_name": LAKEBASE}})
    for _ in range(60):
        _proj = api_get_or_none(f"/api/2.0/postgres/projects/{LAKEBASE}")
        if _proj:
            break
        time.sleep(5)
    print(f"{OK if _proj else NO} Projeto Lakebase '{LAKEBASE}' {'criado' if _proj else 'não apareceu em 5 min'}.")
if _proj:
    # CAN_USE: o aluno cria a synced table no projeto (módulo 2).
    give_group("database-projects", LAKEBASE, "CAN_USE")
    print(f"{OK} CAN_USE no projeto Lakebase para {GROUP}.")
    # CAN_USE não dá login no Postgres: cada aluno precisa de um role OAuth (nasce só com LOGIN).
    _roles = {r["status"]["postgres_role"] for r in api("GET", LAKEBASE_ROLES).get("roles", [])}
    for _a in ALUNOS:
        if _a in _roles:
            continue
        api("POST", LAKEBASE_ROLES, query={"role_id": ("aluno-" + re.sub(r"[^a-z0-9]+", "-", _a.lower()))[:63].strip("-")},
            body={"spec": {"identity_type": "USER", "postgres_role": _a, "auth_method": "LAKEBASE_OAUTH_V1"}})
    print(f"{OK} Role OAuth no Postgres para os {len(ALUNOS)} aluno(s) ({len(set(ALUNOS) - _roles)} criados).")

# COMMAND ----------

# --- 3f. Endpoints de AI Search, cada um aquecido com um índice descartável ---
# O primeiro índice num endpoint novo leva ~15 min (spike 02); o índice de aquecimento paga esse tempo
# antes do workshop. Ele fica no endpoint até o teardown.
WARM_TABLE = f"{SHARED}.aquecimento"
spark.sql(f"""CREATE TABLE IF NOT EXISTS {WARM_TABLE} (id BIGINT NOT NULL, texto STRING)
              TBLPROPERTIES (delta.enableChangeDataFeed = true)
              COMMENT 'Fonte dos índices de aquecimento do AI Search (descartável)'""")
if spark.table(WARM_TABLE).count() == 0:
    spark.sql(f"INSERT INTO {WARM_TABLE} VALUES (1, 'Vida+ Saúde: índice de aquecimento')")

for _ep in VS_ENDPOINTS:
    if not api_get_or_none(f"/api/2.0/vector-search/endpoints/{_ep}"):
        api("POST", "/api/2.0/vector-search/endpoints", body={"name": _ep, "endpoint_type": "STANDARD"})
        print(f"  endpoint '{_ep}' criado, esperando ficar ONLINE…")
for _ in range(90):  # até ~30 min
    _states = {e: api("GET", f"/api/2.0/vector-search/endpoints/{e}")["endpoint_status"]["state"] for e in VS_ENDPOINTS}
    if all(s != "PROVISIONING" for s in _states.values()):
        break
    time.sleep(20)
print(f"  estados: {_states}")

for _ep in VS_ENDPOINTS:
    if _states[_ep] != "ONLINE":
        print(f"{NO} Endpoint '{_ep}' está {_states[_ep]}.")
        continue
    give_group("vector-search-endpoints", api("GET", f"/api/2.0/vector-search/endpoints/{_ep}")["id"], "CAN_USE")
    _idx = f"{WARM_TABLE}_{_ep.rsplit('-', 1)[1]}"
    if not api_get_or_none(f"/api/2.0/vector-search/indexes/{_idx}"):
        api("POST", "/api/2.0/vector-search/indexes", body={
            "name": _idx, "endpoint_name": _ep, "primary_key": "id", "index_type": "DELTA_SYNC",
            "delta_sync_index_spec": {"source_table": WARM_TABLE, "pipeline_type": "TRIGGERED",
                                      "embedding_source_columns": [{"name": "texto",
                                                                    "embedding_model_endpoint_name": EMBEDDING}]}})
        print(f"{OK} Endpoint '{_ep}' ONLINE, CAN_USE para {GROUP}, índice de aquecimento '{_idx}' criado.")
    else:
        print(f"{OK} Endpoint '{_ep}' ONLINE, CAN_USE para {GROUP}, índice de aquecimento já existe.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Checagem
# MAGIC | Item | Sinal | Usado em |
# MAGIC |---|---|---|
# MAGIC | Serverless | este notebook roda no serverless e um pipeline serverless passa no dry run | Módulo 1 (pipeline e job) |
# MAGIC | Lakebase | projeto existe, grupo com `CAN_USE` | Módulo 2 |
# MAGIC | AI Search e quota | endpoints `ONLINE`, aquecidos, grupo com `CAN_USE`, vagas para N índices, embedding pronto | Módulo 3 |
# MAGIC | `ai_parse_document` | extrai os blocos de texto de um PDF do Volume | Módulo 3 (trechos dos documentos) |
# MAGIC | Genie | API responde e há um SQL warehouse serverless que o grupo pode usar | Módulo 3 |
# MAGIC | Apps | API responde e cabem 2 apps por aluno no limite de 100 | Módulos 3 e 4 |
# MAGIC | Agent Runtime | API das lojas responde e o PyPI serve o `databricks-agentbricks` | Módulo 3 |
# MAGIC | Model service | `system.ai.claude-sonnet-4-5` responde pelo AI Gateway | Módulo 3 |
# MAGIC | Grants do `system.ai` | o grupo tem `USE CATALOG` no `system` e `USE SCHEMA` + `EXECUTE` efetivos no `system.ai` | Módulo 3 |
# MAGIC | Web terminal | setting `enableWebTerminal` ligado | Módulo 3 (deploy do agente) |

# COMMAND ----------

import json
import os
import urllib.request

import pandas as pd

time.sleep(5)  # grants recém-aplicados levam alguns segundos para aparecer


def check(fn):
    """Roda uma checagem; exceção vira ❌ com o motivo."""
    try:
        return fn(), ""
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:150]}"


def _grupo():
    _r = acct_scim("GET", "/Groups", query={"filter": f'displayName eq "{GROUP}"'}).get("Resources") or []
    if not _r:
        return False
    _ids = {m["value"] for m in (acct_scim("GET", f"/Groups/{_r[0]['id']}").get("members") or [])}
    _want = {(acct_scim("GET", "/Users", query={"filter": f'userName eq "{a}"'}).get("Resources") or [{}])[0].get("id")
             for a in ALUNOS}
    return None not in _want and _want <= _ids


def _volume():
    return (len([f for f in os.listdir(f"{VOLUME_PATH}/docs") if f.endswith(".pdf")]) == len(PDFS) > 0
            and uc_has("schema", SHARED, GROUP, {"USE_SCHEMA", "READ_VOLUME"}))


def _job():
    _s = api("GET", "/api/2.2/jobs/get", query={"job_id": JOB_ID})["settings"]
    return _s["tasks"][0]["notebook_task"]["notebook_path"] == GERADOR_NOTEBOOK


def _serverless():
    _dry = api("POST", "/api/2.0/pipelines", body={
        "name": "edia-checagem-dry-run", "serverless": True, "catalog": CATALOG, "schema": "shared",
        "dry_run": True, "libraries": [{"glob": {"include": f"{DATA}/src/**"}}]})
    return os.environ.get("IS_SERVERLESS") == "TRUE" and "effective_settings" in _dry


def _lakebase():
    _p = api_get_or_none(f"/api/2.0/postgres/projects/{LAKEBASE}")
    if not _p or _p.get("delete_time"):
        return False
    _roles = {r["status"]["postgres_role"] for r in api("GET", LAKEBASE_ROLES).get("roles", [])}
    return set(ALUNOS) <= _roles and bool((acl_level("database-projects", LAKEBASE, GROUP) or set()) & {"CAN_USE", "CAN_MANAGE"})


def _ai_search():
    for _ep in VS_ENDPOINTS:
        _e = api("GET", f"/api/2.0/vector-search/endpoints/{_ep}")
        if _e["endpoint_status"]["state"] != "ONLINE" or not (acl_level("vector-search-endpoints", _e["id"], GROUP) or set()) & {"CAN_USE", "CAN_MANAGE"}:
            return False
    return True


def _aquecido():
    return all((api_get_or_none(f"/api/2.0/vector-search/indexes/{WARM_TABLE}_{e.rsplit('-', 1)[1]}") or {})
               .get("status", {}).get("ready") for e in VS_ENDPOINTS)


def _quota_indices():
    _livres = sum(50 - (api("GET", f"/api/2.0/vector-search/endpoints/{e}").get("num_indexes") or 0) for e in VS_ENDPOINTS)
    return _livres >= len(ALUNOS)


def _embedding():
    return api("GET", f"/api/2.0/serving-endpoints/{EMBEDDING}")["state"]["ready"] == "READY"


def _parse_document():
    # O mesmo que o documentos.sql do módulo 3 faz, num PDF só.
    return spark.sql(f"""
        WITH d AS (
          SELECT ai_parse_document(content, map('version', '2.0')) AS parsed
          FROM read_files('{VOLUME_PATH}/docs/03_prazos_atendimento.pdf', format => 'binaryFile'))
        SELECT count(*) AS n
        FROM d, LATERAL variant_explode(parsed:document:elements) AS e
        WHERE e.value:type::string = 'text'""").first().n > 0


def _genie():
    api("GET", "/api/2.0/genie/spaces", query={"page_size": 1})
    _whs = [x for x in api("GET", "/api/2.0/sql/warehouses").get("warehouses", []) if x.get("enable_serverless_compute")]
    return any((acl_level("warehouses", x["id"], GROUP) or set()) & {"CAN_USE", "CAN_MONITOR", "CAN_MANAGE", "IS_OWNER"}
               for x in _whs)


def _apps():
    _n, _tok = 0, None
    while True:
        _r = api("GET", "/api/2.0/apps", query={"page_size": 100, **({"page_token": _tok} if _tok else {})})
        _n += len(_r.get("apps", []))
        _tok = _r.get("next_page_token")
        if not _tok:
            break
    global APPS_EXISTENTES
    APPS_EXISTENTES = _n
    return _n + 2 * len(ALUNOS) <= 100


def _agent_runtime():
    api("GET", "/api/2.0/agents/memory-stores", query={"page_size": 1})
    _name, _ver = AGENTBRICKS.split("==")
    return urllib.request.urlopen(f"https://pypi.org/pypi/{_name}/{_ver}/json", timeout=15).status == 200


def _modelo():
    _r = api("POST", "/ai-gateway/mlflow/v1/chat/completions",
             body={"model": MODELO, "messages": [{"role": "user", "content": "Responda só: ok"}], "max_tokens": 5})
    return bool(_r["choices"][0]["message"]["content"])


def _system_ai():
    return (uc_has("catalog", "system", GROUP, {"USE_CATALOG"}, effective=True) is True
            and uc_has("schema", "system.ai", GROUP, {"USE_SCHEMA", "EXECUTE"}, effective=True) is True)


def _web_terminal():
    return api("GET", "/api/2.0/workspace-conf", query={"keys": "enableWebTerminal"}).get("enableWebTerminal") == "true"


APPS_EXISTENTES = None
CHECKS = [
    (f"Grupo '{GROUP}' com os {len(ALUNOS)} aluno(s)", _grupo,
     "Alunos que não são usuários de conta não entram no grupo: adicione-os à conta."),
    (f"Catálogo '{CATALOG}': grupo com USE CATALOG + CREATE SCHEMA",
     lambda: uc_has("catalog", CATALOG, GROUP, {"USE_CATALOG", "CREATE_SCHEMA"}), ""),
    (f"Catálogo '{CATALOG}': account users com USE CATALOG",
     lambda: uc_has("catalog", CATALOG, "account users", {"USE_CATALOG"}), "Os SPs dos apps atravessam o catálogo com ele."),
    (f"Volume {VOLUME} com os PDFs e grupo com USE SCHEMA + READ VOLUME", _volume, ""),
    (f"Job do gerador '{JOB_GERADOR}' aponta para 00_gerador_eventos", _job, ""),
    ("Serverless (notebooks, jobs e pipelines)", _serverless, "Rode este notebook no serverless."),
    (f"Lakebase: projeto '{LAKEBASE}' com CAN_USE para o grupo e role Postgres para cada aluno", _lakebase, ""),
    (f"AI Search: {len(VS_ENDPOINTS)} endpoint(s) ONLINE com CAN_USE para o grupo", _ai_search, ""),
    ("AI Search: endpoints aquecidos (índice de aquecimento pronto)", _aquecido,
     "Leva ~15 min depois da criação do endpoint. Rode o notebook de novo."),
    (f"AI Search: vagas para {len(ALUNOS)} índice(s) (50 por endpoint)", _quota_indices, ""),
    (f"Embedding '{EMBEDDING}' pronto", _embedding, "Sem ele, o índice do módulo 3 não sincroniza."),
    ("ai_parse_document lê os PDFs do Volume", _parse_document,
     "Sem ele, o pipeline do módulo 3 não gera os trechos dos documentos."),
    ("Genie: API responde e há SQL warehouse serverless para o grupo", _genie,
     "Dê CAN_USE num warehouse serverless ao grupo (ou a users)."),
    ("Apps: cabem 2 por aluno no limite de 100 por workspace", _apps,
     "Peça aumento do limite de apps ou reduza a turma (~45 alunos sem aumento)."),
    (f"Agent Runtime: API das lojas responde e o PyPI serve {AGENTBRICKS}", _agent_runtime,
     "O agentbricks é Beta: o Agent Runtime pode precisar ser habilitado no workspace."),
    (f"Model service: {MODELO} responde pelo AI Gateway", _modelo, ""),
    ("Grants do system.ai em vigor (USE CATALOG system; USE SCHEMA + EXECUTE system.ai)", _system_ai,
     "Precisa de um admin do metastore para conceder no system.ai."),
    ("Web terminal habilitado (enableWebTerminal)", _web_terminal, "Settings → Compute → Web terminal."),
]

report = []
for _label, _fn, _hint in CHECKS:
    _v, _err = check(_fn)
    report.append({"Item": _label, "Status": sym(_v), "Detalhe": _err or ("" if _v is True else _hint)})
    print(sym(_v), _label, f"— {_err}" if _err else "")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Relatório final
# MAGIC Um ✅/❌ por item (⚠️ = não deu para determinar). Qualquer ❌/⚠️ deixa o ambiente **não pronto**.

# COMMAND ----------

_all_ok = all(r["Status"] == OK for r in report)
print("=" * 70)
if _all_ok:
    print(f"{OK} CHECKS COMPLETOS: ambiente pronto para {len(ALUNOS)} aluno(s). 🎉")
else:
    print(f"{NO} AMBIENTE NÃO PRONTO: corrija os itens ❌/⚠️ abaixo e rode o notebook de novo.")
print("=" * 70)
print(f"ℹ️  Genie: a doc não publica limite de perguntas por minuto. O workshop assume um space por aluno "
      f"(ADR-0002); se a Genie engasgar, o fallback é um space compartilhado.")
if APPS_EXISTENTES is not None:
    print(f"ℹ️  Apps: {APPS_EXISTENTES} já existem + {2 * len(ALUNOS)} da turma. Se o limite do cliente foi aumentado, "
          f"o ❌ de apps pode ser ignorado.")
print(f"ℹ️  Na abertura: abra o job '{JOB_GERADOR}' (id {JOB_ID}), clique em **Run now** (lote 1 na hora) e "
      f"**Resume** no schedule. Ele se pausa sozinho depois do 42º lote.")
display(pd.DataFrame(report, columns=["Item", "Status", "Detalhe"]))
