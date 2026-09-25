# SPEC-009 — Targeted independent rereview

Data: 2026-09-25. Escopo exclusivo: MAJOR-001 (isolamento de prontuários) e
MAJOR-002 (persistência de configurações). Nenhum gate ambiental foi executado
e nenhum closure, staging, commit, push ou SPEC-010 foi iniciado.

## CONTEXT_RECOVERY_RESULT

`PASS_WITH_PREEXISTING_CHANGES_PRESERVED`. Repository:
`feature/spec-008-architecture-foundation`; HEAD e upstream sincronizados em
`0/0`; staging vazio. O delta de remediação, o parecer independente FAIL,
Evidence original, D009-06, resíduos históricos e alterações de outras SPECs
foram preservados. Generation 9/canonical e estado operacional não foram
alterados.

## MAJOR001_INDEPENDENT_REREVIEW

`PASS`. O service deriva o escopo exclusivamente de `current_user.psychologist_id`,
que corresponde ao vínculo `User.psychologist_id`; não houve nova regra de
domínio, coluna ou migration. Listagem, leitura por ID, criação, PUT/PATCH,
finalização, retificação e exclusão passam pelo vínculo/autorização no backend.

## CLINICAL_RECORD_AUTHORIZATION_RESULT

`PASS`. Psicólogo vinculado acessa apenas seu escopo; psicólogo sem vínculo,
usuário não autenticado, reception e admin são rejeitados. Criação com
`psychologist_id` divergente retorna 403. Registro inexistente ou pertencente a
outro psicólogo não retorna conteúdo clínico e a leitura/alteração direta por ID
retorna 404.

## CROSS_PSYCHOLOGIST_ACCESS_RESULT

`PASS`. Registros sintéticos de dois psicólogos foram criados e o segundo não
foi retornado na listagem do primeiro nem pôde ser lido ou alterado.

## DIRECT_ID_BYPASS_RESULT

`PASS`. O acesso direto por ID é filtrado pelo vínculo antes da resposta; as
rotas derivadas de `get_record` mantêm o mesmo comportamento.

## SPEC002_SECURITY_COMPATIBILITY_RESULT

`PASS`. Autenticação Bearer e autorização por role permaneceram efetivas;
admin não recebeu acesso clínico automático; testes de auth/authorization e
gestão de usuários passaram.

## CLINICAL_CONTRACT_COMPATIBILITY_RESULT

`PASS` nos ciclos selecionados de vínculo, imutabilidade, versionamento,
finalização, retificação e exclusão. Nenhum schema operacional ou migration foi
alterado.

## MAJOR002_INDEPENDENT_REREVIEW

`PASS`. O formulário de configurações tem `onSubmit={save}`, o botão é
`type="submit"`, o handler chama `PUT /settings` pelo cliente API e o payload
converte o valor monetário para número.

## SETTINGS_PERSISTENCE_RESULT

`PASS`. O salvamento mostra loading, desabilita o botão durante a requisição e
só mostra sucesso após resposta positiva real.

## SETTINGS_ERROR_HANDLING_RESULT

`PASS`. Falhas preservam retry, limpam o sucesso anterior, mostram erro
sanitizado e não produzem falso sucesso. A autorização admin-only do backend
permanece efetiva.

## ADVERSARIAL_REREVIEW_RESULT

`PASS_WITH_NEW_MINOR`. Bypass por ownership, ID, listagem, criação, atualização,
finalização, retificação e exclusão não revelou prontuário de outro
profissional. Foi identificado que `GET /clinical-records?patient_id=...`
distingue paciente inexistente (`404`) de paciente existente sem registros no
escopo (`200 []`), permitindo inferência de existência de paciente, sem revelar
conteúdo clínico. Classificado como `NEW-MINOR-001`; não é bypass de conteúdo de
prontuário e não impede o fechamento dos MAJORs.

## TARGETED_TESTS_INDEPENDENT_RESULT

`PASS`: 20 testes Python direcionados passaram.

