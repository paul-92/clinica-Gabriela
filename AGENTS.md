# AGENTS.md

## Objetivo do projeto

Sistema desktop e web/API para clinica de psicologia. O projeto combina app desktop Python/Tkinter, backend FastAPI, banco SQLite/SQLAlchemy e frontend Electron + React para fluxos de recepcao, pacientes, psicologos, agenda, prontuario, financeiro, relatorios, backup e licenciamento local.

## Arquitetura

- `app/`: aplicacao desktop Tkinter em camadas.
- `backend/`: API FastAPI em camadas.
- `frontend/`: frontend Electron + React + Vite.
- `scripts/`: automacoes PowerShell/Python para instalacao, execucao, build, licenca e backup.
- `docs/`: documentacao funcional, tecnica, visual e de licenciamento.
- `tests/`: testes Python existentes.
- Persistencia local em SQLite, criada automaticamente na primeira execucao.

As camadas confirmadas pela documentacao sao:

- `views`: telas Tkinter.
- `controllers`: entrada das acoes de interface.
- `services`: regras de negocio.
- `repositories`: acesso ao banco.
- `models`: entidades SQLAlchemy.
- `database`: sessao, criacao de tabelas, migracoes leves e seed.

## Estrutura principal de diretorios

- `main.py`: ponto de entrada do app desktop.
- `app/`: dominio desktop, views, controllers, services, repositories, models, database, reports e utils.
- `backend/main.py`: ponto de entrada FastAPI.
- `backend/api/routes/`: rotas HTTP.
- `backend/models/`, `backend/schemas/`, `backend/repositories/`, `backend/services/`, `backend/database/`: camadas da API.
- `frontend/src/`: interface React.
- `frontend/electron/`: processo principal e preload do Electron.
- `docs/`: arquitetura, API, frontend, Windows, licenciamento, apostila e imagens.
- `scripts/`: comandos auxiliares.
- `tests/test_security.py`: teste de hash/verificacao de senha.

## Convencoes de codigo

- Python em camadas, evitando acesso direto ao banco pelas telas.
- Telas chamam controllers; controllers coordenam services e repositories.
- Services concentram regras de negocio.
- Repositories concentram operacoes de banco.
- Models SQLAlchemy representam entidades persistidas.
- Schemas Pydantic representam contratos da API.
- Frontend React consome a API em `http://127.0.0.1:8000` e possui fallback local quando a API esta desligada.
- Manter textos de interface e documentacao em portugues.

## Regras arquiteturais

- Nao misturar regra de negocio diretamente nas views quando houver controller/service adequado.
- Nao acessar SQLite diretamente a partir da UI.
- Manter os modelos, schemas, repositories e services alinhados quando alterar entidades.
- Manter o frontend sincronizado com endpoints e contratos da API.
- Nao versionar bancos locais, licencas geradas, segredos, caches, ambientes virtuais ou dependencias instaladas.
- Nao remover o mecanismo de licenciamento sem decisao explicita do usuario.
- Nao usar dados reais de pacientes em seeds, docs ou testes.

## Comandos de instalacao

Python:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Windows:

```bat
install_windows.bat
```

Instalacao completa:

```bat
INSTALAR_TUDO.bat
```

Frontend:

```powershell
cd frontend
npm install
```

## Execucao

Desktop:

```powershell
python main.py
```

Windows:

```bat
run_desktop.bat
```

API:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend Electron:

```powershell
cd frontend
npm run dev
```

API e Electron juntos:

```bat
run_all.bat
```

## Testes

Teste Python confirmado:

```powershell
python -m pytest
```

## Lint

Nao ha comando de lint configurado confirmado.

## Build

Build Windows:

```bat
build_windows.bat
```

Frontend:

```powershell
cd frontend
npm run build
```

Pacote Electron:

```powershell
cd frontend
npm run dist
```

## Arquivos sensiveis

Nao versionar:

- `.env` e variantes.
- `.license_secret`.
- `license.json`.
- chaves privadas, certificados, tokens e credenciais.
- `data/*.db` e `backend/data/*.db`.
- `.venv/`.
- `frontend/node_modules/`.
- caches e arquivos `*.pyc`.
- builds (`dist/`, `build/`, `release/`, `frontend/dist/`, `frontend/release/`).

## Regras que futuros agentes devem respeitar

- Ler `AGENTS.md`, `.context/PROJECT_CONTEXT.md` e `.context/AI_HANDOFF.md` antes de alterar o projeto.
- Rodar `git status --short --branch` antes de editar.
- Preservar alteracoes do usuario.
- Nao fazer commit nem push sem autorizacao explicita.
- Antes de qualquer staging/commit, revisar `.gitignore`, varrer segredos e conferir `git diff --cached --name-status`.
- Atualizar `.context/COMMANDS.md` quando comandos reais mudarem.
- Atualizar docs quando arquitetura, rotas ou fluxos mudarem.

## Criterios minimos para considerar uma alteracao concluida

- Mudanca implementada na camada correta.
- Testes seguros existentes executados ou falha/impedimento registrado.
- Frontend/API/docs atualizados quando necessario.
- Nenhum segredo, banco local, cache ou dependencia instalada no staging.
- `git status` revisado.
