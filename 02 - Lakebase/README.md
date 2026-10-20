# 02 - Lakebase

O app do módulo 4 precisa responder em milissegundos "qual o status da autorização AUT-00058?" e gravar a observação que o atendente escreve. Isso é trabalho de banco transacional (OLTP), não de lakehouse. Neste módulo você leva a `silver_autorizacao_status` para o **Lakebase**, o Postgres gerenciado do Databricks, com uma **synced table**, e cria no Postgres a tabela onde o app vai escrever.

## Objetivo
- Adicionar ao bundle uma synced table *Triggered* e a task que a sincroniza depois de cada run do pipeline
- Conectar no Postgres com o seu usuário do Databricks e conferir que a cópia acompanha a silver
- Criar a tabela de escrita `observacao_atendente`

## Como fica

```
gerador → Volume → pipeline → silver_autorizacao_status ──sync_lakebase──▶ Postgres: <aluno>.autorizacao_status (só leitura)
                                                                           Postgres: <aluno>.observacao_atendente (o app escreve)
```

O projeto Lakebase `edia-workshop` já existe: o instrutor criou um para a turma. Cada aluno tem o próprio schema Postgres, com o mesmo nome do schema do Unity Catalog.

---

## Partes

- [2.1 - Synced table no bundle](2.1%20-%20Synced%20table%20no%20bundle.md)
- [2.2 - Populando a base](2.2%20-%20Populando%20a%20base.md)
