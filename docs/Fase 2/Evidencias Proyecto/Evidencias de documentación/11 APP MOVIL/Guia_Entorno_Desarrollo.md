# Guía del entorno de desarrollo: servidor y app móvil

Cómo está preparado el equipo Windows donde se desarrolla la app móvil del
técnico y cómo reproducirlo en otro equipo. Complementa la
[Bitácora](Bitacora_App_Movil.md) (qué se hizo y por qué) y la
[Guía de la API](Guia_API_App_Movil.md) (cómo se usa la API).

Fecha de la última actualización: 14-11-2026.

---

## 1. Resumen del equipo

| Elemento | Estado en el equipo Windows |
|---|---|
| Sistema | Windows 10 |
| Disco C: | Tenía **≈0,2 GB libres** al instalar las herramientas (14-11-2026); después quedó en ≈4 GB. Por eso todas las herramientas nuevas, cachés y temporales se instalaron en D:. |
| Repositorio | `D:\proyecto_semaxel`, rama `feature/app-movil` |
| Python | 3.13, con entorno virtual en `D:\proyecto_semaxel\venv` (no se sube a Git) |
| MySQL | **No instalado todavía** (ver sección 2.3) |
| Herramientas Android | `D:\herramientas-android\` (JDK 21, Gradle 8.11.1, SDK de Android 35) |
| Android Studio y emulador | No instalados |

---

## 2. Servidor Django

### 2.1 Instalación

```bash
cd D:\proyecto_semaxel
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` incluye, además de Django y MySQL, las dependencias de la
API: `djangorestframework`, `drf-spectacular` (documentación OpenAPI) y
`Pillow` (validación de imágenes).

### 2.2 Variables de entorno (`.env`)

El proyecto lee un archivo `.env` en la raíz (no se sube a Git). Variables
mínimas:

| Variable | Ejemplo | Para qué |
|---|---|---|
| `SECRET_KEY` | (texto largo y aleatorio) | Obligatoria: sin ella Django no arranca. |
| `DEBUG` | `True` en desarrollo | Con `True`, Django sirve las fotos subidas (`/media/`). |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,192.168.1.50` | Agregar la IP o el dominio por el que entra el celular. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | `capstone_semaxel`, `root`, … | Conexión a MySQL. |
| `SEMAXEL_RADIO_LLEGADA_METROS` | `150` | Radio para verificar la llegada con GPS (opcional). |
| `SEMAXEL_PUSH_BACKEND` | `consola` | `fcm` cuando Firebase esté configurado (opcional). |
| `FCM_CREDENTIALS_FILE` | `D:\secretos\firebase.json` | Solo con `fcm` (opcional). |

El código menciona un `.env.example`, pero ese archivo no existe en el
repositorio. Queda pendiente crearlo.

### 2.3 Base de datos

El proyecto usa MySQL 8. **Este equipo todavía no tiene MySQL**, así que
durante el desarrollo de la API las pruebas se ejecutaron con SQLite en memoria
mediante un archivo de configuración temporal, que no se sube a Git:

```python
# settings_local_sqlite.py (fuera del repositorio)
from config.settings import *  # noqa

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
```

```bash
set SECRET_KEY=solo-pruebas-locales
set PYTHONPATH=<carpeta donde está settings_local_sqlite.py>
venv\Scripts\python.exe manage.py test --settings=settings_local_sqlite
```

Para levantar un servidor de prueba con datos de demostración se usó la misma
idea, pero con SQLite en un archivo, `DEBUG = True` y `MEDIA_ROOT` propio:

```bash
venv\Scripts\python.exe manage.py migrate --settings=settings_demo_sqlite
venv\Scripts\python.exe manage.py seed_demo --settings=settings_demo_sqlite
venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000 --settings=settings_demo_sqlite
```

`seed_demo` crea usuarios de prueba (técnicos `cdiaz`, `atorres`,
`lfernandez`), sucursales con coordenadas y horario hipotéticos, tickets y
ofertas. Al terminar muestra en la consola la contraseña común de esos
usuarios.

**Pendiente (parte 9 de la bitácora):** instalar MySQL en este equipo, crear el
`.env`, correr `migrate` y repetir las pruebas sobre MySQL antes de abrir los
puertos.

### 2.4 Comandos útiles

| Para qué | Comando |
|---|---|
| Pruebas | `venv\Scripts\python.exe manage.py test` |
| Revisar que no falten migraciones | `venv\Scripts\python.exe manage.py makemigrations --check --dry-run` |
| Regenerar el esquema OpenAPI | `venv\Scripts\python.exe manage.py spectacular --file "docs/Fase 2/Evidencias Proyecto/Evidencias de documentación/11 APP MOVIL/openapi_app_movil.yaml"` |
| Documentación interactiva | Con el servidor corriendo: `http://localhost:8000/api/v1/docs/` |

---

## 3. App Android

### 3.1 Qué se instaló (14-11-2026)

