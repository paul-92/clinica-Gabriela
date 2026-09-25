# SPEC-009 — Independent review of verifiable scope

Data: 2026-09-25
Natureza: revisão independente, read-only, baseada em código, contratos e
reprodução local. Nenhuma correção foi executada nesta revisão.

## CONTEXT_RECOVERY_RESULT

`PASS_WITH_PREEXISTING_CHANGES_PRESERVED`.

- repository: `feature/spec-008-architecture-foundation`
- HEAD: `523eea7551cc35c6d082e6460d66b830143bd482`
- upstream: `origin/feature/spec-008-architecture-foundation`
- ahead/behind: `0/0`
- staged: nenhum
- unstaged: alterações da SPEC-009, documentação e handoff já existentes
- untracked: Evidence e resíduos históricos de revisões anteriores, inclusive
  diretórios com ACL restrita
- delta verificável da SPEC-009: rotas/serviço/schemas de usuários, shell/API
  React, agenda, estados fail-closed, design tokens e documentação associada

Nenhuma mutation operacional foi necessária ou executada.

## D00906_INDEPENDENT_RECONCILIATION_RESULT

`PASS`. Permanecem explicitamente não validados e classificados como
`DEFERRED_ENVIRONMENTAL_VALIDATION`:

1. Electron build/package;
2. Electron smoke;
3. responsiveness runtime em 1366x768/1920x1080, 100%/125%;
4. accessibility runtime, incluindo teclado, foco, contraste e modais.

Não foram promovidos a PASS por inferência, code review ou Evidence anterior.

## SPEC009_CONTRACT_REVIEW_RESULT

`PARTIAL` para o conjunto verificável. A direção visual, tokens, agenda
Lista/Dia/Semana, gestão admin de usuários, API como autoridade e fail-closed
visual estão presentes. A ausência de fallback operacional fictício foi
confirmada. Porém, a implementação atual não mantém isolamento de prontuários
por ator no backend e a ação de salvar configurações não está ligada ao form.

## E00901_INDEPENDENT_RESULT

`PASS`. O contrato congelado, os limites E009-01..E009-08 e as decisões HUMAN
D009-01..D009-06 estão documentados e não houve tentativa de fechar a SPEC.

## E00902_INDEPENDENT_RESULT

`PARTIAL`. Tokens reutilizáveis, paleta sage/blush/creme, tipografia, espaçamento,
raios, foco e shell compartilhado foram confirmados por inspeção estática.
Validação visual/runtime permanece deferida.

## E00903_INDEPENDENT_RESULT

`PASS` no escopo executável. Login usa API e `/auth/me`, logout limpa a sessão,
timeouts e erros são sanitizados, e a UI não cria sessão offline. Testes de
autenticação/autorização e frontend passaram.

## E00904_INDEPENDENT_RESULT

`PASS` no escopo verificável. Dashboard, pacientes, psicólogos e agenda possuem
contratos reais; a agenda oferece Lista, Dia e Semana e preserva `If-Match` nas
alterações/transições. A travessia visual runtime permanece deferida.

## E00905_INDEPENDENT_RESULT

`FAIL`. As rotas de prontuário exigem o papel `psychologist`, mas
`GET /clinical-records`, `GET /clinical-records/{id}`, `PATCH` e `PUT` não
recebem nem validam o ator/profissional autorizado. O serviço
`ClinicalRecordService` lista, consulta e atualiza por id sem restringir o
registro ao psicólogo autenticado. Um psicólogo autenticado pode, portanto,
consultar conteúdo clínico de outro profissional e editar rascunho alheio.

Evidence: `backend/api/routes/clinical_records.py:12-40` e
`backend/services/clinical_record_service.py:27-53`.

## E00906_INDEPENDENT_RESULT

`FAIL` no fluxo de configurações. A integração backend `GET /settings`/`PUT
/settings` é real e protegida por admin, mas em `frontend/src/main.jsx:1092-1114`
o botão “Salvar configurações” está fora do `<form onSubmit={save}>` e não tem
`type="submit"`, `form` ou `onClick`. A ação visível não dispara o PUT nem pode
produzir o sucesso declarado.

