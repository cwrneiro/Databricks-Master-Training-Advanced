# 00 - Setup and teardown: ambiente compartilhado, checagem e teardown

Notebooks do **líder** (o admin do workspace do cliente). Os alunos não rodam nada daqui.

## Conteúdo

| Pasta | O quê |
|---|---|
| `notebooks/` | `00_setup.py` (prepara o workspace e confere tudo o que o dia usa, antes do workshop), `00_gerador_eventos.py` (task do job do gerador, um lote por run: não abra à mão) e `00_teardown.py` (remove o que o setup e os alunos criaram, depois do workshop) |
| `data/` | `docs/` (os 9 PDFs da operadora), `src/generator.py` (o gerador de eventos, com seed fixa) e `scripts/gerar_pdfs.py` (gera os PDFs) |

> ***Rode no workspace corporativo do cliente, no serverless, como administrador de conta.***

## Antes de começar

Clone o repo como **Git folder** (**Workspace → Create → Git folder**, URL `https://github.com/cwrneiro/Databricks-Master-Training-Advanced` ou a do fork da turma). Os notebooks precisam rodar de dentro dela: o setup copia os PDFs de `data/docs/` e cria o job do gerador apontando para `notebooks/00_gerador_eventos`, que importa `data/src/generator.py`.

## O que o setup faz
> É idempotente: pode rodar quantas vezes precisar.

1. Cria o grupo de conta `edia_alunos`, atribui ao workspace, adiciona os alunos e dá `workspace-access` + `databricks-sql-access`.
2. Cria (ou reaproveita) o catálogo `academydb`.
3. Cria o schema `academydb.shared` com o Volume `raw` e copia os 9 PDFs para `raw/docs/`.
4. Concede (ADR-0002):
    - ao grupo: `USE CATALOG` + `CREATE SCHEMA` no `academydb`, `USE SCHEMA` + `READ VOLUME` no `shared` e `USE SCHEMA` + `EXECUTE` no `system.ai`;
    - a `account users`: `USE CATALOG` no `academydb` (para os SPs dos apps atravessarem o catálogo).
5. Cria o job `edia_gerador_eventos` (cron a cada 10 min, **pausado**).
6. Cria o projeto Lakebase `edia-workshop`, dá `CAN_USE` ao grupo (o aluno cria a synced table nele no módulo 2) e cria um role OAuth no Postgres para cada aluno (o `CAN_USE` não dá login no Postgres). Se o projeto estiver em *soft delete* (apagado sem purge, o nome fica preso por 7 dias), o setup para com ❌ e diz como restaurar ou apagar de vez.
7. Cria `ceil(N/40)` endpoints de AI Search (`edia-ai-search-1`, …), dá `CAN_USE` ao grupo e aquece cada um com um índice descartável (o primeiro índice num endpoint novo leva ~15 min).
8. Checa: serverless, Lakebase, AI Search e quota de índices, embedding, Genie e SQL warehouse, limite de apps (2 por aluno), Agent Runtime e PyPI, `system.ai.claude-sonnet-4-5` pelo AI Gateway, grants do `system.ai` em vigor e web terminal.

Não cria schemas de aluno (o bundle de cada aluno cria o dele) nem cluster.

## Passos

1. Abra `notebooks/00_setup` na Git folder e ligue no **serverless**.
2. Rode as duas primeiras células para exibir os widgets.
3. Escolha os alunos em **2. Alunos**.
4. **Run all**.
    - Se aparecer `O metastore não tem storage padrão`, crie o catálogo `academydb` à mão (**Catalog → Create catalog**) e rode de novo com **1. Criar catálogo** = `false`.
5. Confira a seção **5. Relatório final**. Se só o aquecimento do AI Search estiver ❌, espere ~15 min e rode de novo.

## Na abertura do workshop

Abra o job `edia_gerador_eventos` e:

1. **Run now**: o lote 1 chega na hora.
2. **Resume** no schedule: um lote a cada 10 min, 42 lotes (~7 h). Depois do último, o job se pausa sozinho.

Se o dia encurtar, os últimos lotes não chegam, sem quebrar nada.

## Teardown (depois do workshop)
> Também é idempotente.

Os alunos são achados pelos schemas que o bundle criou (`dev_<usuario>_<aluno>` e `<aluno>`, pelo comentário `Schema do aluno <aluno> no workshop Vida+ Saúde`). Cada alternador é `true`/`false`:

1. **Recursos dos alunos** (`true`): apps do módulo 4 `vida-saude-<aluno>`, apps do agente `agent-bricks-<aluno>` (Runtime Store antes do app, depois as lojas de memória e sessões e o experimento de tracing), pipelines e jobs de dev e prod, a synced table do módulo 2 (com o pipeline de sync) e os schemas com `CASCADE`. Apagar o pipeline não apaga as streaming tables, por isso o `CASCADE`.
2. **Recursos compartilhados** (`true`): job do gerador, endpoints de AI Search com todos os índices, projeto Lakebase (com purge: sem ele, o nome fica preso por 7 dias e o próximo setup não consegue recriar o projeto) e o schema `shared`.
3. **Grupo** (`true`): o grupo `edia_alunos` (e com ele os grants) e o `USE CATALOG` de `account users`.
4. **REMOVER CATÁLOGO** (`false`): `DROP CATALOG academydb CASCADE`. Ligue só se o catálogo foi criado para o workshop.

Passos: abra `notebooks/00_teardown`, rode as duas primeiras células, ajuste os alternadores, **Run all** e confira a seção **3. Relatório final** (`✅ Teardown concluído`).
