# Levanta todo lo necesario para probar SEMAXEL, cada servicio en su ventana:
#   1. MySQL   2. servidor web y API   3. emulador de Android
# Lo que ya está corriendo se deja como está.
#   -SinEmulador  solo MySQL y el servidor (para probar la web).
#   -InstalarApp  además compila e instala la app en el emulador.
#   -Desarrollo   servidor con runserver (se reinicia al cambiar el código).
param([switch]$SinEmulador, [switch]$InstalarApp, [switch]$Desarrollo)

. "$PSScriptRoot\_comun.ps1"

Write-Paso '1/3 MySQL'
if (Test-Puerto $Semaxel.PuertoMysql) { Write-Ok 'Ya estaba corriendo.' }
else {
    Start-Ventana 'iniciar-mysql.ps1'
    Wait-Puerto $Semaxel.PuertoMysql 'MySQL' 60
    Write-Ok 'Listo.'
}

Write-Paso '2/3 Servidor web y API'
if (Test-Puerto $Semaxel.PuertoWeb) { Write-Ok 'Ya estaba corriendo.' }
else {
    $argumentos = @()
    if ($Desarrollo) { $argumentos += '-Desarrollo' }
    Start-Ventana 'iniciar-servidor.ps1' $argumentos
    Wait-Puerto $Semaxel.PuertoWeb 'El servidor web' 180
    Write-Ok 'Listo.'
}

if ($SinEmulador) {
    Write-Paso '3/3 Emulador: omitido (-SinEmulador)'
} else {
    Write-Paso '3/3 Emulador de Android'
    Use-EntornoAndroid
    if (Get-Emulador) { Write-Ok 'Ya estaba corriendo.' }
    else {
        Start-Ventana 'iniciar-emulador.ps1'
        Write-Aviso 'Esperando que Android termine de arrancar (1 a 3 minutos)...'
        Start-Sleep -Seconds 5
        $null = Wait-ArranqueEmulador
        Write-Ok 'Listo.'
    }
    if ($InstalarApp) { & (Join-Path $PSScriptRoot 'instalar-app.ps1') }
}

& (Join-Path $PSScriptRoot 'estado.ps1')
