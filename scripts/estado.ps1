# Muestra qué servicios de SEMAXEL están corriendo y dónde entrar.
. "$PSScriptRoot\_comun.ps1"

function Show-Estado([string]$nombre, [bool]$corriendo, [string]$detalle) {
    $texto = if ($corriendo) { 'corriendo' } else { 'apagado' }
    $color = if ($corriendo) { 'Green' } else { 'DarkGray' }
    Write-Host ('    {0,-14} ' -f $nombre) -NoNewline
    Write-Host ('{0,-10}' -f $texto) -ForegroundColor $color -NoNewline
    Write-Host " $detalle"
}

$emulador = $null
try { Use-EntornoAndroid; $emulador = Get-Emulador } catch { }
$web = Test-Puerto $Semaxel.PuertoWeb

Write-Paso 'Estado de SEMAXEL'
Show-Estado 'MySQL' (Test-Puerto $Semaxel.PuertoMysql) "puerto $($Semaxel.PuertoMysql)"
Show-Estado 'Servidor web' $web "http://localhost:$($Semaxel.PuertoWeb)/"
Show-Estado 'Emulador' ([bool]$emulador) $(if ($emulador) { $emulador } else { '' })

if ($web) {
    Write-Host ''
    Write-Host "    Web:            http://localhost:$($Semaxel.PuertoWeb)/"
    Write-Host "    API (Swagger):  http://localhost:$($Semaxel.PuertoWeb)/api/v1/docs/"
    foreach ($ip in Get-IpLocal) { Write-Host "    Desde la red:   http://${ip}:$($Semaxel.PuertoWeb)/" }
    $claveQa = Join-Path $Semaxel.Credenciales 'qa.txt'
    if (Test-Path $claveQa) { Write-Host "    Clave QA:       $claveQa" }
}