## AFFECTED_REGRESSION_INDEPENDENT_RESULT

`PASS`: auth/authorization, prontuário e user management selecionados passaram.

## FRONTEND_TESTS_INDEPENDENT_RESULT

`PASS`: `npm test` — 14 passed, 0 failed.

## WEB_BUILD_INDEPENDENT_RESULT

`PASS`: `npm run build` passou fora do sandbox após o bloqueio inicial
`esbuild spawn EPERM`.

## FULL_SUITE_FAILURE_CLASSIFICATION

`ENVIRONMENTAL_NON_CAUSAL`. A suíte completa reproduziu erros de setup e
limpeza ao criar/acessar diretórios temporários e locks sob ACL Windows/OneDrive;
não houve falha funcional causal dos dois MAJORs. A suíte completa não é
considerada integralmente validada.

## STATIC_VALIDATION_RESULT

`PASS`: `git diff --check`, `compileall` e inspeção estática do delta passaram.

## SENSITIVE_DATA_CHECK_RESULT

`PASS_WITH_SYNTHETIC_FIXTURE_HITS`. Não foram encontrados segredos privados,
tokens ou PII real no delta. O scan encontrou apenas senhas literais sintéticas
em testes e dados de demonstração, que não são credenciais operacionais.

## AC_TARGETED_REVALIDATION_RESULT

`PASS_WITH_DEFERRED_ENVIRONMENTAL_VALIDATION`. AC-004, AC-005 e AC-010, além do
fluxo E009-06 de configurações, foram revalidados no escopo executável. Os
quatro gates ambientais permanecem deferidos e não foram promovidos por
inferência.

## FINDINGS_AND_GATE

`MAJOR001_STATE = CLOSED_BY_REMEDIATION_AND_INDEPENDENT_REREVIEW`

`MAJOR002_STATE = CLOSED_BY_REMEDIATION_AND_INDEPENDENT_REREVIEW`

`BLOCKERS = 0`

`OPEN_MAJORS = 0`

`NEW_MAJORS = 0`

`NEW_MINORS = 1 (NEW-MINOR-001: inferência de existência por patient_id)`

`OBSERVATIONS = TEMP/OneDrive ACL; quatro gates ambientais deferidos`

`QUALITY_GATE_RESULT = QUALITY_GATE_PASS_WITH_DEFERRED_RUNTIME_VALIDATION`

`SPEC009_VERIFIABLE_SCOPE_REVIEW = PASS`

`SPEC009_INDEPENDENT_REVIEW = PASS_WITH_DEFERRED_RUNTIME_VALIDATION`

`SPEC009_RUNTIME_VALIDATION_DEBT = OPEN_TRACKED`

`SPEC009_FINAL_STATE = OPEN`

`SPEC009_CLOSURE_READINESS = NOT_READY_FOR_FINAL_CLOSURE`

`SPEC009_REPOSITORY_CHECKPOINT_READINESS = READY`

## SPEC010_RUNTIME_VALIDATION_HANDOFF_RESULT

`READY_FOR_HANDOFF`. A próxima etapa pode ser `SPEC009_REPOSITORY_CHECKPOINT →
SPEC010`; SPEC-010 deve executar Electron build, Electron smoke,
responsiveness runtime e accessibility runtime para reconciliar a dívida D009-06.

## OPERATIONAL_SENTINEL_RESULT

`READ_ONLY_UNCHANGED`. Nenhuma migration, restore, promotion, pointer switch,
cleanup ou operação no runtime operacional foi executada.

`REPOSITORY_MUTATED = YES` — somente este parecer e a atualização histórica do
handoff.

`OPERATIONAL_STATE_MUTATED = NO`

`STAGED = NO`; `COMMIT_EXECUTED = NO`; `PUSH_EXECUTED = NO`.

`STOP_CONDITION = SPEC009_TARGETED_INDEPENDENT_REREVIEW_PASS`

`NEXT_READY = SPEC009_REPOSITORY_CHECKPOINT`
