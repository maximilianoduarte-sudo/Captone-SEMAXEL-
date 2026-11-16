# Configuración y funciones que comparten los scripts de SEMAXEL.
# No se ejecuta solo: lo cargan los demás scripts.
#
# Las rutas por defecto son las del equipo de pruebas (todo en D:).
# En otro equipo: copia config.local.ejemplo.ps1 como config.local.ps1
# (no se sube a Git) y cambia ahí lo que corresponda.

$ErrorActionPreference = 'Stop'

$Raiz = Split-Path -Parent $PSScriptRoot          # carpeta del proyecto
$Semaxel = @{
    HerramientasServidor = 'D:\herramientas-servidor'   # MySQL portable, claves, temporales
    HerramientasAndroid  = 'D:\herramientas-android'    # JDK, SDK, Gradle y emulador
    Avd                  = 'SEMAXEL_Pixel7_API35'       # dispositivo virtual del emulador
    ServicioMysql        = 'MySQL80'                    # si MySQL está instalado como servicio de Windows
    PuertoWeb            = 8000
    PuertoMysql          = 3306
    MysqlBin             = $null                        # se calcula abajo si queda vacío
    Credenciales         = $null                        # carpeta de claves (fuera del repo)
}

$configLocal = Join-Path $PSScriptRoot 'config.local.ps1'
if (Test-Path $configLocal) { . $configLocal }

if (-not $Semaxel.MysqlBin) {
    $mysqlDir = Get-ChildItem (Join-Path $Semaxel.HerramientasServidor 'mysql-*') -Directory -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($mysqlDir) { $Semaxel.MysqlBin = Join-Path $mysqlDir.FullName 'bin' }
}
if (-not $Semaxel.Credenciales) { $Semaxel.Credenciales = Join-Path $Semaxel.HerramientasServidor 'credenciales' }

$Python = Join-Path $Raiz 'venv\Scripts\python.exe'
$PaqueteApp = 'cl.semaxel.tecnico'

function Write-Paso([string]$texto) { Write-Host "==> $texto" -ForegroundColor Cyan }
function Write-Ok([string]$texto) { Write-Host "    $texto" -ForegroundColor Green }
function Write-Aviso([string]$texto) { Write-Host "    $texto" -ForegroundColor Yellow }

function Test-Puerto([int]$puerto) {
    [bool](Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue)
}

function Wait-Puerto([int]$puerto, [string]$nombre, [int]$segundos = 90) {
    $limite = (Get-Date).AddSeconds($segundos)
    while (-not (Test-Puerto $puerto)) {
        if ((Get-Date) -gt $limite) { throw "$nombre no respondió en el puerto $puerto después de $segundos s. Revisa su ventana." }
        Start-Sleep -Seconds 1
    }
}

# Carga JAVA_HOME, ANDROID_HOME y el PATH de las herramientas de Android.
function Use-EntornoAndroid {
    $entorno = Join-Path $Semaxel.HerramientasAndroid 'entorno.ps1'
    if (Test-Path $entorno) { . $entorno; return }
    if (-not $env:ANDROID_HOME) {
        throw "No encuentro $entorno ni la variable ANDROID_HOME. Revisa HerramientasAndroid en scripts\config.local.ps1."
    }
    $env:Path = "$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\emulator;$env:Path"
}

# Número de serie del emulador conectado (por ejemplo emulator-5554), o $null.
function Get-Emulador {
    if (-not (Get-Command adb -ErrorAction SilentlyContinue)) { return $null }
    $linea = & adb devices | Select-String '^(emulator-\d+)\s+device' | Select-Object -First 1
    if ($linea) { return $linea.Matches[0].Groups[1].Value }
    return $null
}

function Wait-ArranqueEmulador([int]$segundos = 240) {
    $limite = (Get-Date).AddSeconds($segundos)
    while ($true) {
        $serie = Get-Emulador
        $listo = $false
        # Mientras arranca, adb puede responder "device offline" por stderr.
        if ($serie) { try { $listo = (& adb -s $serie shell getprop sys.boot_completed 2>$null) -match '1' } catch { } }
        if ($listo) { return $serie }
        if ((Get-Date) -gt $limite) { throw "El emulador no terminó de arrancar en $segundos s. Revisa su ventana." }
        Start-Sleep -Seconds 3
    }
}

# Abre un script de esta carpeta en una ventana de PowerShell nueva.
function Start-Ventana([string]$script, [string[]]$argumentos = @()) {
    $ruta = '"' + (Join-Path $PSScriptRoot $script) + '"'   # comillas por si la ruta tiene espacios
    $lista = @('-NoProfile', '-NoExit', '-ExecutionPolicy', 'Bypass', '-File', $ruta) + $argumentos
    Start-Process powershell.exe -ArgumentList $lista -WorkingDirectory $Raiz | Out-Null
}

# IP del equipo en la red local (para entrar desde otro PC o un celular).
# Solo las tarjetas con puerta de enlace: así no aparecen las redes virtuales.
function Get-IpLocal {
    Get-NetIPConfiguration -ErrorAction SilentlyContinue |
        Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } |
        ForEach-Object { $_.IPv4Address.IPAddress }
}
