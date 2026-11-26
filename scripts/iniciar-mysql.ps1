# Arranca MySQL. Con el MySQL portable queda en primer plano en esta ventana
# (Ctrl+C o apagar-todo.ps1 lo detienen). Con el servicio de Windows, lo inicia.
. "$PSScriptRoot\_comun.ps1"
$Host.UI.RawUI.WindowTitle = 'SEMAXEL - MySQL'
Disable-ModoSeleccion

if (Test-Puerto $Semaxel.PuertoMysql) {
    Write-Ok "MySQL ya está corriendo (puerto $($Semaxel.PuertoMysql))."
    return
}

$mysqld = if ($Semaxel.MysqlBin) { Join-Path $Semaxel.MysqlBin 'mysqld.exe' }
$ini = Join-Path $Semaxel.HerramientasServidor 'mysql.ini'

if ($mysqld -and (Test-Path $mysqld) -and (Test-Path $ini)) {
    Write-Paso "Arrancando MySQL portable ($mysqld)"
    Write-Aviso 'Deja esta ventana abierta mientras uses el sistema.'
    & $mysqld --defaults-file="$ini" --console
    return
}

$servicio = Get-Service $Semaxel.ServicioMysql -ErrorAction SilentlyContinue
if ($servicio) {
    Write-Paso "Iniciando el servicio de Windows $($Semaxel.ServicioMysql)"
    Start-Service $Semaxel.ServicioMysql   # puede pedir PowerShell como administrador
    Wait-Puerto $Semaxel.PuertoMysql 'MySQL' 30
    Write-Ok 'MySQL listo.'
    return
}

throw "No encontré MySQL: ni $ini con su carpeta mysql-*, ni el servicio $($Semaxel.ServicioMysql). Revisa scripts\config.local.ps1."