Financeiro e relatórios preservam os contratos de período, centavos e dados
suportados; a validação visual/runtime permanece deferida.

## E00907_INDEPENDENT_RESULT

`PASS` no escopo verificável. `GET /users`, `POST /users` e `PATCH /users/{id}`
estão registrados; a UI é filtrada para admin, tem estados de loading/erro/
sucesso, confirmação para mudanças destrutivas e não exibe hashes.

## USER_MANAGEMENT_SECURITY_INDEPENDENT_RESULT

`PASS`. Bearer obrigatório, autorização `admin` no backend, hashing antes da
persistência, `UserRead` sem `password_hash`, payload extra proibido, validação
de tamanho/papel, duplicidade sanitizada, proteção contra auto-desativação e
mensagens sem detalhes SQL/segredos foram confirmados. Quatro testes dirigidos
passaram.

## SPEC002_SECURITY_COMPATIBILITY_RESULT

`PASS` para a regressão selecionada. Não houve alteração material do contrato
de autenticação da SPEC-002; os testes de auth/authorization selecionados
passaram.

## API_FAIL_CLOSED_INDEPENDENT_RESULT

`PASS` no código/testes verificáveis. Timeout e falha de fetch produzem erro
sanitizado, 401 encerra a sessão, dados operacionais são limpos e não há
fallback operacional fictício. Retry é explícito pelo botão da UI; não há
retry automático ilimitado.

## AGENDA_INDEPENDENT_RESULT

`PASS` no contrato verificável. Lista/Dia/Semana existem; ações de edição,
cancelamento, falta, realização e remarcação enviam `If-Match`. Conflitos e
autorização continuam no backend. Smoke visual não foi executado.

## CLINICAL_RECORD_INDEPENDENT_RESULT

`FAIL`, pelos mesmos motivos de E009-05. A UI não renderiza `private_notes` na
timeline, mas isso não corrige a exposição pelo contrato JSON/backend nem a
ausência de autorização por registro.

## FINANCIAL_INDEPENDENT_RESULT

`PASS` no escopo verificável. A UI usa centavos, períodos explícitos e não
infere `paid_at` nem transforma quarentena em dado operacional. Os valores
iniciais do formulário são defaults de entrada, não dados apresentados como
reais.

## SETTINGS_INDEPENDENT_RESULT

`FAIL` no fluxo de usuário: o backend é real e admin-only, porém o botão de
salvar não submete o formulário, conforme E009-06.

## TARGETED_TESTS_INDEPENDENT_RESULT

`PASS`: `.venv\\Scripts\\python.exe -m pytest tests/test_user_management_api.py
-q` resultou em `4 passed`.

## AFFECTED_REGRESSION_INDEPENDENT_RESULT

`PASS` para a regressão selecionada de autenticação/autorização; nenhuma falha
funcional foi observada nos testes direcionados.

## FULL_SUITE_FAILURE_CLASSIFICATION

`ENVIRONMENTAL_NON_CAUSAL`: `.venv\\Scripts\\python.exe -m pytest -q` terminou
com `155 passed, 206 errors`. Os erros ocorreram no setup de `tmp_path`, ao
criar `.lock` em `%TEMP%\\pytest-of-paulo.trajano`, com `PermissionError`
associado à ACL/OneDrive. Isso não valida a suíte completa e não mascara os
dois achados independentes acima.

## FRONTEND_TESTS_INDEPENDENT_RESULT

`PASS`: `npm test` resultou em `12 passed, 0 failed`.

## WEB_BUILD_INDEPENDENT_RESULT

`DEFERRED_ENVIRONMENTAL_VALIDATION`. A execução independente de `npm run build`
falhou em `esbuild` com `spawn EPERM` no ambiente sandboxed. A Evidence do
executor registra uma execução posterior fora desse bloqueio, mas ela não foi
reclassificada como validação independente nesta revisão.

## STATIC_VALIDATION_RESULT

`PASS` para sintaxe e higiene: `compileall` passou, `git diff --check` passou e
não foram encontradas violações de sintaxe no delta. A inspeção estática ainda
produziu os achados funcionais acima.

## SENSITIVE_DATA_CHECK_RESULT

