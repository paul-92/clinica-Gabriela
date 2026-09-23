# SPEC-005 — Evidence de reconciliação D005-08

Data: 22/09/2026

Classificação: `VERIFIED_BY_IMPLEMENTATION_EXECUTOR`

Estado: `READY_FOR_SPEC005_D005_08_INDEPENDENT_REVIEW`

## Context recovery

- Repositório: Clínica Gabriela, raiz local verificada.
- Branch: `feature/spec-008-architecture-foundation`.
- HEAD inicial: `b466fb8481d049d1e954c3960238b8af04ae5018`.
- Upstream: `origin/feature/spec-008-architecture-foundation`, sync `0/0`.
- Worktree preexistente preservado, inclusive `.context/COMMANDS.md` e diretórios
  forenses/homologação não relacionados.
- SPEC, plano D005-08, decisão R1–R6, Evidence E002–E010 e handoff integralmente
  reconciliados com Git e estado material.

## Implementação reconciliada

| Camada | Resultado D005-08 |
|---|---|
| Database/model | `competence_date` removido; colunas inteiras `competence_year` e `competence_month`; checks ano `1..9999`, mês `1..12`; índices compostos mensais |
| Schemas/API | create/read/update por ano+mês; update exige par completo; `competence_period` serializa `YYYY-MM`; payload diário é rejeitado |
| Filtros | CASH usa `start`/`end` diários; ACCRUAL usa quatro limites explícitos de ano/mês e comparação semiaberta |
| Repository/service | consultas ACCRUAL operam por chave cronológica ano/mês; CASH continua por `paid_at`; payloads e summaries não misturam regimes |
| Frontend | inputs de competência usam `type="month"`; parsing gera o par canônico; filtro ACCRUAL não cria `YYYY-MM-DD`; exibição usa `YYYY-MM` |
| Reports/dashboard | resumo financeiro mantém CASH e ACCRUAL separados; frontend renderiza o regime e o período devolvidos pela API |
| Migration | schema candidato e índices usam ano/mês; fonte diária é `REVIEW/BLOCK`; paid sem `paid_at` continua `REVIEW/BLOCK`; proteções operacionais preservadas |
| Seed | fixtures financeiras sintéticas usam ano/mês atual sem fabricar dia de competência |

## Harness first

Após atualizar somente o harness de schema/contrato, a primeira execução produziu:

- `2 failed, 6 passed`;
- falhas causais: ausência de `competence_year` e `competence_month` no modelo;
- nenhuma asserção foi enfraquecida para obter GREEN.

Depois da implementação e dos repair loops, o mesmo escopo e seus descendentes
ficaram verdes.

## Selective invalidation E002–E010

| Unidade | Previous status | Invalidation reason | Revalidation | New status |
|---|---|---|---|---|
| E002 | PASS | fixtures/harness descreviam campo diário | RED causal e suite schema/contrato com ano/mês e casos negativos | REVALIDATED |
| E003 | PASS | modelo, schema, constraints e índices usavam `competence_date` | introspecção SQLAlchemy, Pydantic e constraints SQLite | REVALIDATED |
| E004 | PASS técnico | migrador criava/copiava competência diária | candidato sintético ano/mês, rejeição diária, recovery, R2 e guards operacionais | REVALIDATED; operacional não executado |
| E005 | PASS | serviços serializavam e validavam data diária | domínio CASH/ACCRUAL, período mensal, lifecycle e `paid_at` invariant | REVALIDATED |
| E006 | PASS | repository filtrava ACCRUAL por DATE | filtros por chave ano/mês, dezembro/janeiro e regressão CAS | REVALIDATED |
| E007 | PASS | contratos e queries da API usavam datas para ACCRUAL | payloads, 422 legado, filtros mensais, auth e erros controlados | REVALIDATED |
| E008 | PASS | UI usava seletor diário e payload `competence_date` | testes JS, `type="month"`, query mensal sem dia e build Vite | REVALIDATED |
| E009 | PASS | sem dependência causal da representação de competência | autoridade legada reexecutada na suite SPEC-005 | PRESERVED / REGRESSION PASS |
| E010 | PASS | rastreabilidade e regressão dependentes ficaram desatualizadas | SPEC-005, regressão afetada, full suite, docs e checks finais | REVALIDATED |

## Rastreabilidade D005-08

`D005-08 → competência mensal explícita → model/schema/repository/service/API/UI/migration → testes Python/JS/build → esta Evidence`.

Cobertura material:

- criação e persistência por ano/mês;
- ano fora de `1..9999`, mês `0` e mês `13` rejeitados em schema e banco;
- par obrigatório e atômico;
- ausência de `competence_date` canônico;
- `competence_period` em `YYYY-MM`;
- filtros mensais e fronteira dezembro/janeiro;
- ACCRUAL por ano/mês e CASH por `paid_at`;
- frontend sem input diário;
- migração sem fabricação de dia;
- R1–R6 em `2026/7` no registro HUMAN;
- R2 bloqueado, sem inferência de `paid_at`.

## R1–R6 e R2

- R1–R6: decisão HUMAN validada como `competence_year=2026` e
  `competence_month=7`.
- R2: `status=paid`, `paid_at=null/desconhecido`.
- Inferência de `paid_at`: `PROHIBITED / NOT PERFORMED`.
- Eligibility: `REVIEW/BLOCK / EXCLUDED_FROM_VALID_CANONICAL_CANDIDATE`.
- A invariant `paid → paid_at obrigatório` permanece no modelo candidato, migrador,
  serviço e testes.

## Validação

- RED inicial: `2 failed, 6 passed` pela causa esperada.
- Primeiro GREEN direcionado: `35 passed`.
- SPEC-005 final: `44 passed`.
- Regressão diretamente afetada: `59 passed`.
- Full Python suite: `281 passed`.
- Frontend: `12 passed`.
- Vite build: `PASS`, 1.582 módulos transformados.
- Falhas ambientais reproduzidas: ACL de `tmp_path` no sandbox e `spawn EPERM` do
  esbuild; ambos foram repetidos fora do sandbox com raízes/execuções isoladas.

## Limites operacionais

- Generation antes/depois: `8/canonical`.
- Pointer SHA-256 antes: `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`.
- Manifest SHA-256 antes: `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`.
- Database SHA-256 antes: `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`.
- Valores finais são registrados após a sentinela final no handoff.
- E011/E012, migração operacional, candidate promotion e cutover: `NOT EXECUTED`.
- Staging, commit, push, merge, rebase, tag e release: `NOT EXECUTED`.

## Próximo gate

`READY_FOR_SPEC005_D005_08_INDEPENDENT_REVIEW`.

Esta classificação não equivale a E011, E012, candidato operacional, promoção,
cutover ou aceitação HUMAN final.
