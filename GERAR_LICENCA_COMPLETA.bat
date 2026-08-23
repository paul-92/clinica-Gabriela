@echo off
setlocal
set /p CUSTOMER=Nome do cliente:
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\generate_license.ps1" -Customer "%CUSTOMER%" -Type full -Days 0
pause