Todo quedó en `D:\herramientas-android\`, sin instalar Android Studio ni
cambiar la configuración del sistema:

| Herramienta | Versión | Origen | Carpeta |
|---|---|---|---|
| JDK (Eclipse Temurin) | 21.0.13 | api.adoptium.net | `jdk\jdk-21.0.13+9` |
| Gradle | 8.11.1 (SHA-256 verificado con el publicado por Gradle) | services.gradle.org | `gradle-8.11.1` |
| Android command-line tools | 11076708 | dl.google.com | `sdk\cmdline-tools\latest` |
| Android SDK Platform | 35 | sdkmanager | `sdk\platforms\android-35` |
| Build-Tools | 35.0.0 y 34.0.0 (la 34 la pidió Gradle automáticamente) | sdkmanager | `sdk\build-tools` |
| Platform-Tools (adb) | la vigente | sdkmanager | `sdk\platform-tools` |

Para instalar los paquetes del SDK, `sdkmanager` exige aceptar la licencia del
SDK de Android de Google. Se aceptó con la autorización de Sebastián Maturana.

Además se creó `D:\herramientas-android\entorno.ps1`, que configura las
variables solo para la consola donde se ejecuta (no cambia nada del sistema):

```powershell
$base = 'D:\herramientas-android'
$env:JAVA_HOME = "$base\jdk\jdk-21.0.13+9"
$env:ANDROID_HOME = "$base\sdk"
$env:ANDROID_SDK_ROOT = "$base\sdk"
$env:ANDROID_USER_HOME = "$base\android-user"   # en vez de C:\Users\...\.android
$env:GRADLE_USER_HOME = "$base\gradle-home"     # caché de Gradle fuera de C:
$env:TEMP = "$base\tmp"
$env:TMP = "$base\tmp"
$env:Path = "$env:JAVA_HOME\bin;$base\gradle-8.11.1\bin;$base\sdk\cmdline-tools\latest\bin;$base\sdk\platform-tools;$env:Path"
```

¿Por qué JDK 21 si el equipo ya tenía el JDK 25? Gradle 8.11 no puede
ejecutarse con Java 25; el JDK 21 es la versión con soporte largo compatible
con Gradle y con el plugin de Android.

### 3.2 Compilar y probar

```powershell
. D:\herramientas-android\entorno.ps1
cd D:\proyecto_semaxel\app-movil
.\gradlew.bat assembleDebug testDebugUnitTest
```

- APK generado: `app-movil\app\build\outputs\apk\debug\app-debug.apk`.
- Resultados de las pruebas: `app-movil\app\build\reports\tests\testDebugUnitTest\index.html`.
- La primera compilación descarga las bibliotecas (unos minutos); quedan en
  `D:\herramientas-android\gradle-home`.

### 3.3 Prueba de contrato contra el servidor

La prueba `ContratoApiTest` usa la capa de datos real de la app contra un
servidor SEMAXEL. Se ejecutó así el 14-11-2026 (pasó):

```powershell
# 1. Servidor de demostración con datos recién cargados (ver 2.3)
venv\Scripts\python.exe manage.py migrate --settings=settings_demo_sqlite
venv\Scripts\python.exe manage.py seed_demo --settings=settings_demo_sqlite
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8765 --settings=settings_demo_sqlite

# 2. En otra consola
. D:\herramientas-android\entorno.ps1
cd D:\proyecto_semaxel\app-movil
.\gradlew.bat testDebugUnitTest --tests "cl.semaxel.tecnico.data.ContratoApiTest" "-Psemaxel.apiContrato=http://127.0.0.1:8765/" "-Psemaxel.usuarioContrato=cdiaz" "-Psemaxel.claveContrato=CLAVE_DE_SEED_DEMO"
```

En PowerShell, cada argumento `-P...` va entre comillas: sin ellas, PowerShell
corta el argumento en el punto y Gradle falla con "Cannot locate tasks".

### 3.4 Reproducir en otro equipo

- **Con Android Studio (por ejemplo, el Mac):** abrir la carpeta `app-movil/`;
  Android Studio usa el `gradlew` del proyecto e instala lo que falte del SDK.
- **Sin Android Studio:** instalar JDK 21 y las command-line tools, ejecutar
  `sdkmanager "platforms;android-35" "build-tools;35.0.0" "platform-tools"` y
  luego `./gradlew assembleDebug`.

### 3.5 Dirección del servidor

Se define en `app-movil/gradle.properties` (`semaxel.apiUrl`) y queda dentro
del APK al compilar:

- Emulador: `http://10.0.2.2:8000/` (es el `localhost` del computador).
- Celular en la misma red Wi-Fi: `http://<IP del computador>:8000/`.
- Servidor publicado: su dominio o IP pública (parte 9 de la bitácora).

---

## 4. Problemas conocidos del entorno

| Problema | Efecto | Qué hacer |
|---|---|---|
| Disco C: casi lleno | Programas que escriben en C: (caché, temporales) pueden fallar. | Liberar espacio en C:; mientras tanto, usar `entorno.ps1`. |
| Word por automatización se quedó colgado una vez | La conversión de Word a PDF para revisar los documentos falló la primera vez. | Se resolvió copiando el archivo a una ruta sin tildes antes de abrirlo. |
| Sin MySQL | Las pruebas no se han ejecutado sobre la base real. | Instalar MySQL (parte 9). |
| Sin emulador | La app no se ha probado en pantalla. | Probar en un celular o instalar el emulador (requiere virtualización activada en el equipo). |
