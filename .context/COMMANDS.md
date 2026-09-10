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
python -m backend.supervisor run
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
python -m backend.supervisor run
```

O supervisor aguarda `GET /health` com timeout antes de confirmar a inicializacao e
encerra somente o processo backend que ele proprio criou. Para apenas aguardar uma
API iniciada por outro fluxo:

```powershell
python -m backend.supervisor wait
```

```powershell
cd frontend
npm run dev
```

## Testes

Backend/Python:

```powershell
python -m pytest
```

Frontend:

```powershell
cd frontend
npm test
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

Inventario read-only dos bancos desktop e backend:

```powershell
python scripts/sqlite_inventory.py
```

Analise read-only e privacy-safe de identidade entre os bancos:

```powershell
python scripts/sqlite_identity_analysis.py
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
