# SPEC-006 — MAJOR Remediation Evidence

Data: 2026-09-25<br>
Escopo autorizado: somente `MAJOR-001` e `MAJOR-002` do parecer independente.

## MAJOR001_REMEDIATION_RESULT

`PASS` por implementação e testes direcionados.

- `runtime_version` e `application_version` agora são campos obrigatórios,
  comparados com versões esperadas antes do restore;
- `schema_version` e `user_version` são comparados no boundary de validação;
- restore deriva o `user_version` esperado do banco-alvo quando não fornecido,
  impedindo restore silencioso entre versões incompatíveis;
- o manifesto exige o conjunto completo de campos contratuais;
- o recovery package exige exatamente `canonical.database.db` e
  `recovery-manifest.json`, sem extras, ausências ou links simbólicos;
- adulteração de manifesto, banco, checksum ou versões é rejeitada antes do
  pre-restore backup e do restore.

## MAJOR002_REMEDIATION_RESULT

`PASS` por implementação e testes direcionados.

- 7 unidades mais recentes da classe `daily` são preservadas;
- 4 unidades mais recentes da classe `weekly` são preservadas;
- `pre-restore`, `pre-update`, `recovery-unit`, `special` e `protected` são
  classificados como protegidos e não entram na rotação normal;
- seleção é determinística por `created_at` convertido para
  `America/Sao_Paulo`, com nome do pacote como desempate;
- classes desconhecidas não são removidas pela rotação;
- execução repetida é idempotente.

## TARGETED_TESTS

`21 direct targeted cases passed`, incluindo:

- versões compatíveis/incompatíveis;
- restore bloqueado antes de pre-restore para versão incompatível;
- schema/user_version;
- package extra, ausente, checksum e adulteração;
- retenção diária/semanal, coexistência, proteção, excesso, fronteira civil e
  idempotência.

Execução formal com pytest continuou limitada pelo ACL do ambiente. A última
execução formal direcionada completou `18 passed, 1 failed`; a falha ocorreu na
abertura SQLite do fixture pre-restore em diretório temporário criado durante o
teste. O workaround não alterou permissões persistentes.

## AFFECTED_REGRESSION

As referências de produção à recuperação são restritas a
`backend/services/recovery.py` e `tests/test_spec006_recovery.py`; não houve
alteração em API, frontend, modelos ou banco operacional.

## FULL_BACKEND_SUITE

Executada sobre `tests` com harness isolado de `tmp_path`: `279 passed, 68 failed,
1 skipped`. Os failures estão concentrados em fixtures Windows/OneDrive:
`PermissionError`/`unable to open database file`, `MAX_PATH` em diretórios de
teste profundos e guards que recusam caminhos locais específicos. O resultado
não é declarado PASS; a limitação ambiental permanece registrada. A suíte não
abriu o banco operacional em modo write-capable.

## STATIC_VALIDATION

- AST parse de `backend/services/recovery.py`: PASS.
- AST parse de `tests/test_spec006_recovery.py`: PASS.
- `git diff --check`: PASS; somente avisos preexistentes de conversão LF/CRLF.

## OPERATIONAL_SENTINEL_RESULT

Antes/depois: Generation `9/canonical`; pointer SHA-256
`bc93237792fb51d538a9168c883ac9be7f4866d6941a571eecb048c1014d47c0`; runtime
manifest SHA-256 registrado `47e7805a1745cd01a59b3b59a2ebf3c5330177bc3f00343b0d4e878276260017`;
banco SHA-256 `bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb`;
`integrity_check=ok`; FK `0`; `user_version=5`; sidecars `0`; lock ausente.

`OPERATIONAL_STATE_MUTATED = NO`.

## FINDINGS

`BLOCKERS = 0`<br>
`NEW_MAJORS = 0`<br>
`NEW_MINORS = 0`

## GOVERNANCE

`REPOSITORY_MUTATED = YES` — código, testes, Evidence de remediação e handoff.<br>
`STAGED = NO`<br>
`COMMIT_EXECUTED = NO`<br>
`PUSH_EXECUTED = NO`

`STOP_CONDITION = SPEC006_MAJOR_REMEDIATION_COMPLETE`<br>
`NEXT_READY = SPEC006_TARGETED_INDEPENDENT_REREVIEW`
