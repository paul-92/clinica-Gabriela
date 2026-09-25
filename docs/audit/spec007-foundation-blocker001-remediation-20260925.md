# Evidence — SPEC-007 Foundation BLOCKER-001 Remediation

**Data:** 2026-09-25
**Finding:** `BLOCKER-001 = WINDOWS_FILE_URI_RUNTIME_GUARD_BYPASS`
**Escopo:** somente runtime guard, testes do guard, Evidence e handoff.
**Privacy-safe:** somente targets sintéticos ou paths redigidos; nenhum banco operacional foi aberto para a matriz adversarial.

## CONTEXT_RECOVERY_RESULT

PASS. Repositório `https://github.com/paul-92/clinica-Gabriela.git`, branch
`feature/spec-008-architecture-foundation`, `HEAD=1820ab2`, upstream no mesmo
commit e sync `0/0`. Não havia staging. Alterações documentais, foundation
anterior e resíduos temporários foram preservados.

Arquivos responsáveis confirmados: `tests/conftest.py` e
`tests/support/runtime_guard.py`; testes específicos em
`tests/test_spec007_foundation.py`.

## BLOCKER001_ROOT_CAUSE_RESULT

PASS. O código anterior removia manualmente o prefixo `file:` e tratava apenas
uma forma `/C:`. Não interpretava `urlsplit`/`netloc`, não fazia decoding seguro
de percent-encoding e não diferenciava URI malformada. Por isso
`file:///C:/...` e `file://C:/...` não convergiam para o mesmo `Path` do target
operacional.

## REMEDIATION_SCOPE_RESULT

PASS. A alteração ficou limitada à canonicalização do runtime guard, testes
adversariais/positivos, Evidence e handoff. Nenhum código funcional,
autenticação, agenda, financeiro, backup, migration, SPEC-009, SPEC-010,
Generation, pointer ou banco operacional foi alterado.

## REMEDIATION_STRATEGY

`urllib.parse.urlsplit` passou a interpretar a URI; `unquote` faz decoding
determinístico com validação de percent-encoding; drive local, localhost e UNC
são convertidos para paths Windows; fragmentos e URI malformada falham fechado;
comparação do target usa `normcase`.

## ORIGINAL_BYPASS_REGRESSION_RESULT

PASS. As representações originais `file:///C:/...` e `file://C:/...` agora
produzem rejeição `RuntimeError` antes de chamar o conector SQLite. O teste
substitui o conector por uma função sentinela que falha se houver acesso ao
filesystem.

Resultado: `BLOCK_BEFORE_FILESYSTEM_ACCESS`.

## ADVERSARIAL_RUNTIME_GUARD_TEST_RESULT

PASS — 8 testes direcionados. A matriz cobre:

- path absoluto operacional;
- variação de caixa;
- `/` e `\\`;
- path relativo e traversal `..`;
- `file:///C:/...` e `file://C:/...`;
- percent-encoding e URI canonicalizada equivalente;
- path sintético permitido;
- URI sintética permitida;
- URI malformada fail-closed;
- UNC sintético sem acesso ao filesystem.

## POSITIVE_PATH_RESULT

PASS. Path sintético dentro da raiz temporária e URI `file:` sintética
canonicalizam para o mesmo target permitido. A correção não transformou o
guard em bloqueio universal.

## FOUNDATION REGRESSION

`TARGETED_TESTS = 8 passed` (`tests/test_spec007_foundation.py` e
`tests/test_security.py`).

`AFFECTED_REGRESSION = 27 passed` nos módulos de autenticação/autorização;
frontend `12 passed, 0 failed`; agenda `6 setup errors` antes do corpo funcional.
Os resultados anteriores de financeiro, recovery e migrations permanecem sem
causalidade com esta alteração, que não toca produto.

`TEST_FAILURE_CLASSIFICATION = ENVIRONMENTAL_NON_CAUSAL_TMP_PATH_ACL` para os
erros de `tmp_path`: `PermissionError` na criação do lock sob
`%TEMP%\\pytest-of-...`, reproduzido fora do guard.

## STATIC_VALIDATION_RESULT

PASS. AST parse dos três arquivos Python alterados passou; não há import de
dependência nova fora da biblioteca padrão; nenhum código de produção foi
alterado.

## DIFF_CHECK_RESULT

PASS. `git diff --check` passou.

## SENSITIVE_DATA_CHECK_RESULT

PASS. Delta composto por código de teste/guard e documentação; somente dados
sintéticos, sem segredo, token, credencial ou PII.

## OPERATIONAL_SENTINEL_RESULT

PASS, somente leitura. Generation 9/canonical permanece authoritative; pointer,
manifest e banco não foram alterados. Hashes autoritativos continuam
consistentes; SQLite read-only retornou `integrity=ok`, `foreign_key_check=[]`,
`user_version=5`; sem sidecars e sem maintenance lock.

## RESULTADO E LIMITE

`BLOCKER001_REMEDIATION_RESULT = PASS`
`BLOCKER001_STATE = REMEDIATED_PENDING_INDEPENDENT_REREVIEW`
`SPEC007_FOUNDATION_STATE = REMEDIATED_PENDING_INDEPENDENT_REREVIEW`
`SPEC007_FINAL_STATE = OPEN`
`SPEC009_READINESS = NOT_READY_PENDING_FOUNDATION_REREVIEW`

O blocker não está formalmente fechado. O fechamento pertence à rerevisão
independente, em papel distinto do executor.

`NEW_BLOCKERS = 0`
`NEW_MAJORS = 0`
`NEW_MINORS = 0`
`REPOSITORY_MUTATED = YES`
`OPERATIONAL_STATE_MUTATED = NO`
`STAGED = NO`
`COMMIT_EXECUTED = NO`
`PUSH_EXECUTED = NO`

`STOP_CONDITION = SPEC007_FOUNDATION_BLOCKER001_REMEDIATION_COMPLETE`
`NEXT_READY = SPEC007_FOUNDATION_TARGETED_INDEPENDENT_REREVIEW`
