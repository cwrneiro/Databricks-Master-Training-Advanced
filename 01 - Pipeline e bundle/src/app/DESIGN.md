---
name: Vida+ Saúde · Central de autorizações
description: Tela do atendente desenhada como uma guia TISS em papel, com o status carimbado em tinta.
colors:
  mesa: "#dfe6f1"
  papel: "#ffffff"
  tinta: "#1b2b4b"
  tinta-2: "#44567a"
  azul: "#2f5da8"
  violeta: "#5b3a8c"
  vermelho: "#c0392b"
  regua: "#9fb0cc"
  tom: "#eef2f9"
  faixa-texto-suave: "#c6d3ea"
  faixa-fio: "#5d7099"
  marca-mais: "#8fb2ee"
  selecao: "#c9d6ee"
  placeholder: "#5f6f8f"
typography:
  marca:
    fontFamily: "\"Helvetica Neue\", Helvetica, Arial, sans-serif"
    fontSize: "18px"
    fontWeight: 800
    letterSpacing: "0.02em"
  titulo-guia:
    fontFamily: "\"Helvetica Neue\", Helvetica, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 700
    letterSpacing: "0.03em"
  valor-campo:
    fontFamily: "\"Helvetica Neue\", Helvetica, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 600
  contagem:
    fontFamily: "\"Helvetica Neue\", Helvetica, Arial, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.1
  body:
    fontFamily: "\"Helvetica Neue\", Helvetica, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "\"tnum\""
  rotulo:
    fontFamily: "\"Helvetica Neue\", Helvetica, Arial, sans-serif"
    fontSize: "11px"
    fontWeight: 700
    letterSpacing: "0.08em"
  faixa:
    fontFamily: "\"Helvetica Neue\", Helvetica, Arial, sans-serif"
    fontSize: "11px"
    fontWeight: 700
    letterSpacing: "0.1em"
  carimbo:
    fontFamily: "\"Helvetica Neue\", Helvetica, Arial, sans-serif"
    fontSize: "22px"
    fontWeight: 900
    letterSpacing: "0.08em"
  etiqueta:
    fontFamily: "\"Helvetica Neue\", Helvetica, Arial, sans-serif"
    fontSize: "10px"
    fontWeight: 800
    letterSpacing: "0.06em"
  mono:
    fontFamily: "\"SF Mono\", Menlo, Consolas, \"Courier New\", monospace"
    fontSize: "0.95em"
rounded:
  none: "0px"
spacing:
  "2": "2px"
  "4": "4px"
  "6": "6px"
  "8": "8px"
  "10": "10px"
  "12": "12px"
  "16": "16px"
components:
  button-primary:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.papel}"
    rounded: "{rounded.none}"
    padding: "7px 14px"
  button-primary-hover:
    backgroundColor: "{colors.azul}"
    textColor: "{colors.papel}"
  button-claro:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.none}"
    padding: "7px 14px"
  button-claro-hover:
    backgroundColor: "{colors.tom}"
    textColor: "{colors.tinta}"
  button-faixa:
    backgroundColor: "transparent"
    textColor: "{colors.papel}"
    typography: "{typography.rotulo}"
    rounded: "{rounded.none}"
    padding: "2px 8px"
  input:
    backgroundColor: "{colors.tom}"
    textColor: "{colors.tinta}"
    typography: "{typography.body}"
    rounded: "{rounded.none}"
    padding: "7px 10px"
  faixa-titulo:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.papel}"
    typography: "{typography.faixa}"
    padding: "6px 10px"
  campo:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta}"
    typography: "{typography.valor-campo}"
    padding: "3px 6px 5px"
    height: "46px"
  etiqueta:
    backgroundColor: "transparent"
    typography: "{typography.etiqueta}"
    padding: "0 5px"
  carimbo:
    backgroundColor: "transparent"
    typography: "{typography.carimbo}"
    padding: "2px 12px"
---

# Design System: Vida+ Saúde · Central de autorizações

## Overview

**Creative North Star: "A Guia TISS"**

Cada autorização é uma guia de papel, e a tela é o formulário que o atendente já conhece. Folhas brancas ficam sobre uma mesa azul-acinzentada; tudo o que é estrutura (bordas, faixas de seção, cabeçalho) é desenhado em uma única tinta azul-formulário, com fio de 1 px e raio zero. Os campos são caixas numeradas ("1 - Número da guia"), com o rótulo pequeno em azul e o valor logo abaixo, como na guia impressa.

A situação da guia não é um badge: é tinta de carimbo. Cada situação tem uma tinta (solicitada, em análise, aprovada, negada), e a mesma tinta aparece na etiqueta da lista, na contagem do quadro e no carimbo grande da guia aberta. O carimbo tem borda dupla, leve rotação e "bate" ao abrir uma guia ou quando a situação muda.

