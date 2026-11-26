@echo off
rem Doble clic: abre Android Studio con la app de SEMAXEL.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0abrir-android-studio.ps1"
if errorlevel 1 pause
