# SPEC-006 — Post-Human-Decision Dependency Reconciliation

Data: 2026-09-25<br>
Modo: somente leitura operacional; escrita documental autorizada

## CONTEXT_RECOVERY_RESULT

Generation 9/canonical foi revalidada como autoridade operacional. Pointer,
runtime manifest e banco permanecem compatíveis com a baseline aprovada.

## HUMAN_DECISIONS_RECONCILIATION_RESULT

As decisões D006-01, D006-02 e D006-03 foram incorporadas:

- dados persistentes não são removidos automaticamente no uninstall;
- o layout atual da Generation 9 é o binding operacional oficial;
- o boundary de pre-update é `INSTALLER HOOK`;
- falha do backup/validação bloqueia update/migration;
- a unidade inicial não contém arquivos físicos externos;
- o ciclo diário usa `America/Sao_Paulo`;
- restore usa a role administrativa existente `admin`.

## SPEC010_INTERFACE_CONTRACT_RESULT

SPEC-010 permanece responsável pela instalação, update, reinstall, uninstall e
integração concreta do installer hook. SPEC-006 fornece a capacidade de
pre-update backup e seu contrato de sucesso/falha.

| Campo | Binding aprovado |
|---|---|
| `persistent_data_root` | `%LOCALAPPDATA%\\ClinicaGabriela` |
| `runtime_root` | `%LOCALAPPDATA%\\ClinicaGabriela\\runtime` |
| `database_root` | `%LOCALAPPDATA%\\ClinicaGabriela\\runtime\\generations` |
| `backup_root` | `%LOCALAPPDATA%\\ClinicaGabriela\\runtime\\backups` |
| `runtime_version` | versão registrada no recovery manifest/runtime manifest |
| `uninstall_policy` | preservar dados persistentes por padrão |
| `upgrade_hooks` | installer hook chamando SPEC-006 pre-update backup |
| `ACL_policy` | Administradores, Sistema e usuário operacional |

O layout paralelo `...\\data` e `...\\backups` não deve ser criado nesta
etapa.

## PERSISTENT_PATH_CONTRACT_RESULT

`PASS — FROZEN`

O contrato garante que o backup fica fora da instalação descartável, sobrevive
a upgrade/reinstall e permanece preservado durante uninstall, salvo ação
explícita e confirmada do usuário.

## UNINSTALL_POLICY_RESULT

`PASS — FROZEN`

Preservar por padrão banco operacional, backups, generations, runtime
manifests, recovery manifests e Evidence necessária à recuperação.

## PRE_UPDATE_CONTRACT_RESULT

`PASS — CONTRACT FROZEN; INTEGRATION NOT IMPLEMENTED`

```text
installer
→ SPEC-006 pre-update backup
→ validação do recovery package
→ PASS
→ update/migration
→ validação
→ startup
```

Falha no backup ou validação produz `PRE_UPDATE_BACKUP=FAIL` e
`UPDATE=BLOCKED`. SPEC-010 fará a integração concreta.

## RECOVERY_UNIT_FREEZE_RESULT

`PASS — FROZEN`

```text
recovery-package/
  canonical.database.db
  recovery-manifest.json
```

O manifesto registra checksum SHA-256, generation, schema_version,
user_version, runtime/application version, backup type, timestamp, integridade,
compatibilidade e Evidence privacy-safe.

`CURRENT_ATTACHMENT_SCOPE = NONE`<br>
`PHYSICAL_EXTERNAL_FILES_IN_RECOVERY_UNIT = NO`

## COMPATIBILITY_BASELINE_RESULT

`PASS`

- Generation: `9/canonical`
- Pointer SHA-256: `bc93237792fb51d538a9168c883ac9be7f4866d6941a571eecb048c1014d47c0`
- Runtime manifest SHA-256: `47e7805a1745cd01a59b3b59a2ebf3c5330177bc3f00343b0d4e878276260017`
- Operational DB SHA-256: `bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb`
- schema_version: `backend-models-v2-credential-reset`
- user_version: `5`
- integrity_check: `ok`
- FK violations: `0`
- sidecars: `0`
- maintenance lock: ausente

## SPEC006_EXECUTION_PLAN_RESULT

| Item | Estado |
|---|---|
| E006-02 | READY |
| E006-03 | READY |
| E006-04 | READY |
| E006-05 | READY |
| E006-06 | READY |
| E006-07 | READY |
| E006-08 | READY |
| E006-09 | READY |
| E006-10 | READY |
| E006-11 | READY |
| E006-12 | READY |
| E006-13 | READY |
| E006-14 | READY, condicionado às dependências normais de implementação/homologação |

`READY` significa liberado contratualmente para a próxima etapa; não significa
execução autorizada.

## AC_TRACEABILITY_RESULT

| AC | Itens responsáveis |
|---|---|
| AC-001 | E006-02, E006-04 |
| AC-002 | E006-06, E006-07 |
| AC-003 | E006-10, E006-14 |
| AC-004 | E006-09, E006-10 |
| AC-005 | E006-06 |
| AC-006 | E006-07, E006-10 |
| AC-007 | E006-07 |
| AC-008 | E006-11 |
| AC-009 | E006-09 |
| AC-010 | E006-12 |
| AC-011 | E006-03 |
| AC-012 | E006-01, E006-02, E006-03 |

## GOVERNANCE

Aplicada governança proporcional: validação do executor, testes proporcionais,
Evidence privacy-safe e revisão independente somente nos boundaries definidos.
Controles extraordinários da SPEC-005 não foram importados.

## BLOCKERS

Nenhum blocker contratual remanescente.

## MAJORS

Nenhum major novo encontrado nesta reconciliação.

## OPEN_HUMAN_DECISIONS

Nenhuma decisão HUMAN material pendente para abrir a autorização de
implementação da SPEC-006.

## IMPLEMENTATION_READINESS

`READY`

`STOP_CONDITION = SPEC006_PRE_IMPLEMENTATION_DEPENDENCIES_RESOLVED`<br>
`NEXT_READY = HUMAN_SPEC006_IMPLEMENTATION_AUTHORIZATION`

## EXECUTION_CONTROL

```text
REPOSITORY_MUTATED = YES (somente documentação contratual/Evidence)
OPERATIONAL_STATE_MUTATED = NO
STAGED = NO
COMMIT_EXECUTED = NO
PUSH_EXECUTED = NO
```
