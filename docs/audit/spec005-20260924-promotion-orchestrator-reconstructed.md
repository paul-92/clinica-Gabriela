# SPEC-005 — Promotion Orchestrator reconstruído

Estado: plano de execução reconstruído após E012, antes da primeira mutation operacional. Autoridade HUMAN de promoção: GRANTED na instrução de retomada da sessão, para o candidate SHA-256 `bcad54253b1eb5684cd145ad0e2225600fe3c5f63ac1542eaa0a3078c5a850cb`. Esta autorização sucede a E012. O orquestrador originalmente emitido não foi localizado; este artifact não se apresenta como cópia dele.

## Fatos e origem

| Classe | Fato |
|---|---|
| CONTRACT_FACT | SPEC-005 D005-01–13, E011 e E012 exigem centavos inteiros, competência mensal, quarentena de R2, candidato isolado, fonte preservada, recovery e gate HUMAN separado para promoção. |
| CONTRACT_FACT | E012: CLOSED / QUALITY_GATE_PASS / INDEPENDENTLY_VERIFIED; E001–E011 11/11 PASS; AC-001–AC-012 12/12 PASS; BLOCKERS 0; MAJORS 0. |
| CONTRACT_FACT | Autorização HUMAN posterior à E012 fixa exatamente o SHA do candidate acima; não autoriza stage, commit ou push. |
| IMPLEMENTATION_FACT | `backend.cutover.infrastructure` oferece lock de manutenção com SQLite exclusivo, backup verificado, freeze/verify de runtime, `promote_candidate` com ACL aprovada, `atomic_swap_pointer` com CAS e `rollback_pointer` progressivo. |
| IMPLEMENTATION_FACT | A política de ACL HUMAN para `runtime/generations` fixa `5ad951ab8d53b98516f342d637e1028f26e4a83b7e03f0b339ab0ebde70aac91`; medição local confere. |
| IMPLEMENTATION_FACT | E011 Evidence fixa source Generation 8, pointer `d83a0654ce964f93c3191bb4a9bbe24fa78c55087666e6831f04f60630a1c50a`, manifest `cd806a300f182c5d0f70cb6a6e4b2b0b9a574ff2f4cf02d7271cfcdaec5ef519`, DB `1edb9c5c77a8eb56da6cb5254e2bf795aa56a1d8c94dbbc855d0b70d40f404c8`; candidate `user_version=5`, integrity ok, FK 0. |
| RECONSTRUCTED_EXECUTION_STEP | O executor está em `scripts/spec005_operational_promotion.py`; usa manifest novo dos bytes atuais do código runtime, sem alegar recuperação 128/128 da baseline histórica. O manifest ativo anterior é preservado como Evidence. |

## Ordem e gates

1. **Preflight somente leitura:** provar E012 PASS e autorização HUMAN posterior, candidate SHA e E011 identities/Evidence; Generation 8 pointer/manifest/DB SHA; integrity/FK/`user_version`; ausência de sidecars e lock; ACL exata, espaço, destinos novos, source snapshot de E011 e recuperação existente. Recalcular closure v9 do migrador sem modificar código ou candidate. Persistir preflight Evidence no repositório.
2. **Primeira mutation:** criação exclusiva de `runtime/maintenance.lock`; lock SQLite exclusivo do banco Generation 8. Revalidar o pointer e os hashes sob lock.
3. **Freeze do runtime:** fixar em novo manifest content-addressed todos os arquivos do manifest anterior ainda existentes e os módulos runtime atuais `app/`, `backend/` e scripts de execução relevantes; verificar bytes atuais. O freeze ocorre sob lock após preflight. Nenhum código é alterado depois do freeze. Qualquer divergência interrompe antes do pointer.
4. **Backup final:** `create_final_backup` da Generation 8 em pasta nova imutável; conferir hash, integrity, FK e cópia de restauração isolada antes do pointer.
5. **Nova Generation:** `promote_candidate` copia o candidate para `runtime/generations/canonical-spec005-v1-<sha>.db`; preserva candidate e Generation 8; SHA, integrity, FK e `user_version=5` conferidos.
6. **Pointer CAS:** construir Generation 9/canonical com novo manifest e SHA do candidate, predecessor SHA Generation 8. `atomic_swap_pointer` é a única troca de autoridade, sob lock e CAS esperado.
7. **Post-switch smoke:** backend em modo read-only sob maintenance lock, rota `/health`, leitura financeira por API, proteção de escrita 503, hash do DB inalterado.
8. **Estabilização:** soltar lock, validar pointer/manifest/DB; readquirir lock na Generation 9, backup estabilizado e restauração isolada; soltar lock e verificar sentinela final. Evidence de promoção preservada.
9. **Falha/recovery:** antes do pointer, preservar Generation 8 e registrar Evidence, sem remover candidate, manifest, backup ou Generation parcial. Após pointer, `rollback_pointer` com CAS e Generation 10 apontando ao banco/manifest preservados da Generation 8; verificar integridade e registrar Evidence. Nunca fazer rollback silencioso ou sobrescrever banco antigo.

O executor deve parar antes da primeira mutation se qualquer gate não puder ser provado. Após sucesso, SPEC-005 permanece `PROMOTED_PENDING_FINAL_INDEPENDENT_OPERATIONAL_VERIFICATION`; não é ACCEPTED/DONE.
