# SPEC-005 E011 — parecer independente do candidate real

Data: 2026-09-24. Papel: independent reviewer. Escopo: leitura do candidate existente; nenhuma migração, correção ou promoção.

## Contexto e identidades

- Repositório: `clinica_psicologia_desktop`; branch `feature/spec-008-architecture-foundation`; HEAD e upstream `c5100dd3cc347a9263c64a52a64d6bb0967b1db5`. Árvore previamente alterada, preservada.
- HANDOFF anterior terminava na remediação v9 pré-execução; first-write checkpoint e E011 Evidence registram a execução posterior. Autoridade independente real: registro de SHA `6974adba6c7a1ecfd633c46764e3f08d5fab2eb44ab6fd54ed80935cc5d23ba9`, vinculado ao artifact de SHA `f83413b3417facf0a227bf5261d2885df7e51a30f1d6ee0f109f08e33d851e46`. Binding checkpoint SHA `64ec020a5e9944c793a376925f9dcc6f8aae5a41380255f40028cea665305dbe` também recalculado.
- SOURCE_IDENTITY_RESULT: **PASS**, SHA recalculado sobre a fonte persistida `4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`.
- MIGRATION_IDENTITY_V9_RESULT: **PASS**, SHA do manifesto `90754472d5c15012e1caecf73cec272f3339bb6bc22ef2f6b1c3bb6b3b77649c`; 30 entradas recalculadas, closure de imports com os mesmos 30 caminhos.
- TRANSFORMATION_IDENTITY_RESULT: **PASS**, binding reproduzido `3dfcdd7c719a89fed15a7f15da0757adfc09ae2a592ddc4d16dcd412f2223035`.
- E011_EVIDENCE_RESULT: **PASS**, SHA do arquivo `db71cd7153901eef9a331b101b98173aa6975ab5303d1328213444ff7a48bf99`; claims comparados com o estado real, sem tratá-los como prova autônoma.

## Candidate e banco

- CANDIDATE_FOUND: **YES**, exatamente no caminho da Evidence: `C:\Users\PAULO~1.TRA\AppData\Local\Temp\spec005-e011-v9-78781bd6fa70\candidate.db`.
- CANDIDATE_SHA_RESULT: **PASS**; CANDIDATE_SHA: `bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb`, recalculado antes e depois da revisão.
- CANDIDATE_ISOLATED: **YES**, fora do runtime operacional; CANDIDATE_UNPROMOTED: **YES**, pointer ainda aponta Generation 8.
- CANDIDATE_INTEGRITY: `ok`; CANDIDATE_FK: `0`; CANDIDATE_USER_VERSION: `5`; CANDIDATE_SCHEMA_RESULT: **PASS**. Tabelas financeiras canônicas usam `amount_cents INTEGER`, competências mensais e CHECKs de valor, mês, ano e lifecycle. Quarentena possui UNIQUE de identidade e CHECKs de razão, estado e origem; nenhum `competence_date` canônico.

## Reconciliação e projeção semântica

Leitura independente em SQLite `mode=ro&immutable=1` do snapshot de SHA `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8` e do candidate. Os seis fingerprints foram recalculados diretamente das linhas fonte e conferidos com o manifesto D005-10. Para cada chave `(entity_type,id)`, conferi placement exclusivo, valores com `Decimal`, competência, descrições, estados, datas e vínculos. Categorias das três despesas também conferidas pelo join, e cinco eventos de importação referem somente os canônicos.

| Identidade | Resultado | Centavos | Competência |
| --- | --- | ---: | --- |
| payment/3 | PAYMENT3_RESULT = CANONICAL_MIGRATED | 18000 | 2026/07 |
| payment/4 | PAYMENT4_RESULT = QUARANTINED_UNRESOLVED | 18000 | 2026/07 |
| payment/5 | PAYMENT5_RESULT = CANONICAL_MIGRATED | 18000 | 2026/07 |
| expense/3 | EXPENSE3_RESULT = CANONICAL_MIGRATED | 120000 | 2026/07 |
| expense/4 | EXPENSE4_RESULT = CANONICAL_MIGRATED | 1000 | 2026/07 |
| expense/5 | EXPENSE5_RESULT = CANONICAL_MIGRATED | 120000 | 2026/07 |

