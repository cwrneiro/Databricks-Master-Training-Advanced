# 03 - Agente

O atendente da Vida+ Saúde recebe dois tipos de pergunta: as de regra ("qual o prazo de uma ressonância?"), que estão nos PDFs da operadora, e as de número ("quantas ressonâncias estão em análise agora?"), que estão nas suas tabelas. Neste módulo você publica um **agente** que responde as duas: ele busca nos documentos com **AI Search** (RAG), consulta as tabelas com a **Genie** e lembra da conversa.

## Objetivo
- Levar os PDFs para uma tabela de trechos, dentro do seu pipeline, e indexá-la no AI Search
- Declarar no bundle o seu model service, que aponta para o Claude
- Criar um Genie space sobre a silver e a gold
- Publicar o agente pronto do repo pelo web terminal, como um app do Agent Runtime
- Dar ao app do agente, pelo bundle, acesso ao que ele usa

## Como fica

```
PDFs (shared/raw/docs) → pipeline → documentos_chunks ──▶ índice documentos_idx (AI Search) ─┐
silver_autorizacao_status + gold_kpi_autorizacoes ──▶ Genie space ──────────────────────────┤
model service academydb.<aluno>.llm (Claude) ───────────────────────────────────────────────┼─▶ app agent-bricks-<aluno>
lojas de sessões e de memória (Agent Runtime) ──────────────────────────────────────────────┘
```

Os endpoints de AI Search já existem: o instrutor criou e aqueceu para a turma. O índice, o Genie space, o model service e o app são seus.

---

## Passo 1: Trechos dos documentos e model service
Os dois entram no bundle de `01 - Pipeline e bundle/`.

**Trechos.** Na pasta `src/pipeline/`, crie o arquivo `documentos.sql` (**Create → File**) e cole:

```sql
-- Trechos dos documentos da operadora (PDFs), a fonte do índice de AI Search do agente.
-- Streaming table: cada PDF novo é lido uma vez só, e os runs seguintes do job não reprocessam nada.
CREATE OR REFRESH STREAMING TABLE documentos_chunks (
  CONSTRAINT texto_presente EXPECT (texto IS NOT NULL AND texto <> '') ON VIOLATION DROP ROW
)
COMMENT 'Trechos dos documentos da operadora, um por bloco de texto. Fonte do índice de AI Search.'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
AS
WITH documentos AS (
  -- ai_parse_document lê o PDF e devolve os blocos (títulos, parágrafos, rodapés...) com o tipo de cada um.
  SELECT _metadata.file_name AS documento, ai_parse_document(content, map('version', '2.0')) AS parsed
  FROM STREAM read_files('/Volumes/${catalog}/shared/raw/docs/', format => 'binaryFile')
)
SELECT
  concat(documento, '-', e.pos) AS chunk_id,
  documento,
  e.value:content::string AS texto
FROM documentos, LATERAL variant_explode(parsed:document:elements) AS e
-- Fica só o texto corrido: cabeçalhos, rodapés e números de página não ajudam a responder perguntas.
WHERE e.value:type::string = 'text'
```

O pipeline lê todos os arquivos de `src/pipeline/`, então o arquivo novo já faz parte dele. Um pipeline aceita Python e SQL juntos. `${catalog}` vem do `configuration` do pipeline, o mesmo que o Python lê com `spark.conf.get`. O Change Data Feed é o que o índice lê para acompanhar a tabela, como a synced table do módulo 2 faz com a silver. O `ai_parse_document` fica no `WITH`, e não dentro do `LATERAL`: o Spark não aceita uma função não determinística (cada chamada ao modelo pode responder diferente) dentro de um `LATERAL`.

**Model service.** Na pasta `resources/`, crie `llm.model_service.yml` e cole:

```yaml
resources:
  model_services:
    llm:
      # academydb.<aluno>.llm: um nome seu no AI Gateway para o Claude do system.ai.
      parent: schemas/${var.catalog}.${resources.schemas.aluno.name}
      model_service_id: llm
      config:
        routing:
          destinations:
            - destination_type: DESTINATION_TYPE_PAY_PER_TOKEN_FOUNDATION_MODEL
              name: system.ai.databricks-claude-sonnet-4-5
              pay_per_token_config:
                model: models/system.ai.databricks-claude-sonnet-4-5
              traffic_percentage: 100
```

