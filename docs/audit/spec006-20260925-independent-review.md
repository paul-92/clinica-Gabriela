# SPEC-006 — Independent Implementation Review

Data: 2026-09-25<br>
Modo: `INDEPENDENT_REVIEW`<br>
Escopo: implementação SPEC-006; revisão somente leitura, com escrita apenas deste parecer e do handoff.

## CONTEXT_RECOVERY_RESULT

`Generation 9/canonical` permanece a autoridade operacional. A leitura independente
confirmou os sentinelas documentados:

- pointer SHA-256: `bc93237792fb51d538a9168c883ac9be7f4866d6941a571eecb048c1014d47c0`;
- runtime manifest SHA-256 registrado: `47e7805a1745cd01a59b3b59a2ebf3c5330177bc3f00343b0d4e878276260017`;
- banco operacional SHA-256: `bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb`;
- `integrity_check=ok`, `foreign_key_violations=0`, `user_version=5`;
- sidecars SQLite: `0`; maintenance lock: ausente.

Nenhum banco, pointer, Generation ou runtime manifest foi aberto para escrita.

## INDEPENDENT_REVIEW_RESULT

`QUALITY_GATE_FAIL` — foram encontrados dois MAJOR. A implementação não está pronta
para encerramento da SPEC-006.

### RECOVERY_UNIT_RESULT

`PARTIAL PASS`. `create_recovery_unit` produz os dois arquivos autorizados:
`canonical.database.db` e `recovery-manifest.json`, e não cria attachments físicos.
Entretanto, `validate_manifest` não exige que o diretório contenha exatamente esses
dois componentes; um pacote com arquivos extras continua elegível para restore.

### PERSISTENT_PATH_RESULT

`PASS` por inspeção estática e confirmação do binding: `%LOCALAPPDATA%\\ClinicaGabriela\\runtime\\backups`,
fora da instalação descartável, sem criação de layout paralelo pelo serviço.
A preservação em upgrade/reinstall/uninstall permanece boundary contratual da SPEC-010,
não uma integração implementada nesta mudança.

### SQLITE_CONSISTENCY_RESULT

`PASS` por inspeção estática: o snapshot usa `sqlite3.Connection.backup`, com validação
SQLite antes da publicação do resultado e replace do banco temporário. O diretório do
pacote, contudo, fica visível antes da validação final; isso é uma exposição transitória
de artefato incompleto, ainda que o manifesto não seja publicado como válido.

### MANIFEST_RESULT

`PARTIAL PASS`. O manifesto produzido contém SHA-256, generation, schema_version,
user_version, application_version, backup_type, timestamp, integridade, FK,
compatibility metadata, attachments e boundary de encryption. Checksums e adulteração
do banco/manifesto são rejeitados pela validação existente.

### INTEGRITY_RESULT

`PASS` por inspeção do fluxo: `integrity_check`, `foreign_key_check`, tamanho, SHA-256
e vínculo manifesto↔banco são verificados. A reprodução fixture não pôde ser executada
neste ambiente porque o ACL do diretório temporário impede a criação do lock do pytest;
isso não é tratado como substituto da inspeção.

### COMPATIBILITY_RESULT

`MAJOR-001`. `validate_manifest` compara schema, user_version e generation somente
quando parâmetros são fornecidos. Não há parâmetro nem comparação de
`application_version`/runtime version, e `compatibility_status` é gravado como
`pending-runtime-validation` mas não impede validação ou restore. Além disso, campos
materiais como `application_version`, `backup_type`, `created_at` e `generation` não
fazem parte do conjunto obrigatório do manifesto. Um pacote incompatível ou
estruturalmente adulterado pode, portanto, passar além do contrato declarado.

### RETENTION_RESULT

`MAJOR-002`. `apply_retention` implementa apenas `keep=N` global, com default 7,
ordenado por mtime. Não há política de 7 diários + 4 semanais + especiais, nem
classificação/proteção de backups especiais, protegidos, pre-restore ou necessários à
recuperação. Backups válidos dessas categorias podem ser removidos pela fatia
`candidates[keep:]`.

### ADMIN_RESTORE_RESULT

`PASS` por inspeção: role diferente de `admin` é rejeitada. O parecer não executou
restore no banco operacional.

### PRE_RESTORE_RESULT

`PASS` por inspeção: o backup pre-restore é criado antes do replace e uma falha nessa
etapa impede a restauração.

### ISOLATED_RESTORE_RESULT

`NOT_REPRODUCED` por bloqueio ambiental de fixtures temporárias. O executor reportou
restore isolado no Evidence anterior, mas essa evidência não substitui a reprodução
independente. O código valida o pacote e o temporário antes do replace; não há rollback
automático se uma falha ocorrer depois do `os.replace`.

### PRE_UPDATE_RESULT

`PASS` como capability: `pre_update_backup` valida novamente o pacote e converte falha
em `PRE_UPDATE_BACKUP=FAIL; UPDATE=BLOCKED`. A integração concreta do installer hook
continua corretamente fora do escopo desta revisão da SPEC-006.

