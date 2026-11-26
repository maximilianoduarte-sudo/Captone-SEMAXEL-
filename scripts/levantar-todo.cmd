@echo off
rem Doble clic: levanta MySQL, el servidor web y el emulador de SEMAXEL.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0levantar-todo.ps1" %*
pause
