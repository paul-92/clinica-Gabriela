# AI Handoff

## Repositorio

Remoto local `origin`: `https://github.com/paul-92/clinica-Gabriela.git`

## Branch

`main`

## Commit atual

Nenhum commit local ainda. O repositorio foi inicializado nesta raiz e ainda esta em estado de primeiro commit.

## Estado da arvore de trabalho

Git inicializado na raiz correta, `origin` configurado e staging do primeiro commit preparado. Nao executar commit ou push sem autorizacao explicita.

## Objetivo

Usar esta pasta desktop/API/frontend como fonte de verdade compartilhada entre Codex, GitHub e ChatGPT, substituindo a preparacao feita anteriormente na pasta estatica. A pasta anterior teve o staging removido e nao sera usada para o primeiro commit.

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

- Git ainda precisa ser inicializado nesta raiz.
- Primeiro commit ainda nao foi criado.
- Push para GitHub ainda nao autorizado.
- Lint/type checking nao estao configurados de forma confirmada.

## Falhas conhecidas

- Arquivos locais sensiveis/gerados existem na pasta e devem ficar fora do Git: `.license_secret`, `license.json`, bancos `.db`, `.venv`, `frontend/node_modules`, caches e `*.pyc`.
- Usuarios e senhas de exemplo existem para demonstracao.

## Restricoes arquiteturais

- Nao versionar licencas geradas, segredos, bancos locais ou dependencias instaladas.
- Nao fazer push sem autorizacao explicita.
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
- `.venv\Scripts\python.exe -m pytest`: executar antes do commit final.
- Checagem direta de `hash_password`/`verify_password` com `.venv\Scripts\python.exe -c "..."`
  passou antes da instalacao do pytest.
- `git ls-remote --heads origin`: passou e nao retornou branches, consistente com repositorio vazio.

## Proximo passo recomendado

Revisar a lista staged, pedir autorizacao explicita do usuario e executar o primeiro commit. Pedir autorizacao separada antes de qualquer push.

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
