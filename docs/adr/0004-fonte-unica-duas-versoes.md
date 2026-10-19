# ADR-0004: Fonte única para a versão principal e a versão do cliente

Status: aceito (2026-10-15)

## Contexto
A versão principal não tem analogias com Kafka/K8s/Helm. Uma versão paralela, para um cliente específico, tem.

## Decisão
Notebooks e READMEs são idênticos nas duas versões e nunca mencionam Kafka/K8s/Helm. As analogias vivem num `analogias.md` por módulo (tabela De → Para + "onde a analogia quebra"). `mkdocs.yml` não inclui essas páginas. `mkdocs-cliente.yml` inclui.

## Consequências
Uma única base para manter. Nada de branch divergente. O `mkdocs.yml` existe desde a issue 17 e é o que o GitHub Pages publica; o `mkdocs-cliente.yml` vem na issue 18.
