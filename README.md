# Sistema Desktop para Clinica de Psicologia

Estrutura inicial completa de um sistema para clinica de psicologia, usando Python, Tkinter, FastAPI, SQLite e SQLAlchemy.

## Modulos incluidos

- Login com senha criptografada.
- Dashboard.
- Cadastro e listagem de pacientes.
- Cadastro estrutural de psicologos.
- Agenda de atendimentos.
- Prontuario clinico estruturado.
- Financeiro.
- Relatorios.
- Backup local.
- Configuracoes.
- Backend FastAPI com models, schemas, repositories e services.
- Frontend Electron + React com telas principais.

## Instalar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Windows, tambem pode usar:

```bat
install_windows.bat
```

Para uma instalacao automatica completa, com verificacao de Python, Node.js, dependencias e banco inicial:

```bat
INSTALAR_TUDO.bat
```

## Executar

```bash
python main.py
```

No Windows:

```bat
run_desktop.bat
```

## Executar API

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

A documentacao interativa fica em `http://127.0.0.1:8000/docs`.

## Executar frontend Electron

```bash
cd frontend
npm install
npm run dev
```

O frontend consome a API em `http://127.0.0.1:8000`.

No Windows, voce tambem pode usar:

```bat
run_api.bat
run_frontend.bat
```

Para iniciar API e Electron juntos:

```bat
run_all.bat
```

Para gerar builds Windows:

```bat
build_windows.bat
```

## Usuarios de exemplo

- `admin` / `admin123`
- `marilia` / `marilia123`
- `recepcao` / `recepcao123`

## Banco de dados

O banco SQLite e criado automaticamente em `data/clinica_psicologia.db` na primeira execucao.

O backend cria seu banco em `backend/data/clinica_api.db`.

## Backup

```bash
python scripts/backup_database.py
```

## Aprender e manter o sistema

Leia a apostila didatica em:

```text
docs/APOSTILA_MANUTENCAO.md
```

## Licencas e testes gratuitos

Para gerar licenca de teste:

```bat
GERAR_LICENCA_TESTE.bat
```

Para liberar cliente pagante:

```bat
GERAR_LICENCA_COMPLETA.bat
```

Detalhes em:

```text
docs/LICENCIAMENTO.md
```

## Previa comercial

Resumo dos modulos:

```text
docs/PREVIA_MODULOS.md
```

Imagens para apresentacao:

```text
docs/PREVIA_VISUAL.md
```

Imagens com o layout da Marilia Gabriela Gaspar:

```text
docs/PREVIA_VISUAL_MARILIA.md
```

## Tema visual do cliente

Identidade aplicada com base na referencia do Instagram:

```text
docs/TEMA_CLIENTE_MARILIA.md
```
