# SPEC-005 D005-13 — targeted independent re-review (2026-09-24)

## Contexto e escopo

Branch `feature/spec-008-architecture-foundation`, HEAD `c5100dd3cc347a9263c64a52a64d6bb0967b1db5`, upstream `origin/feature/spec-008-architecture-foundation`. Working tree já modificada antes desta revisão; alterações preservadas. Revisão limitada ao MAJOR-01, à remediação D005-13 e à não invalidação das três identidades críticas. Sem autoridade de reparo. A revisão independente D005-11/D005-12 anterior permanece historicamente FAIL.

## Matriz e proveniência

Regeneração com `scripts/spec005_recovery_matrix.py` a partir do manifest operacional: bytes idênticos ao artifact; SHA-256 `3ceee484320520c296c82b4a5da1bd45b8f29677ba6357ef2d831a6b4760ff53`. São 128 entradas, 128 paths únicos. Classes determinísticas: 94 `SOURCE_COMMIT_AND_CURRENT`, 15 `SOURCE_COMMIT_EXACT`, 14 `CURRENT_BYTE_MATCH_TEMPORAL_UNPROVEN`, 5 `NO_DIRECT_EXACT_SOURCE`. O gerador lê bytes diretos do commit de origem e da árvore atual, sem conversão EOL. Amostras SHA independentes das quatro classes: `app/__init__.py`, `app/api/client.py`, `app/utils/initial_admin.py`, `app/database/seed.py`; hashes dos dois candidatos coincidiram com as respectivas colunas da matriz e a classificação. Conferidos individualmente os cinco sem exemplar exato: `app/database/seed.py`, `app/views/main_view.py`, `backend/api/routes/dashboard.py`, `backend/api/routes/finance.py`, `backend/database/seed.py`; SHA esperado difere de ambos os SHA candidatos em cada caso.

`ORIGINAL_RECOVERY_OBSERVATION=111/128`, com `ORIGINAL_111_PATH_MEMBERSHIP=UNKNOWN`. `INDEPENDENT_REVIEW_OBSERVATION=126/128`, incluindo três matches derivados de LF→CRLF (`app/database/seed.py`, `backend/api/routes/dashboard.py`, `backend/api/routes/finance.py`). `CURRENT_DIRECT_BYTE_MATCHES=123/128`; `ORIGIN_PROVENANCE_CONFIRMED=109/128`; `CURRENT_ONLY_EXACT_MATCHES_WITHOUT_TEMPORAL_PROVENANCE=14/128`; `NO_DIRECT_EXACT_EXEMPLAR=5/128`. `FULL_128_RECONSTRUCTION=NOT_ESTABLISHED`; `HISTORICAL_BASELINE_RECONSTRUCTION=INCOMPLETE`. D005-13 preserva os checkpoints distintos, não inventa a composição dos 111 nem data retroativamente os 14. A autoridade D005-12 continua sendo os artefatos operacionais persistidos. O campo `PARTIAL_111_OF_128` na identidade registra o checkpoint original, não a medição atual.

## Identidades e validação

- `REAL_SOURCE_IDENTITY=4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`, recalculada da serialização canônica do source identity persistido.
- Migration manifest v5 SHA `a5e9f0bf65e32845acb71fff459d3a88bfbab0adc9f3f023bd747ccf4bf38893`; 29 entradas e closure de código verificadas.
- `TRANSFORMATION_IDENTITY=03832f1350b5b527216603fb2285f6dcda7bd0e322b582fb6a4434ed8dc940f0`, recalculada independentemente. `CRITICAL_IDENTITIES_INVALIDATED=NO`.
- Testes direcionados D005-11/D005-12: 7 passed, usando `C:\tmp\s5rr` para evitar MAX_PATH em fixtures. Primeiras tentativas falharam por permissão de diretório temporário e comprimento do caminho, sem falha funcional. `py_compile` do gerador: PASS. `git diff --check`: PASS, com avisos de LF/CRLF preexistentes. Full backend não repetida: D005-13 alterou Evidence e ferramenta de recovery, sem alteração causal de código de produção/migração desde os 315 passed da revisão anterior. Frontend sem impacto causal.

## Sentinela e gate

Antes e depois: Generation 8/canonical; pointer SHA `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`; runtime manifest SHA `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`; database SHA `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`; `integrity_check=ok`; FK violations 0; sidecars 0; maintenance lock ausente. Leitura operacional apenas.

`MAJOR-01=CLOSED_BY_INDEPENDENT_REREVIEW`. BLOCKERS=0; NEW_MAJORS=0; MINORS=0; OBSERVATIONS=0. `QUALITY_GATE_RESULT=QUALITY_GATE_PASS`; `D005-13=INDEPENDENTLY_VERIFIED`; `D005-11/D005-12=INDEPENDENT_REVIEW_QUALITY_GATE_PASS` após fechamento do MAJOR-01. `E011=NOT_EXECUTED/READY_FOR_HUMAN_RECONFIRMATION`; E012 não executada. `STOP_CONDITION=SPEC005_D00513_TARGETED_INDEPENDENT_REREVIEW_PASS`; `NEXT_READY=HUMAN_E011_RECONFIRMATION_REQUIRED`.

Mutação do repositório: somente este artifact e o handoff canônico. Nenhuma mutação operacional, stage, commit, push, E011, E012 ou promotion.