### PRIVACY_RESULT

`PASS` por inspeção: o manifesto não registra source path, dados clínicos, credenciais,
secrets ou PII desnecessária.

### ENCRYPTION_BOUNDARY_RESULT

`PASS`: encryption permanece `not_enabled`, com boundary extensível, sem ativação
fictícia.

### ADVERSARIAL_TEST_RESULT

Adulteração de manifesto e banco é rejeitada pelo caminho estático de checksum.
Package incompleto é rejeitado quando falta arquivo, mas package com arquivo extra não é
rejeitado. Incompatibilidade de schema/user_version/generation fornecida ao validador é
rejeitada; incompatibilidade de runtime/application version não é fechada. Falha de
pre-update é convertida em bloqueio. Retenção permanece não conforme à política
aprovada.

## E006_REVIEW_MATRIX

| Item | Resultado independente |
|---|---|
| E006-02 | PARTIAL PASS — shape final simétrico, validador aceita extras |
| E006-03 | PASS — path persistente confirmado |
| E006-04 | PARTIAL PASS — Online Backup API; publicação transitória antecipada |
| E006-05 | PASS — checksum/integridade/FK presentes |
| E006-06 | PARTIAL PASS — falhas limpam em condições normais |
| E006-07 | MAJOR-001 |
| E006-08 | MAJOR-002 |
| E006-09 | PASS — admin e pre-restore obrigatório |
| E006-10 | NOT_REPRODUCED — fixture bloqueada por ACL; risco pós-replace observado |
| E006-11 | PASS — capability pre-update fail-closed |
| E006-12 | PASS — Evidence/manifest privacy-safe por inspeção |
| E006-13 | PASS — boundary de encryption |
| E006-14 | FAIL — closure não pode ser declarado com os MAJOR |

## AC_REVIEW_MATRIX

| AC | Resultado independente |
|---|---|
| AC-001 | PARTIAL — banco/manifest, sem validação de extras |
| AC-002 | PASS por fluxo estático |
| AC-003 | NOT_REPRODUCED independentemente |
| AC-004 | PASS por fluxo pre-restore |
| AC-005 | PARTIAL — artefato incompleto pode ficar transitório |
| AC-006 | PARTIAL — safety backup existe, rollback pós-replace não automático |
| AC-007 | FAIL — runtime version e campos materiais não são exigidos |
| AC-008 | PASS como boundary/capability |
| AC-009 | PASS por role admin |
| AC-010 | PASS por inspeção privacy-safe |
| AC-011 | PASS — path fora da instalação |
| AC-012 | PASS quanto à fonte explícita/Generation 9 não tocada |

## TARGETED_TESTS

- `python -m pytest ...`: não executado; pytest ausente no Python global.
- `.venv\\Scripts\\python.exe -m pytest -p no:cacheprovider tests/test_spec006_recovery.py`:
  `1 passed, 7 errors`; os erros ocorreram antes dos testes, ao criar o lock de
  `tmp_path`, por `PermissionError` no ACL do diretório temporário.
- Um diretório fixture `.spec006-independent-ejb84m40/` foi criado pela tentativa
  manual, mas seu ACL também impediu a remoção posterior. Ele não contém dados
  operacionais e permanece não staged; remoção forçada não foi autorizada.
- `git diff --check`: sem erros de whitespace; apenas avisos de conversão LF/CRLF.
- Full backend suite: não repetida; a Evidence do executor registra `336 passed / 1
  skipped`, preservada como evidência do executor e não como substituto desta revisão.

## FINDINGS

- `MAJOR-001`: compatibilidade de runtime/application version e esquema obrigatório do
  manifesto não são fail-closed; packages com extras também são aceitos.
- `MAJOR-002`: retenção não implementa 7 diários, 4 semanais e especiais protegidos.
- `MINOR-001`: diretório do pacote é publicado antes da validação final e a restauração
  não possui rollback automático após `os.replace` se a validação final falhar.
- `OBSERVATION-001`: reprodução pytest ficou limitada pelo ACL do ambiente.

## QUALITY_GATE_RESULT

`QUALITY_GATE_FAIL`<br>
`SPEC006_CLOSURE_READINESS = NOT_READY`<br>
`STOP_CONDITION = SPEC006_INDEPENDENT_REVIEW_FAIL`<br>
`NEXT_READY = REMEDIATION_REQUIRED`

## OPERATIONAL_SENTINEL_BEFORE / AFTER

O sentinel antes e depois permaneceu: Generation 9/canonical, pointer SHA,
runtime-manifest SHA, banco SHA, integridade, FK, sidecars e lock conforme os valores
registrados em `CONTEXT_RECOVERY_RESULT`. Não houve restore operacional.

## GOVERNANCE

`REPOSITORY_MUTATED = YES` — este parecer, a atualização do handoff e o fixture
temporário não removível descrito acima.<br>
`OPERATIONAL_STATE_MUTATED = NO`<br>
`STAGED = NO`<br>
`COMMIT_EXECUTED = NO`<br>
`PUSH_EXECUTED = NO`
