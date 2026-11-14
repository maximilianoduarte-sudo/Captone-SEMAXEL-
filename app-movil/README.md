# SEMAXEL Técnico (app Android)

App nativa para el técnico de terreno de SEMAXEL. Consume la API REST del
servidor Django (`/api/v1/`), documentada en
[`docs/.../11 APP MOVIL/Guia_API_App_Movil.md`](../docs/Fase%202/Evidencias%20Proyecto/Evidencias%20de%20documentaci%C3%B3n/11%20APP%20MOVIL/Guia_API_App_Movil.md).

**Estado:** login, navegación con las cinco secciones, Inicio y Perfil. Ofertas,
Mis trabajos y Evidencias muestran por ahora un aviso de "próximamente". Ver la
bitácora para el detalle de cada parte.

## Tecnología

| Pieza | Uso |
|---|---|
| Kotlin 2.0 + Jetpack Compose (Material 3) | Interfaz |
| Navigation Compose | Barra inferior con 5 secciones |
| ViewModel + StateFlow | Estado de cada pantalla |
| Retrofit + OkHttp + kotlinx.serialization | Llamadas a la API y JSON |
| DataStore | Guarda el token en el celular |

Requisitos: Android Studio (Ladybug o más nuevo), JDK 17 o 21, SDK de
Android 35. Mínimo Android 8.0 (API 26).

## Abrir y ejecutar

1. En Android Studio: **File → Open** y elegir la carpeta `app-movil/`.
   Si pregunta por Gradle, aceptar usar el wrapper (Gradle 8.11.1). Si falta el
   SDK 35, Android Studio ofrece instalarlo.
2. Levantar el servidor Django en el computador:
   `python manage.py runserver 0.0.0.0:8000`.
3. Ejecutar la app en el emulador. Por defecto apunta a `http://10.0.2.2:8000/`,
   que es el `localhost` del computador visto desde el emulador.
4. Iniciar sesión con un técnico (por ejemplo `cdiaz` de `seed_demo`).

### Celular físico o servidor de pruebas

Cambiar `semaxel.apiUrl` en `gradle.properties` por la dirección del servidor
(debe terminar en `/`), por ejemplo `http://192.168.1.50:8000/`, y agregar esa
IP o dominio a `ALLOWED_HOSTS` en el `.env` de Django.

La app permite HTTP sin cifrar (`res/xml/network_security_config.xml`) porque
el servidor de pruebas aún no tiene HTTPS. En producción hay que usar HTTPS.

## Pruebas

Pruebas unitarias (JVM, sin emulador) en `app/src/test/`:

```bash
./gradlew testDebugUnitTest
```

Desde Android Studio: clic derecho en la carpeta `app/src/test` → **Run Tests**.

## Estructura

```
app/src/main/java/cl/semaxel/tecnico/
├── SemaxelApp.kt, Contenedor.kt   Arranque y objetos compartidos
├── MainActivity.kt                Única Activity (Compose)
├── data/
│   ├── remote/                    API: SemaxelApi (Retrofit), Modelos (JSON),
│   │                              ClienteApi (token y 401), ErroresApi
│   ├── local/SesionStore.kt       Token guardado (DataStore)
│   ├── Repositorio.kt             Lo único que usan las pantallas
│   └── Resultado.kt               Éxito o error ya explicado
└── ui/
    ├── SemaxelRaiz.kt             Login o app, según haya token
    ├── login/, principal/, inicio/, perfil/
    ├── comun/                     Cargando, error, "próximamente"
    └── tema/                      Colores de SEMAXEL
```
