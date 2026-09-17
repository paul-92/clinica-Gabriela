# SPEC-004 — Remediation Operational Gate Report

## Estado

`READY_FOR_SPEC004_SECOND_INDEPENDENT_QUALITY_REVIEW`

## Commits

- remediação R1–R9: `0832eccd03e9bcb64f02b2944e9ecedd721596af`;
- Evidence de candidato: `2e1de7e7a96792c25eb24a4236d1f3b9c6b246a9`;
- executor operacional: `2e38425cbcb996d817f4d7ed6ff73afcb3446f5f`;
- reparo EOL-only: `71499c2f1b619cde5865dba01c7ac0853795e9c9`.

Nenhum push, merge ou release foi executado.

## Predecessor

Generation 7/canonical foi validada antes da mutação: pointer
`9d3300076994702b6e60d48c9c16cb0bcd5e6a38ed290e55aa663bbf2a104ba2`, banco
`7f4412c6fefccbccce5fa511e35a21bd88eec97447ffbe4787fc2c2101939a07`, v4,
integridade OK, zero FKs e zero sidecars. A Generation 7 não foi modificada ou excluída.

## Migration e nova Generation

A migration forward-only v4→v5 foi aplicada somente à cópia candidata e promovida como
Generation 8. IDs, contagens, timestamps, `legacy_unverified` e histórico foram
preservados. Resultado:

- Generation `8`, estado `canonical`;
- banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`;
- `user_version=5`, `integrity_check=ok`, zero violações FK;
- índice único original→sucessor presente;
- guards físicos de UPDATE/DELETE de eventos e guard relacional presentes.

## Pointer e manifest

- pointer SHA-256 `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`;
- runtime manifest SHA-256 `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`;
- freeze autorizado `41236c2f285bf8ba7260e34abc6b139a51ab5e1687282e74ff4a2d35e96ed852`;
- CAS e histórico de pointer: PASS;
- manifest registra bytes efetivamente executados e hashes dos bytes do commit fonte.

## Backups e recovery

- backup manifestado da Generation 7 criado antes da promoção;
- restore isolado reproduziu checksum v4 exato;
- backup estabilizado da Generation 8 criado;
- restore isolado v5 reproduziu checksum exato;
- nenhuma Generation, backup, history, manifest ou Evidence foi removido;
- recovery não foi necessário; `NO_SILENT_POINTER_ROLLBACK` permaneceu respeitado.

## Default operational path

Os smokes read-only sob maintenance lock e write-enabled após liberação exercitaram:

`pointer → manifest → runtime → database → python -m backend.main → /health`

Ambos passaram sem `CLINICA_OPERATIONAL_POINTER`, `CLINICA_RUNTIME_CODE_ROOT`,
`CLINICA_RUNTIME_ROOT`, override de manifest ou override de banco. O lock foi removido ao
final e não há WAL, SHM ou journal residual.

## R1–R9 e regressão

O harness pós-promoção foi executado contra cópia isolada da composição promovida:
`27 passed`. Cobriu correção excepcional, retroatividade, timezone/ClinicSettings,
gap/fold DST, original/sucessor, append-only, API com login real, referências,
self-exclusion, estados/ocupação, migration e binding default. Permanecem válidos:

- regressão Python pré-promoção: `235 passed`, 237 testes coletados após os harnesses;
- frontend: `5 passed`;
- build Vite: PASS;
- concorrência SQLite e rollback/fault injection: PASS.

Nenhum dado clínico fictício foi inserido no banco operacional.

## Reparos

A primeira execução abortou antes de lock/CAS porque o freeze do commit tinha LF e o
checkout executado tinha CRLF. O reparo aceitou exclusivamente equivalência byte a byte
após normalização LF↔CRLF, preservou hashes dos bytes fonte e manifestou os bytes ativos.
O candidato pré-CAS só foi reutilizado após validação do SHA-256 autorizado. Não houve
aceitação de divergência semântica.

## Evidence

Evidence operacional content-addressed:
`977581ae9291c4cf54e4dbd30d6715b921e7ad09a0514f7956353b49b3dfcceb`.

## Riscos residuais

- a revisão independente final ainda não foi executada;
- dados legados permanecem `legacy_unverified`, deliberadamente sem inferência;
- nenhuma aceitação final da SPEC-004 é declarada por este gate.

`STOP_CONDITION = READY_FOR_SPEC004_SECOND_INDEPENDENT_QUALITY_REVIEW`
