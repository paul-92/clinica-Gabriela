# Commands

## Instalacao

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

## Ambiente virtual

Criar:

```powershell
python -m venv .venv
```

Ativar no Windows:

```powershell
.venv\Scripts\activate
```

## Execucao

Desktop:

```powershell
python main.py
```

Desktop no Windows:

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

API e frontend juntos:

```bat
run_all.bat
```

Scripts individuais:

```bat
run_api.bat
run_frontend.bat
```

## Desenvolvimento

Rodar API e frontend em terminais separados:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

## Testes

```powershell
python -m pytest
```

## Lint

Nenhum comando de lint confirmado no projeto.

## Type checking

Nenhum comando de type checking confirmado no projeto.

## Build

Build Windows:

```bat
build_windows.bat
```

Build frontend:

```powershell
cd frontend
npm run build
```

Distribuicao Electron:

```powershell
cd frontend
npm run dist
```

## Migrations

Nao ha comando CLI dedicado confirmado. Migracoes leves sao chamadas por `main.py` e `backend/main.py`.

## Scripts uteis

Backup:

```powershell
python scripts/backup_database.py
```

Licenca de teste:

```bat
GERAR_LICENCA_TESTE.bat
```

Licenca completa:

```bat
GERAR_LICENCA_COMPLETA.bat
```

Scripts PowerShell equivalentes estao em `scripts/`.
