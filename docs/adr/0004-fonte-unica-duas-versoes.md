# ADR-0004: Fonte única para a versão principal e a versão do cliente

Status: aceito (2026-10-15)

## Contexto
A versão principal não tem analogias com Kafka/K8s/Helm. Uma versão paralela, para um cliente específico, tem.

## Decisão
Notebooks e READMEs são idênticos nas duas versões e nunca mencionam Kafka/K8s/Helm. As analogias vivem num `analogias.md` (tabela De → Para + "onde a analogia quebra"), só onde o pedido original (`docs/original_ref.md`) pede analogia: pipeline, jobs e DABs, que hoje são todos o módulo 01. Revisto em 2026-10-20: os módulos 02–04 não têm `analogias.md`. `mkdocs.yml` não inclui essas páginas. `mkdocs-cliente.yml` inclui.

## Consequências
Uma única base para manter. Nada de branch divergente. O GitHub Pages publica as duas: o `mkdocs.yml` na raiz do site e o `mkdocs-cliente.yml` em `/compared/` (`.github/workflows/docs.yml`). As duas herdam o `mkdocs-base.yml`; cada uma declara o próprio `nav`. O `analogias.md` fica no repo público: é genérico (Kafka/K8s/Helm), sem o nome do cliente. A versão do cliente não tem link a partir da principal.
