# SPEC-001 — Auditoria, Estabilização e Evolução

Status: DONE — auditoria estática. Implementação: não iniciada.
Prioridade: P0/P1. Tipo: Brownfield.

## Objetivo
Estabelecer uma baseline técnica e funcional do software existente antes de modificar seu comportamento.

## Arquitetura observada
- Desktop Tkinter com services, repositories e SQLite próprio.
- Electron/React consumindo FastAPI, com outro SQLite.
- Módulos: autenticação, pacientes, psicólogos, agenda, prontuário, financeiro, relatórios, configurações, backup e licenciamento.
- Testes identificados na auditoria: tests/test_security.py.

## Achados
1. P0: rotas privadas da API sem autenticação/autorização efetiva.
2. P0: fallback de login admin/admin123 no Electron.
3. P0/P1: acesso clínico sem proteção adequada por perfil.
4. P1: aplicação efetiva das Foreign Keys SQLite precisa ser comprovada.
5. P1: ausência de prevenção de conflitos de agenda confirmada.
6. P1/P2: validações financeiras insuficientes e cálculo chamado mensal que agrega histórico.
7. P1: backup cobre somente o banco desktop.
8. P1/P2: licenciamento local precisa de fortalecimento para distribuição comercial.
9. P1: cobertura automatizada insuficiente.
10. P1: duas fontes persistentes independentes.

## Resultado
Auditoria estática concluída; achados convertidos em SPEC-002 a SPEC-010.
Não equivale a homologação funcional ou execução de testes.

## Regras
Preservar dados, licenciamento e arquitetura existente até migração aprovada.
Não usar dados reais em testes. Não alterar main sem autorização.
