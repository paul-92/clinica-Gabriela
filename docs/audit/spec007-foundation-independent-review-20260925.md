# Parecer independente — SPEC-007 Foundation

**Data:** 2026-09-25
**Escopo:** revisão independente e proporcional exclusivamente da foundation da SPEC-007
**Privacy-safe:** sem dados clínicos, credenciais ou PII no parecer.

## CONTEXT_RECOVERY_RESULT

PASS. Repositório `https://github.com/paul-92/clinica-Gabriela.git`, branch
`feature/spec-008-architecture-foundation`, `HEAD=1820ab2`, upstream no mesmo
commit e sync `0/0`. Não havia staging. Alterações documentais e resíduos
temporários preexistentes foram preservados; a foundation em revisão é composta
por `pytest.ini`, `.coveragerc`, `tests/conftest.py`, `tests/support/` e
`tests/test_spec007_foundation.py`.

## FOUNDATION_SCOPE_REVIEW_RESULT

PASS. A implementação revisada permanece transversal e limitada a descoberta e
markers do pytest, configuração de coverage, factories sintéticas, fixtures
isoladas e guard de paths. Não foram antecipadas funcionalidades da SPEC-009 ou
SPEC-010, não houve tentativa de closure integral da SPEC-007 e não foi
transportado controle extraordinário da SPEC-005 para a foundation.

## FOUNDATION_IMPLEMENTATION_REVIEW_RESULT

FAIL. `pytest.ini`, `.coveragerc` e as factories/fixtures são coerentes com o
escopo e os testes direcionados passam. O runtime guard bloqueia caminhos
absolutos, relativos com `..` e os caminhos operacionais normais, mas não
canonicaliza corretamente URIs Windows `file:///C:/...` e `file://C:/...`.
Nessas variantes a rejeição preventiva não ocorre; a chamada chega ao SQLite e
termina em `OperationalError`. Não houve abertura bem-sucedida nem mutação do
banco operacional, mas o controle crítico está incompleto.

## RUNTIME_GUARD_INDEPENDENT_RESULT

FAIL. Em harness isolado e sem escrever nos arquivos operacionais:

- caminho absoluto do banco operacional: bloqueado;
- caminho relativo com `..`: bloqueado;
- `file:C:/...` e `file:/C:/...`: bloqueados;
- `file:///C:/...` e `file://C:/...`: não bloqueados pelo guard; a chamada
  falhou no SQLite antes de uma abertura útil.

O bypass é reproduzível pela função `_resolved_sqlite_target` em
`tests/conftest.py`, que não remove a autoridade/encoding da URI antes de
comparar o caminho canonicalizado.

## TARGETED_TESTS_INDEPENDENT_RESULT

PASS: `.venv\Scripts\python.exe -m pytest tests/test_spec007_foundation.py
tests/test_security.py -q` resultou em **3 passed**.

## AFFECTED_REGRESSION_INDEPENDENT_RESULT

PASS para os casos que chegaram ao código funcional: autenticação/API e
autorização somaram **27 passed**; a seleção com agenda, financeiro,
recovery/migrations somou mais **10 passed** e **47 setup errors**. Os erros
ocorreram na fixture `tmp_path`, ao criar `.lock` sob `%TEMP%\pytest-of-...`,
antes do corpo funcional dos testes. Frontend: **12 passed, 0 failed**.

## TMP_PATH_FAILURE_INDEPENDENT_CLASSIFICATION

`ENVIRONMENTAL_NON_CAUSAL`. Os erros convergem para `PermissionError` de ACL do
TEMP/OneDrive na criação do lock do pytest, reproduzem-se em módulos anteriores
à foundation e também impedem um `--basetemp` curto no workspace. Não há
evidência de causalidade ou amplificação por `pytest.ini`, factories ou runtime
guard.

## STATIC_VALIDATION_RESULT

PASS. AST parse dos quatro arquivos Python da foundation passou; `git diff
--check` passou; não foram identificadas alterações acidentais em código de
produção nos arquivos revisados. O workspace contém resíduos temporários
restritos, preservados sem alteração de ACL.

## SENSITIVE_DATA_CHECK_RESULT

PASS. Factories e fixtures usam somente valores sintéticos; a varredura dos
arquivos da foundation não encontrou padrões de segredo, token ou credencial.

## OPERATIONAL_SENTINEL_RESULT

PASS, somente leitura. O runtime operacional está materializado. O pointer
canônico indica `generation=9` e `state=canonical`; o hash do banco e o hash do
manifest conferem com o pointer. A verificação SQLite read-only retornou
`integrity=ok`, `foreign_key_check=[]` e `user_version=5`; não havia sidecars
do banco nem maintenance lock. Nenhuma mutação operacional foi executada.

## AC_TRACEABILITY_INDEPENDENT_RESULT

AC-001, AC-002 e AC-012 permanecem **foundation candidates**, sem promoção a
PASS integral. Requisitos dependentes da SPEC-009 e SPEC-010 permanecem
parciais, e a integração/closure final permanece pendente. O blocker do runtime
guard impede declarar a foundation independentemente verificada.

## QUALITY_GATE_RESULT

`QUALITY_GATE_FAIL`

## FINDINGS

`BLOCKERS = 1` — runtime guard não rejeita todas as formas equivalentes de URI
Windows para o banco operacional.

`MAJORS = 0`

`MINORS = 0`

`OBSERVATIONS = 2` — ACL do TEMP/OneDrive impede parte da regressão; há resíduos
temporários com permissões restritivas no workspace, preservados por segurança.

## STATE

`SPEC007_FOUNDATION_STATE = REMEDIATION_REQUIRED`
`SPEC007_FINAL_STATE = OPEN`
`SPEC009_READINESS = NOT_READY_BLOCKED_BY_FOUNDATION_REMEDIATION`

## EVIDENCE_RESULT

Parecer independente criado em `docs/audit/` com reprodução dos controles
materiais. O parecer não autoriza SPEC-009, SPEC-010, closure, staging, commit,
push ou qualquer operação de promoção.

`OPERATIONAL_STATE_MUTATED = NO`
`STAGED = NO`
`COMMIT_EXECUTED = NO`
`PUSH_EXECUTED = NO`

`STOP_CONDITION = SPEC007_FOUNDATION_INDEPENDENT_REVIEW_FAIL`
`NEXT_READY = REMEDIATION_OR_HUMAN_DECISION_REQUIRED`
