# Apaga de forma ordenada lo que levantó levantar-todo.ps1:
#   1. emulador   2. servidor web   3. MySQL
# Los datos quedan guardados en la base. Las ventanas de cada servicio quedan
# abiertas con su mensaje final y se pueden cerrar.
. "$PSScriptRoot\_comun.ps1"

Write-Paso '1/3 Emulador'
try { Use-EntornoAndroid } catch { }
$serie = Get-Emulador
if ($serie) {
    & adb -s $serie emu kill | Out-Null
    Start-Sleep -Seconds 3
    Write-Ok 'Cerrado.'
} else { Write-Ok 'No estaba corriendo.' }
# A veces quedan procesos del emulador colgados después de cerrarlo.
$carpetas = @($Semaxel.HerramientasAndroid, $env:ANDROID_HOME) | Where-Object { $_ }
Get-Process -Name 'qemu-system-*', 'emulator', 'crashpad_handler' -ErrorAction SilentlyContinue |
    Where-Object { $p = $_.Path; $p -and ($carpetas | Where-Object { $p -like "$_*" }) } |
    Stop-Process -Force -ErrorAction SilentlyContinue

Write-Paso '2/3 Servidor web'
$conexiones = Get-NetTCPConnection -LocalPort $Semaxel.PuertoWeb -State Listen -ErrorAction SilentlyContinue
if ($conexiones) {
    foreach ($id in $conexiones.OwningProcess | Sort-Object -Unique) {
        $proceso = Get-Process -Id $id -ErrorAction SilentlyContinue
        if ($proceso -and $proceso.Name -in 'python', 'waitress-serve') { Stop-Process -Id $id -Force }
        elseif ($proceso) { Write-Aviso "El puerto $($Semaxel.PuertoWeb) lo usa '$($proceso.Name)', que no es de SEMAXEL: no lo toco." }
    }
    Write-Ok 'Detenido.'
} else { Write-Ok 'No estaba corriendo.' }

Write-Paso '3/3 MySQL'
if (-not (Test-Puerto $Semaxel.PuertoMysql)) { Write-Ok 'No estaba corriendo.' }
else {
    $servicio = Get-Service $Semaxel.ServicioMysql -ErrorAction SilentlyContinue
    $mysqladmin = if ($Semaxel.MysqlBin) { Join-Path $Semaxel.MysqlBin 'mysqladmin.exe' }
    $archivoClave = Join-Path $Semaxel.Credenciales 'mysql-root.txt'
    if ($servicio -and $servicio.Status -eq 'Running') {
        Stop-Service $Semaxel.ServicioMysql   # puede pedir PowerShell como administrador
        Write-Ok 'Servicio detenido.'
    } elseif ($mysqladmin -and (Test-Path $mysqladmin) -and (Test-Path $archivoClave)) {
        # La clave de root es la última línea del archivo ("clave=..."); se pasa
        # por variable de entorno para que no aparezca en la lista de procesos.
        $linea = (Get-Content $archivoClave | Where-Object { $_.Trim() } | Select-Object -Last 1).Trim()
        if ($linea -match '[:=]\s*(\S+)$') { $linea = $Matches[1] }
        $env:MYSQL_PWD = $linea
        try { & $mysqladmin -u root -h 127.0.0.1 shutdown } finally { Remove-Item Env:MYSQL_PWD }
        if ($LASTEXITCODE -ne 0) { throw 'mysqladmin no pudo apagar MySQL.' }
        Write-Ok 'Apagado de forma ordenada.'
    } else {
        Write-Aviso 'No sé cómo apagar este MySQL: ciérralo desde su ventana con Ctrl+C.'
    }
}

Start-Sleep -Seconds 3
& (Join-Path $PSScriptRoot 'estado.ps1')