- SOURCE_FINANCIAL_RECORDS: **6**; CANONICAL_MIGRATED_RECORDS: **5**; QUARANTINED_LEGACY_RECORDS: **1**; RECONCILIATION_RESULT: **PASS**, chaves distintas e partição exata `6 = 5 + 1`, sem ausência, duplicidade, overlap ou dupla contagem.
- PAYMENT4_QUARANTINE_REASON: `PAID_WITH_UNKNOWN_PAID_AT`; source `status=paid`, `paid_at=NULL`; quarantine `unresolved`, JSON legado e fingerprint idênticos. PAID_AT_INVENTED: **NO**.
- MONEY_RESULT: **PASS**, 180.00→18000, 1200.00→120000, 10.00→1000; sem arredondamento ou truncamento. COMPETENCE_RESULT: **PASS**, 2026/07 nas seis disposições, sem competência diária artificial.
- SEMANTIC_PROJECTION_RESULT: **PASS**, comparação independente dos campos materiais fonte→disposition→candidate, inclusive categorias, links, datas, lifecycle e quarantine.
- QUARANTINE_ISOLATION_RESULT: **PASS**. `payment/4` ausente de `payments` e `financial_events`. `PaymentRepository.get(4)` retornou `None`; `list_filtered` de caixa retornou `[]` e de competência retornou `[5,3]`. A API usa este repositório; CASH/revenue dependem de `paid_at` real, enquanto ACCRUAL usa ano/mês. O registro em quarantine não entra nesses resultados.
- EVIDENCE_CONSISTENCY_RESULT: **PASS** para SHA, counts, dispositions, money, competence, quarantine, integrity, FK, schema e sentinel.

## Sentinel e validação

- SENTINEL_BEFORE (E011 Evidence): Generation `8/canonical`; pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`; runtime manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`; DB `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`; integrity `ok`, FK `0`, sidecars `0`, maintenance lock absent.
- SENTINEL_AFTER (leitura independente): mesmos generation/state e três hashes; integrity `ok`, FK `0`, sidecars `0`, lock absent. OPERATIONAL_STATE_CHANGED: **NO**.
- TARGETED_INDEPENDENT_TESTS: verificações read-only de candidate, source fingerprints, seis projeções, schema, repositório real e sentinel **PASS**. Seleção de quatro testes pytest: um passou; três não chegaram ao corpo de teste por `PermissionError` na fixture `tmp_path` (diretório temporário do ambiente), inclusive com `--basetemp` no workspace. Não há evidência de falha funcional nesses três. `git diff --check` passou (avisos de conversão LF/CRLF).
- FULL_BACKEND_SUITE_DECISION: **NOT REPEATED**; executor registrou 329 PASS, sem risco concreto adicional a justificar repetição.

## Decisão

BLOCKERS: **0**. MAJORS: **0**. MINORS: **1**, limitação ambiental da fixture pytest. OBSERVATIONS: o HANDOFF anterior ainda não descrevia a execução E011; este parecer fecha a lacuna. A baseline histórica de código continua parcialmente recuperada (111/128), conforme autoridade D005-12 já aceita; não é uma nova alegação de freeze completo.

QUALITY_GATE_RESULT: **QUALITY_GATE_PASS**. E011_INDEPENDENT_VERIFICATION: **PASS**. E011_STATUS: **INDEPENDENTLY_VERIFIED_READY_FOR_CLOSURE**. STOP_CONDITION: `SPEC005_E011_INDEPENDENT_VERIFICATION_PASS`. NEXT_READY: `SPEC005_E011_CLOSURE`.

E012_EXECUTED: **NO**. PROMOTION_EXECUTED: **NO**. HANDOFF_RESULT: **UPDATED**. STAGED: **NO**. COMMIT_EXECUTED: **NO**. PUSH_EXECUTED: **NO**.
