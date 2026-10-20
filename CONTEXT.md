# Engenharia de Dados e IA no Databricks

Workshop hands-on de 1 dia (~7h30), síncrono, para até 50 **alunos** num workspace Databricks único. Um fluxo contínuo leva um **evento de autorização** do gerador até um app: bundle (pipeline SDP + job) → Lakebase → agente → app. Spec completa: `.scratch/workshop/spec.md` (só local, fora do repo público). Decisões: `docs/adr/`.

Prosa em PT-BR; código, nomes de tabelas e identificadores em inglês/snake_case sem acento.

## Glossário

### Domínio (dados sintéticos)

- **Vida+ Saúde**: a operadora de plano de saúde fictícia. Não use nomes de operadoras reais.
- **Beneficiário**: pessoa coberta pelo plano.
- **Prestador**: hospital, clínica ou médico que solicita a autorização.
- **Autorização** (autorização prévia, ou "guia"): pedido do prestador para realizar um procedimento num beneficiário. Chave: `autorizacao_id`.
- **Evento de autorização**: uma mudança de status de uma autorização (`solicitada → em_analise → aprovada | negada`). É append-only. Várias por autorização.
- **Status atual**: o último status de cada autorização (`silver_autorizacao_status`, SCD1). É o que o app consulta.
- **Documentos da operadora**: PDFs sintéticos (rol de cobertura, regras de autorização prévia, prazos de atendimento, FAQ do prestador) que alimentam o RAG.
- **Trechos dos documentos** (chunks): um bloco de texto de um PDF, extraído com `ai_parse_document` pelo pipeline do aluno (`documentos_chunks`). É o que o índice de AI Search busca.
- **Observação do atendente**: texto que o atendente escreve no app sobre uma autorização. É gravado direto no Lakebase.

### Workshop

- **Aluno**: o participante. Use "aluno" (não "usuário", nem "participante") nos textos do workshop.
- **Schema do aluno**: `academydb.<aluno>` (primeira letra do nome + sobrenome, ex.: `acarneiro`), criado pelo bundle. No target `dev` ele se chama `dev_<usuario>_<aluno>`. Todos os objetos de UC do aluno ficam aqui. As camadas medallion são **prefixos** de tabela (`bronze_`, `silver_`, `gold_`), não schemas.
- **Líder**: o admin do workspace do cliente (um por workspace). Roda o setup, dispara o gerador na abertura e roda o teardown.
- **Recursos compartilhados**: criados pelo setup e usados por todos (catálogo `academydb`, grupo, schema `academydb.shared`, projeto Lakebase, endpoints de AI Search, antigo Vector Search). Ver ADR-0002.
- **Gerador** (producer): job do líder que escreve um lote de eventos JSON a cada 10 min em `academydb.shared.raw`, o dia inteiro (42 lotes). Seed fixa, sempre em modo caos e com alguns eventos inválidos.
- **Modo caos**: duplicatas e eventos fora de ordem. As duplicatas de um lote caem no lote seguinte.
- **Falha do dev**: a primeira execução do módulo 1, sem `AUTO CDC`. A silver ganha uma linha por evento e a task `validar` fica vermelha. O aluno corrige, valida em dev e promove para prod.
- **Equivalente em Structured Streaming** ("por baixo do capô"): comentário `# --- Equivalente em Structured Streaming ---` logo abaixo de cada bloco do pipeline, com o mesmo código "na mão". Só leitura.
- **Checkpoint de validação**: célula `assert` que confirma o estado esperado ao fim de uma etapa. Não confundir com o *checkpoint* de streaming.
- **Guia do módulo**: as páginas de um módulo no site. O `README.md` da pasta é a entrada (objetivo, arquitetura e a lista das partes), e os passos ficam nas **partes** ao lado (`1.1 - Deploy do bundle.md`, `1.2 - Job e pipeline.md`...). Os passos são numerados em sequência no módulo inteiro, não por parte: "passo 9" é um endereço estável, citado nos notebooks e no código.
- **Marcador `# TODO (passo N)`**: aponta, no código ou no notebook, o que o aluno muda num passo. O guia mostra o código a colar à vista; só a solução do 🎯 Desafio fica fechada num `<details>`.
- **App do agente**: o app `agent-bricks-<aluno>` que o aluno publica com `agentbricks deploy` no módulo 3. O código vem pronto e fica fora do bundle. Ver ADR-0006.
- **App do atendente**: o app `vida-saude-<aluno>` do módulo 4 (AppKit, código pronto em `01 - Pipeline e bundle/src/app/`), declarado no bundle. Lê o status e grava observações no Lakebase pelo SP do app, e conversa com o app do agente com o token de quem está logado.
- **Bundle**: o `databricks.yml` na pasta do módulo 1. Vem pronto com schema, pipeline e job, e cresce até o módulo 4. Targets `dev` e `prod`. Ver ADR-0005.
- **Model service do aluno**: `academydb.<aluno>.llm`, um model service do AI Gateway declarado no bundle que aponta para o Claude do `system.ai`. Existe para que o aluno, dono dele, possa concedê-lo ao SP do app do agente.
- **Versão principal** / **versão do cliente**: o mesmo conteúdo. A versão do cliente só tem os módulos 01 e 02 (sem Início) e acrescenta a página `analogias.md` do módulo 01 (Kafka/K8s/Helm). Ver ADR-0004.

## Convenções do guia

O tom e a condução seguem o workshop de referência ([Databricks-Master-Training](https://github.com/CaduBettanim/Databricks-Master-Training)): clique → veja → porquê.

- **README do módulo**: abre com um gancho "vamos" que retoma o módulo anterior, depois Objetivo, o diagrama "Como fica" e a lista das partes. Cada parte abre com uma frase do que ela faz.
- **Passo**: título com verbo; logo abaixo, a linha `> Recurso · Recurso` com os recursos da plataforma usados; uma frase de introdução; cliques numerados, com os rótulos da UI em **negrito** e caminhos com `→`; depois, "Repare…", no máximo uma frase de porquê e um `>` de dica opcional. Fale com o aluno por "você".
- **Código a colar** fica à vista, dentro do item da lista. As **saídas de erro** que o aluno precisa reconhecer também.
- **👉** (`<details>`): respostas. Saídas de sucesso (`✅`, resultados esperados), a solução do 🎯 Desafio e os arquivos finais do fechamento.
- **💡** (`<details>`): aprofundamentos. Os conceituais ficam no fim da parte; os que explicam o código de um passo (o que cada parte do YAML faz), logo abaixo dele.
- **Render** (Python-Markdown): dois `>` seguidos viram um bloco só (separe com `<!-- -->`), e o número inicial de uma lista é ignorado (não quebre uma lista numerada com um parágrafo no meio). Lista de um item vira texto corrido.

## Site

O repositório também é um site [Zensical](https://zensical.org), publicado em https://cwrneiro.github.io/Databricks-Master-Training-Advanced/ a cada push no `main`. Para ver localmente:

```bash
pip install -r requirements-docs.txt
zensical serve
```