Por que um model service, e não o `system.ai.claude-sonnet-4-5` direto? O app do agente roda com uma identidade própria, que precisa de permissão para chamar o modelo. No `system.ai`, só o admin concede. O `academydb.<aluno>.llm` é seu, e você mesmo concede (passo 6). Ele também é o lugar onde, no dia a dia, você trocaria de modelo ou poria limites de uso sem mexer no agente.

No painel **Deployments**, com o target `prod`, clique em **Deploy** e, em seguida, em **Run job** (~3 min). Lembre-se: em `prod`, código novo só vale depois de deploy.

## Passo 2: Índice de AI Search
O índice precisa da `documentos_chunks`, que o run do passo 1 criou. Em `resources/`, crie `documentos.index.yml` e cole:

```yaml
resources:
  vector_search_indexes:
    documentos:
      name: ${var.catalog}.${resources.schemas.aluno.name}.documentos_idx
      endpoint_name: edia-ai-search-1 # endpoint do instrutor; troque só se ele indicar outro
      primary_key: chunk_id
      # Delta Sync: o índice acompanha a tabela pelo Change Data Feed.
      index_type: DELTA_SYNC
      delta_sync_index_spec:
        source_table: ${var.catalog}.${resources.schemas.aluno.name}.documentos_chunks
        pipeline_type: TRIGGERED
        # O AI Search calcula o embedding de cada trecho com este modelo, que entende português.
        embedding_source_columns:
          - name: texto
            embedding_model_endpoint_name: databricks-qwen3-embedding-0-6b
```

**Deploy** em `prod` (~40 s). O índice fica pronto ~1 min depois.

Abra `03 - Agente/03_agente.py`, conecte no **serverless**, preencha o widget `aluno` e rode a **seção 1**. Ela confere o índice e faz a busca que o agente vai fazer: a pergunta sobre ressonância devolve primeiro os trechos com "21 dias úteis".

## Passo 3: Genie space
No menu lateral, **Genie Agents → New**:

1. Em **Connect your data**, escolha `academydb` → `<aluno>` → `silver_autorizacao_status` e `gold_kpi_autorizacoes`, e clique em **Create**.
2. **Configure → Instructions**: em **General Instructions**, cole o texto abaixo e clique em **Save**.
3. Pergunte "Quantas autorizações de ressonância magnética estão em análise?" para conferir. A resposta mostra o SQL que a Genie escreveu, com `procedimento = 'ressonancia_magnetica'`.
4. Copie o ID do space: em **Configure → About**, é o **Agent ID** (também é o trecho depois de `/genie/rooms/` na URL).

```
Você responde perguntas sobre as autorizações prévias da operadora de saúde Vida+ Saúde.

Tabelas:
- silver_autorizacao_status: uma linha por autorização, com o status atual. Use para contagens, taxas e listas por status, procedimento, prestador ou beneficiário.
- gold_kpi_autorizacoes: totais por procedimento e prestador (autorizacoes, aprovadas, negadas, taxa_negativa, tempo_medio_aprovacao_horas). Para a taxa de um procedimento ou de um prestador inteiro, some autorizacoes e negadas de todas as linhas e divida; não tire a média de taxa_negativa.

Valores das colunas (use exatamente estes códigos, em minúsculas e sem acento; nunca filtre com LIKE nem com o nome escrito pelo usuário):
- procedimento: consulta_cardiologia, ressonancia_magnetica, tomografia, endoscopia, cirurgia_ortopedica, ultrassom, fisioterapia, internacao. Exemplo: "ressonância magnética" é ressonancia_magnetica; "consulta com cardiologista" é consulta_cardiologia; "internação" é internacao.
- status: solicitada, em_analise, aprovada, negada. "Em análise" é em_analise; "aprovação" é aprovada; "negativa" ou "recusada" é negada.
- IDs: autorizações no formato AUT-00001, prestadores PRE-001, beneficiários BEN-0001.

Definições:
- Taxa de aprovação geral = autorizações com status aprovada / total de autorizações da silver_autorizacao_status.
- Taxa de negativa de um procedimento = negadas / autorizações daquele procedimento.
- Os dados chegam ao longo do dia; responda com o estado atual e diga o total de autorizações considerado.

Responda em português.
```

Sem a lista de códigos, a Genie filtra por `'%ressonância magnética%'`, não acha nada (o valor gravado é `ressonancia_magnetica`) e responde 0.

