# Arranca la web y la API de SEMAXEL en el puerto 8000 (todas las interfaces).
# Antes aplica las migraciones pendientes y reúne los archivos estáticos.
#   -Desarrollo  usa "manage.py runserver" (se reinicia solo al cambiar el código)
#                en vez de Waitress.
param([switch]$Desarrollo)

. "$PSScriptRoot\_comun.ps1"
$Host.UI.RawUI.WindowTitle = 'SEMAXEL - Servidor web'
Set-Location $Raiz

if (-not (Test-Path $Python)) { throw 'Falta el entorno virtual. Ejecuta primero scripts\instalar.ps1.' }
if (-not (Test-Path (Join-Path $Raiz '.env'))) { throw 'Falta el archivo .env. Ejecuta primero scripts\instalar.ps1.' }
if (-not (Test-Puerto $Semaxel.PuertoMysql)) { throw 'MySQL no está corriendo. Ejecuta primero scripts\iniciar-mysql.ps1.' }
if (Test-Puerto $Semaxel.PuertoWeb) {
    Write-Ok "Ya hay un servidor en el puerto $($Semaxel.PuertoWeb)."
    return
}

# El disco C: del equipo de pruebas está casi lleno: los temporales van a D:.
$tmp = Join-Path $Semaxel.HerramientasServidor 'tmp'
if (Test-Path $tmp) { $env:TEMP = $tmp; $env:TMP = $tmp }

Write-Paso 'Aplicando migraciones pendientes'
& $Python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { throw 'Fallaron las migraciones (revisa la conexión a MySQL en el .env).' }

Write-Paso 'Reuniendo archivos estáticos'
& $Python manage.py collectstatic --noinput | Select-Object -Last 1

$puerto = $Semaxel.PuertoWeb
Write-Paso "Servidor en http://localhost:$puerto/  (deja esta ventana abierta)"
foreach ($ip in Get-IpLocal) { Write-Ok "Desde la red: http://${ip}:$puerto/" }
Write-Ok "Desde el emulador: http://10.0.2.2:$puerto/"

if ($Desarrollo) {
    & $Python manage.py runserver "0.0.0.0:$puerto"
} else {
    & (Join-Path $Raiz 'venv\Scripts\waitress-serve.exe') "--listen=0.0.0.0:$puerto" --threads=8 config.wsgi:application
}
