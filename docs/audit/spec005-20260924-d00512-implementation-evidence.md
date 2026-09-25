# SPEC-005 D005-12 — Evidence do executor

## Sequência e autoridade

HUMAN aprovou D005-12 em 2026-09-24, após o bloqueio do runtime freeze,
implementação e validação sintética D005-11, busca histórica e tentativa final
read-only em `.review-spec005-rereview` (pasta vazia). A baseline histórica
permanece **PARTIAL: 111/128 hashes exatos, 17/128 não recuperados, zero paths
ausentes**. Os 17 bytes não foram fabricados, normalizados nem declarados
recuperados. O manifest operacional ativo não foi regenerado.

Decisão: `spec005-20260924-d00512-human-decision.json`. O parecer independente
D005-09/D005-10 e a Evidence D005-11 anteriores continuam preservados.

## Contrato implementado

- `verify_persisted_source` compara SHA do pointer contra valor externo, lê e
  valida Generation 8/canonical, schema, hash e inventário de 128 entradas do
  runtime manifest persistido, hash do banco apontado e do snapshot, `user_version`,
  `integrity_check`, FKs, sidecars e maintenance lock. Não verifica fisicamente os
  128 arquivos históricos nem relata sucesso dessa verificação.
- A identidade retornada contém explicitamente
  `historical_runtime_bytes_verification=PARTIAL_111_OF_128` e
  `historical_runtime_baseline_recovery=PARTIAL`.
- O caminho D005-10 anterior com baseline explícita permanece para compatibilidade
  e seus testes. O caminho D005-12 exige expectativas persistidas explícitas.
  O CLI de preflight aceita `--source-authority persisted`; o CLI do candidato
  continua bloqueando E011 mesmo após preflight.
- A identidade migradora recalcula a closure de imports Python e cada hash.
  Manifest v4 D005-11 preservado com SHA
  `33de0cbaeb3b4e96552af1495303d27a31a04a3c21d876404337b05ad7528cff`.
  Manifest sucessor v5 D005-12, 29 arquivos, SHA
  `a5e9f0bf65e32845acb71fff459d3a88bfbab0adc9f3f023bd747ccf4bf38893`.
- O binding inclui a identidade persistida, o SHA migrador verificado, SPEC-005 e
  D005-09/D005-10/D005-11/D005-12. Checkpoint proposto:
  `spec005-20260924-d00512-binding-checkpoint.json`, SHA
  `3cb27129cb2343684a57d55119d73a4bbffc553861842f7f6ce5be1b88c0bfe5`.
  Ele não autoriza E011.

## Validação

- Harness sintético D005-12: source persistida válida e recovery 111/128 passam;
  divergências de pointer, manifest, banco/snapshot, Generation, schema,
  integridade, FK, código migrador, identidade migradora, contrato e alegação
  histórica 128/128 bloqueiam. A execução usa temporários isolados.
- Testes D005-12/D005-11/D005-10/runtime/freeze: **55 passed**.
- Regressão afetada SPEC-005: **32 passed**.
- Suíte backend completa no estado D005-12: **315 passed**.
- AST de cinco arquivos afetados: PASS; `git diff --check`: PASS. Frontend não
  executado, sem alteração causal em API normal ou UI.
- Preflight real read-only: `IDENTITY_PREFLIGHT_PASS_NOT_E011_AUTHORIZATION`.
  Não foi criado snapshot operacional; a leitura usou o banco apontado como
  argumento `snapshot` apenas para validar a identidade atual. A E011 futura
  ainda deve obter e verificar sua cópia isolada pelo mesmo SHA.

## Identidades reais e sentinela

- Fonte operacional persistida: PASS; SHA canônico da identidade
  `4a9dbef317a982a626ab7cf6fc2aa5bebec62e256f6d3a9e4edaceb38c9c4ffe`.
- Migração v5: PASS, 29 arquivos.
- Transformation Identity:
  `03832f1350b5b527216603fb2285f6dcda7bd0e322b582fb6a4434ed8dc940f0`.
- Generation 8/canonical; pointer
  `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`;
  runtime manifest
  `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`;
  banco `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`;
  `user_version=5`, `integrity_check=ok`, FK=0, sidecars=0, lock ausente.
  Antes/depois iguais. Nenhuma mutação operacional.

## Estado

D005-12 = IMPLEMENTED / VALIDATED_BY_IMPLEMENTATION_EXECUTOR.
D005-11 = IMPLEMENTED / REAL_BINDING_VALIDATED_BY_IMPLEMENTATION_EXECUTOR /
INDEPENDENT_REVIEW_PENDING. E011 = AUTHORIZED_PREVIOUSLY / SUSPENDED_PENDING_INDEPENDENT_REVIEW.
E012 = NOT_AUTHORIZED / NOT_EXECUTED. Nenhum candidato, stage, commit, push ou
promotion foi executado.
