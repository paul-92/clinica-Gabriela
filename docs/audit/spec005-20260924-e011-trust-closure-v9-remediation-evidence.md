# SPEC-005 E011 — remediacao da trust closure v9 (2026-09-24)

## Finding e correcao

A independent rereview v8 confirmou que `scripts/spec005_provision_e011_review.py` cria o registro canonico de Independent Review Authority consumido pelo CLI E011, mas seus bytes nao participavam da Migration Execution Identity v8 nem de outra identidade imutavel equivalente. Causa: dependency closure incompleta. Nenhuma autoridade real foi provisionada.

A verificacao unica de completude identificou o provisionador e `scripts/spec005_candidate_migration.py` como executaveis materiais para emissao e resolucao da autoridade. O CLI e suas dependencias ja estavam cobertos. O provisionador foi incluido em `ENTRYPOINTS` no modulo de identidade; sua logica de provisionamento nao foi alterada. O protocolo, o caminho canonico e o registro mantem o mesmo contrato. A closure apos a correcao tem 30 arquivos: os 29 do v8 mais `scripts/spec005_provision_e011_review.py`.

O invariant testado e: cada componente executavel material que cria, provisiona, seleciona ou valida a Independent Review Authority usada por E011 participa da identidade content-addressed; uma alteracao de bytes em qualquer participante faz `verify_manifest` falhar fechado. Em fixture isolado, a verificacao passou, bytes do provisionador foram alterados, a verificacao falhou, os bytes foram restaurados e a verificacao voltou a passar. O mesmo ciclo passou para o CLI, o modulo de identidade e a infraestrutura de cutover. Nenhum arquivo de producao foi adulterado para o teste.

## Identidades

- v8 historico/superseded: 29 arquivos; Migration Manifest SHA-256 `d4efc92187d615c3d04808c140dfa6d1a24501cd935ac2fcf8683c88ce73f968`; Transformation Identity `6d6d93d2769bc2370f632d3f82f574ed586940a1974bf916636e34d0e2ce6bd8`.
- v9 successor: `docs/audit/spec005-20260924-e011-migration-execution-manifest-v9.json`; 30 paths unicos; SHA-256 `90754472d5c15012e1caecf73cec272f3339bb6bc22ef2f6b1c3bb6b3b77649c`. BUILD e VERIFY foram operacoes separadas; VERIFY passou contra bytes reais.
- Source Identity operacional, read-only e inalterada: `4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`.
- Nova Transformation Identity, calculada com Source, v9, contrato SPEC-005 e gate E011 fixado: `3dfcdd7c719a89fed15a7f15da0757adfc09ae2a592ddc4d16dcd412f2223035`.

## Validacao e estado

Targeted trust/identity/gate tests, inclusive A-J: 18 passed. Suite completa `tests/`: 329 passed, executada porque o codigo do inventario mudou. A primeira tentativa de coleta na raiz encontrou um diretorio temporario antigo sem permissao; `tests/` concluiu. A permissao de diretrios temporarios do pytest foi ajustada apenas no processo de teste, sem alterar ACL ou codigo de producao. Compilacao estatica, `git diff --check` e sentinela read-only foram conferidas apos a estabilizacao.

Generation 8/canonical preservada: pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`; runtime manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`; database `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`; integrity `ok`, FK 0, sidecars 0, maintenance lock ausente.

BLOCKER-01 = `REMEDIATED_BY_EXECUTOR / PENDING_TARGETED_INDEPENDENT_REREVIEW`. E011 = `AUTHORIZED / NOT EXECUTED / NOT_READY`. E012 e promotion nao autorizadas. Sem review PASS real, snapshot/candidate real, stage, commit ou push.

`STOP_CONDITION=SPEC005_E011_TRUST_CLOSURE_REMEDIATION_COMPLETE`; `NEXT_READY=TARGETED_INDEPENDENT_REREVIEW_ONLY`.
