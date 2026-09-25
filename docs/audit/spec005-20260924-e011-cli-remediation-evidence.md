# SPEC-005 E011 — remediação do CLI e identidade sucessora (2026-09-24)

## Causa e autoridade

O CLI `scripts/spec005_candidate_migration.py` mantinha um `parser.error` incondicional após o preflight de identidades. A autorização HUMAN E011 havia sido reconfirmada e o review independente D005-13 havia fechado MAJOR-01, mas o entrypoint content-addressed continuava suspenso. Invocar diretamente `migrate_finance_candidate` contornaria esse entrypoint. Evidence anterior: `spec005-20260924-e011-precondition-blocked.md`.

Esta tarefa autorizou exclusivamente remediar o CLI, recalcular identidades e validar, sem executar E011, E012 ou promotion. Branch `feature/spec-008-architecture-foundation`, HEAD `c5100dd3cc347a9263c64a52a64d6bb0967b1db5`, upstream `origin/feature/spec-008-architecture-foundation`; alterações preexistentes preservadas.

## Mudança

O CLI agora exige manifesto de identidade legada, migration manifest, pointer, runtime manifest dir e binding checkpoint. Exige `source-authority=persisted`. Confere o gate E011 persistido pelo SHA fixado no próprio CLI, os estados `QUALITY_GATE_PASS`, D005-13 PASS, MAJOR-01 fechado e autorização HUMAN GRANTED, mais SHA do parecer independente. Confere SHA e estado do binding checkpoint, manifest migrador, source operacional persistida e identidade da transformação. Não há flag de force/skip. A chamada à migração ocorre somente após esse conjunto de verificações. O checkpoint v6 atual tem estado `PENDING_INDEPENDENT_IDENTITY_REREVIEW` e bloqueia execução. Um review independente futuro deverá produzir novo checkpoint content-addressed e Evidence de revisão correspondente; o CLI valida ambos antes de E011.

Arquivos de código alterados: `scripts/spec005_candidate_migration.py`, `backend/cutover/spec005_execution_identity.py`. Testes: `tests/test_spec005_e011_cli_gate.py`. O algoritmo de serialização canônica foi preservado; o binding novo inclui D005-13 e SHA do gate HUMAN E011. O caminho histórico D005-12 de `bind_transformation` continua disponível para preservar verificações antigas.

## Selective invalidation e identidades

- `REAL_SOURCE_IDENTITY=4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`, inalterada; D005-12 continua sendo a Source Authority.
- Manifest v5 SHA `a5e9f0bf65e32845acb71fff459d3a88bfbab0adc9f3f023bd747ccf4bf38893`: preservado, `SUPERSEDED_FOR_FUTURE_E011` pela alteração autorizada do código.
- Transformation Identity anterior `03832f1350b5b527216603fb2285f6dcda7bd0e322b582fb6a4434ed8dc940f0`: preservada historicamente, `INVALIDATED_BY_MIGRATION_IDENTITY_CHANGE` para E011 futura.
- Gate E011 persistido SHA `b331a7f4511b17967a2f77bffbf5c0e4eff7fc18e5e7bbe8d2eccc377fd40ff8`.
- Manifest v6 `spec005-20260924-e011-migration-execution-manifest-v6.json`: 29 entradas, SHA `b0bc52392cb40bd4e4c19d8c89651452a3651b6adbaa88cbc3ba87e505cff36b`. BUILD persistido seguido de `verify` separado PASS contra os bytes reais.
- New Transformation Identity `41b1c6f91fae82530f3a28bbb8baa348f4209212bb49f43a6a36e6d1ff6b81c3`, calculada por `bind_transformation` com source persistida, manifest v6, contrato D005-09/10/11/12, D005-13 e gate HUMAN E011.
- Novo binding checkpoint: `spec005-20260924-e011-binding-checkpoint-v6.json`, `PENDING_INDEPENDENT_IDENTITY_REREVIEW`.

As duas novas identidades estão `EXECUTOR_VERIFIED/PENDING_INDEPENDENT_VERIFICATION`; o executor não as declara independentemente verificadas.

## Validação e estado operacional

Testes direcionados CLI e D005-11/D005-12: 10 passed antes da rodada completa. Suíte backend completa no estado final do código: 318 passed. `py_compile` dos arquivos alterados: PASS. `git diff --check`: PASS. Invocação real do CLI com o checkpoint v6 pendente: exit 2, bloqueio explícito da revisão de identidade, nenhum candidato criado. Frontend sem impacto causal.

Sentinela antes/depois: Generation 8/canonical; pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`; runtime manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`; banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`; integridade ok, FK=0, sidecars=0, maintenance lock ausente.

`E011_AUTHORIZATION=GRANTED`; `E011_EXECUTED=NO`; `E011_READINESS=PENDING_INDEPENDENT_IDENTITY_REREVIEW`; `E012=NOT_AUTHORIZED/NOT_EXECUTED`; promotion não executada. Nenhum snapshot/candidate criado. Nenhuma alteração operacional, stage, commit ou push.

`STOP_CONDITION=SPEC005_E011_CLI_REMEDIATION_COMPLETE`; `NEXT_READY=READY_FOR_E011_IDENTITY_INDEPENDENT_REREVIEW`.
