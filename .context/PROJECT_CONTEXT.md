# Project Context

## Visao geral do projeto

Sistema para clinica de psicologia com tres superficies principais: aplicacao desktop Python/Tkinter, backend FastAPI e frontend Electron + React. O projeto tambem inclui banco SQLite com SQLAlchemy, scripts Windows, documentacao, imagens de previa, licenciamento local e testes Python.

## Estado atual

O projeto local existe em:

`C:\Users\paulo.trajano\Documents\Codex\2026-07-06\create-psychology-clinic-desktop-crie-a\outputs\clinica_psicologia_desktop`

Ele ainda nao tinha repositorio Git inicializado nesta pasta quando foi identificado. Ha dependencias ja instaladas localmente em `.venv/` e `frontend/node_modules/`, alem de bancos SQLite e arquivos de licenca gerados; esses itens sao runtime/local e nao devem ser versionados.

## Arquitetura

- Desktop: `main.py` inicializa licenca, banco, migracoes leves, seed e abre `LoginView`.
- Backend: `backend/main.py` cria app FastAPI, inicializa banco, migracoes, seed, middleware de licenca e inclui rotas.
- Frontend: `frontend/` usa Vite, React, Electron e lucide-react. Consome API em `http://127.0.0.1:8000`.
- Banco: SQLite local com SQLAlchemy.
- Licenciamento: `app.utils.license` gera/valida `license.json` usando `.license_secret`.

## Principais componentes

- Login com senha criptografada.
- Dashboard.
- Cadastro/listagem de pacientes.
- Cadastro estrutural de psicologos.
- Agenda de atendimentos.
- Prontuario clinico.
- Financeiro.
- Relatorios.
- Backup local.
- Configuracoes.
- Backend FastAPI com rotas, schemas, services, repositories e models.
- Frontend Electron + React com telas principais.

## Estrutura do repositorio

- `main.py`
- `requirements.txt`
- `README.md`
- `app/`
- `backend/`
- `frontend/`
- `scripts/`
- `docs/`
- `tests/`
- arquivos `.bat` de instalacao, execucao, build e licenca.
- `.context/`
- `AGENTS.md`
- `.gitignore`

## Fluxos principais

1. Desktop:
   - `python main.py`.
   - Valida licenca.
   - Inicializa banco.
   - Roda migracoes leves.
   - Executa seed.
   - Abre login Tkinter.

2. API:
   - `uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`.
   - Disponibiliza `/health`, `/docs`, `/auth/login`, rotas de dashboard, pacientes, psicologos, agenda, prontuarios, financeiro, configuracoes e licenca.
   - Middleware bloqueia rotas nao publicas quando a licenca nao e valida.

3. Frontend Electron:
   - `cd frontend`.
   - `npm run dev`.
   - Abre Electron e consome a API.
   - Se a API estiver desligada, usa dados locais de demonstracao para manter telas navegaveis.

4. Licenciamento:
   - `GERAR_LICENCA_TESTE.bat` cria licenca trial.
   - `GERAR_LICENCA_COMPLETA.bat` cria licenca full.
   - `license.json` e `.license_secret` sao locais/sensiveis e nao devem ir para o Git.

5. Backup:
   - `python scripts/backup_database.py`.

## Tecnologias

- Python.
- Tkinter.
- FastAPI.
- SQLAlchemy.
- SQLite.
- Pydantic.
- Uvicorn.
- PyInstaller.
- React.
- Electron.
- Vite.
- lucide-react.
- PowerShell e batch scripts Windows.

## Dependencias

Python em `requirements.txt`:

- SQLAlchemy.
- fastapi.
- uvicorn[standard].
- pydantic.
- pyinstaller.
- pytest.

Frontend em `frontend/package.json`:

- react.
- react-dom.
- lucide-react.
- Electron/Vite e ferramentas de build como devDependencies.

## Banco/persistencia

- Desktop: `data/clinica_psicologia.db`, criado automaticamente.
- Backend: `backend/data/clinica_api.db`, criado automaticamente.
- Esses arquivos `.db` sao locais e ignorados no Git.
- Seeds existem em `app/database/seed.py` e `backend/database/seed.py`.

## APIs

Confirmado em docs/API.md e frontend:

- `GET /health`
- `POST /auth/login`
- `GET/POST/PUT /patients`
- `GET/POST/PUT /psychologists`
- `GET/POST/PUT /appointments`
- `GET/POST/PUT /clinical-records`
- `GET/POST /finance/payments`
- `GET/POST /finance/expenses`
- `GET /finance/summary`
- `GET/PUT /settings`
- `GET /license/status`

## Integracoes

- Frontend Electron consome API local.
- Scripts Windows integram instalacao, execucao, build e licenciamento.
- Repositorio GitHub pretendido: `https://github.com/paul-92/clinica-Gabriela.git`.

## Ambiente de desenvolvimento

Python:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Frontend:

```powershell
cd frontend
npm install
```

## Testes

Ha teste em `tests/test_security.py` para hash/verificacao de senha. Comando esperado:

```powershell
python -m pytest
```

## Decisoes arquiteturais

- Aplicacao desktop e API usam bancos SQLite locais separados.
- Licenciamento local e aplicado no desktop e no backend.
- Frontend Electron usa fallback local para navegacao quando API esta offline.
- Estrutura em camadas separa UI, controllers, services, repositories, models e database.

## Trabalho atual

Fonte de verdade corrigida para esta pasta desktop/API/frontend. Git foi inicializado nesta raiz, `origin` foi configurado e o staging inicial foi preparado sem commit e sem push.

## Pendencias

- Aguardar autorizacao explicita do usuario para executar o primeiro commit.
- Aguardar autorizacao separada antes de qualquer push.
- Manter `pytest` disponivel via `requirements.txt` para a suite de testes automatizados.

## Divida tecnica

- Arquivos de licenca e bancos locais existem na pasta de trabalho e precisam permanecer ignorados.
- Ha dependencias instaladas dentro do projeto (`.venv`, `frontend/node_modules`) que nao devem ir para Git.
- Usuarios/senhas de exemplo aparecem em README, seeds e telas de demo.
- Nao ha lint/type checking configurado confirmado.

## Proximos passos

1. Autorizar o primeiro commit.
2. Executar o commit inicial.
3. Autorizar o push para GitHub.
4. Evoluir validacoes automatizadas de lint/type checking.

## Arquivos criticos

- `main.py`
- `app/utils/license.py`
- `app/database/seed.py`
- `backend/main.py`
- `backend/database/seed.py`
- `frontend/src/main.jsx`
- `frontend/package.json`
- `requirements.txt`
- `.gitignore`
- `AGENTS.md`
- `.context/AI_HANDOFF.md`
- `.context/COMMANDS.md`
