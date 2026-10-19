# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
O atendente da Vida+ Saúde, uma operadora de plano de saúde fictícia. Ele atende prestadores (hospitais, clínicas, médicos) que ligam para saber de autorizações prévias: consulta o status atual de uma guia, registra uma observação sobre ela e tira dúvidas de regra (prazos, coberturas) ou de número (quantas estão em análise) com um agente. No workshop, o aluno faz o papel desse atendente com o próprio app; o design serve o atendente, não o aluno (decisão do usuário, 2026-10-17).

## Product Purpose
Uma tela de atendimento: achar uma autorização pelo ID (ou pelo beneficiário/prestador), ver o status atual, deixar uma observação, e perguntar ao agente sem sair da tela. Sucesso: o atendente responde ao prestador em segundos para status e observações, e em até alguns minutos para perguntas ao agente, sem perder o contexto da conversa.

## Operating Context
- Os status chegam ao longo do dia (um lote a cada 10 min): `solicitada → em_analise → aprovada | negada`. A tela mostra o estado atual, não um histórico.
- Status e observações vêm do Postgres (Lakebase), em milissegundos. As respostas do agente levam de ~10 s (documentos) a alguns minutos (Genie, consulta às tabelas).
- O usuário logado vem da autenticação nativa do Databricks Apps (e-mail); ele é o autor das observações e o dono da memória do agente.
- Exibido também em projetor durante o workshop.

## Capabilities and Constraints
- Stack fixa: AppKit (React + `@databricks/appkit-ui` + Tailwind), servidor Express do AppKit.
- `autorizacao_status` é só leitura (synced table). `observacao_atendente` aceita inserção, sem edição nem exclusão.
- IDs: autorizações `AUT-00001`, prestadores `PRE-001`, beneficiários `BEN-0001`. Procedimentos são códigos (`ressonancia_magnetica`, `consulta_cardiologia`...), exibidos por extenso.
- O chat é uma sessão por conversa (`session_id`); "nova conversa" abre outra. A resposta do agente vem em markdown e diz quais tools usou (documentos ou Genie).
- Interface em PT-BR.

## Brand Commitments
- Nome: Vida+ Saúde. Fictícia: nunca usar nomes, cores ou logos de operadoras reais.
- Sem ativos de marca; a identidade visual fica a critério do design (decisão do usuário, 2026-10-17).

## Evidence on Hand
- Dados sintéticos do gerador (`00 - Setup and teardown/data/src/generator.py`) e perguntas de exemplo com respostas conferidas em `03 - Agente/perguntas.md`. Não inventar números, clientes ou depoimentos.

## Product Principles
- Status primeiro: a pergunta mais comum ("como está a guia X?") se resolve com uma busca e um olhar.
- Espera honesta: quando o agente demora, a tela diz o que está acontecendo e não trava o resto do trabalho.
- Erros que dizem o que fazer: falta de permissão ou de tabela vira uma instrução, não um stack trace.
- Ferramenta, não vitrine: densidade e leitura rápida acima de decoração.
