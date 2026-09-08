# SPEC-007 — Baseline de Testes Automatizados

Status: BACKLOG — especificação detalhada pendente. Prioridade: P1.

## Objetivo preliminar
Criar baseline de regressão para autenticação, pacientes, psicólogos, agenda, prontuário, financeiro, configurações, licença e backup.

## Diretrizes
- Testes unitários, de API, integração e smoke.
- Bancos temporários e dados fictícios.
- Testes de segurança iniciados na SPEC-002.
- Registrar comandos, resultados, falhas e bloqueios.
- Não declarar cobertura ou aprovação sem execução.
- Definir metas de cobertura e ferramentas após inventário.

A suíte identificada na auditoria contém tests/test_security.py; revalidar estado atual antes de implementar.
