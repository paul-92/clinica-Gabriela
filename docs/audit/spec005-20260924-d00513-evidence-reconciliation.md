# SPEC-005 D005-13 - Evidence de reconciliacao historica

Decisao HUMAN APPROVED: `spec005-20260924-d00513-human-decision.json`. Escopo: MAJOR-01 da revisao D005-11/D005-12. A revisao independente original permanece FAIL ate nova revisao.

## Estado canonico

- `HISTORICAL_BASELINE_RECONSTRUCTION = INCOMPLETE`; `FULL_128_BYTE_RECONSTRUCTION = NOT_ESTABLISHED`.
- `ORIGINAL_RECOVERY_OBSERVATION = 111/128`; `ORIGINAL_111_PATH_MEMBERSHIP = UNKNOWN`. Nenhuma matriz por path desse checkpoint foi preservada.
- `INDEPENDENT_REVIEW_OBSERVATION = 126/128`; tres matches dependiam de conversao LF para CRLF e foram excluidos do metodo direto.
- `CURRENT_DIRECT_BYTE_MATCHES = 123/128`; `PROVENANCE_CONFIRMED_FROM_ORIGIN_COMMIT = 109/128`; `CURRENT_ONLY_EXACT_MATCHES_WITHOUT_TEMPORAL_PROVENANCE = 14/128`; `NO_DIRECT_EXACT_EXEMPLAR = 5/128`.

As observacoes 111, 126 e 123 usam momentos e metodos diferentes. Nao inferir a composicao dos 111 originais. BYTE_MATCH e TEMPORAL_PROVENANCE sao provas distintas. A matriz `spec005-20260924-d00511-d00512-recovery-matrix.json` registra os 128 paths e SHA; o gerador nao transforma EOL.

## 14 matches somente atuais

Cada entrada tem `CURRENT_EXACT_MATCH / TEMPORAL_PROVENANCE_UNESTABLISHED`; disponibilidade no levantamento anterior = `UNKNOWN`.

| Path | SHA esperado = SHA atual |
|---|---|
| `app/utils/initial_admin.py` | `141cecc8dde0d828eef7bfb7fe64da8988f9ca647b1bcd0d3e3011aa8428d2fa` |
| `app/views/login_view.py` | `81bcdcf2914a51b03624b498f4d47e8507f7d23d9f88201c53b7664344dbaf80` |
| `backend/api/dependencies.py` | `44de239d7836f29dbe44e1d28585584440d437639a3f4db80379aa16a8c18296` |
| `backend/api/routes/appointments.py` | `7632e0d8eb34d4b5db411d0344e0366cadb425ea04e0bad60af6dd1257d500ab` |
| `backend/api/routes/auth.py` | `2f8020ce21836174f91bef3c8c478cf51cdc90c99d789869758e955575fd37b5` |
| `backend/api/routes/clinical_records.py` | `9f073cb32b716264087c30779baebaae17d343ac696f3e6c654c0a46d31ef004` |
| `backend/api/routes/patients.py` | `7d129eed28e4bd3baf58602380e5add2db094d5b43406229062c0458190c2de0` |
| `backend/api/routes/psychologists.py` | `9f07ef1bfc687f0a6d398e3e676b1625fe8aa3dc6050c33a45aaac5517141416` |
| `backend/api/routes/settings.py` | `50d84bc7a7e697baa2cabb1d14dc695bfe7f630bcca1d4f7377c7884956a96e5` |
| `backend/config.py` | `45b234942ed1a8b127b8bb70bc50f7268cb1d1f132a31089f21a2e4cc2524c56` |
| `backend/repositories/user_repository.py` | `68ca7ca14f5ca99052bd901a7a3895e8275753333127273d863a658544502569` |
| `backend/schemas/user.py` | `3bdc346d61eb6edde88fa0a2c07e6aad0b8597e7a30757e6e5f051dbdb047d68` |
| `backend/utils/tokens.py` | `81b13a92a6001fd2f096793a1db5d0938bae0eb6e9d2261e5867b9c5b7bbd3bf` |
| `requirements.txt` | `4436aa2c33bfbbb2496599a9fe952eb8f979ae8f2ef6274184dc4153abb7fad2` |