A densidade é de ferramenta: corpo de 14 px, entrelinha compacta, números tabulares, três colunas lado a lado no desktop. Nada de cartão arredondado, sombra projetada, gradiente decorativo ou contador de painel SaaS.

**Key Characteristics:**
- Papel branco sobre mesa azul-acinzentada, uma tinta só para a estrutura.
- Raio zero e fio de 1 px em todo lugar; profundidade por fio e tom, nunca por sombra projetada.
- Campos numerados em caixas, com rótulo em maiúsculas pequenas e tracking.
- Situação codificada por tinta, repetida em etiqueta, contagem e carimbo.
- Helvetica/Arial como nos formulários da ANS; mono só para IDs e datas.

## Colors

Uma tinta azul-escura de formulário sobre papel branco, com três tintas de carimbo reservadas à situação.

### Primary
- **Tinta Azul-Formulário** (tinta): bordas de 1 px de folhas, campos e entradas; faixas de título e de seção; cabeçalho; botão principal; texto padrão. Também é a tinta do carimbo "solicitada".
- **Azul de Rótulo** (azul): rótulos de campo e de entrada, anel de foco, cursor de texto, hover do botão principal, borda da mensagem do agente e das fontes citadas. Também é a tinta do carimbo "aprovada".

### Secondary
- **Violeta de Carimbo** (violeta): só a situação "em análise" (etiqueta, contagem, carimbo) e os pontos de espera do agente.
- **Vermelho de Carimbo** (vermelho): só a situação "negada" e os estados de erro (aviso de erro, mensagem de erro do agente).

### Neutral
- **Mesa Azul-Acinzentada** (mesa): fundo da página, visível entre as folhas.
- **Papel** (papel): fundo de folhas, campos, fichas e botão claro; texto sobre faixas de tinta.
- **Tom de Formulário** (tom): fundo de entradas, hover e seleção de fichas e caixas do quadro, faixa de total, linha de carregamento.
- **Régua** (regua): divisórias internas (entre fichas, entre caixas do quadro, entre observações), borda tracejada do aviso, tabelas no markdown do agente, polegar da rolagem.
- **Tinta Secundária** (tinta-2): metadados (hora da ficha, procedimento e IDs da ficha, autor da observação, mensagem em espera).
- **Texto Suave da Faixa** (faixa-texto-suave): subtítulo e hora no cabeçalho escuro.
- **Fio da Faixa** (faixa-fio): bordas de 1 px de elementos sobre a tinta (e-mail do usuário, botão de faixa).
- **Mais da Marca** (marca-mais): só o "+" de "Vida+" no cabeçalho.
- **Seleção** (selecao): fundo da seleção de texto.
- **Placeholder** (placeholder): texto de exemplo nas entradas.

### Named Rules
**The Uma Tinta por Situação Rule.** Cada situação tem exatamente uma tinta (solicitada = tinta, em análise = violeta, aprovada = azul, negada = vermelho), aplicada por uma variável de situação; a mesma tinta vai na etiqueta, na contagem e no carimbo. Não introduza verde, amarelo ou outra cor para status.

**The Tinta Estrutural Rule.** Toda estrutura (bordas de folha e campo, faixas, cabeçalho) usa a tinta azul-formulário. Violeta e vermelho nunca viram cor de estrutura ou de decoração.

## Typography

**Body Font:** Helvetica Neue (com Helvetica, Arial, sans-serif)
**Label/Mono Font:** SF Mono (com Menlo, Consolas, Courier New, monospace)

**Character:** A grotesca neutra dos formulários impressos da ANS, usada em todas as funções; a hierarquia vem de peso, caixa e tracking, não de troca de família. A mono marca o que é identificador ou data.

### Hierarchy
- **Marca** (800, 18 px, tracking 0.02em): só "Vida+ Saúde" no cabeçalho.
- **Carimbo** (900, 22 px; 18 px abaixo de 600 px; tracking 0.08em, maiúsculas): o carimbo de situação da guia aberta.
- **Contagem** (700, 22 px, entrelinha 1.1; 18 px abaixo de 600 px): números do quadro de situações, na tinta da situação. O total usa 16 px.
- **Título da Guia** (700, 15 px, tracking 0.03em, maiúsculas): o título impresso da guia ("Guia de autorização prévia").
- **Valor de Campo** (600, 15 px): o conteúdo de cada campo numerado, quebrando em qualquer ponto.
- **Body** (400, 14 px, entrelinha 1.4; 1.45 em parágrafos e listas; números tabulares): texto corrido, observações (até 70ch), entradas. Mensagens do chat usam 13 px; metadados, 12 px.
- **Rótulo** (700, 11 px, tracking 0.08em, maiúsculas, azul): rótulos de campo e de entrada, nomes de situação no quadro, autor da mensagem.
- **Faixa** (700, 11 px, tracking 0.1em, maiúsculas, branco sobre tinta): faixas de título das folhas e faixas de seção dentro da guia.
- **Etiqueta** (800, 10 px, tracking 0.06em, maiúsculas): etiqueta de situação na lista.
- **Mono** (0.95em): IDs (AUT-, BEN-, PRE-), datas, horas e o cronômetro de espera.