## Passo 4: Ler o agente
O agente já vem pronto em `03 - Agente/agente/`. É um projeto do **Agent Runtime** (`agentbricks`), com LangChain. Os arquivos que importam:

| Arquivo | O que tem |
|---|---|
| `agent/agent.py` | `ALUNO` e `MODEL` (o seu model service), o prompt de sistema e `create_agent_graph`, que junta o modelo e as tools |
| `agent/mcps.py` | A busca no seu índice `documentos_idx`, oferecida ao agente como tool pelo MCP do AI Search |
| `agent.toml` | As lojas de sessões e de memória, o experimento de tracing e, depois do passo 5, a tool da Genie |

O modelo decide sozinho qual tool chamar. O prompt de sistema só dá a regra: documentos para regras e prazos, Genie para números.

## Passo 5: Deploy do agente pelo web terminal
No notebook `03_agente.py`, rode a **seção 2**: ela imprime os comandos com o caminho da sua pasta e o seu nome. Abra o web terminal (painel inferior do notebook → **Terminal**), cole os comandos e troque `<id do Genie space>` pelo ID do passo 3:

```bash
pip install databricks-agentbricks==0.5.1
cd "/Workspace/Users/<seu e-mail>/<repo>/03 - Agente/agente"
sed -i 's/troque_pelo_seu_nome/<aluno>/g' agent.toml agent/agent.py
agentbricks tools add genie-agent <id do Genie space>
agentbricks deploy <aluno>
```

- O `sed` põe o seu nome em `agent/agent.py` (`ALUNO`) e nas lojas do `agent.toml`.
- O `tools add` grava a Genie no `agent.toml` com `auth = "user"`: a Genie roda como quem conversa com o agente, com as permissões dessa pessoa nas tabelas.
- O `deploy` cria o app `agent-bricks-<aluno>`, as lojas de sessões e de memória e o experimento de tracing, e sobe o código (~3 min). Um redeploy leva ~40 s.

O agente fica **fora do bundle**: o `agentbricks deploy` cria peças (as lojas e o Runtime Store) que o bundle ainda não sabe declarar.

## Passo 6: TODO — dar acesso ao app do agente
Se você abrir o app agora, a primeira pergunta falha com `agent invocation failed`: o service principal (SP) do app ainda não tem permissão no seu model service nem no seu índice. Rode a **seção 3** do notebook para ver o application ID do SP.

Conceda o acesso pelo bundle:

1. Em `databricks.yml`, crie a variável `agent_sp` com o application ID do SP como `default`.
2. No schema (`resources/aluno.schema.yml`), dê ao SP `USE_SCHEMA` e `SELECT`. O `SELECT` no schema cobre o índice, que mora nele.
3. No model service (`resources/llm.model_service.yml`), dê ao SP `EXECUTE`.
4. **Deploy** em `prod`.

Como validar: rode o **checkpoint** do notebook. Ele fica verde:

```
✅ O app agent-bricks-<aluno> pode usar o índice e o model service. Abra <url> e converse com o agente.
```

<details markdown="1">
<summary>👉 Solução</summary>

Em `databricks.yml`, dentro de `variables:`:

```yaml
  agent_sp:
    description: Application ID do service principal do app do seu agente (agent-bricks-<aluno>).
    default: 00000000-0000-0000-0000-000000000000 # o ID que a seção 3 mostrou
```

No fim de `resources/aluno.schema.yml`, alinhado com `comment:`:

```yaml
      grants:
        - principal: ${var.agent_sp}
          privileges: [USE_SCHEMA, SELECT]
```

No fim de `resources/llm.model_service.yml`, alinhado com `config:`:

```yaml
      grants:
        - principal: ${var.agent_sp}
          privileges: [EXECUTE]
```

O `USE CATALOG` no `academydb` o SP já tem: a preparação deu a todos os usuários da conta. Os grants ficam declarados junto com os recursos, então um deploy em outro workspace leva as permissões junto.

</details>

## Passo 7: Conversar com o agente
Abra a URL do app (a seção 3 mostra). A UI de chat já vem com o projeto: cada conversa é uma sessão (**New session** abre outra), e o histórico fica na loja de sessões. Os botões **Documentos (RAG)**, **Tabelas (Genie)** e **Memória** preenchem uma pergunta de exemplo; clique em **Send message** para enviar. No chat aparecem as chamadas de tool e o que voltou delas.

