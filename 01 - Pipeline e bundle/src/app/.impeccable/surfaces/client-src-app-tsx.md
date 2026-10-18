---
version: 1
slug: "client-src-app-tsx"
primary_target: "client/src/App.tsx"
related_targets: []
---

Escopo: tela única do app do atendente (client/src/App.tsx). Modo: Operate.
Tarefa: achar uma guia, ver o status, registrar observação, perguntar ao agente sem perder a tela.

## Direction contract
THESIS: Cada autorização é uma guia TISS. A tela é o formulário que o atendente já conhece (campos numerados em caixas, rótulos em versalete, faixas de seção), e o status entra como carimbo de tinta. Recusa o painel SaaS de cartões, contadores e badges arredondados.
OWN-WORLD: Papel branco sobre mesa azul-acinzentada #DFE6F1; tinta azul-formulário #1B2B4B nas bordas de 1 px, faixas e cabeçalho; azul #2F5DA8 nos rótulos; carimbos em violeta #5B3A8C (em análise), azul (aprovada), vermelho #C0392B (negada), tinta (solicitada), com borda dupla e leve rotação. Arial/Helvetica, como os formulários da ANS; mono só para IDs e horas. Raio 0, sem sombra.
STORY: O atendente busca a guia, lê o carimbo num olhar, anota a ligação no campo de observação e pergunta ao agente na coluna ao lado enquanto a Genie demora.
FIRST VIEWPORT: Faixa de busca no topo, em largura total. Três colunas: fichário de guias (quadro de contagem por status em caixas numeradas, mais a lista); a guia selecionada no centro, maior, com o carimbo no canto superior direito; o agente à direita, com o campo de mensagem ancorado embaixo.
FORM: Guia TISS, candidato 1 da lista ordenada (escolha do usuário pelo pick); seed 25ffae0c. Interação-assinatura: o carimbo "bate" (escala e rotação assentando, 180 ms) ao abrir uma guia e quando o status muda numa atualização.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
