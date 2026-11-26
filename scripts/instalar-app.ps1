# Compila la app de depuración y la instala y abre en el emulador (o en el
# celular conectado por USB si no hay emulador).
#   -SinCompilar  instala el último APK compilado sin volver a compilar.
param([switch]$SinCompilar)

. "$PSScriptRoot\_comun.ps1"
Use-EntornoAndroid
$carpetaApp = Join-Path $Raiz 'app-movil'
$apk = Join-Path $carpetaApp 'app\build\outputs\apk\debug\app-debug.apk'

if (-not $SinCompilar) {
    Write-Paso 'Compilando la app (la primera vez tarda unos minutos)'
    Push-Location $carpetaApp
    try {
        & .\gradlew.bat assembleDebug --quiet
        if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación de la app.' }
    } finally { Pop-Location }
}
if (-not (Test-Path $apk)) { throw "No existe $apk. Ejecuta el script sin -SinCompilar." }

Write-Paso 'Esperando al dispositivo'
$serie = Get-Emulador
if ($serie) { $serie = Wait-ArranqueEmulador }
else {
    $usb = & adb devices | Select-String '^(\S+)\s+device$' | Select-Object -First 1
    if (-not $usb) { throw 'No hay emulador ni celular conectado. Ejecuta scripts\iniciar-emulador.ps1.' }
    $serie = $usb.Matches[0].Groups[1].Value
}

Write-Paso "Instalando en $serie"
& adb -s $serie install -r $apk
if ($LASTEXITCODE -ne 0) { throw 'Falló la instalación.' }
& adb -s $serie shell "monkey -p $PaqueteApp -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1"
Write-Ok 'App instalada y abierta.'