> Deixe o **Agent model** no padrão (`academydb.<aluno>.llm (project default)`). Os outros modelos da lista são do `system.ai`, onde o SP do app não tem grant seu.

Faça as perguntas de `bundle/docs/perguntas.md`:

- **RAG** (documentos): resposta exata, por exemplo "21 dias úteis" para a ressonância (~15 s).
- **Genie** (tabelas): os números dependem de quantos lotes já chegaram, e o `perguntas.md` traz as faixas esperadas. Cada pergunta à Genie leva de ~30 s a alguns minutos.

Faça uma pergunta de acompanhamento ("e para tomografia?"): o agente lembra do contexto da sessão. Cada resposta vira um trace no experimento `/Shared/agentbricks_traces/edia-<aluno>`, com cada chamada de tool, os trechos que voltaram do índice e o tempo de cada etapa.

---

## RAG e Genie: quem responde o quê
- **RAG** (AI Search sobre os PDFs): texto que não muda ao longo do dia. A busca acha os trechos parecidos com a pergunta, e o modelo responde com base neles. Bom para regras, prazos e coberturas.
- **Genie** (SQL sobre as tabelas): números que mudam a cada lote. A Genie escreve e roda o SQL. Bom para contagens, taxas e rankings.

Perguntar à Genie sobre o prazo de uma ressonância, ou ao RAG quantas estão em análise, dá errado. É por isso que o agente tem as duas tools, e não uma.

## Sessões e memória
- **Sessão**: o histórico de uma conversa. Mesma `session_id`, mesmo contexto.
- **Memória de longo prazo**: fatos sobre quem conversa, que valem entre sessões. O agente tem as tools `remember` e `recall` sobre a loja de memória, separada por *actor*. Na UI de chat, o actor é o seu e-mail.

## 🎯 Desafio: memória entre sessões
Numa conversa, diga ao agente algo sobre você ("eu atendo os prestadores de cardiologia, lembre disso"). Abra uma **nova** conversa e pergunte "quais prestadores eu atendo?". O que mudou de uma resposta para a outra? Nos traces, procure as chamadas de `remember` e `recall`.

## Contrato de `/api/invocations` (usado no módulo 4)
O app do módulo 4 conversa com o agente pelo mesmo endpoint que a UI de chat usa.

`POST https://agent-bricks-<aluno>-<workspace id>.<cloud>.databricksapps.com/api/invocations`, com um token OAuth do Databricks no `Authorization: Bearer`.

```json
{
  "id": "<uuid novo a cada pergunta>",
  "session_id": "<uuid estável da conversa>",
  "input": {
    "actor": "<e-mail do atendente>",
    "messages": [{"role": "user", "content": "Qual o prazo de uma ressonância?"}]
  }
}
```

Resposta (sem `stream`):

```json
{
  "id": "<o mesmo id>",
  "status": "completed",
  "output": {
    "status": "completed",
    "output": [
      {"type": "ai", "content": "", "tool_calls": [{"name": "academydb__<aluno>__documentos_idx", "args": {"query": "..."}}]},
      {"type": "tool", "name": "academydb__<aluno>__documentos_idx", "content": [{"type": "text", "text": "[{\"chunk_id\": ...}]"}]},
      {"type": "ai", "content": "O prazo máximo é de **21 dias úteis**..."}
    ]
  }
}
```

- `id`: identifica a invocação e serve de chave de idempotência. Repetir o mesmo `id` devolve o resultado gravado; mudar o corpo com o mesmo `id` dá `409`.
- `session_id`: o mesmo em todas as perguntas da conversa, para o agente lembrar do contexto.
- `input.actor`: dono da memória de longo prazo. Sem ele, o actor vira o `session_id`, e o que o agente guardou não aparece em outra sessão. `input` também aceita só a lista de mensagens, sem `actor`.
- A resposta final é o `content` da última mensagem de `output.output` (`type: "ai"`). As mensagens `tool` trazem o que cada tool devolveu.
- `"stream": true`: a resposta vem como SSE, com eventos `delta` (pedaços do texto) e `message` (mensagens completas).
- `"background": true`: devolve `202` com `status_url`. Útil para as perguntas à Genie, que levam minutos.
- A Genie roda como quem chama (`auth = "user"`). O app do módulo 4 chama o agente com o token de quem está logado, então a Genie roda como o atendente, com as permissões dele.
