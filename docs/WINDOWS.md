# Scripts Windows

Este projeto inclui scripts para instalacao, execucao e build no Windows.

## Instalar tudo

Modo mais simples:

```bat
INSTALAR_TUDO.bat
```

Esse arquivo verifica Python, Node.js, dependencias Python, dependencias Electron e inicializa os bancos SQLite.

Modo tecnico:

```bat
install_windows.bat
```

Ou:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_windows.ps1
```

O script cria `.venv`, instala dependencias Python e, se `npm` estiver disponivel, instala dependencias do frontend Electron.

## Executar desktop Python

```bat
run_desktop.bat
```

## Executar API FastAPI

```bat
run_api.bat
```

A API fica em `http://127.0.0.1:8000`.

## Executar frontend Electron

```bat
run_frontend.bat
```

## Executar API e Electron juntos

```bat
run_all.bat
```

## Gerar builds Windows

```bat
build_windows.bat
```

Saidas esperadas:

- Desktop Python: `dist\windows\desktop`
- Electron: `frontend\release`

## Requisitos

- Python 3.11 ou superior.
- Node.js LTS para o frontend Electron.
- Windows PowerShell.
