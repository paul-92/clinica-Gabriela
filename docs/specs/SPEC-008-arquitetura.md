# SPEC-008 — Unificação Arquitetural

Status: DRAFT. Prioridade: P1.
Dependências: SPEC-002; alinhamento com SPEC-003/006/010.

## Objetivo
Consolidar uma fonte operacional de verdade e um núcleo de regras de negócio.

## Arquitetura alvo proposta
Electron/React → FastAPI → Services → Repositories → SQLite único.

## Decisões propostas
- Electron/React como interface operacional principal.
- Backend FastAPI como autoridade de regras e persistência.
- Tkinter permanece legado durante transição; não apagar antes de paridade e aceite.
- Banco backend é candidato à autoridade futura, sujeito a inventário e validação.
- Não manter dois bancos independentes como operação permanente.

## Requisitos
- Inventariar schemas, modelos, serviços, migrations e dados.
- Definir banco alvo e diretório persistente.
- Mapear campos e relacionamentos sem perda.
- Migração auditável, não destrutiva, com backup e rollback.
- Validar contagens, relacionamentos e equivalência.
- Electron utiliza API real; sem fallback silencioso em produção.
- Não duplicar novas regras críticas no Tkinter.
- Preservar legado até aceite explícito.

## Gates
1. MIGRATION_MATRIX.md.
2. Definição DB_TARGET.
3. Consolidação de modelos.
4. Script de migração e backup.
5. Validação antes/depois.
6. Fluxos Electron via API.
7. Classificação do Tkinter como legado.
8. Alinhamento com backup.
9. Alinhamento com instalador.

## Aceitação
Uma fonte operacional ativa, migração comprovada sem perda, rollback documentado, API como autoridade e legado preservado até aceite.

## Fora do escopo
Cloud, PostgreSQL, SaaS, mobile, novo layout e novas regras de negócio.
