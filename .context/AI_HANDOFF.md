# AI Handoff

## Repositorio

Remoto local `origin`: `https://github.com/paul-92/clinica-Gabriela.git`

## Branch

`main`

## Commit atual

`00939f3b39b196784c2a98647b7fc8fe5f556a66`

Mensagem: `chore: adicionar projeto inicial da clinica desktop`

## Estado da arvore de trabalho

Repositorio publicado com sucesso. `main` local acompanha `origin/main`, e a arvore de trabalho estava limpa apos o push.

## Objetivo

Usar esta pasta desktop/API/frontend como fonte de verdade compartilhada entre Codex, GitHub e ChatGPT.

## Estado atual da implementacao

Projeto funcional em camadas com desktop Tkinter, backend FastAPI, frontend Electron + React, SQLite local, scripts Windows, docs e testes de seguranca.

## O que funciona

- App desktop inicia por `main.py`.
- API FastAPI em `backend.main:app`.
- Frontend Electron + React em `frontend/`.
- Seeds e migracoes leves existem para desktop e backend.
- Licenciamento local existe.
- Teste de hash/verificacao de senha existe.
- Documentacao tecnica e funcional existe em `docs/`.

## O que esta incompleto

- Lint/type checking nao estao configurados de forma confirmada.
- Auditoria funcional e tecnica completa do sistema ainda nao foi realizada apos a publicacao inicial.
- Gaps entre desktop, backend e frontend ainda precisam ser mapeados e priorizados.

## Falhas conhecidas

- Arquivos locais sensiveis/gerados existem na pasta e devem ficar fora do Git: `.license_secret`, `license.json`, bancos `.db`, `.venv`, `frontend/node_modules`, caches e `*.pyc`.
- Usuarios e senhas de exemplo existem para demonstracao.

## Restricoes arquiteturais

- Nao versionar licencas geradas, segredos, bancos locais ou dependencias instaladas.
- Trabalhar em branches de feature para proximas mudancas funcionais.
- Manter separacao em camadas.
- Se alterar modelos ou rotas, atualizar schemas, services, repositories, frontend e docs afetados.

## Testes/build

Comandos confirmados nos arquivos do projeto:

- `python -m pytest`
- `python main.py`
- `uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`
- `cd frontend && npm run dev`
- `cd frontend && npm run build`
- `cd frontend && npm run dist`
- `build_windows.bat`

Validacao executada nesta preparacao:

- `npm run build` em `frontend/`: passou.
- `pytest>=8.0` foi adicionado a `requirements.txt` por ser necessario para a suite existente e nao havia arquivo de dependencias de desenvolvimento.
- `python -m pytest`: passou com `1 passed`.
- `git diff --cached --check`: passou antes do commit.
- `main` remoto aponta para `00939f3b39b196784c2a98647b7fc8fe5f556a66`.

## Proximo passo recomendado

1. Realizar auditoria funcional/tecnica do sistema atual.
2. Identificar gaps entre desktop, backend e frontend.
3. Priorizar bugs, divida tecnica e funcionalidades.
4. Trabalhar em branch de feature para proximas mudancas.

## Arquivos que outra IA deve ler primeiro

1. `AGENTS.md`
2. `.context/PROJECT_CONTEXT.md`
3. `.context/AI_HANDOFF.md`
4. `.context/COMMANDS.md`
5. `README.md`
6. `docs/ARCHITECTURE.md`
7. `docs/API.md`
8. `docs/FRONTEND.md`
9. `main.py`
10. `backend/main.py`
11. `frontend/src/main.jsx`
