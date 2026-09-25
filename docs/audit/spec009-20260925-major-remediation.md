# SPEC-009 — Targeted major remediation Evidence

Data: 2026-09-25
Escopo autorizado: somente MAJOR-001 e MAJOR-002 da revisão independente.
Nenhum gate ambiental foi reavaliado.

## CONTEXT_RECOVERY_RESULT

`PASS_WITH_PREEXISTING_CHANGES_PRESERVED`.

Repository: `feature/spec-008-architecture-foundation`; HEAD/upstream estavam
sincronizados em `0/0`; não havia staging. Alterações de outras SPECs, resíduos
históricos, implementação original, E009-08, D009-06 e o parecer independente
foram preservados. A remediação alterou apenas backend de prontuário, frontend
de configurações e testes/Evidence associados.

## MAJOR001_RECONCILIATION_RESULT

`CONFIRMED`. O parecer independente identificou que as rotas de prontuário
exigiam papel `psychologist`, mas não filtravam por profissional autenticado.
Evidence original: `docs/audit/spec009-20260925-independent-review.md`;
arquivos: `backend/api/routes/clinical_records.py` e
`backend/services/clinical_record_service.py`; ACs afetados: AC-004, AC-005 e
AC-010.

## MAJOR001_ROOT_CAUSE_RESULT

`SUFFICIENT_EXISTING_CONTRACT`. O vínculo determinístico já existia em
`User.psychologist_id`, com unicidade para `Psychologist.id`, e o registro já
possuía `ClinicalRecord.psychologist_id`. Nenhuma coluna, tabela, migration,
regra nova de ownership ou decisão de compartilhamento foi necessária.

## MAJOR001_REMEDIATION_RESULT

`PASS_PENDING_INDEPENDENT_REREVIEW`. O backend agora:

- exige usuário autenticado nas operações de listagem, leitura e atualização;
- lista somente registros do `psychologist_id` vinculado ao usuário;
- retorna 404 para leitura/alteração direta de registro de outro profissional;
- rejeita psicólogo sem vínculo;
- rejeita criação cujo `psychologist_id` diverge do vínculo autenticado;
- aplica a mesma autorização em finalização, retificação e exclusão;
- mantém admin sem acesso clínico automático, conforme SPEC-002.

Não houve alteração de schema ou migration.

## CLINICAL_AUTHORIZATION_TEST_RESULT

`PASS`: casos sintéticos cobriram psicólogo autorizado, psicólogo não
autorizado, psicólogo sem vínculo, listagem, leitura direta por ID, criação e
alteração. A regressão de rotas confirmou 401 sem autenticação, 403 para
reception/admin e acesso de psicólogo vinculado.

## SPEC002_SECURITY_REGRESSION_RESULT

`PASS`: testes selecionados de autenticação/autorização e gestão de usuários
passaram; o contrato de perfis e a regra de que admin não recebe acesso clínico
automático foram preservados.

## CLINICAL_CONTRACT_REGRESSION_RESULT

`PASS` nos testes selecionados de ciclo de prontuário, vínculo, imutabilidade,
retificação e exclusão. Fixtures passaram a declarar explicitamente o vínculo
existente, sem inventar dados clínicos.

## MAJOR002_RECONCILIATION_RESULT

`CONFIRMED`. O botão estava fora do `<form onSubmit={save}>`, sem submit handler,
e por isso não disparava `PUT /settings`. Evidence original: parecer
independente, E009-06 e `frontend/src/main.jsx`.

## MAJOR002_ROOT_CAUSE_RESULT

`CONFIRMED`: o handler `save` e o cliente API já existiam, mas o clique não
alcançava o handler por causa da estrutura HTML.

## MAJOR002_REMEDIATION_RESULT

`PASS_PENDING_INDEPENDENT_REREVIEW`. O botão foi colocado dentro do formulário
com `type="submit"`; o fluxo agora usa `PUT /settings`, converte o valor da
sessão com helper explícito, desabilita o botão durante o request, mostra
`Salvando...`, mostra sucesso somente após resposta positiva e mostra erro
sanitizado sem falso sucesso.

## SETTINGS_SAVE_TEST_RESULT

