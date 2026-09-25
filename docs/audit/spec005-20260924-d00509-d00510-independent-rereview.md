# SPEC-005 D005-09/D005-10 — Independent Re-review

Checkpoint: 2026-09-24 12:02 UTC. Papel: INDEPENDENT REVIEWER. Escopo: remediação dos três MAJORs e da observação da revisão inicial, regressão contratual e prontidão para E011. Esta revisão não executou E011 ou E012.

## Baseline e sequência

- Branch `feature/spec-008-architecture-foundation`; HEAD `c5100dd3cc347a9263c64a52a64d6bb0967b1db5`; upstream `origin/feature/spec-008-architecture-foundation`. Working tree já continha alterações não commitadas, preservadas.
- Revisão inicial: `QUALITY_GATE_FAIL` (0 blockers, 3 majors, 1 observation), registrada no handoff. Remediação do executor: `docs/audit/spec005-20260923-d00509-d00510-implementation-evidence.md`. Os números de testes desse documento não foram tratados como execução independente.
- Contratos inspecionados: `docs/specs/SPEC-005-financeiro.md`, decisões D005-09/D005-10, manifesto de identidade D005-10 e implementação corrente de `backend/migration/spec005.py`, `backend/migration/spec005_identity.py`, `backend/models/finance.py`, `backend/config.py` e `backend/cutover/infrastructure.py`.

## Revisão dos achados

| Achado | Resultado | Evidência independente |
|---|---|---|
| MAJOR-01 — provenance binding | CLOSED para o caminho isolado revisado | `_verified_operational_source_identity` lê o pointer, verifica o runtime manifest/freeze e compara SHA do snapshot antes de `_verify_identity_manifest` confrontar geração, manifesto, banco, IDs e fingerprints. Execução dirigida bloqueou geração, SHA do manifesto e SHA do banco falsos. Verificação read-only direta confirmou seis identidades/fingerprints da Generation 8. |
| MAJOR-02 — reconciliação integral | CLOSED | `_assert_candidate_reconciliation` compara projeções materiais de payments, expenses e quarantine, partição disjunta/completa de identidades e centavos totais. Testes dirigidos alteraram identidade, vínculo, dinheiro, status, competência, datas, provenance, motivo, conteúdo legado e estado de paid_at; divergências foram bloqueadas. |
| MAJOR-03 — caminho operacional padrão | CLOSED no harness isolado | O teste subprocessado atravessou `get_runtime_settings`, freeze, pointer, source identity, manifesto legado e classificação com `LOCALAPPDATA` configurado pelo caminho público. Runtime coerente passou; manifesto, freeze e pointer adulterados bloquearam. A verificação direta do runtime operacional atual revelou bloqueio separado abaixo. |
| OBSERVATION-01 — schema alignment | CLOSED | Constraints declarativas de quarentena/eventos foram comparadas à DDL produzida pela migração; teste passou. Inspeção confirmou tabelas separadas e triggers contra UPDATE/DELETE. |

## Validação executada nesta revisão

- `tests/test_spec005_d00510.py`: **26 passed**. Inclui os testes adversariais de provenance, reconciliação, caminho padrão isolado e schema.
- Regressão afetada (`test_spec005_migration.py`, `test_spec005_domain_repository.py`, `test_spec005_api.py`, `test_spec005_authority_isolation.py`, `test_spec005_seed_traceability.py`, `test_cutover_runtime_guards.py`): **42 passed**.
- Suíte backend `tests`: **307 passed**.
- AST parse de seis módulos afetados: PASS. `git diff --check`: PASS. Frontend não executado: nenhuma mudança causal de frontend/contrato normal de API nesta remediação.
- Verificação read-only adicional, fora do pytest: identidades e fingerprints do manifesto coincidem com as seis linhas da Generation 8; cinco dispositions `CANONICAL_MIGRATED` e payment/4 `QUARANTINED_UNRESOLVED`; payment/4 conserva `paid` com `paid_at=NULL`, competência 2026/07 e motivo `PAID_WITH_UNKNOWN_PAID_AT`. Nenhuma linha ou valor identificável foi emitido.
- O primeiro teste pytest em temporário do workspace falhou por `PermissionError` do ambiente antes de fornecer resultado válido. A repetição em diretórios temporários isolados acessíveis produziu os números acima.

## Sentinela operacional antes e depois

| Item | Antes | Depois |
|---|---|---|
| Generation | 8/canonical | 8/canonical |
| Pointer SHA-256 | `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a` | igual |
| Runtime manifest SHA-256 | `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519` | igual |
| Database SHA-256 | `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8` | igual |
| SQLite integrity / FK | `ok` / 0 | `ok` / 0 |
| Sidecars / maintenance lock | 0 / absent | 0 / absent |

## Novo blocker de prontidão operacional

`verify_runtime_manifest` aplicado ao runtime operacional apontado e ao code root local atual retornou `RuntimeFreezeError: runtime local diverge do manifest congelado`. Foi observado diretamente antes da revisão; a importação normal do backend repetiu a falha. Os hashes do pointer, manifest e banco são corretos, mas a ligação do código atual ao freeze não passa. O harness isolado prova o comportamento do código sob um freeze coerente; ele não corrige nem substitui a precondição operacional real. A fonte não foi alterada. Resolver esta divergência exige checkpoint próprio fora da autoridade desta revisão. Nenhuma inferência de prontidão E011 é segura enquanto ela persistir.

## Parecer

- `MAJOR_01=CLOSED`; `MAJOR_02=CLOSED`; `MAJOR_03=CLOSED`; `OBSERVATION_01=CLOSED`.
- `NEW_BLOCKERS=1` (runtime freeze operacional divergente); `NEW_MAJORS=0`; `NEW_MINORS=0`; `NEW_OBSERVATIONS=0`.
- `QUALITY_GATE_RESULT=QUALITY_GATE_FAIL`; `E011_READINESS=NOT_READY`. O FAIL inicial permanece histórico; este é um novo resultado após a remediação, com causa distinta.
- Mutação operacional: nenhuma. Mutação do repositório pelo reviewer: este parecer e atualização correspondente do handoff. Sem stage, commit, push, candidate, E011, E012 ou promoção.

`STOP_CONDITION=SPEC005_D00509_D00510_INDEPENDENT_REREVIEW_FAIL`

`NEXT_READY=REMEDIATION_REQUIRED`
