# Commands

## Ambiente de desenvolvimento isolado (Windows)

Ver `DEVELOPMENT_BOOTSTRAP.md`. Escolha caminho absoluto novo fora do
repositorio e do runtime operacional:

```powershell
& .\scripts\bootstrap-dev.ps1 -DevRoot 'C:\dev\clinica-gabriela-sintetico' -DryRun
& .\scripts\bootstrap-dev.ps1 -DevRoot 'C:\dev\clinica-gabriela-sintetico'
& .\scripts\validate-dev.ps1 -DevRoot 'C:\dev\clinica-gabriela-sintetico'
```

O script copia apenas codigo e contratos permitidos para `DevRoot\workspace`, cria
venv/banco/temp na raiz DEV e executa npm/build/testes na copia externa.
`requirements-dev.lock` fixa diretas e transitivas na baseline Windows/Python 3.12.10.

Os comandos de instalacao gerais abaixo sao legados e nao garantem isolamento
do runtime operacional; para novo desenvolvimento, use o fluxo acima.

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

Migracoes leves continuam chamadas por `main.py` e `backend/main.py`.

Dry-run/candidato explícito da SPEC-003 (nunca troca o pointer operacional):

```powershell
python scripts/spec003_candidate_migration.py --source <generation-2.db> --output-dir <diretorio-novo>
```

Migração financeira SPEC-005 somente sobre snapshot/cópia isolada (nunca aceita
caminho operacional nem promove o candidato):

```powershell
python scripts/spec005_candidate_migration.py --source <snapshot-isolado.db> --output <candidato-novo.db> --identity-manifest <manifesto-D005-10.json>
```

## Scripts uteis

Identidade D005-11 (somente build/verify/preflight; não executa E011):

```powershell
python -B -m scripts.spec005_d00511_identity build --code-root . --manifest <novo-manifest.json>
python -B -m scripts.spec005_d00511_identity verify --code-root . --manifest <manifest.json> --manifest-sha256 <sha256-aprovado>
python -B -m scripts.spec005_d00511_historical_probe
```

O probe histórico é somente leitura para a Generation 8, mas cria uma cópia
temporária do código. Falha fechada se os bytes históricos não puderem ser
reconstruídos do Git e conferidos com o runtime manifest.

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

Auditoria read-only de integridade referencial dos bancos:

```powershell
python scripts/sqlite_integrity_audit.py
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

SPEC-005 D005-12: verificar o manifest migrador sucessor (somente leitura):

```powershell
.venv\Scripts\python.exe -B -m scripts.spec005_d00511_identity verify --code-root . --manifest docs/audit/spec005-20260924-d00512-migration-execution-manifest-v5.json --manifest-sha256 a5e9f0bf65e32845acb71fff459d3a88bfbab0adc9f3f023bd747ccf4bf38893
```

O preflight D005-12 usa `--source-authority persisted`, pointer, diretório do
runtime manifest, banco/snapshot e checkpoint externo com SHA fornecido
separadamente. Ele lê a fonte e não cria candidato nem autoriza E011.

SPEC-005 E011: provisionamento exclusivo da revisão da identidade, somente
pelo revisor independente após aprovação real. O executor de implementação
não deve executar este comando para a autoridade operacional:

```powershell
.venv\Scripts\python.exe -m scripts.spec005_provision_e011_review --review <parecer-aprovado.json>
```

O comando criou `docs/audit/spec005-e011-review-<SHA256>.json` e o registro
canônico `docs/audit/spec005-e011-independent-review-authority.json` na E011.
O CLI E011 lê esse registro por localização fixa; não aceita sua localização
por argumento. Estes comandos de execução histórica não devem ser repetidos.

SPEC-005 promotion (executed once on 2026-09-24; do not rerun against Generation 9):

```powershell
.venv\Scripts\python.exe -m scripts.spec005_operational_promotion preflight
.venv\Scripts\python.exe -m scripts.spec005_operational_promotion execute
```

The reconstructed orchestrator and preflight Evidence are in `docs/audit/`.
Execution Evidence is in `%LOCALAPPDATA%\ClinicaGabriela\runtime\evidence\spec005-promotion-20260924T205031Z.json`.
Current authoritative Generation is 9/canonical. Further promotion requires a new
contractual gate; the commands above are bound to Generation 8 and fail closed.
