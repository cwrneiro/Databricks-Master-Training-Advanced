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

## Partes

- [4.1 - App no bundle](4.1%20-%20App%20no%20bundle.md)
- [4.2 - Usando o app](4.2%20-%20Usando%20o%20app.md)
