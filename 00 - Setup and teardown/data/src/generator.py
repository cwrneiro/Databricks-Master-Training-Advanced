"""Gerador de eventos de autorização da Vida+ Saúde (dados sintéticos).

Função pura, só stdlib: mesmo seed -> mesmos eventos, na mesma ordem.
Cada autorização percorre solicitada -> em_analise -> aprovada | negada,
com timestamps estritamente crescentes. Parte delas ainda está em aberto
na data de referência (para no meio da máquina de status).

Lotes: os eventos (mais uma fração de inválidos) são ordenados por event_ts e
fatiados em N_BATCHES lotes, que simulam chegada contínua ao longo do dia. Sempre
em modo caos: reenvia duplicatas e atrasa eventos para o lote seguinte (chegam
fora de ordem), sem mudar o status final.

Inválidos (alvo das expectations): metade com autorizacao_id nulo, metade com
status fora do domínio 1 min depois do último evento válido da autorização. Sem
o expect_or_drop na silver, esse evento venceria o AUTO CDC.
"""

import random
from datetime import datetime, timedelta

SEED = 42
REFERENCE_DATE = datetime(2026, 1, 5)
N_BENEFICIARIOS = 500
N_PRESTADORES = 100
N_AUTORIZACOES = 2000
N_BATCHES = 42
CHAOS_DUP_RATE = 0.10
CHAOS_LATE_RATE = 0.05
INVALID_RATE = 0.02
STATUS_INVALIDO = "cancelada"

PROCEDIMENTOS = [
    "consulta_cardiologia", "ressonancia_magnetica", "tomografia", "endoscopia",
    "cirurgia_ortopedica", "ultrassom", "fisioterapia", "internacao",
]

# Contagens fixadas pelo teste (test_generator.py). Os asserts dos módulos usam estas.
EXPECTED = {
    "eventos": 5414,
    "status_final": {"solicitada": 178, "em_analise": 230, "aprovada": 1349, "negada": 243},
    "invalidos": {"autorizacao_nula": 54, "status_fora_do_dominio": 54},
    "linhas": 6045,  # nos 42 lotes, com caos e inválidos
}


def generate_events(seed=SEED):
    """Todos os eventos, ordenados por (event_ts, event_id)."""
    rng = random.Random(seed)
    events = []
    for i in range(1, N_AUTORIZACOES + 1):
        auth_id = f"AUT-{i:05d}"
        base = {
            "autorizacao_id": auth_id,
            "beneficiario_id": f"BEN-{rng.randint(1, N_BENEFICIARIOS):04d}",
            "prestador_id": f"PRE-{rng.randint(1, N_PRESTADORES):03d}",
            "procedimento": rng.choice(PROCEDIMENTOS),
        }
        r = rng.random()
        if r < 0.09:
            path = ["solicitada"]
        elif r < 0.19:
            path = ["solicitada", "em_analise"]
        elif r < 0.88:
            path = ["solicitada", "em_analise", "aprovada"]
        else:
            path = ["solicitada", "em_analise", "negada"]
        ts = REFERENCE_DATE - timedelta(days=30) + timedelta(minutes=rng.randint(0, 26 * 24 * 60))
        for n, status in enumerate(path, 1):
            if n > 1:
                ts += timedelta(minutes=rng.randint(30, 48 * 60))
            events.append({**base, "event_id": f"{auth_id}-{n}", "status": status,
                           "event_ts": ts.isoformat()})
    events.sort(key=lambda e: (e["event_ts"], e["event_id"]))
    return events


def invalid_events(events, seed=SEED):
    """Eventos inválidos extras (INVALID_RATE dos eventos), sobre o último evento de autorizações sorteadas."""
    last = {}
    for e in events:
        last[e["autorizacao_id"]] = e
    rng = random.Random(seed + 2)
    alvo = rng.sample(sorted(last), round(len(events) * INVALID_RATE))
    out = []
    for n, auth_id in enumerate(alvo):
        e = {**last[auth_id], "event_id": last[auth_id]["event_id"] + "-inv"}
        if n % 2:
            e["status"] = STATUS_INVALIDO
            e["event_ts"] = (datetime.fromisoformat(e["event_ts"]) + timedelta(minutes=1)).isoformat()
        else:
            e["autorizacao_id"] = None
        out.append(e)
    return out


def is_valid(e):
    return e["autorizacao_id"] is not None and e["status"] in EXPECTED["status_final"]


def batches(events, seed=SEED):
    """Eventos + inválidos em N_BATCHES lotes, com duplicatas e atrasos (modo caos)."""
    todos = sorted(events + invalid_events(events, seed), key=lambda e: (e["event_ts"], e["event_id"]))
    size = -(-len(todos) // N_BATCHES)
    out = [todos[k * size:(k + 1) * size] for k in range(N_BATCHES)]
    rng = random.Random(seed + 1)
    caos = [[] for _ in range(N_BATCHES)]
    for k, lote in enumerate(out):
        for e in lote:
            late = k + 1 < N_BATCHES and rng.random() < CHAOS_LATE_RATE
            caos[k + 1 if late else k].append(e)
            if rng.random() < CHAOS_DUP_RATE:
                caos[min(k + 1, N_BATCHES - 1)].append(dict(e))
    for lote in caos:
        rng.shuffle(lote)
    return caos


def final_status(events):
    """Status atual por autorização: o evento válido de maior event_ts vence (como o AUTO CDC + expect_or_drop)."""
    last = {}
    for e in filter(is_valid, events):
        cur = last.get(e["autorizacao_id"])
        if cur is None or e["event_ts"] > cur["event_ts"]:
            last[e["autorizacao_id"]] = e
    counts = dict.fromkeys(EXPECTED["status_final"], 0)
    for e in last.values():
        counts[e["status"]] += 1
    return counts
