# SPEC-005 — execução da promoção autorizada

Data: 2026-09-24. Referência: `spec005-promotion-20260924T205031Z`. Fonte de Evidence operacional: `%LOCALAPPDATA%/ClinicaGabriela/runtime/evidence/spec005-promotion-20260924T205031Z.json`. Plano reconstruído: `spec005-20260924-promotion-orchestrator-reconstructed.md`. Preflight persistido antes da primeira mutation: `spec005-20260924-promotion-preflight-v2.json`, SHA-256 `ea5199df5809e3902aec1bcb47a4d1eda24fbd1cc93004f86e38e5b990c04f89`.

| Campo | Resultado |
|---|---|
| PROMOTION_ORCHESTRATOR_RECOVERY_RESULT | PASS — reconstruído a partir de contrato, E011, E012, cutover e handoff; original não localizado |
| PROMOTION_PREFLIGHT_RESULT | PASS — candidate, E012, autorização HUMAN posterior, v9 migration identity, source snapshot, Generation 8, ACL, integrity/FK, sidecars, lock e espaço |
| AUTHORIZED_CANDIDATE_SHA | `bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb` |
| SOURCE_GENERATION | 8/canonical |
| SOURCE_POINTER_SHA | `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a` |
| FIRST_MUTATION_BOUNDARY | `runtime/maintenance.lock`, adquirido exclusivamente após preflight persistido; SQLite source sob `BEGIN EXCLUSIVE` |
| BACKUP_RESULT | PASS — backup final Generation 8 SHA de manifest `0d652e78a51683bdbf244acebd6041e3d7573e7fbcadf1b22fa375afa54ce75f`; cópia DB com SHA da fonte, integrity ok, FK 0 |
| NEW_RUNTIME_MANIFEST_RESULT | PASS — SHA `47e7805a1745cd01a59b3b59a2ebf3c5330177bc3f00343b0d4e878276260017`; bytes de código verificados após a troca |
| NEW_GENERATION_RESULT | PASS — Generation 9/canonical, DB SHA idêntico ao candidate, integrity ok, FK 0, `user_version=5` |
| POINTER_CAS_RESULT | PASS — predecessor SHA Generation 8, novo pointer `bc93237792fb51d538a9168c883ac9be7f4866d6941a571eecb048c1014d47c0` |
| POST_SWITCH_SMOKE_RESULT | PASS — startup, `/health`, leitura financeira, write guard 503 e DB inalterado |
| STABILIZATION_RESULT | PASS — backup estabilizado manifest SHA `494e32e082aecba97614d0fab130912d6d99795d777517c8f1f3d1605501f987`; DB de backup verificado |
| FINAL_OPERATIONAL_GENERATION | 9/canonical |
| FINAL_POINTER_SHA | `bc93237792fb51d538a9168c883ac9be7f4866d6941a571eecb048c1014d47c0` |
| FINAL_RUNTIME_MANIFEST_SHA | `47e7805a1745cd01a59b3b59a2ebf3c5330177bc3f00343b0d4e878276260017` |
| FINAL_OPERATIONAL_DB_SHA | `bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb` |
| ROLLBACK_READINESS_RESULT | PASS — Generation 8 intacta (`1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`), backup final e backup estabilizado verificados; rollback progressivo por pointer CAS disponível |
| SPEC005_PROMOTION_RESULT | PASS |
| SPEC005_FINAL_STATE | `PROMOTED_PENDING_FINAL_INDEPENDENT_OPERATIONAL_VERIFICATION` |

Verificação read-only posterior: novo pointer, manifest e DB com os hashes acima; Generation 8 preservada com integrity ok/FK 0; Generation 9 integrity ok/FK 0; sidecars 0; maintenance lock ausente. E012 não foi repetida. Stage, commit e push não executados. Próximo gate: `SPEC005_POST_PROMOTION_INDEPENDENT_VERIFICATION`.
