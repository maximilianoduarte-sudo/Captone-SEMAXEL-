# SEMAXEL: gestión de mantenimiento de infraestructura

Sistema para gestionar el mantenimiento de la infraestructura física de
sucursales. Tiene tres partes:

- **Aplicación web** (Django): sucursales, técnicos, especialidades, tickets,
  ofertas de trabajo, órdenes de trabajo, SLA, mantenimiento preventivo,
  reportes y un dashboard con indicadores.
- **API REST** (`/api/v1/`) para la app móvil.
- **App Android "SEMAXEL Técnico"** (`app-movil/`) para el técnico en terreno:
  toma ofertas, registra la llegada con GPS, sube fotos y pide la firma de
  conformidad.

Proyecto de título de Ingeniería en Informática (Duoc UC, PTY4614).

## Stack tecnológico

| Parte | Tecnología |
|---|---|
| Servidor | Python 3.10+, Django 5.2, Django REST Framework, drf-spectacular (Swagger), Waitress |
| Base de datos | MySQL 8 (en el equipo de pruebas: MySQL 8.4 portable) |
| Web | HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js |
| App móvil | Kotlin, Jetpack Compose, Retrofit (ver [`app-movil/README.md`](app-movil/README.md)) |
| Herramientas | Git y GitHub, emulador de Android (SDK 35) |

## Estructura del proyecto

```text
Captone-SEMAXEL-/
├── config/            # Configuración del proyecto Django
├── accounts/          # Usuarios y roles
├── empresas/          # Empresas cliente
├── sucursales/        # Sucursales
├── tecnicos/          # Técnicos y especialidades
├── tickets/           # Tickets, órdenes de trabajo, evidencias y firmas
├── ofertas/           # Ofertas de trabajo para técnicos
├── sla/               # SLA
├── mantenimiento/     # Mantenimiento preventivo
├── dashboard/         # Dashboard, reportes y comandos seed_demo y preparar_qa
├── api/               # API REST para la app móvil
├── app-movil/         # App Android del técnico
├── scripts/           # Scripts para instalar, levantar y apagar todo (Windows)
├── docs/              # Documentación del proyecto
├── templates/         # Plantillas globales
├── static/            # CSS, JS, Bootstrap, Chart.js
├── manage.py
├── requirements.txt
├── .env.example       # Plantilla del .env
└── .env               # Variables de entorno (no se sube a Git)
```

## Inicio rápido (equipo ya preparado)

Si el equipo ya tiene todo instalado (por ejemplo, el servidor de pruebas):

1. **Levantar todo:** doble clic en `scripts\levantar-todo.cmd`, o en
   PowerShell, desde la carpeta del proyecto:

   ```powershell
   .\scripts\levantar-todo.ps1
   ```

   El script abre una ventana por servicio y espera a que cada uno responda
   antes de pasar al siguiente:

   1. **MySQL**
   2. **Servidor web y API**: aplica las migraciones pendientes y queda en
      `http://localhost:8000/`
   3. **Emulador de Android**: espera a que Android termine de arrancar

   Lo que ya está corriendo no se vuelve a abrir. Al final muestra el estado
   y las direcciones para entrar.

