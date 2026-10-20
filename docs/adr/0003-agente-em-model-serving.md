# ADR-0003: Agente por aluno em Model Serving

Status: **substituída** (2026-10-15). Um spike mostrou que `agents.deploy` não autentica no Lakebase Autoscaling, e o usuário decidiu mover o agente para Databricks Apps. Substituída pela ADR-0006 (Agent Runtime via `agentbricks`).

## Contexto
O app (módulo 6) precisa chamar o agente do aluno, e o agente usa memória no Lakebase. As alternativas eram um endpoint compartilhado ou o app chamar a Genie direto.

## Decisão
Cada aluno faz `agents.deploy` do próprio agente (LangChain v1 + MCP gerenciado + checkpointer Lakebase). O deploy é disparado no começo do módulo 5 para rodar em background (~15–20 min). Fallback documentado: um endpoint de referência compartilhado, criado pelo setup.

## Consequências
- São 50 serving endpoints, então a quota entra nos pré-requisitos.
- A orientação atual do Databricks está migrando agentes para Apps. Se o spike mostrar que `agents.deploy` com checkpointer no Lakebase é frágil, reabrir esta decisão.
