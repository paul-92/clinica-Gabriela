# Evidence — SPEC-007 Foundation

**Data:** 2026-09-25
**Escopo:** foundation transversal da SPEC-007
**Privacy-safe:** somente dados sintéticos; nenhum dado clínico, credencial ou PII.

## Estado inicial e autorização

- Branch: `feature/spec-008-architecture-foundation`.
- Alterações preexistentes preservadas em `.context/COMMANDS.md`,
  `SPEC-010-instalador.md` e resíduos temporários.
- Generation 9/canonical permanece o baseline operacional.
- `HUMAN_SPEC007_FOUNDATION_IMPLEMENTATION_AUTHORIZATION = GRANTED`.
- SPEC-009, SPEC-010, closure, migration, restore, promotion, rollback, stage,
  commit e push permaneceram fora do escopo.

## FOUNDATION_DELTA_ANALYSIS

O inventário mostrou que já existiam: `tests/conftest.py` com raiz temporária,
isolamento de `BACKEND_DATA_DIR`/`BACKEND_DATABASE_PATH` e bloqueio de conexão
SQLite ao banco operacional; suíte Python ampla; e `frontend/test/api.test.js`
com script `npm test`. O menor delta foi complementar essa base com configuração
determinística, markers, cobertura, factories sintéticas e guard explícito de
paths, sem mover ou duplicar a infraestrutura existente.

## Componentes implementados

- `pytest.ini`: descoberta determinística e categorias `unit`, `integration`,
  `api`, `smoke`, `regression`, `frontend` e `desktop`.
- `.coveragerc`: branch coverage para `app` e `backend`, omitindo testes e
  dependências instaladas.
- `tests/support/factories.py`: factories dataclass sintéticas e reutilizáveis.
- `tests/support/runtime_guard.py`: validação de raiz isolada e rejeição de
  raízes operacionais.
- `tests/conftest.py`: fixtures de raiz/banco isolados e entidades sintéticas,
  reutilizando a barreira SQLite já existente.
- `tests/test_spec007_foundation.py`: smoke/unit tests da foundation.

## Traceability

| Componente | Requisito / AC | Resultado |
|---|---|---|
| pytest.ini | organização determinística; AC-012 | FOUNDATION_PASS |
| factories sintéticas | dados fictícios; AC-002 | FOUNDATION_PASS |
| runtime guard + conftest | isolamento; AC-001 | FOUNDATION_PASS |
| .coveragerc | coleta de cobertura | FOUNDATION_PASS |
| suporte frontend existente | estratégia transversal frontend | PARTIAL_PENDING_SPEC009 |
| testes Electron/Desktop finais | AC-010 e integração UI | PARTIAL_PENDING_SPEC009 |
| installer/máquina limpa | cenários SPEC-010 | PARTIAL_PENDING_SPEC010 |
| closure integrada | AC-013 e fechamento | PENDING_FINAL_INTEGRATION |

## Validação

- Targeted foundation + segurança: **3 passed**.
- Coleta estática: **352 tests collected**.
- Regressão afetada: **36 passed, 28 erros de setup**.
- Suíte Python completa: **146 passed, 206 erros de setup**.
- Os erros ocorreram na criação de locks do `tmp_path` em
  `%TEMP%\pytest-of-...` com `PermissionError`/ACL do Windows/OneDrive; não
  foram classificados como regressão funcional.
- Frontend: **12 passed, 0 failed** via `npm test`.
- `git diff --check`: PASS.
- Varredura de padrões de segredo nos arquivos da foundation: NONE.
- Arquivos executáveis de produção alterados: nenhum.

## Sentinel operacional

Verificação somente leitura. A pasta `runtime` operacional não está materializada
nesta workspace; o handoff canônico mantém Generation 9/canonical, pointer,
runtime manifest, banco operacional, integridade, FK, sidecars e maintenance
lock declarados sem alteração. Nenhuma escrita operacional foi executada antes,
durante ou depois dos testes.

## Itens deliberadamente adiados

- implementação SPEC-009;
- implementação SPEC-010;
- E2E final, testes visuais e responsividade final;
- testes de instalador/máquina limpa;
- validação integrada final e closure da SPEC-007;
- revisão independente.

## Resultado

Foundation implementada e pronta para revisão independente proporcional. A
SPEC-007 permanece aberta; a autorização seguinte é somente para a revisão
independente da foundation.
