# ADR-0005: Bundle como espinha dorsal, via UI de bundles

Status: aceito (2026-10-15), revisto em 2026-10-16

## Contexto
O doc pede versionar e fazer deploy do pipeline inteiro como código. Os alunos não têm CLI local, e CI para 50 pessoas é inviável.

## Decisão
- O workshop **começa** num bundle pronto, na pasta do módulo 1: `databricks.yml` com schema, pipeline e job, mais o código em `src/`. O aluno preenche `var.aluno`, faz deploy em `dev` pela UI de bundles, corrige o pipeline, faz deploy de novo em `dev` e promove para `prod`.
- Os targets são `dev` (`mode: development`, que prefixa o schema com `dev_<usuario>_` e pausa os triggers) e `prod` (`mode: production`, com `workspace.root_path` no home do usuário). A partir da promoção, o dia inteiro segue em `prod`, com a ressalva explícita de que o recomendado é desenvolver em `dev`.
- Os módulos 2–4 adicionam recursos ao mesmo `databricks.yml` (sync Lakebase, chunking, índice, model service, grants, app). No fim do dia, um deploy sobe a solução inteira, menos o agente.
- Exceção (ADR-0006): o app do agente fica fora do bundle. O deploy dele é `agentbricks deploy` pelo web terminal, porque o `agentbricks` cria lojas e um Runtime Store que o bundle não declara. O model service e os grants ao SP do agente ficam no bundle.
- O CLI (`validate`, `deploy -t`) aparece como espelho só no guia, junto com `run_as` SP e CI (seção **O mesmo pelo CLI, e num CI** do README do módulo 1).

Revisão (2026-10-16): sai o *Add existing* com bind (o pipeline e o job não são mais criados pela UI) e saem os notebooks de recuperação. O target `prod` entra no hands-on.

## Consequências
- O deploy pela UI não atravessa workspaces, o que não importa aqui.
- Cada aluno tem 2 pipelines e 2 jobs (dev e prod). O teardown remove os dois.
- Confirmado na issue 03 (2026-10-16): a UI de bundles numa Git folder faz deploy de `dev` e de `prod` (`mode: production`) e roda o job nos dois, com CLI v1.21.0.
- Em `dev`, o deploy pela UI é source-linked: o pipeline e o job leem o código da Git folder, então a correção do módulo 1 dispensa redeploy. Em `prod`, o deploy copia o código, e cada mudança exige redeploy. O roteiro precisa deixar essa diferença explícita.
