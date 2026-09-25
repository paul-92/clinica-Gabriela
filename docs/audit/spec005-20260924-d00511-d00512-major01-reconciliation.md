# SPEC-005 D005-11/D005-12 — MAJOR-01: tentativa de reconciliação

## Resultado

`PREVIOUS_RECOVERY_RESULT = 111/128` permanece um resultado histórico declarado pelo executor. `INDEPENDENT_REVIEW_RESULT = 126/128` foi reproduzido, mas **não pode ser promovido a recuperação comprovada**: três dos 126 bytes foram criados por conversão LF→CRLF de blobs do Git. O escopo atual proíbe usar normalização EOL para obter correspondência.

A [matriz de 128 entradas](spec005-20260924-d00511-d00512-recovery-matrix.json) verifica apenas duas fontes físicas diretas: bytes do working tree atual e bytes de `git show 0832eccd03e9bcb64f02b2944e9ecedd721596af:<path>`. Cada linha registra path, SHA esperado, estado, fonte verificada, SHA real e classe de proveniência, além dos SHA dos dois candidatos. O gerador é `scripts/spec005_recovery_matrix.py`; não lê o banco, não modifica EOL nem tenta preimage.

| Classe | Entradas | Alcance da prova |
|---|---:|---|
| Commit de origem e working tree | 94 | Bytes exatos no commit histórico |
| Somente commit de origem | 15 | Bytes exatos no commit histórico |
| Somente working tree atual | 14 | Bytes exatos hoje; disponibilidade na investigação anterior não demonstrada |
| Nenhuma fonte direta exata | 5 | UNRECOVERED pelo método autorizado |

Portanto, `CURRENT_DIRECT_EXACT_RESULT = 123/128`; `SOURCE_COMMIT_EXACT_RESULT = 109/128`; `CURRENT_ONLY_TEMPORAL_UNPROVEN = 14/128`; `DIRECT_UNRECOVERED = 5/128`. A soma é 128. **`RECONCILED_RECOVERY_RESULT = UNDETERMINED`** até obter a matriz por path do levantamento 111/128 e evidência temporal dos arquivos atuais. A matriz registra `previous_111_status=NOT_RECORDED_PER_PATH` para cada linha. Não é possível identificar honestamente os 111 comuns e os 15 novos por path; o conjunto de 15 entradas presentes apenas no commit de origem não é automaticamente esse delta. Busca nos commits acessíveis por path não localizou os 14 bytes do grupo “somente working tree”; isso não prova quando passaram a existir localmente.

## Diferença metodológica dos 126

A revisão anterior aceitou `current`, `git show` ou uma versão LF→CRLF produzida durante a verificação. Os três resultados obtidos apenas pela terceira via foram `app/database/seed.py`, `backend/api/routes/dashboard.py` e `backend/api/routes/finance.py`. Nenhum desses três possui exemplar direto byte-exact nas duas fontes analisadas. Os 14 matches somente atuais não têm provenance temporal suficiente para afirmar que estavam disponíveis durante o recovery anterior.

## Arquivos destacados

Na observação 126/128, os dois sem correspondência eram:

| Path | SHA esperado | SHA atual | SHA do commit de origem | Estado |
|---|---|---|---|---|
| `app/views/main_view.py` | `04085d53d5e1e547878ff39e304e9968610e207e13a0f5a9aa4827ef7f7938a1` | `bb82da12e448813e95f2c3d5ecc8f05917296e2ea438eab392be56c0419f461c` | `8c6b7125cc3fcffb31f1ac3a48f2e692923905418cdd85687db8c8c83adc9471` | Ainda sem bytes exatos; diferenças de EOL misto no histórico não autorizam reconstrução. |
| `backend/database/seed.py` | `903f8e669b5df486e92aea5a5256f7e1d681831c3d898c292719b64c3d82eb9d` | `8493e9ef15b3e5df907844850ddb6eb43853ca63b5991079a3b86c1cfefd094b` | `502fd32fef32234ea939187e56077df40654247cead6ac6ef363c54dd46a6d0a` | Ainda sem bytes exatos nas fontes diretas. |

Os três arquivos obtidos antes só por transformação EOL elevam a contagem direta de não recuperados de dois para cinco. A matriz contém os SHA dos candidatos de todos os cinco. Nenhum byte foi fabricado ou normalizado para marcar recuperação.

## Impacto e próximo gate

MAJOR-01 continua **ABERTO**. A divergência é de Evidence/provenance e do método da revisão, sem prova de defeito no verificador de fonte persistida D005-12. O status semântico `PARTIAL_111_OF_128` nas identidades permanece intacto como checkpoint histórico, pendente de decisão e revisão; não se substituiu por 123 ou 126. É necessária a lista por path dos 111 recuperados originalmente, ou decisão humana explícita sobre como registrar a nova medição sem alegar proveniência retroativa.

`MAJOR01_EXECUTOR_STATUS = BLOCKED_BY_MISSING_HISTORICAL_PER_PATH_PROVENANCE`; `E011_READINESS = NOT_READY`. Handoff não atualizado nesta tentativa, conforme instrução de fazê-lo somente após reconciliação validada. Sem alteração de código de produção ou migração; sem E011/E012/promotion, stage, commit ou push.

## Validação

- Gerador executado contra o manifest operacional ativo; matriz serializada em JSON canônico com SHA-256 `3ceee484320520c296c82b4a5da1bd45b8f29677ba6357ef2d831a6b4760ff53`.
- Regeneração em memória idêntica ao artifact: 128 paths distintos, 123 correspondências diretas, cinco não recuperadas e contagens por classe somando 128. Todo `EXACT_RECOVERED` tem `actual_sha256 == expected_sha256`.
- `python -m py_compile scripts/spec005_recovery_matrix.py`: PASS. `tests/test_spec005_d00512.py`: 3 passed. Full backend não repetida: nenhuma alteração no runtime ou migrador; suíte 315 passed na revisão independente imediatamente anterior.
- Identidades preservadas: fonte `4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`, manifest migrador v5 `a5e9f0bf65e32845acb71fff459d3a88bfbab0adc9f3f023bd747ccf4bf38893`, transformação `03832f1350b5b527216603fb2285f6dcda7bd0e322b582fb6a4434ed8dc940f0`.
- Sentinela antes/depois: Generation 8/canonical; pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`; runtime manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`; banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`; integridade ok, FK=0, sidecars=0, lock ausente.
- `git diff --check`: PASS, com avisos de conversão LF/CRLF em arquivos preexistentes. Working tree e alterações anteriores preservados.