### Named Rules
**The Rótulo Pequeno Rule.** Rótulos de formulário são maiúsculas reais de 11 px com tracking de 0.08em a 0.1em, em peso 700. Eles nomeiam campos, entradas e seções; não servem de chamada decorativa acima de títulos.

**The Mono É Identificador Rule.** A mono aparece só em IDs, datas, horas e contadores de tempo. Texto corrido, nomes de procedimento e e-mails ficam na grotesca.

## Layout

Página de altura total em coluna: cabeçalho escuro (padding 8 px 16 px), faixa de busca em largura total sobre papel, fechada por um fio de 2 px de tinta, e a mesa com três folhas lado a lado. As colunas são `minmax(320px, 1fr) minmax(460px, 1.5fr) minmax(320px, 1.1fr)` (fichário, guia aberta, agente), com 12 px de gutter e 12 px de margem; cada folha rola por dentro, então a busca e o cabeçalho nunca saem da tela.

Dentro da guia, os campos vivem numa grade de 6 colunas: campo padrão ocupa 2, largo ocupa 3, inteiro ocupa 6, e as faixas de seção ocupam a linha toda. O quadro de situações é uma grade de 4 caixas com a faixa de total embaixo. O ritmo de espaçamento é miúdo e de formulário: 2, 4, 6, 8, 10, 12 e 16 px.

Abaixo de 1100 px as colunas empilham, a página passa a rolar e as listas ganham altura máxima de 460 px (a guia não tem limite). Abaixo de 600 px todos os campos ocupam a linha toda, a busca empilha rótulo e entrada, o cabeçalho da guia empilha título e carimbo, e os botões de ação ficam em largura total, com a ação principal em cima.

## Elevation & Depth

O sistema é plano: nenhuma sombra projetada. Profundidade vem de três camadas tonais (mesa, papel, tom) e de fios de tinta. O que parece sombra no código é só fio desenhado por dentro: a caixa do quadro selecionada ganha um sublinhado interno de 3 px na tinta da situação (`box-shadow: inset 0 -3px 0 var(--st)`), a ficha selecionada ganha um contorno interno de 1 px de tinta (`box-shadow: inset 0 0 0 1px var(--tinta)`), e a mensagem do agente dobra o fio azul (`box-shadow: inset 0 0 0 1px var(--azul)`).

### Named Rules
**The Fio, Não Sombra Rule.** Estado e destaque se desenham com fio (borda ou `inset` sem desfoque), nunca com sombra projetada ou desfocada. Folhas ficam sobre a mesa por contraste tonal e borda de 1 px.

## Shapes

Raio zero em tudo, inclusive entradas e botões (o raio do appkit-ui é anulado). A forma vem do vocabulário do papel impresso: fio sólido de 1 px para estrutura, fio de 2 px sob a busca, tracejado de régua para avisos e para a mensagem em espera, pontilhado de régua entre observações, e borda dupla de 3 px no carimbo. As únicas formas inclinadas são de tinta carimbada: a etiqueta da lista a -2° e o carimbo da guia a -6°. Marcadores de lista são quadrados; os pontos de espera são quadrados de 6 px.

## Components

### Buttons
Blocos de tinta retos, de formulário.
- **Shape:** cantos retos (0), borda de 1 px.
- **Primary:** fundo tinta, texto papel, peso 700, padding 7 px 14 px. No build, o texto usa versalete sintetizado (`font-variant: small-caps` com caixa baixa, tracking 0.05em).
- **Hover / Focus:** hover troca fundo e borda para azul; foco é o contorno global de 2 px azul com 1 px de afastamento. Desabilitado fica a 45% de opacidade.
- **Claro:** fundo papel, texto tinta, mesma borda; hover vai para o tom. Usado para a ação secundária ("Perguntar ao agente") ao lado da principal.
- **Botão de faixa:** dentro de uma faixa de título, transparente, texto branco no estilo de rótulo (11 px, 700, tracking 0.08em, maiúsculas), fio da faixa de 1 px, padding 2 px 8 px; hover deixa o fio branco; desabilitado a 40%.

