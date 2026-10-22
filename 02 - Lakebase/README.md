# 02 - Lakebase

A silver já tem uma linha por guia, atualizada a cada 10 min. Agora vamos levá-la para onde o app consegue ler e gravar em milissegundos.

Responder "qual o status da guia AUT-00058?" e gravar a observação do atendente é trabalho de banco transacional (OLTP), não de lakehouse. Neste módulo, você copia a `silver_autorizacao_status` para o **Lakebase**, o Postgres gerenciado do Databricks, com uma **synced table**, e cria no Postgres a tabela onde o app vai escrever.

## Objetivo
- Adicionar ao bundle uma synced table *Triggered* e a task que a sincroniza depois de cada run do pipeline
- Conectar no Postgres com o seu usuário do Databricks e conferir que a cópia acompanha a silver
- Criar a tabela de escrita `observacao_atendente`

## Como fica

```
gerador → Volume → pipeline → silver_autorizacao_status ──sync_lakebase──▶ Postgres: <aluno>.autorizacao_status (só leitura)
                                                                           Postgres: <aluno>.observacao_atendente (o app escreve)
```

O projeto Lakebase `edia-workshop` já existe: o instrutor criou um para a turma. Dentro dele, você tem o seu próprio schema Postgres, com o mesmo nome do seu schema no Unity Catalog.

---

## Partes

- [2.1 - Synced table no bundle](2.1%20-%20Synced%20table%20no%20bundle.md)
- [2.2 - Explorando o Lakebase](2.2%20-%20Explorando%20o%20Lakebase.md)