`PASS` para o delta revisado: nenhum segredo privado foi encontrado e os dados
de testes/Evidence são sintéticos. Os usuários e dados de demonstração
históricos permanecem fora da conclusão de ausência de PII real.

## AC_TRACEABILITY_INDEPENDENT_RESULT

- AC-001: `DEFERRED_ENVIRONMENTAL_VALIDATION` — Electron smoke/build runtime.
- AC-002: `PARTIAL` — shell consistente por inspeção; validação visual deferida.
- AC-003: `PARTIAL` — tokens/componentes confirmados; build/runtime deferidos.
- AC-004: `PARTIAL` — sidebar/backend de papel confirmados; prontuário falha em
  isolamento por registro; runtime deferido.
- AC-005: `FAIL` — backend não aplica autorização por ator nos endpoints de
  prontuário.
- AC-006: `PARTIAL` — estados existem; runtime deferido.
- AC-007: `PASS` — autenticação não usa fallback local.
- AC-008: `PASS` — dashboard consome API e limpa dados em erro.
- AC-009: `PARTIAL` — contrato financeiro verificável passa; runtime deferido.
- AC-010: `FAIL` — isolamento/autorização de conteúdo clínico não está completo.
- AC-011: `DEFERRED_ENVIRONMENTAL_VALIDATION` — matriz runtime de resolução.
- AC-012: `DEFERRED_ENVIRONMENTAL_VALIDATION` — teclado/foco runtime.
- AC-013: `PASS` no escopo estático — API client e componentes compartilhados.
- AC-014: `DEFERRED_ENVIRONMENTAL_VALIDATION` — smoke visual.

## BLOCKERS

`0`.

## MAJORS

`2`.

- `MAJOR-001 / PRODUCT_FINDING`: ausência de autorização/isolamento por ator
  nas rotas de prontuário; risco de exposição e alteração de conteúdo clínico.
- `MAJOR-002 / PRODUCT_FINDING`: botão de configurações não submete o PUT;
  fluxo funcional prometido é inoperante.

## MINORS

`0`.

## OBSERVATIONS

`2`: ACL de TEMP/OneDrive bloqueia parte da suíte Python; resíduos temporários
restritos preexistentes foram preservados. Esses itens são ambientais/históricos,
não novos defeitos de produto.

## QUALITY_GATE_RESULT

`QUALITY_GATE_FAIL` — há dois `MAJOR` no escopo verificável.

## SPEC009_VERIFIABLE_SCOPE_REVIEW

`FAIL`.

## SPEC009_INDEPENDENT_REVIEW

`FAIL`.

## SPEC009_RUNTIME_VALIDATION_DEBT

`OPEN_TRACKED`: Electron build, Electron smoke, responsiveness runtime e
accessibility runtime permanecem deferidos.

## SPEC009_FINAL_STATE

`OPEN`.

## SPEC009_CLOSURE_READINESS

`NOT_READY_FOR_FINAL_CLOSURE`.

## SPEC010_RUNTIME_VALIDATION_HANDOFF_RESULT

`REQUIRED_NOT_STARTED`. SPEC-010 deve herdar e produzir Evidence para os quatro
gates ambientais: Electron build, Electron smoke, responsiveness 1366x768 e
1920x1080 em 100%/125%, accessibility runtime e regressão integrada. Antes
disso, os dois MAJOR de produto exigem remediação e nova revisão independente.

## OPERATIONAL_SENTINEL_RESULT

`READ_ONLY / NOT_MUTATED`. Nenhuma migration, restore, promotion, pointer
switch, maintenance operation, Generation 9/canonical mutation ou cleanup foi
executado. A revisão não acessou artefatos operacionais para alteração.

## REPOSITORY_MUTATED

`YES — somente este parecer independente foi criado.`

## OPERATIONAL_STATE_MUTATED

`NO`.

## STAGED

`NO`.

## COMMIT_EXECUTED

`NO`.

## PUSH_EXECUTED

`NO`.

## STOP_CONDITION

`SPEC009_INDEPENDENT_REVIEW_FAIL`.

## NEXT_READY

`REMEDIATION_OR_HUMAN_DECISION_REQUIRED`.
