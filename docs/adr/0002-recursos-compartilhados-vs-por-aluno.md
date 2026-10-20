# ADR-0002: Recursos compartilhados vs por aluno

Status: aceito (2026-10-15), revisto em 2026-10-16

## Contexto
São 50 alunos num workspace. Alguns recursos são caros ou lentos de provisionar. Limites relevantes: 50 índices por endpoint de Vector Search e 100 apps por workspace.

## Decisão
| Recurso | Escopo |
|---|---|
| Catálogo `academydb`, grupo | Compartilhado (setup) |
| Schema `academydb.shared` com o Volume `raw` (eventos e PDFs) e o job do gerador | Compartilhado: o líder roda, o aluno só lê |
| Projeto Lakebase | 1 compartilhado, um schema Postgres por aluno |
| Endpoints de AI Search (antigo Vector Search) | `ceil(N/40)`, cada aluno atribuído por hash do usuário |
| Schemas UC (`dev_<usuario>_<aluno>` e `<aluno>`), tabelas, pipelines, jobs, model service | Por aluno, criados pelo bundle dele |
| Índice AI Search, Genie space, app do agente (Agent Runtime, ADR-0006), app do módulo 4 | Por aluno |

As camadas medallion são prefixos de tabela no schema do aluno, não schemas separados.

Grants do setup: o grupo recebe `USE CATALOG` + `CREATE SCHEMA` no `academydb`, `USE SCHEMA` + `READ VOLUME` no `shared` e `USE SCHEMA` + `EXECUTE` no `system.ai` (sem `MANAGE`). `account users` recebe `USE CATALOG` no `academydb` para os SPs dos apps, que nascem fora do grupo. O resto (schema, índice, model service) o próprio aluno concede ao SP, porque é dono.

Fora do UC, o grupo recebe `CAN_USE` no projeto Lakebase e nos endpoints de AI Search: sem isso o aluno não cria a synced table nem o índice.

Revisão (2026-10-16): sai o cluster all-purpose (ADR-0001). Sai o schema por aluno criado pelo setup: o bundle cria. Sai o Volume por aluno: os eventos vêm de um Volume único.

## Consequências
- A checagem de pré-requisitos precisa conferir quotas: apps (2 por aluno; com o limite de 100, a turma vai até ~45 sem aumento), rate limit da Genie e índices. O job de prod do aluno usa schedule, não file arrival: sem file events no external location, o limite é de 50 jobs com esse trigger por workspace, e habilitar file events depende da IAM do cliente.
- Fallback se o rate limit da Genie não aguentar: um space compartilhado.
- Dois alunos com o mesmo nome (ex.: dois `jsilva`) colidem só no prod. Em dev o prefixo do usuário separa os dois.