### Inputs / Fields
- **Style:** fundo tom, borda de 1 px de tinta, raio 0, padding 7 px 10 px, fonte herdada; placeholder na cor placeholder. Áreas de texto têm altura mínima de 64 px e redimensionam na vertical (a do chat não redimensiona).
- **Focus:** contorno global de 2 px azul, afastado 1 px.
- **Label:** sempre um rótulo visível no estilo Rótulo, ligado à entrada.

### Folha e faixa de título
- **Corner Style:** reto (0).
- **Background:** papel, com borda de 1 px de tinta.
- **Shadow Strategy:** nenhuma (ver Elevation & Depth).
- **Faixa de título:** primeira linha de toda folha, fundo tinta, texto no estilo Faixa, padding 6 px 10 px; pode levar um botão de faixa à direita.

### Campo numerado (componente-assinatura)
Caixa da grade de 6 colunas com fio de tinta à direita e embaixo (a grade fecha em cima e à esquerda), altura mínima de 46 px, padding 3 px 6 px 5 px. Rótulo no formato "n - Nome" e valor no estilo Valor de Campo, em mono para IDs e datas. Faixas de seção ("Beneficiário e prestador") cortam a grade em largura total com o estilo Faixa e padding 2 px 6 px.

### Carimbo e etiqueta (componente-assinatura)
- **Carimbo:** texto da situação em maiúsculas, 900, 22 px, borda dupla de 3 px na tinta da situação, padding 2 px 12 px, rotação de -6°, opacidade 0.92. Fica no canto superior direito da guia. Ao abrir uma guia ou mudar a situação, "bate": parte de -2° e escala 1.35 transparente e assenta em 180 ms com `cubic-bezier(0.16, 1, 0.3, 1)`. Sem animação com movimento reduzido.
- **Etiqueta:** a versão de lista, 10 px, 800, maiúsculas, borda de 1.5 px na tinta da situação, padding 0 5 px, rotação de -2°.

### Quadro de situações e fichas
- **Quadro:** 4 caixas lado a lado separadas por fio de régua, cada uma com rótulo e contagem na tinta da situação; clicar filtra a lista (estado pressionado = fundo tom e sublinhado interno de 3 px). Embaixo, faixa de total sobre tom.
- **Ficha:** linha de lista em grade (ID mono em peso 700, etiqueta, hora mono à direita; procedimento e IDs embaixo em 12 px tinta-2), padding 6 px 10 px, fio de régua embaixo. Hover = tom; selecionada = tom com contorno interno de 1 px de tinta.
- **Carregando:** fichas vazias pautadas (listras de papel e tom) e linhas de tom de 14 px no lugar do texto.

### Avisos e mensagens do agente
- **Aviso:** caixa com tracejado de régua, padding 8 px 10 px, 13 px, com uma segunda linha de instrução em 12 px tinta-2. Erro troca borda e texto para vermelho.
- **Mensagem:** caixa reta de 1 px, padding 5 px 8 px, 13 px, até 92% da largura. Do atendente: à direita, fundo tom, borda tinta. Do agente: à esquerda, fio azul dobrado; as fontes usadas aparecem como pequenas etiquetas azuis de 10 px. Em espera: borda tracejada, texto tinta-2, três quadrados violeta piscando (1.2 s, defasados 0.2 s) e cronômetro mono. Erro: borda e texto vermelhos.

### Navigation
Não há navegação. O cabeçalho é uma faixa de tinta com a marca, o subtítulo, a hora da última atualização (empurrada à direita) e o e-mail do usuário numa caixa de fio da faixa.

## Do's and Don'ts

### Do:
- **Do** desenhar toda estrutura com fio de 1 px de tinta e raio 0, sobre papel branco, com a mesa visível entre as folhas.
- **Do** abrir toda folha com uma faixa de título de tinta e texto em maiúsculas de 11 px, 700, tracking 0.1em.
- **Do** mostrar dados da guia como campos numerados ("n - Nome") na grade de 6 colunas, separados por faixas de seção.
- **Do** aplicar a tinta de situação pela variável de situação, para que etiqueta, contagem e carimbo sempre concordem.
- **Do** usar mono só para IDs, datas, horas e cronômetros.
- **Do** marcar seleção e estado com fio interno sem desfoque (sublinhado de 3 px ou contorno de 1 px).
- **Do** usar tracejado de régua para avisos e espera, e vermelho só para erro e para "negada".

### Don't:
- **Don't** usar cantos arredondados, cartões flutuantes ou sombra projetada ou desfocada.
- **Don't** criar cores de status fora das quatro tintas de situação, nem usar violeta ou vermelho como decoração.
- **Don't** trocar o status carimbado por badges arredondados, pílulas ou contadores de painel SaaS.
- **Don't** usar rótulos de 11 px em maiúsculas como chamada decorativa acima de títulos; eles nomeiam campos, entradas e seções.
- **Don't** usar nomes, cores ou logos de operadoras reais.
