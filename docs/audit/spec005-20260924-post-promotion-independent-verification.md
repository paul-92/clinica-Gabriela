# SPEC-005 — verificação independente pós-promoção

Data: 2026-09-24. Escopo: estado operacional já promovido, somente leitura. Nenhuma repetição de E011/E012, promoção, rollback ou remediação. Fonte operacional: `%LOCALAPPDATA%/ClinicaGabriela/runtime`.

## Resultado obrigatório

| Campo | Resultado |
|---|---|
| POST_PROMOTION_INDEPENDENT_VERIFICATION_RESULT | PASS |
| GENERATION_AUTHORITY_RESULT | PASS — pointer operacional único declara 9/canonical; cadeia aponta ao pointer 8 preservado |
| POINTER_RESULT | PASS — SHA-256 `bc93237792fb51d538a9168c883ac9be7f4866d6941a571eecb048c1014d47c0`; resolve exatamente `generations/canonical-spec005-v1-bcad54253b1e.db` |
| RUNTIME_MANIFEST_RESULT | PASS — SHA-256 `47e7805a1745cd01a59b3b59a2ebf3c5330177bc3f00343b0d4e878276260017`; 173 entradas únicas, 173 arquivos presentes com tamanho e SHA idênticos; schema do manifest e pointer coincidem |
| OPERATIONAL_DB_RESULT | PASS — SHA-256 `bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb`, igual ao candidate E011 e à promoção; `user_version=5` |
| INTEGRITY_RESULT | PASS — `PRAGMA integrity_check=ok` na Generation 9, Generation 8 e nos backups final e estabilizado |
| FK_RESULT | PASS — `PRAGMA foreign_key_check` retorna 0 violações nos mesmos quatro bancos |
| FINANCIAL_RECONCILIATION_RESULT | PASS — SOURCE=6, CANONICAL=5, QUARANTINED=1; 3 payments + 3 expenses na Generation 8, 2 payments + 3 expenses canônicos e 1 quarentena na Generation 9 |
| QUARANTINE_ISOLATION_RESULT | PASS — `payment/4` somente na quarentena, sem evento canônico; não aparece em CASH, ACCRUAL ou indicadores |
| POST_PROMOTION_RUNTIME_RESULT | PASS — startup real sob modo de verificação somente leitura, `/health` 200, consultas financeiras 200, `payment/4` 404 e guarda de escrita 503 |
| ROLLBACK_READINESS_RESULT | PASS — predecessor Generation 8, pointer histórico, manifest anterior, banco e backup final preservados; backup estabilizado da Generation 9 íntegro; caminho de rollback progressivo por CAS disponível, não executado |
| QUALITY_GATE_RESULT | QUALITY_GATE_PASS |
| SPEC005_FINAL_STATE | CLOSED_PASS_PROMOTED_INDEPENDENTLY_VERIFIED |
| NEXT_READY | SPEC005_FINAL_REPOSITORY_CHECKPOINT |

## Verificação direta

- Recalculei os hashes do pointer, manifest, bancos e manifests de backup dos bytes atuais. O pointer tem `generation=9`, `state=canonical`, checksum do banco e checksum do runtime correspondentes aos arquivos apontados, `schema_version=backend-models-v2-credential-reset` e predecessor `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`. O pointer histórico com esse SHA declara Generation 8/canonical e banco SHA `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`.
- SQLite foi aberto por `mode=ro&immutable=1`. Generation 9: integrity `ok`, FK 0, `user_version=5`. Generation 8: integrity `ok`, FK 0, `user_version=5`. Nenhum `-wal`, `-shm` ou `-journal` nesses bancos; `runtime/maintenance.lock` ausente. Não há arquivos temporários de criação/troca nas pastas de autoridade inspecionadas.
- Generation 9 contém payments 3 e 5, ambos 18000 centavos, pendentes, competência 2026/07; expenses 3, 4 e 5, respectivamente 120000, 1000 e 120000 centavos, competência 2026/07. A única quarentena é `payment/4`, `legacy_status=paid`, `resolution_state=unresolved`, `reason_code=PAID_WITH_UNKNOWN_PAID_AT`, 18000 centavos e competência 2026/07. `legacy_row_json.paid_at` é `null`; nenhum `paid_at` foi inventado. Não há payment canônico nem financial event para id 4.
- No startup de teste, o próprio resolvedor de pointer/manifest selecionou a Generation 9. Um lock descartável **fora** do runtime operacional, no workspace, satisfez a condição do modo `BACKEND_VERIFY_READ_ONLY=true`; foi removido ao final. A conexão SQLite da aplicação usou `mode=ro&immutable=1`. A licença e o usuário foram substituídos apenas no processo de teste para permitir chamadas de leitura. `/health` retornou 200. ACCRUAL de 2026/07 listou payments `[5,3]`, receita 36000, a receber 36000, despesa 241000 e saldo -205000 centavos. CASH no intervalo julho/agosto listou nenhum payment, receita 0, despesa 241000 e saldo -241000 centavos. Despesas ACCRUAL listaram `[5,4,3]`. `GET /finance/payments/4` retornou 404; POST retornou 503 pelo write guard. O SHA do banco antes/depois permaneceu idêntico.
- Backup final da Generation 8: manifest SHA `0d652e78a51683bdbf244acebd6041e3d7573e7fbcadf1b22fa375afa54ce75f`, DB SHA igual à Generation 8, integrity `ok`, FK 0. Backup estabilizado da Generation 9: manifest SHA `494e32e082aecba97614d0fab130912d6d99795d777517c8f1f3d1605501f987`, DB SHA igual à Generation 9, integrity `ok`, FK 0. Candidate e snapshot E011 ainda existem nos caminhos da Evidence. Nenhuma restauração ou rollback foi feita.

## Comparação com Evidence histórica

E011 closure e E012 independent review fixaram o candidate SHA, a reconciliação `6=5+1`, o estado unresolved de `payment/4` e o sentinel Generation 8 anterior. O preflight fixou a origem Generation 8, identidade da migração, candidate e requisitos de backup. A execução de promoção registrou o CAS para Generation 9, os três hashes finais e os dois backups. O handoff canônico registra E011/E012; seus trechos anteriores permanecem históricos. Todas as identidades e disposições materiais conferem com a leitura atual. Os FAILs, findings e remediações anteriores permanecem em seus artifacts; este relatório não os substitui.

BLOCKERS: 0.
MAJORS: 0.
MINORS: 0.
OBSERVATIONS: 1 — o primeiro harness de startup encontrou a restrição já documentada de permissão no `%TEMP%` Windows antes de iniciar a aplicação. A repetição com lock descartável no workspace passou e o lock foi removido. A verificação de runtime exerceu a API local in-process, não um servidor de rede externo.

STOP_CONDITION: `SPEC005_POST_PROMOTION_INDEPENDENT_VERIFICATION_PASS`.
OPERATIONAL_STATE_MUTATED: NO.
STAGED: NO.
COMMIT_EXECUTED: NO.
PUSH_EXECUTED: NO.
