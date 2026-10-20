# 01 - Pipeline e bundle

Os eventos de autorização já estão chegando no Volume, um lote a cada 10 min. Vamos transformá-los no status atual de cada guia.

Você recebe um **bundle** pronto: um `databricks.yml` que declara, em código, o seu schema, um pipeline e um job. Você faz deploy em `dev`, vê o job falhar, corrige o pipeline e promove para `prod`. Tudo o que vem depois, no resto do dia, se apoia no que você sobe aqui.

## Objetivo
- Conhecer a estrutura de um bundle e a UI de bundles do workspace
- Entender o pipeline (Lakeflow Spark Declarative Pipelines): Auto Loader, expectations, `AUTO CDC`, materialized view e sink
- Fazer deploy em `dev`, corrigir um bug e promover para `prod`

---

## Partes

- [1.1 - Deploy do bundle](1.1%20-%20Deploy%20do%20bundle.md)
- [1.2 - Job e pipeline](1.2%20-%20Job%20e%20pipeline.md)
