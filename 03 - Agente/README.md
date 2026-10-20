# 03 - Agente

O status das guias já está no Postgres. Agora vamos dar ao atendente alguém a quem perguntar.

Ele recebe dois tipos de pergunta: as de regra ("qual o prazo de uma ressonância?"), que estão nos PDFs da operadora, e as de número ("quantas ressonâncias estão em análise agora?"), que estão nas suas tabelas. Neste módulo, você publica um **agente** que responde as duas: ele busca nos documentos com **AI Search** (RAG), consulta as tabelas com a **Genie** e lembra da conversa.

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

## Partes

- [3.1 - AI Search](3.1%20-%20AI%20Search.md)
- [3.2 - Genie space](3.2%20-%20Genie%20space.md)
- [3.3 - Deploy do agente](3.3%20-%20Deploy%20do%20agente.md)
- [3.4 - Testando o agente](3.4%20-%20Testando%20o%20agente.md)
