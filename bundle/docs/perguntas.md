# Perguntas RAG vs Genie - Módulo 3 (agente)

Este documento lista 5 perguntas que apenas o RAG (documentos PDF) pode responder e 5 que apenas o Genie (dados tabulares do generator) pode responder. As de RAG têm resposta exata e fonte no PDF. As da Genie têm faixas, porque os dados chegam ao longo do dia, e um snippet Python para recalcular.

## Perguntas que APENAS RAG responde (dos PDFs)

---

### 1. Qual é o prazo máximo para realização de uma ressonância magnética?

**Resposta esperada**: 21 dias úteis

**Fonte**: `03_prazos_atendimento.pdf`, página 1, seção "Prazos Máximos por Procedimento (Dias Úteis)"

**Sentença exata do PDF**:
> "Ressonância Magnética: 21 dias úteis (Eletivo)"

---

### 2. Quantas consultas preventivas anuais com cardiologista o beneficiário tem direito e o que elas incluem?

**Resposta esperada**: 2 consultas por ano, incluindo eletrocardiograma e avaliação básica, ambas com autorização prévia

**Fonte**: `08_coberturas_especiais.pdf`, página 1, seção "Programa de Prevenção"

**Sentença exata do PDF**:
> "Beneficiários têm direito a 2 consultas preventivas anuais com cardiologista, incluindo eletrocardiograma e avaliação básica, ambas com autorização prévia."

---

### 3. Qual é o prazo máximo de análise de uma solicitação de autorização prévia para um procedimento de urgência?

**Resposta esperada**: 24 horas

**Fonte**: `04_faq_prestador.pdf`, página 1, seção "Perguntas Frequentes", resposta a "Qual é o prazo máximo para análise?"

**Sentença exata do PDF**:
> "R: 24 horas para urgências; 5 dias úteis para os demais procedimentos."

---

### 4. Qual é o período de carência para procedimentos ambulatoriais no plano?

**Resposta esperada**: 30 dias

**Fonte**: `05_termos_condicoes.pdf`, página 1, seção "Carência"

**Sentença exata do PDF**:
> "30 dias para procedimentos ambulatoriais; 60 dias para internações (exceto emergência)."

---

### 5. Quantas sessões anuais de fisioterapia são cobertas para procedimentos ortopédicos pós-operatórios?

**Resposta esperada**: Até 30 sessões anuais, com prazo de 3 dias úteis por sessão

**Fonte**: `08_coberturas_especiais.pdf`, página 1, seção "Reabilitação e Fisioterapia"

**Sentença exata do PDF**:
> "Cobertura de até 30 sessões anuais de fisioterapia para procedimentos ortopédicos pós-operatórios, com autorização prévia. Cada sessão segue prazo de 3 dias úteis."

---

## Perguntas que APENAS Genie responde (dos dados do generator)

Os dados chegam o dia inteiro (42 lotes, um a cada 10 min), então as respostas da Genie dependem de quantos lotes já chegaram. A tabela traz o valor medido com 10 lotes (~1h40 depois da abertura), 20 lotes (~3h20) e 42 lotes (fim do dia), e a faixa entre o mínimo e o máximo observados. Com 42 lotes, os números são os finais do gerador.

**Fonte**: tabela `silver_autorizacao_status` (estado final por `autorizacao_id`, só os eventos válidos), no Lakebase e no catálogo.

| # | Pergunta | 10 lotes | 20 lotes | 42 lotes | Faixa |
|---|---|---|---|---|---|
| 1 | Qual procedimento tem a maior taxa de negativa? | Ressonância magnética, 14,0% (8/57) | Ultrassom, 13,6% (17/125) | Ressonância magnética, 14,0% (35/250) | 13,6%–14,0%; o procedimento muda ao longo do dia |
| 2 | Quantas autorizações de ressonância magnética estão atualmente em status "em análise"? | 11 | 16 | 19 | 11–19 |
| 3 | Qual prestador tem o maior número de autorizações negadas? | Empate: PRE-043, PRE-082 e PRE-087, com 2 | Empate: PRE-009, PRE-039 e PRE-087, com 4 | PRE-087, com 8 | 2–8; com empate até o fim da manhã |
| 4 | Quantas autorizações estão ainda no status "solicitada" (não iniciaram análise)? | 124 | 165 | 178 | 124–178 |
| 5 | Qual é a taxa de aprovação geral (aprovadas / total)? | 47,7% (264/554) | 57,5% (590/1.026) | 67,5% (1.349/2.000) | 47,7%–67,5% |

O total de autorizações cresce com os lotes: 554, 1.026 e 2.000.

**Snippet Python para recalcular** com `k` lotes (rode em `bundle/src/`):
```python
from generator import batches, generate_events, is_valid

k = 42
last = {}
for e in filter(is_valid, (e for b in batches(generate_events())[:k] for e in b)):
    cur = last.get(e["autorizacao_id"])
    if cur is None or e["event_ts"] > cur["event_ts"]:
        last[e["autorizacao_id"]] = e
auths = list(last.values())

proc = {}
for e in auths:
    t = proc.setdefault(e["procedimento"], [0, 0])
    t[0] += 1
    t[1] += e["status"] == "negada"
pior = max(proc, key=lambda p: proc[p][1] / proc[p][0])
print("1.", pior, proc[pior])

print("2.", sum(e["procedimento"] == "ressonancia_magnetica" and e["status"] == "em_analise" for e in auths))

neg = {}
for e in auths:
    if e["status"] == "negada":
        neg[e["prestador_id"]] = neg.get(e["prestador_id"], 0) + 1
top = max(neg.values())
print("3.", sorted(p for p, n in neg.items() if n == top), top)

print("4.", sum(e["status"] == "solicitada" for e in auths))

aprovadas = sum(e["status"] == "aprovada" for e in auths)
print(f"5. {100 * aprovadas / len(auths):.1f}% ({aprovadas}/{len(auths)})")
```

---

## Notas para o módulo 3

### RAG (Retrieval-Augmented Generation)
- **Entrada**: Documentos PDF em linguagem natural
- **Processamento**: Busca semântica, chunking, embedding e recuperação
- **Saída**: Respostas sobre políticas, prazos, coberturas, procedimentos, regras de negócio
- **Características**: Respostas citam documentos originais, rastreáveis

### Genie (Tabular Data Intelligence)
- **Entrada**: Tabelas estruturadas (`silver_autorizacao_status`, `gold_kpi_autorizacoes`)
- **Processamento**: SQL queries, agregações, filtros
- **Saída**: Métricas, distribuições, contagens, taxas, rankings de entidades
- **Características**: Respostas baseadas em fatos observáveis do sistema em tempo real

### Integração
- O agente do módulo 3 combina ambas as estratégias:
  - Consultas RAG para questões sobre políticas/regras (contexto fixo dos PDFs)
  - Consultas Genie para questões sobre operação/status do sistema (contexto dinâmico)
  - MCP gerenciado fornece Vector Search (RAG) e Genie (Databricks)
