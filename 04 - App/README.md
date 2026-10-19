# 04 - App

Até aqui, tudo o que você construiu se vê pelo Databricks: o pipeline, o Postgres, o agente. O atendente da Vida+ Saúde precisa de uma tela só, onde ele procura uma guia, vê o status, anota o que o prestador disse na ligação e tira dúvidas com o agente. Neste módulo você sobe essa tela, o **app do atendente**, como mais um recurso do seu bundle.

O código do app vem pronto em `01 - Pipeline e bundle/src/app/` (AppKit: Node.js no servidor, React na tela). Você não escreve React: declara o app, faz deploy, dá a ele acesso ao Postgres e usa.

## Objetivo
- Declarar o app no bundle, com os recursos de que ele precisa (o Postgres e o app do agente)
- Fazer deploy em `prod` e subir o código do app
- Dar ao service principal do app acesso ao seu schema no Postgres
- Usar o app: consultar uma guia, gravar uma observação e conversar com o agente

## Como fica

```
                         ┌─ SP do app ───────────────▶ Postgres: <aluno>.autorizacao_status (lê)
atendente ─▶ app vida-saude-<aluno> ─┤                           <aluno>.observacao_atendente (lê e grava)
                         └─ token do atendente ─────▶ app agent-bricks-<aluno> (RAG + Genie)
```

O app tem duas identidades. Para o Postgres, usa o próprio service principal (SP). Para o agente, usa o token de quem está logado, e a Genie roda com as permissões do atendente.

---

## Passo 1: Declarar o app no bundle
> Apps: Resources · Bundles

Na pasta `01 - Pipeline e bundle/resources/`, crie o arquivo `app.app.yml` (**Create → File**) e cole:

```yaml
resources:
  apps:
    vida_saude:
      # O app do atendente: status (synced table), observações (Lakebase) e chat com o seu agente.
      name: vida-saude-${var.aluno}
      description: Atendimento de autorizações da Vida+ Saúde (${var.aluno})
      source_code_path: ../src/app
      # O chat chama o agente com o seu token; genie é o escopo que o app do agente pede.
      user_api_scopes: [genie]
      # Os nomes postgres e agente são os que o app.yaml do código usa em valueFrom.
      resources:
        - name: postgres
          postgres:
            branch: projects/edia-workshop/branches/production
            database: projects/edia-workshop/branches/production/databases/databricks-postgres
            permission: CAN_CONNECT_AND_CREATE
        - name: agente
          app:
            name: agent-bricks-${var.aluno}
            permission: CAN_USE
```

O que cada parte faz:

- `source_code_path`: a pasta do código, relativa a este arquivo. O Databricks instala os pacotes e compila o app quando o código sobe (passo 2).
- `user_api_scopes`: o que o app pode fazer em nome de quem está logado. O app do agente pede `genie`, então o app do atendente precisa pedir o mesmo para repassar o token.
- `resources.postgres`: dá ao SP do app o direito de conectar no projeto Lakebase da turma. O deploy cria um role com o application ID do SP no Postgres, mas sem acesso ao seu schema (passo 3).
- `resources.agente`: dá ao SP do app `CAN_USE` no app do agente.

Como o app recebe esses valores? Abra `src/app/app.yaml`: ele diz como iniciar o app (`npm run start`) e lê dois valores dos recursos acima com `valueFrom`, o endpoint do Postgres e o nome do app do agente (`agent-bricks-<aluno>`). Do nome do agente, o app tira o seu nome de aluno, que é também o nome do seu schema no Postgres.

O nome do app é `vida-saude-<aluno>`, e não ganha prefixo em `dev`. Por isso este módulo roda só em `prod`.

## Passo 2: Deploy em `prod` e código do app
> Apps · AppKit

1. No painel **Deployments**, com o target `prod`, clique em **Deploy**. O app é criado junto com o SP dele.
2. O deploy do bundle cria o app e guarda a configuração, mas **não** sobe o código. Em **Bundle resources → Apps**, clique em `vida-saude-<aluno>`: abre a página do app. Clique em **Deploy** (canto superior direito). O Databricks copia o código da pasta do bundle, lê o `app.yaml`, instala os pacotes, compila e inicia o app (~1 min).
3. Quando o status ficar **Running**, abra a URL do app. No primeiro acesso, o Databricks pergunta com que identidade autorizar o app: escolha a sua.

A tela abre, mas o fichário mostra o erro:

```
O app ainda não tem permissão no schema <aluno> do Postgres. Rode os GRANTs do módulo 4 para o service principal do app.
```

É o esperado: o SP do app conecta no Postgres, mas não enxerga o seu schema.

> Mudou alguma coisa no código do app? Em `prod`, faça **Deploy** no bundle (copia o código) e depois **Deploy** na página do app (sobe o código).

## Passo 3: TODO — dar ao app acesso ao Postgres
> Lakebase: Postgres roles

Abra `04 - App/notebook_app.py`, conecte no **serverless**, preencha o widget `aluno` e rode a **seção 1**: ela mostra o application ID do SP do app e confere que o role dele existe no Postgres.

