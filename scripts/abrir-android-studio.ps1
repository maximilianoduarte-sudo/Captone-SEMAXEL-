# Abre Android Studio con el proyecto de la app (app-movil), usando el JDK,
# el SDK, Gradle y el emulador de HerramientasAndroid.
# Abrirlo con este script (y no desde el menú Inicio) hace que Studio vea el
# emulador de SEMAXEL y guarde sus cachés en D: en vez de C:.
. "$PSScriptRoot\_comun.ps1"
Use-EntornoAndroid

$studio = Join-Path $Semaxel.AndroidStudio 'bin\studio64.exe'
if (-not (Test-Path $studio)) {
    throw "No encuentro Android Studio en $($Semaxel.AndroidStudio). Revisa AndroidStudio en scripts\config.local.ps1."
}

# Configuración, cachés, complementos y registros de Studio junto a las
# herramientas (por defecto Studio los deja en C:\Users\...\AppData).
$datos = Join-Path $Semaxel.HerramientasAndroid 'android-studio-datos'
$propiedades = Join-Path $datos 'idea.properties'
if (-not (Test-Path $propiedades)) {
    New-Item -ItemType Directory -Force $datos | Out-Null
    $d = $datos -replace '\\', '/'
    $texto = @(
        '# Generado por scripts\abrir-android-studio.ps1 (SEMAXEL).'
        "idea.config.path=$d/config"
        "idea.system.path=$d/system"
        "idea.plugins.path=$d/config/plugins"
        "idea.log.path=$d/system/log"
        '# Sin asistente inicial: el SDK ya está instalado.'
        'disable.android.first.run=true'
    ) -join "`r`n"
    [IO.File]::WriteAllText($propiedades, $texto + "`r`n", (New-Object Text.UTF8Encoding $false))
}
$env:STUDIO_PROPERTIES = $propiedades

# JDK con que Studio ejecuta Gradle ("GRADLE_LOCAL_JAVA_HOME"): el mismo de la
# consola. Sin esto, Studio descarga otro JDK a C:\Users\...\.jdks.
if ($env:JAVA_HOME) {
    $gradleLocal = Join-Path $Raiz 'app-movil\.gradle'
    New-Item -ItemType Directory -Force $gradleLocal | Out-Null
    $java = $env:JAVA_HOME -replace '\\', '\\' -replace ':', '\:'
    [IO.File]::WriteAllText((Join-Path $gradleLocal 'config.properties'), "java.home=$java`r`n", (New-Object Text.UTF8Encoding $false))
}

Write-Paso 'Abriendo Android Studio con app-movil'
Start-Process $studio -ArgumentList ('"' + (Join-Path $Raiz 'app-movil') + '"')
Write-Ok 'La primera vez tarda en indexar y sincronizar Gradle (barra inferior).'
