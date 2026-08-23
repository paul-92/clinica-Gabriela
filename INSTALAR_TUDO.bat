@echo off
setlocal
title Instalador - Clinica Psicologia

echo.
echo ================================================
echo  Instalador automatico - Clinica Psicologia
echo ================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_all_windows.ps1"

echo.
if errorlevel 1 (
  echo A instalacao terminou com erro.
  echo Verifique as mensagens acima.
) else (
  echo Instalacao concluida com sucesso.
  echo.
  echo Para iniciar o sistema completo, execute:
  echo   run_all.bat
)
echo.
pause
