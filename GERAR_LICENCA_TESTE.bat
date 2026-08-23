@echo off
setlocal
set /p CUSTOMER=Nome do cliente:
set /p DAYS=Dias de teste [14]:
if "%DAYS%"=="" set DAYS=14
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\generate_license.ps1" -Customer "%CUSTOMER%" -Type trial -Days %DAYS%
pause
