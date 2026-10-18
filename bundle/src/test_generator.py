"""Teste local do gerador: python3 bundle/src/test_generator.py"""

import json

from generator import (EXPECTED, N_AUTORIZACOES, N_BATCHES, STATUS_INVALIDO, batches, final_status,
                       generate_events, invalid_events, is_valid)

events = generate_events()
lotes = batches(events)

# Determinismo: mesmo seed -> mesmos bytes, inclusive caos e inválidos.
assert json.dumps(events) == json.dumps(generate_events())
assert json.dumps(lotes) == json.dumps(batches(generate_events()))

# Contagens fixadas em EXPECTED.
assert len(events) == EXPECTED["eventos"]
assert final_status(events) == EXPECTED["status_final"]
assert sum(EXPECTED["status_final"].values()) == N_AUTORIZACOES
assert len(lotes) == N_BATCHES and all(lotes)

# Máquina de status: timestamps estritamente crescentes por autorização.
order = ["solicitada", "em_analise", "aprovada", "negada"]
by_auth = {}
for e in events:
    by_auth.setdefault(e["autorizacao_id"], []).append(e)
for evs in by_auth.values():
    evs.sort(key=lambda e: e["event_id"])
    assert [e["status"] for e in evs] == order[:len(evs)] or [e["status"] for e in evs] == order[:2] + ["negada"]
    assert all(a["event_ts"] < b["event_ts"] for a, b in zip(evs, evs[1:]))

# Inválidos: os dois tipos, e o de status vence o último válido se não for descartado.
inv = invalid_events(events)
assert sum(e["autorizacao_id"] is None for e in inv) == EXPECTED["invalidos"]["autorizacao_nula"]
assert sum(e["status"] == STATUS_INVALIDO for e in inv) == EXPECTED["invalidos"]["status_fora_do_dominio"]
assert not any(map(is_valid, inv)) and all(map(is_valid, events))
for e in inv:
    if e["status"] == STATUS_INVALIDO:
        assert e["event_ts"] > max(v["event_ts"] for v in by_auth[e["autorizacao_id"]])

# Caos: mais linhas, os mesmos eventos distintos (válidos + inválidos), mesmo status final.
rows = [e for b in lotes for e in b]
assert len(rows) == EXPECTED["linhas"]
assert {e["event_id"] for e in rows} == {e["event_id"] for e in events + inv}
assert final_status(rows) == EXPECTED["status_final"]

print("ok")
