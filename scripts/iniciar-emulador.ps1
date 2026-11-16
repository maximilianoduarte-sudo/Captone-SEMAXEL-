# Arranca el emulador de Android con el dispositivo virtual de SEMAXEL.
# Queda en primer plano en esta ventana. La app de depuración se conecta a
# http://10.0.2.2:8000/, que es el propio computador visto desde el emulador.
. "$PSScriptRoot\_comun.ps1"
$Host.UI.RawUI.WindowTitle = 'SEMAXEL - Emulador'
Use-EntornoAndroid

$serie = Get-Emulador
if ($serie) {
    Write-Ok "El emulador ya está corriendo ($serie)."
    return
}

$avds = & emulator -list-avds
if ($avds -notcontains $Semaxel.Avd) {
    throw "No existe el dispositivo virtual '$($Semaxel.Avd)'. Disponibles: $($avds -join ', '). Cambia Avd en scripts\config.local.ps1."
}

Write-Paso "Arrancando el emulador $($Semaxel.Avd) (deja esta ventana abierta)"
& emulator -avd $Semaxel.Avd -no-snapshot-save -no-boot-anim -accel on