## 5 sem exemplar direto exato

| Path | SHA esperado | SHA atual | SHA commit de origem | Status |
|---|---|---|---|---|
| `app/database/seed.py` | `d2ef426a41e0a6758f583a9e0b90b8b9f455b87a261a8357cc8b178bbca3c4d5` | `9a988323ffe04f0b46ea800c1bb016f7866ac75f1914681857dc8b5575e13142` | `cf064c569c4f425af9aae61b1166569206d7a8575635e02d6b53b224b30978e4` | `NO_DIRECT_EXACT_EXEMPLAR` |
| `app/views/main_view.py` | `04085d53d5e1e547878ff39e304e9968610e207e13a0f5a9aa4827ef7f7938a1` | `bb82da12e448813e95f2c3d5ecc8f05917296e2ea438eab392be56c0419f461c` | `8c6b7125cc3fcffb31f1ac3a48f2e692923905418cdd85687db8c8c83adc9471` | `NO_DIRECT_EXACT_EXEMPLAR` |
| `backend/api/routes/dashboard.py` | `b54a99455472324b7a75347808f6c82d7502bf75a3ffca32511d8114063df770` | `9056648149b3ebc29d8486d1d96724accc8233bfb33ea75ac53707a7420fd2ba` | `214b81680ad2d6e3ea368b2f95642d2ebdc3f3f05d8a1af52bb393b19a36d3fe` | `NO_DIRECT_EXACT_EXEMPLAR` |
| `backend/api/routes/finance.py` | `f11b62a892f65d4062eb5727a5fedcd0917bdcf1f3f5c296a8dbbac94003ea40` | `51e8643e1ac3d326c04db5edde6038d8e30d3b282d54b58aa3535e21a2a85f20` | `3cb396f1ec51afea15870aed9e355d1993dd5b770da9f071c37ae7850ca33c90` | `NO_DIRECT_EXACT_EXEMPLAR` |
| `backend/database/seed.py` | `903f8e669b5df486e92aea5a5256f7e1d681831c3d898c292719b64c3d82eb9d` | `8493e9ef15b3e5df907844850ddb6eb43853ca63b5991079a3b86c1cfefd094b` | `502fd32fef32234ea939187e56077df40654247cead6ac6ef363c54dd46a6d0a` | `NO_DIRECT_EXACT_EXEMPLAR` |

`app/database/seed.py`, `backend/api/routes/dashboard.py` e `backend/api/routes/finance.py` constavam entre os 126 somente via conversao EOL. `app/views/main_view.py` e `backend/database/seed.py` eram os outros dois sem match. Nenhum byte foi fabricado. A busca historica nao foi retomada.

## Impacto e validacao

MAJOR-01 = REMEDIATED_BY_D00513 / PENDING_INDEPENDENT_REREVIEW. D005-12 continua usando autoridade dos artefatos operacionais persistidos; a baseline historica integral nao foi reconstituida. O campo `PARTIAL_111_OF_128` da identidade existente representa o checkpoint original, nao a medicao direta atual. E011 = SUSPENDED / NOT_READY; E012 = NOT AUTHORIZED.

- Matriz regenerada byte-identical: SHA-256 `3ceee484320520c296c82b4a5da1bd45b8f29677ba6357ef2d831a6b4760ff53`; 128 entradas e 128 paths distintos; classes 94+15+14+5=128.
- Testes D005-11/D005-12: 7 passed. `py_compile` do gerador: PASS. `git diff --check`: PASS (avisos LF/CRLF preexistentes). Full backend nao repetida porque codigo de producao/migracao nao mudou; ultima suite completa: 315 passed.
- Identidades preservadas: fonte `4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`; migrador v5 `a5e9f0bf65e32845acb71fff459d3a88bfbab0adc9f3f023bd747ccf4bf38893`; transformacao `03832f1350b5b527216603fb2285f6dcda7bd0e322b582fb6a4434ed8dc940f0`.
- Sentinela antes/depois: Generation 8/canonical; pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`; runtime manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`; banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`; integridade ok; FK=0; sidecars=0; lock ausente.

Sem alteracao operacional, codigo de producao, codigo migrador, stage, commit, push, E011, E012 ou promotion.
