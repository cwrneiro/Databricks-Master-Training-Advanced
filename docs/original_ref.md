1. Data Pipeline: Delta, CDF, Structured Streaming, foreachBatch e MERGE
Objetivo: Apresentar os conceitos fundamentais de manipulação de dados. Hoje eles usam Kafka e pode ser bom fazer analogias entre:
Tópicos vs Delta Table com CDF
Offset do consumidor vs checkpoint
Consumers vs foreachBatch
O time deve ser capaz de construir ETS que aceitam retry sem duplicação de dados.


2. Jobs
Objetivo: apresentar comparativo entre Deployments e CronJobs do K8s por Jobs com dependência entre tasks, execução única (max_concurrent_runs: 1 com fila) e availableNow, para que nenhum cluster fique ligado à toa.

3. DABs
Objetivo: versionar e fazer deploy do pipeline inteiro como código, com targets de dev e prod, do mesmo jeito que hoje usam Helm ou Terraform, e rodar tudo via CI com bundle deploy.

4. Lakebase
Objetivo: servir a saída do pipeline para as aplicações com um Postgres gerenciado, alimentado por synced tables a partir do Delta. Isso substitui o padrão “consome do Kafka e grava no Postgres”. Memória de agentes entra como segundo caso de uso mas não acredito que é must have.

5. Databricks Apps
Objetivo: mostrar que o time pode continuar construindo frontends em React/Node, agora rodando junto dos dados, com autenticação nativa e conectados ao Lakebase e ao agente. Não coloquei em prioridade pq o custo dessa solução atualmente é bem alto.

6. LangChain + MCP da Genie
Objetivo: mostrar o que a plataforma permite quando as camadas de pipeline e de serving já existem, com um agente de RAG usando os chunks indexados e a Genie via MCP. A meta é dar um gostinho da solução, não domínio.
