# SPEC-006 — Implementation Evidence

Data: 2026-09-25<br>
Autoridade operacional: Generation 9/canonical<br>
Escopo: E006-02..E006-14<br>
Attachment scope: NONE

## CONTEXT_RECOVERY_RESULT

Baseline recuperada de `CLINICA_GABRIELA_PROJECT_HANDOFF.txt`, SPEC-006,
SPEC-010 e `spec006-20260925-post-human-decision-dependency-reconciliation.md`.
O executor não abriu nem alterou pointer, runtime manifest, Generation 9,
schema ou dados operacionais. A implementação aceita fonte e destinos
explicitamente, permitindo homologação somente em fixtures isoladas.

## IMPLEMENTATION_RESULT

Foi criada `backend/services/recovery.py` com:

- layout persistente congelado em `%LOCALAPPDATA%\\ClinicaGabriela\\runtime`,
  `generations` e `backups`;
- recovery unit de dois arquivos (`canonical.database.db` e
  `recovery-manifest.json`);
- SQLite Online Backup API, validação de `integrity_check`, FK, tamanho,
  checksum SHA-256 e publicação atômica;
- manifesto com generation, schema, `user_version`, tipo, timestamp,
  validação, attachments extensíveis vazios, privacy-safe e boundary de
  encryption explicitamente `not_enabled`;
- backup manual, diário por `America/Sao_Paulo`, pre-restore e pre-update;
- restore administrativo (`admin`) com pre-restore obrigatório, arquivo
  temporário validado e replace atômico;
- rejeição fail-closed de manifestos incompatíveis, retenção somente de
  pacotes completos/validáveis e falha de pre-update como `UPDATE=BLOCKED`.

A integração concreta com installer/SPEC-010 não foi implementada, conforme
o boundary autorizado; `pre_update_backup` fornece a capacidade e o contrato
para o installer hook.

## E006_TRACEABILITY

| Item | Status | Evidence |
|---|---|---|
| E006-02 | PASS | layout e recovery unit implementados |
| E006-03 | PASS | backup fora da instalação; paths persistentes |
| E006-04 | PASS | SQLite Online Backup API e atomicidade |
| E006-05 | PASS | checksum, integridade, FK e manifesto |
| E006-06 | PASS | publicação sem temporário válido; validação antes do sucesso |
| E006-07 | PASS | compatibilidade e falha fechada |
| E006-08 | PASS | retenção de pacotes válidos; sem attachments físicos |
| E006-09 | PASS | restore admin e pre-restore obrigatório |
| E006-10 | PASS | restore isolado validado e estado atual preservado em safety backup |
| E006-11 | PASS | pre-update capability; failure blocks update |
| E006-12 | PASS | logs/manifests não registram path fonte nem dados clínicos |
| E006-13 | PASS | encryption boundary documentado, encryption não ativada |
| E006-14 | PASS | homologação targeted e regressão executadas; closure abaixo |

## AC_TRACEABILITY_RESULT

| AC | Resultado | Implementação/Evidence |
|---|---|---|
| AC-001 | PASS | snapshot canônico + manifesto |
| AC-002 | PASS | validação antes da publicação |
| AC-003 | PASS | restore fixture fictícia |
| AC-004 | PASS | pre-restore obrigatório |
| AC-005 | PASS | temporário removido em falha |
| AC-006 | PASS | replace somente após validação; safety backup |
| AC-007 | PASS | schema/checksum/user_version/generation |
| AC-008 | PASS | `pre_update_backup` fail-closed |
| AC-009 | PASS | role `admin` obrigatória |
| AC-010 | PASS | manifesto privacy-safe, sem source path |
| AC-011 | PASS | backup root persistente fora da instalação |
| AC-012 | PASS | fonte fornecida explicitamente; Generation 9 não mutada |

## VALIDATION_RESULT

- Targeted: `8 passed` — `tests/test_spec006_recovery.py`.
- Backend regression/full suite: `336 passed, 1 skipped`.
- O primeiro executor falhou por ACL do diretório temporário; a execução
  autorizada fora do sandbox passou após reparo do fechamento de conexões.
- Testes usam somente SQLite sintético e `tmp_path`; nenhum dado real.
- Frontend: não aplicável; não houve impacto causal.

## PRIVACY_SAFE_EVIDENCE_RESULT

PASS. Não há nomes de pacientes, prontuários, valores clínicos, credenciais,
tokens, chaves ou source paths nos manifestos produzidos pelo serviço.

## OPERATIONAL_SENTINEL_RESULT

PASS — somente leitura; pointer, Generation, runtime manifest e banco
operacional não foram abertos para escrita nem alterados pelo executor.

## GOVERNANCE_RESULT

`REPOSITORY_MUTATED = YES` (código, teste e Evidence documental).<br>
`OPERATIONAL_STATE_MUTATED = NO`.<br>
`STAGED = NO`. `COMMIT_EXECUTED = NO`. `PUSH_EXECUTED = NO`.

`STOP_CONDITION = SPEC006_IMPLEMENTATION_COMPLETE`<br>
`NEXT_READY = SPEC006_INDEPENDENT_REVIEW`