2. **Probar:** entrar a `http://localhost:8000/`, o abrir la app en el
   emulador, con los usuarios de prueba (ver
   [Usuarios de prueba](#usuarios-de-prueba)).

3. **Apagar todo:** doble clic en `scripts\apagar-todo.cmd`, o:

   ```powershell
   .\scripts\apagar-todo.ps1
   ```

   Cierra el emulador, detiene el servidor y apaga MySQL de forma ordenada.
   Los datos quedan guardados en la base.

Opciones de `levantar-todo.ps1`:

| Opción | Para qué |
|---|---|
| `-SinEmulador` | Solo MySQL y el servidor, para probar la web |
| `-InstalarApp` | Además compila la app, la instala en el emulador y la abre |
| `-Desarrollo` | Servidor con `runserver`, que se reinicia solo al cambiar el código (en vez de Waitress) |

Por ejemplo: `.\scripts\levantar-todo.ps1 -InstalarApp`.

## Scripts disponibles

Todos están en `scripts/` y se ejecutan desde PowerShell en Windows.

| Script | Qué hace |
|---|---|
| `instalar.ps1` | Primera vez: crea `venv\`, instala las dependencias y crea el `.env` con una `SECRET_KEY` nueva |
| `preparar-datos.ps1` | Carga los datos de demostración (`seed_demo`) y el entorno de QA (`preparar_qa`). `-SoloQA` reinicia solo los datos de QA; `-NuevaClave` cambia la clave de los usuarios `qa_*`; `-AgregarTrabajos` suma 8 trabajos nuevos para `qa_tecnico` sin borrar nada |
| `levantar-todo.ps1` / `.cmd` | Levanta MySQL, el servidor y el emulador, cada uno en su ventana |
| `apagar-todo.ps1` / `.cmd` | Apaga el emulador, el servidor y MySQL |
| `estado.ps1` | Muestra qué está corriendo y las direcciones para entrar |
| `iniciar-mysql.ps1` | Solo MySQL (portable en primer plano, o el servicio de Windows `MySQL80`) |
| `iniciar-servidor.ps1` | Solo el servidor web y la API (`-Desarrollo` para `runserver`) |
| `iniciar-emulador.ps1` | Solo el emulador |
| `instalar-app.ps1` | Compila la app de depuración, la instala en el emulador (o en un celular por USB) y la abre. `-SinCompilar` instala el último APK |
| `abrir-android-studio.ps1` / `.cmd` | Abre Android Studio con `app-movil`, el SDK y el emulador del equipo, y sus cachés en D: (ver [Desarrollar la app en Android Studio](#desarrollar-la-app-en-android-studio)) |

Las rutas por defecto son las del equipo de pruebas: MySQL portable en
`D:\herramientas-servidor` y herramientas de Android en
`D:\herramientas-android`. En otro equipo se cambian sin tocar los scripts:
copiar `scripts\config.local.ejemplo.ps1` como `scripts\config.local.ps1` (no
se sube a Git) y ajustar las rutas, el nombre del servicio de MySQL o el del
emulador.

## Primera vez en un equipo nuevo

### Requisitos

- **Python 3.10 o superior** y **Git**.
- **MySQL 8**: el instalador oficial (servicio `MySQL80`) o el ZIP portable,
  como en el equipo de pruebas (ver la
  [Guía del servidor de pruebas](docs/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/11%20APP%20MOVIL/Guia_Servidor_Pruebas.md)).
- **Solo para la app móvil:** Android Studio, o JDK 21 + SDK de Android 35 +
  un emulador (ver la
  [Guía del entorno de desarrollo](docs/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/11%20APP%20MOVIL/Guia_Entorno_Desarrollo.md)).

### Pasos

1. **Clonar el repositorio:**

   ```powershell
   git clone https://github.com/maximilianoduarte-sudo/Captone-SEMAXEL-.git
   cd Captone-SEMAXEL-
   ```

2. **Instalar el proyecto** (entorno virtual, dependencias y `.env`):

   ```powershell
   .\scripts\instalar.ps1
   ```

3. **Crear la base y su usuario en MySQL.** Con el cliente `mysql` como
   `root`, cambiando `CLAVE_SEGURA` por una clave propia:

   ```sql
   CREATE DATABASE capstone_semaxel CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
   CREATE USER 'semaxel'@'localhost' IDENTIFIED BY 'CLAVE_SEGURA';
   GRANT ALL PRIVILEGES ON capstone_semaxel.* TO 'semaxel'@'localhost';
   -- Django crea esta base al correr las pruebas:
   GRANT ALL PRIVILEGES ON test_capstone_semaxel.* TO 'semaxel'@'localhost';
   ```

4. **Completar el `.env`:** poner `DB_USER=semaxel` y
   `DB_PASSWORD=CLAVE_SEGURA`. Cada variable está explicada en
   `.env.example`. Para entrar desde el emulador, agregar `10.0.2.2` a
   `ALLOWED_HOSTS`; para entrar desde otro equipo o un celular, agregar la IP
   del computador en la red.

5. **Ajustar las rutas de los scripts** si son distintas a las del equipo de
   pruebas (ver [Scripts disponibles](#scripts-disponibles)).

6. **Cargar los datos de prueba**, con MySQL corriendo
   (`.\scripts\iniciar-mysql.ps1` en otra ventana):

   ```powershell
   .\scripts\preparar-datos.ps1
   ```

7. **Levantar todo** con `.\scripts\levantar-todo.ps1 -InstalarApp`. La
   primera compilación de la app tarda unos minutos.

> Si PowerShell no deja ejecutar scripts ("la ejecución de scripts está
> deshabilitada"), usa los `.cmd` o ejecuta
> `powershell -ExecutionPolicy Bypass -File .\scripts\<script>.ps1`.

### Sin los scripts (Linux, macOS o paso a paso)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # y completar SECRET_KEY y DB_*
python manage.py migrate
python manage.py seed_demo
python manage.py preparar_qa --archivo-clave ~/semaxel-qa.txt
python manage.py runserver 0.0.0.0:8000
```

La `SECRET_KEY` se genera con
`python -c "import secrets; print(secrets.token_urlsafe(50))"`.

## Desarrollar la app en Android Studio

1. Levantar el servidor: `.\scripts\levantar-todo.ps1` (el emulador también
   se puede abrir desde el **Device Manager** de Studio).
2. Abrir Studio con `scripts\abrir-android-studio.cmd`. **No abrirlo desde el
   menú Inicio:** el script le indica dónde están el SDK, el JDK y el emulador,
   y guarda sus cachés en D:.
3. Esperar a que termine el **Gradle Sync** (barra inferior).
4. Elegir la configuración **app** y el dispositivo **SEMAXEL_Pixel7_API35**,
   y presionar **Run ▶** (Shift+F10). Con el bicho (Shift+F9) se depura con
   puntos de interrupción.
5. **Live Edit:** con la app corriendo, los cambios en las pantallas (textos,
   colores, márgenes) se ven en el emulador sin reinstalar. Los cambios en la
   lógica se aplican con **Apply Changes** (Ctrl+F10) o volviendo a ejecutar.
6. **Logcat** (barra inferior) muestra los registros y errores de la app.

## Usuarios de prueba

| Conjunto | Usuarios | Contraseña |
|---|---|---|
| Demostración (`seed_demo`) | Empresa, gestores, encargados y técnicos de demo (por ejemplo, el técnico `cdiaz`) | Se muestra al terminar `seed_demo` |
| QA (`preparar_qa`) | `qa_admin`, `qa_gestor`, `qa_encargado`, `qa_gerencia`, `qa_tecnico`, `qa_tecnico2`, `qa_tecnico_nodisp`, `qa_tecnico_inactivo`, `qa_otra_admin` | Una sola para todos, guardada en `D:\herramientas-servidor\credenciales\qa.txt` (o en la carpeta `Credenciales` de `config.local.ps1`) |

Las contraseñas nunca se escriben en Git. Qué datos crea el entorno de QA y
los casos de prueba manuales están en la
[Guía de pruebas QA](docs/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/11%20APP%20MOVIL/Guia_Pruebas_QA.md).

## Direcciones

| Dirección | Qué es |
|---|---|
| `http://localhost:8000/` | Web de SEMAXEL |
| `http://localhost:8000/admin/` | Administración de Django |
| `http://localhost:8000/api/v1/docs/` | Documentación interactiva de la API (Swagger) |
| `http://10.0.2.2:8000/` | El mismo servidor visto desde el emulador (la app de depuración usa esta dirección) |
| `http://<IP del equipo>:8000/` | Desde otro equipo o un celular en la misma red (requiere abrir el puerto 8000 en el firewall) |

## Pruebas automáticas

```powershell
.\venv\Scripts\python.exe manage.py test          # servidor (necesita MySQL corriendo)
cd app-movil; .\gradlew.bat testDebugUnitTest     # app móvil
```

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| "MySQL no está corriendo" | Ejecutar `.\scripts\iniciar-mysql.ps1` o `levantar-todo.ps1`. Con el servicio `MySQL80` puede pedir PowerShell como administrador |
| El servidor no arranca: puerto 8000 ocupado | `.\scripts\estado.ps1` para ver qué corre; `.\scripts\apagar-todo.ps1` lo libera |
| La app muestra "No se pudo conectar" a ratos y la ventana del servidor dice "Select ..." | Se hizo clic en la ventana y Windows congeló el servidor. Presionar Esc en esa ventana. Desde la parte 9.6 los scripts desactivan ese modo al abrir cada ventana |
| La app dice que no puede conectarse | Revisar que el servidor esté corriendo y que `ALLOWED_HOSTS` en el `.env` incluya `10.0.2.2` |
| `Bad Request (400)` al entrar por la IP | Agregar esa IP a `ALLOWED_HOSTS` y reiniciar el servidor |
| No existe el dispositivo virtual | Ver los disponibles con `emulator -list-avds` y poner el nombre en `Avd` de `scripts\config.local.ps1` |

## Documentación

La documentación del proyecto está en `docs/`. La de la app móvil y el
servidor de pruebas está en
[`docs/Fase 2/.../11 APP MOVIL/`](docs/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/11%20APP%20MOVIL/):

- **Bitácora de la app móvil:** el paso a paso de cómo se construyó.
- **Guía de la API:** los endpoints que usa la app.
- **Guía del entorno de desarrollo:** el JDK, el SDK de Android y el emulador.
- **Guía del servidor de pruebas:** MySQL, Waitress y el acceso desde la red.
- **Guía de pruebas QA:** los casos de prueba manuales.

## Notas

- El `.env`, `scripts/config.local.ps1`, `venv/` y `media/` no se suben a Git.
- El servidor de pruebas usa HTTP sin cifrar. Antes de publicarlo hay que
  configurar HTTPS y cambiar las contraseñas de demostración.
