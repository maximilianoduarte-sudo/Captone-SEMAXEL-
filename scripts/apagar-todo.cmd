@echo off
rem Doble clic: apaga el emulador, el servidor web y MySQL de SEMAXEL.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0apagar-todo.ps1" %*
pause