Na **seção 2**, complete o TODO: conceda ao SP, no seu schema do Postgres,

- `USAGE` no schema;
- `SELECT` na `autorizacao_status`;
- `SELECT` e `INSERT` na `observacao_atendente`.

Você pode conceder porque é dono do schema e da `observacao_atendente`, e tem `SELECT` com grant option na `autorizacao_status` (módulo 2).

Como validar: o **checkpoint** do notebook fica verde, e o fichário do app carrega quando você recarrega a página.

```
✅ O app vida-saude-<aluno> pode ler e gravar no schema <aluno>. Recarregue <url>.
```

<details markdown="1">
<summary>👉 Solução</summary>

Na célula do TODO:

```python
sql(f'GRANT USAGE ON SCHEMA "{SCHEMA}" TO "{sp}"')
sql(f'GRANT SELECT ON "{SCHEMA}".autorizacao_status TO "{sp}"')
sql(f'GRANT SELECT, INSERT ON "{SCHEMA}".observacao_atendente TO "{sp}"')
```

No Postgres, o role de um SP tem o nome do application ID dele, e o nome vai entre aspas duplas por causa dos hífens. Sem `UPDATE` nem `DELETE`: o app só acrescenta observações, e uma observação gravada não muda.

</details>

## Passo 4: Usar o app
> Apps: User authorization · Lakebase · Agent Bricks

Os dados continuam chegando: a cada 10 min, o gerador escreve um lote, o job atualiza a silver e o sync leva as mudanças para o Postgres. O app relê o Postgres a cada 30 s.

**Consultar.** O fichário mostra quantas guias há em cada status. Clique num status para filtrar a lista, ou busque por uma guia (`AUT-00058`), um beneficiário (`BEN-0428`) ou um prestador (`PRE-048`). Abra uma guia: o carimbo mostra o status atual. Anote o ID de uma guia `em_analise` e volte a ela depois de um ou dois lotes: o status pode ter mudado.

**Observar.** Na guia aberta, escreva uma observação ("Prestador ligou pedindo prioridade") e clique em **Salvar observação**. Ela aparece na hora, com o seu e-mail. Rode a **seção 3** do notebook: a mesma linha está na `observacao_atendente`. Quem gravou foi o SP do app, mas o `autor` é você: o app lê quem está logado e grava junto.

**Conversar.** No painel **Agente Vida+**, faça uma pergunta de cada tipo de [`perguntas.md`](../03%20-%20Agente/perguntas.md):

- "Qual o prazo de uma ressonância magnética?": a resposta vem dos documentos (marca **Documentos**), em ~15 s.
- "Quantas tomografias estão em análise?": a resposta vem das tabelas (marca **Tabelas (Genie)**) e leva de ~40 s a alguns minutos. Enquanto isso, a guia ao lado continua usável.

Faça uma pergunta de acompanhamento ("e ressonâncias?"): o agente lembra da conversa. **Nova conversa** abre outra sessão. As conversas aparecem também nos traces do experimento `/Shared/agentbricks_traces/edia-<aluno>`, como no módulo 3.

---

## Duas identidades
- **SP do app** (Postgres): toda leitura e gravação no Postgres passa pelo SP, com os 3 GRANTs que você deu. Um atendente sem acesso nenhum ao Postgres usa o app normalmente, e ninguém precisa de senha de banco.
- **Token de quem está logado** (agente): o app repassa o seu token ao app do agente, e a Genie roda como você, com as suas permissões no Genie space e nas tabelas. Cada atendente vê só o que pode ver, e o app não precisa de acesso próprio às tabelas do Unity Catalog.

A regra prática: o que o app faz por todo mundo vai pelo SP; o que depende de quem pergunta vai pelo token do usuário.

## Por que o chat não espera a resposta
Uma pergunta à Genie pode levar minutos, e a conexão entre o navegador e o app cai depois de 2 min. Por isso o app manda a pergunta ao agente com `"background": true`: o agente responde na hora com um ID, e a tela consulta o andamento a cada poucos segundos até a resposta ficar pronta.

## Se algo der errado

| O que aparece | O que fazer |
|---|---|
| O app não tem URL, ou o status não é **Running** | Faltou o **Deploy** na página do app (passo 2). Veja a aba **Logs** da página do app. |
| "O app ainda não tem permissão no schema..." | Faltam os GRANTs do passo 3. Rode o checkpoint do notebook. |
| "Tabela não encontrada no schema..." | A `autorizacao_status` vem do sync do módulo 2 e a `observacao_atendente` do notebook do módulo 2. Confira os dois. |
| "O agente respondeu 401/403" ou "Sem o token do usuário" | Confira `user_api_scopes: [genie]` no `app.app.yml`, faça **Deploy** no bundle e **Deploy** na página do app, e abra o app de novo para autorizar. |
| "O agente respondeu 5xx" ou "Não foi possível falar com o app..." | Confira se `agent-bricks-<aluno>` está **Running** e responde pela própria UI de chat (módulo 3). |
