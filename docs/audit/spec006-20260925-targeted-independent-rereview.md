# SPEC-006 — Targeted Independent Re-review

Data: 2026-09-25<br>
Modo: `TARGETED_INDEPENDENT_REREVIEW`<br>
Escopo: somente `MAJOR-001`, `MAJOR-002`, impacto causal da remediação e classificação da suíte completa.

## RESULTADO_AUTORITATIVO

```text
MAJOR001_INDEPENDENT_REREVIEW = PASS
MAJOR002_INDEPENDENT_REREVIEW = PASS
FULL_SUITE_FAILURE_CLASSIFICATION = ENVIRONMENTAL_NON_CAUSAL
AC_INVALIDATION_RESULT = NO_MATERIAL_INVALIDATION
BLOCKERS = 0
MAJORS = 0
MINORS = 0
QUALITY_GATE_RESULT = PASS
SPEC006_CLOSURE_READINESS = READY_FOR_CLOSURE
```

## MAJOR-001

O validador de `backend/services/recovery.py` exige exatamente
`canonical.database.db` e `recovery-manifest.json`, exige o conjunto completo
de campos do manifesto e compara `runtime_version`, `application_version`,
`schema_version`, `user_version` e, quando aplicável, `generation`.

Foi verificado em fixture SQLite sintética que:

- pacote compatível é aceito;
- incompatibilidade de runtime, aplicação, schema e user version é rejeitada;
- arquivos extras e componentes obrigatórios ausentes são rejeitados;
- adulteração de manifesto/checksum é rejeitada;
- restore incompatível falha antes da criação do pre-restore.

## MAJOR-002

`apply_retention` mantém separadamente as 7 unidades `daily` e as 4 unidades
`weekly`, preserva classes protegidas e usa timestamp convertido para
`America/Sao_Paulo`, com desempate determinístico pelo nome do pacote.

Foram verificadas as fronteiras de excesso, coexistência de classes, backups
especiais/protegidos e idempotência.

## REGRESSÃO E SUÍTE COMPLETA

As alterações causais ficaram restritas ao novo serviço de recovery e aos
testes da SPEC-006. Não houve alteração operacional em API, frontend, modelos,
Generation 9 ou banco autoritativo.

O resultado informado da suíte completa foi `279 passed / 68 failed / 1
skipped`. A reprodução local mostrou erros de criação/limpeza de fixtures e
`basetemp` por `WinError 5`/ACL, além das limitações registradas de OneDrive,
MAX_PATH e guards existentes. O harness direto dos contratos direcionados
passou. Não foi encontrada evidência de falha de asserção causada pela
remediação; a classificação é `ENVIRONMENTAL_NON_CAUSAL`.

## SENTINEL

Verificação somente leitura:

- Generation: `9/canonical`;
- pointer SHA-256: `bc93237792fb51d538a9168c883ac9be7f4866d6941a571eecb048c1014d47c0`;
- runtime manifest SHA-256: `47e7805a1745cd01a59b3b59a2ebf3c5330177bc3f00343b0d4e878276260017`;
- banco SHA-256: `bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb`;
- `integrity_check=ok`, FK violations `0`, `user_version=5`;
- sidecars SQLite `0`; maintenance lock ausente.

Nenhum restore, migration, promotion, cleanup ou escrita operacional foi
executado.

## GOVERNANÇA

`REPOSITORY_MUTATED = NO` pela revisão; alterações preexistentes foram
preservadas. `OPERATIONAL_STATE_MUTATED = NO`. `STAGED = NO`.

`STOP_CONDITION = SPEC006_TARGETED_INDEPENDENT_REREVIEW_PASS`<br>
`NEXT_READY = SPEC006_CLOSURE`
