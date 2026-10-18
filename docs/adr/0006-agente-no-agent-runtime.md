# ADR-0006: Agente por aluno no Agent Runtime, com deploy pelo web terminal

Status: aceito (2026-10-16), revisto no mesmo dia. Substitui a ADR-0003.

## Contexto
A ADR-0003 (agente em Model Serving) caiu no spike 04: `agents.deploy` não autentica no Lakebase Autoscaling. Um app FastAPI próprio em Databricks Apps funcionou, mas a documentação trata o Model Serving como legado e aponta o Agent Runtime (Databricks Apps + `agentbricks`) como o caminho principal. O usuário decidiu seguir o caminho oficial.

## Decisão
- O agente é um projeto `agentbricks init --framework langgraph` (LangChain v1 `create_agent`, modelo `system.ai.*` pelo AI Gateway), pronto no repo. O código e a definição do agente são feitos no desenvolvimento, não pelo aluno.
- Tools: Genie nativa no `agent.toml` (`auth = "user"`, roda como o aluno). AI Search code-first em `agent/mcps.py`, pelo MCP de workspace (não há tipo de tool para AI Search).
- Memória: sessões e memória de longo prazo pelas lojas gerenciadas do Agent Runtime, não pelo checkpointer no projeto Lakebase do workshop.
- O aluno começa no deploy: abre o web terminal de um notebook no serverless, `pip install databricks-agentbricks`, entra na pasta do projeto e roda `agentbricks deploy <nome>`. O resultado é um app `agent-bricks-<nome>` por aluno, criado em ~3 min.
- Modelo: um model service do aluno, `academydb.<aluno>.llm`, declarado no bundle com destino pay-per-token `system.ai.databricks-claude-sonnet-4-5` (o mesmo de `system.ai.claude-sonnet-4-5`). O aluno é dono e, portanto, pode concedê-lo ao SP do app, o que não conseguiria no `system.ai`. O código traz um placeholder só, o nome do aluno (`ALUNO` no `agent/agent.py`, de onde saem `MODEL` e o índice; e as lojas `edia-<aluno>-*` no `agent.toml`), trocado por um `sed` no web terminal (issue 14). Com `claude-sonnet-5-5` o agente publicado devolve só reasoning.

## Consequências
- O `agentbricks` é Beta/experimental: fixar a versão (0.5.1 testada) e reconferir antes de cada turma.
- São 2 apps por aluno (agente + app do módulo 4), decisão do usuário. Com 50 alunos isso bate no limite de 100 apps por workspace: o pré-requisito confirma o limite do cliente, e sem aumento a turma vai até ~45 alunos.
- O app do agente fica fora do bundle (decisão do usuário): o `agentbricks deploy` cria lojas e um Runtime Store que o bundle não declara. A ADR-0005 ganha essa exceção.
- O SP do app do agente precisa de `USE CATALOG`, `USE SCHEMA`, `SELECT` no índice e `EXECUTE` no model service, e só existe depois do deploy. O `USE CATALOG` vem da preparação (`account users`). O resto o aluno concede no módulo 3, de forma declarativa: cola o application ID do SP em `var.agent_sp` e faz redeploy do bundle.
- O app do módulo 4 chama o app do agente (`/api/invocations` com `session_id`), testado na issue 15: o recurso de app `app` (`CAN_USE`) no bundle e o token do atendente (OBO, `user_api_scopes: [genie]`, o mesmo escopo que o app do agente pede). A chamada pelo SP do app também funciona, mas a Genie exigiria recursos de Genie space, warehouse e tabelas.
- A Genie levou ~3 min por pergunta no spike 04 e 25–50 s na issue 14 (3 lotes). Pesa no ritmo do módulo se voltar a demorar.
- A memória de longo prazo é separada por `actor`. A UI de chat manda o e-mail do usuário; um cliente da API (o app do módulo 4) precisa mandar `input.actor`, senão o actor vira o `session_id` e a memória não passa de uma sessão para outra (issue 14).
- O MCP de AI Search de workspace não passa pelo Unity Gateway nem aparece no tracing; trocar quando houver um tipo de tool oficial.
- Deploy por notebook também funciona, mas exige baixar o CLI e ajustar o PATH (o CLI da compute recusa uso fora do web terminal). Fica como fallback.
