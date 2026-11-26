# Carga los datos de prueba en la base (MySQL debe estar corriendo):
#   - seed_demo:   empresa, sucursales, técnicos y tickets de demostración.
#   - preparar_qa: usuarios qa_* de todos los roles y datos falsos para
#                  probar todo. Reinicia los datos de QA cada vez que se corre.
# La clave de los usuarios qa_* se guarda en <Credenciales>\qa.txt (fuera de Git).
#   -SoloQA           no vuelve a correr seed_demo (solo reinicia los datos de QA).
#   -NuevaClave       genera una clave nueva para los usuarios qa_*.
#   -AgregarTrabajos  NO borra nada: suma 8 trabajos nuevos para qa_tecnico
#                     (3 asignados, 2 en ejecución y 3 ofertas).
param([switch]$SoloQA, [switch]$NuevaClave, [switch]$AgregarTrabajos)

. "$PSScriptRoot\_comun.ps1"
Set-Location $Raiz
if (-not (Test-Puerto $Semaxel.PuertoMysql)) { throw 'MySQL no está corriendo. Ejecuta primero scripts\iniciar-mysql.ps1.' }

if ($AgregarTrabajos) {
    Write-Paso 'Agregando trabajos de QA (no se borra nada)'
    & $Python manage.py preparar_qa --agregar-trabajos
    if ($LASTEXITCODE -ne 0) { throw 'Falló preparar_qa --agregar-trabajos.' }
    return
}

Write-Paso 'Aplicando migraciones pendientes'
& $Python manage.py migrate --noinput | Select-Object -Last 1
if ($LASTEXITCODE -ne 0) { throw 'Fallaron las migraciones.' }

if (-not $SoloQA) {
    Write-Paso 'Cargando los datos de demostración (seed_demo)'
    & $Python manage.py seed_demo
    if ($LASTEXITCODE -ne 0) { throw 'Falló seed_demo.' }
}

Write-Paso 'Preparando el entorno de QA (preparar_qa)'
New-Item -ItemType Directory -Force $Semaxel.Credenciales | Out-Null
$argumentos = @('manage.py', 'preparar_qa', '--archivo-clave', (Join-Path $Semaxel.Credenciales 'qa.txt'))
if ($NuevaClave) { $argumentos += '--nueva-clave' }
& $Python @argumentos
if ($LASTEXITCODE -ne 0) { throw 'Falló preparar_qa.' }
