# Ejemplo de configuración local de los scripts de SEMAXEL.
# Copia este archivo como config.local.ps1 (no se sube a Git) y deja solo
# las líneas que cambian en tu equipo.

# MySQL portable (carpeta con mysql-*\bin, mysql.ini y mysql-datos).
# Si no existe, los scripts usan el servicio de Windows ServicioMysql.
$Semaxel.HerramientasServidor = 'C:\semaxel\herramientas-servidor'

# Herramientas de Android (con entorno.ps1). Si no existe, se usa ANDROID_HOME.
$Semaxel.HerramientasAndroid = 'C:\semaxel\herramientas-android'

# Nombre del servicio de MySQL instalado con el instalador oficial.
$Semaxel.ServicioMysql = 'MySQL80'

# Dispositivo virtual del emulador (ver: emulator -list-avds).
$Semaxel.Avd = 'Pixel_7_API_35'

# Carpeta donde se guardan las claves generadas (fuera del repo).
$Semaxel.Credenciales = "$env:USERPROFILE\semaxel-credenciales"
