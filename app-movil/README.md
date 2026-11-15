# SEMAXEL Técnico (app Android)

App nativa para el técnico de terreno de SEMAXEL. Consume la API REST del
servidor Django (`/api/v1/`), documentada en
[`docs/.../11 APP MOVIL/Guia_API_App_Movil.md`](../docs/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/11%20APP%20MOVIL/Guia_API_App_Movil.md).
El paso a paso de cómo se construyó está en la
[bitácora](../docs/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/11%20APP%20MOVIL/Bitacora_App_Movil.md)
y la preparación del equipo, en la
[guía del entorno](../docs/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/11%20APP%20MOVIL/Guia_Entorno_Desarrollo.md).

## Qué hace

| Sección | Funciones |
|---|---|
| Inicio | Resumen: ofertas disponibles, trabajos activos y acceso a cada uno. |
| Ofertas | Ofertas de las especialidades del técnico; detalle con el local, su horario y mapa; **tomar oferta**. |
| Mis trabajos | Órdenes (activas o todas); detalle con **llegada con GPS**, **iniciar**, **resolver**, tiempo de respuesta frente al SLA, datos del local y mapa. |
| Evidencias | **Fotos** con la cámara o la galería (se reducen y enderezan antes de subirlas), eliminarlas, y **firma de conformidad** del encargado con el dedo. |
| Perfil | Datos del técnico, disponibilidad y cerrar sesión. |

Los botones de cada orden los decide el servidor (campo `acciones`), así que la
app no repite las reglas de negocio. Pendiente: notificaciones push (requiere
el proyecto de Firebase).

## Tecnología

| Pieza | Uso |
|---|---|
| Kotlin 2.0 + Jetpack Compose (Material 3) | Interfaz |
| Navigation Compose | Barra inferior con 5 secciones y pantallas de detalle |
| ViewModel + StateFlow | Estado de cada pantalla |
| Retrofit + OkHttp + kotlinx.serialization | Llamadas a la API y JSON |
| DataStore | Guarda el token en el celular |
| Play Services Location | Posición actual para registrar la llegada |
| Coil | Muestra las fotos de evidencia |
| ExifInterface | Endereza las fotos según la orientación de la cámara |

Requisitos: JDK 17 o 21 y SDK de Android 35 (o Android Studio Ladybug o más
nuevo). Funciona desde Android 8.0 (API 26).

## Compilar y ejecutar

1. **Con Android Studio:** **File → Open** y elegir la carpeta `app-movil/`.
   **Desde la consola:** `./gradlew assembleDebug` genera
   `app/build/outputs/apk/debug/app-debug.apk`.
2. Levantar el servidor Django: `python manage.py runserver 0.0.0.0:8000`.
3. Ejecutar la app en el emulador (apunta a `http://10.0.2.2:8000/`, el
   `localhost` del computador) o instalarla en un celular con
   `adb install app/build/outputs/apk/debug/app-debug.apk`.
4. Iniciar sesión con un técnico (por ejemplo `cdiaz`, de `seed_demo`).

### Celular físico o servidor de pruebas

Cambiar `semaxel.apiUrl` en `gradle.properties` por la dirección del servidor
(debe terminar en `/`), por ejemplo `http://192.168.1.50:8000/`, volver a
compilar, y agregar esa IP o dominio a `ALLOWED_HOSTS` en el `.env` de Django.

La app permite HTTP sin cifrar (`res/xml/network_security_config.xml`) porque
el servidor de pruebas aún no tiene HTTPS. En producción hay que usar HTTPS.

### Permisos que pide

- **Ubicación:** solo al tocar "Registrar llegada", para enviar la posición al
  servidor, que calcula la distancia al local.
- **Cámara:** no se pide permiso. La foto se toma con la app de cámara del
  sistema y se guarda en un archivo temporal de la app (`FileProvider`).

## Pruebas

Pruebas unitarias (JVM, sin emulador) en `app/src/test/`:

```bash
./gradlew testDebugUnitTest
```

| Archivo | Qué prueba |
|---|---|
| `ErroresApiTest` | Traducción de los errores del servidor a mensajes. |
| `ModelosJsonTest` | Lectura del JSON real de la API y omisión de campos vacíos. |
| `FormatoTest` | Fechas en hora de Chile, montos en pesos y horario. |
| `LoginViewModelTest` | Lógica del inicio de sesión. |
| `TerrenoViewModelsTest` | Tomar oferta, iniciar, resolver (409) y llegada. |
| `ContratoApiTest` | **Prueba de contrato:** la capa de datos real contra un servidor real (ver abajo). |

### Prueba de contrato (contra el servidor)

Recorre el flujo completo de un trabajo con el código real de la app
(Retrofit, modelos y repositorio): login, ofertas, tomar, llegada, iniciar,
subir y eliminar fotos, firma, resolver y cierre de sesión. Necesita un
servidor con los datos de `seed_demo` recién cargados y se activa con
propiedades de Gradle; sin ellas se omite:

```bash
./gradlew testDebugUnitTest --tests "cl.semaxel.tecnico.data.ContratoApiTest" "-Psemaxel.apiContrato=http://127.0.0.1:8000/" "-Psemaxel.usuarioContrato=cdiaz" "-Psemaxel.claveContrato=CLAVE_DE_SEED_DEMO"
```

En PowerShell, cada `-P...` debe ir entre comillas.

## Estructura

```
app/src/main/java/cl/semaxel/tecnico/
├── SemaxelApp.kt, Contenedor.kt   Arranque y objetos compartidos
├── MainActivity.kt                Única Activity (Compose)
├── data/
│   ├── remote/                    API: SemaxelApi (Retrofit), Modelos (JSON),
│   │                              ClienteApi (token y 401), ErroresApi
│   ├── local/                     Sesion (interfaz) y SesionStore (DataStore)
│   ├── Repositorio.kt             Lo único que usan las pantallas
│   └── Resultado.kt               Éxito o error ya explicado
├── dispositivo/                   GPS (Ubicacion) y fotos (Imagenes)
└── ui/
    ├── SemaxelRaiz.kt             Login o app, según haya token
    ├── principal/                 Barra inferior y navegación
    ├── login/, inicio/, ofertas/, trabajos/, evidencias/, perfil/
    ├── comun/                     Tarjetas, mensajes, formato de datos
    └── tema/                      Colores de SEMAXEL
```