`PASS`: teste frontend confirmou payload numérico, submit, loading/disabled e
tratamento de erro. O build web também passou.

## TARGETED_TESTS

`PASS`: `.venv\\Scripts\\python.exe -m pytest tests/test_spec009_major_remediation.py tests/test_route_authorization.py tests/test_user_management_api.py -q` → `20 passed`.

## AFFECTED_REGRESSION

`PASS`: auth, authorization, contratos clínicos selecionados e user management
→ `47 passed` no conjunto ampliado.

## FRONTEND_TESTS

`PASS`: `npm test` → `14 passed, 0 failed`.

## WEB_BUILD_RESULT

`PASS`: `npm run build` executado fora da limitação `spawn EPERM` do sandbox;
Vite transformou 1.582 módulos e produziu o bundle web.

## FULL_BACKEND_SUITE

`PARTIAL_ENVIRONMENTALLY_BLOCKED`: a execução completa reproduziu a limitação
conhecida de ACL ao criar locks em `%TEMP%\\pytest-of-paulo.trajano`, com
aproximadamente `157 passed` e `206 errors` de setup. Os erros são ambientais,
não causalmente atribuídos à remediação.

## TEST_FAILURE_CLASSIFICATION

`ENVIRONMENTAL_NON_CAUSAL`: erros concentrados em `tmp_path`/lock de TEMP sob
Windows/OneDrive. Nenhuma falha funcional foi observada no escopo direcionado.

## STATIC_VALIDATION_RESULT

`PASS`: `compileall` passou; revisão estática confirmou autorização no service e
fluxo de submit/erro/loading no formulário.

## DIFF_CHECK_RESULT

`PASS`: `git diff --check` passou.

## SENSITIVE_DATA_CHECK_RESULT

`PASS`: scan privacy-safe não encontrou chaves privadas, tokens ou segredos no
delta; fixtures usam dados sintéticos.

## AC_INVALIDATION_RESULT

Os ACs invalidados pelo parecer anterior foram AC-004, AC-005 e AC-010 para
MAJOR-001; o fluxo de configurações de E009-06 foi invalidado por MAJOR-002.
Os quatro gates ambientais continuam fora desta remediação.

## AC_TARGETED_REVALIDATION_RESULT

`PASS_PENDING_INDEPENDENT_REREVIEW`: autorização clínica por vínculo e o fluxo
de salvar configurações foram remediados e cobertos pelos testes acima. Isto
não é closure geral nem revalida Electron smoke, responsividade ou
acessibilidade runtime.

## BLOCKERS

`0`.

## NEW_MAJORS

`0`.

## NEW_MINORS

`0`.

## SPEC009_RUNTIME_VALIDATION_DEBT

`OPEN_TRACKED`: Electron build/package, Electron smoke, responsiveness runtime e
accessibility runtime permanecem `DEFERRED_ENVIRONMENTAL_VALIDATION` conforme
D009-06.

## EVIDENCE_RESULT

`PASS`: esta Evidence é específica da remediação, privacy-safe e não sobrescreve
a implementação original, E009-08, D009-06 ou o parecer independente FAIL.

## MAJOR001_STATE

`REMEDIATED_PENDING_INDEPENDENT_REREVIEW`.

## MAJOR002_STATE

`REMEDIATED_PENDING_INDEPENDENT_REREVIEW`.

## SPEC009_VERIFIABLE_SCOPE_STATE

`REMEDIATED_PENDING_INDEPENDENT_REREVIEW`.

## SPEC009_FINAL_STATE

`OPEN`.

## REPOSITORY_MUTATED

`YES`: código/testes/Evidence autorizados foram alterados.

## OPERATIONAL_STATE_MUTATED

`NO`: nenhuma migration, restore, promotion, pointer/Generation change,
maintenance operation ou cleanup foi executado.

## STAGED

`NO`.

## COMMIT_EXECUTED

`NO`.

## PUSH_EXECUTED

`NO`.

## STOP_CONDITION

`SPEC009_MAJOR_REMEDIATION_COMPLETE`.

## NEXT_READY

`SPEC009_TARGETED_INDEPENDENT_REREVIEW`.
