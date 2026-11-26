# Preparación del proyecto la primera vez (o después de cambiar requirements.txt):
#   1. crea el entorno virtual venv\ si no existe
#   2. instala las dependencias de Python
#   3. crea el .env desde .env.example con una SECRET_KEY nueva, si no existe
# No instala MySQL ni las herramientas de Android: ver el README.
. "$PSScriptRoot\_comun.ps1"
Set-Location $Raiz

Write-Paso '1/3 Entorno virtual'
if (Test-Path $Python) { Write-Ok 'Ya existe venv\.' }
else {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) { & py -3 -m venv venv } else { & python -m venv venv }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Python)) { throw 'No se pudo crear venv\. ¿Está instalado Python 3.10 o superior?' }
    Write-Ok 'Creado venv\.'
}

Write-Paso '2/3 Dependencias de Python'
& $Python -m pip install --disable-pip-version-check -q -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Falló pip install.' }
Write-Ok 'Instaladas.'

Write-Paso '3/3 Archivo .env'
$env_ = Join-Path $Raiz '.env'
if (Test-Path $env_) { Write-Ok 'Ya existe .env (no se modifica).' }
else {
    $clave = & $Python -c "import secrets; print(secrets.token_urlsafe(50))"
    $texto = (Get-Content (Join-Path $Raiz '.env.example') -Raw -Encoding UTF8) -replace '(?m)^SECRET_KEY=.*$', "SECRET_KEY=$clave"
    [IO.File]::WriteAllText($env_, $texto, (New-Object Text.UTF8Encoding $false))
    Write-Ok 'Creado .env con una SECRET_KEY nueva.'
    Write-Aviso 'Completa DB_USER y DB_PASSWORD en el .env con los datos de tu MySQL.'
}
