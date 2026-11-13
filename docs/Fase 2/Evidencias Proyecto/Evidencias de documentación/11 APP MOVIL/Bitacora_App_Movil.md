# Bitácora de desarrollo: app móvil del técnico

Registro paso a paso de lo que se va agregando a SEMAXEL para la app móvil del
técnico. Se actualiza **en cada parte**, en el mismo push que el código (primero el
commit del código y luego el de la bitácora, que cita su número), para que el
historial de Git y esta bitácora siempre coincidan.

- **Rama:** `feature/app-movil` (el código no entra a `main` hasta revisarlo).
- **Autor de los commits:** Sebastián Maturana, con apoyo de IA (Claude).
- **Documentos relacionados:** Documento A (modelo de alta) y Documento B
  (solicitud de cambio de alcance), en esta misma carpeta.
- **Datos:** todos los datos de ejemplo (empresas, locales, personas) son
  hipotéticos.

---

## Cómo leer esta bitácora

Cada parte tiene la misma estructura:

1. **Objetivo:** qué problema resuelve.
2. **Qué se agregó:** archivos tocados y para qué.
3. **Cómo funciona:** el flujo explicado en simple.
4. **Decisiones:** qué se eligió y por qué (lo que hay que saber defender).
5. **Pruebas:** qué se verifica automáticamente.
6. **Probarlo a mano:** comandos para verlo funcionar.

---

## Estado general

| Parte | Qué agrega | Commit | Pruebas totales | Estado |
|---|---|---|---|---|
| 0 | Preparación del entorno en el equipo Windows | (sin commit) | 97 | Hecho |
| 1 | Django REST Framework e inicio de sesión por token | `e555546` | 113 | Hecho |
| 2 | Ofertas disponibles para el técnico | `0d85325` | 123 | Hecho |
| 3 | Tomar una oferta (regla compartida web y API) | `17ebc38` | 135 | Hecho |
| 4 | Mis trabajos: listar y avanzar órdenes (corrige el bug de Gerencia) | `cce1d41` | 160 | Hecho |
| 5 | Fotos de evidencia en la orden | — | — | Pendiente |
| 6 | Coordenadas y horario de la sucursal | — | — | Pendiente |
| 7 | Llegada con GPS | — | — | Pendiente |
| 8 | Proyecto Android: login y navegación | — | — | Pendiente |
| 9 | Pantallas Ofertas y Mis trabajos | — | — | Pendiente |
| 10 | Cámara, GPS y firma en la app | — | — | Pendiente |
| 11 | Notificaciones push | — | — | Pendiente |
| 12 | Servidor de pruebas en el equipo Windows (MySQL, puertos) | — | — | Pendiente |

Las partes 4 en adelante son una propuesta de orden y pueden cambiar.

---

## Panorama: cómo encaja todo

```mermaid
flowchart LR
    App["App Android del técnico<br/>(Kotlin + Compose)"] -- "HTTPS + token" --> API["API REST<br/>/api/v1/ (app api)"]
    Web["Web (navegador)<br/>Admin, Gestor, Encargado, Gerencia"] --> Vistas["Vistas web de Django"]
    API --> Servicios["Servicios de dominio<br/>(services.py)"]
    Vistas --> Servicios
    Servicios --> BD[("MySQL")]
```

Idea central: **las reglas de negocio viven en los servicios**, no en las vistas.
La web y la API son dos "puertas de entrada" que llaman a la misma regla. Así,
si una regla cambia, cambia para las dos al mismo tiempo.

La app **nunca** se conecta directo a MySQL: todo pasa por la API, que aplica los
mismos permisos que la web.

---

## Parte 0: preparación del entorno (13-11-2026)

**Objetivo.** Poder ejecutar y probar el proyecto en el equipo Windows, que
además será el servidor de pruebas para el celular.

**Qué se hizo.**

- Se clonó el repositorio en `D:\proyecto_semaxel` y se creó la rama
  `feature/app-movil` desde `main`.
- Se creó el entorno virtual `venv/` (ya estaba en `.gitignore`, no se sube) y se
  instalaron las dependencias de `requirements.txt`.
- Este equipo **no tiene MySQL**. Para correr las pruebas se usa una
  configuración temporal con SQLite en memoria, que **no se sube** al
  repositorio. Las 97 pruebas originales pasaron así antes de cambiar nada (es
  la línea base).

**Pendiente.** Instalar MySQL en este equipo y repetir las pruebas sobre MySQL
(ver parte 12).

---

## Parte 1: Django REST Framework e inicio de sesión (commit `e555546`)

**Objetivo.** Que la app pueda identificar al técnico antes de mostrarle nada.

**Qué se agregó.**

| Archivo | Para qué |
|---|---|
| `requirements.txt` | Agrega `djangorestframework==3.16.1`. |
| `config/settings.py` | Activa `rest_framework` y `rest_framework.authtoken`, y define la configuración `REST_FRAMEWORK`. |
| `config/urls.py` | Monta la API en `/api/v1/`. |
| `api/` (app nueva) | `views.py`, `serializers.py`, `permissions.py`, `urls.py` y `tests.py`. No tiene modelos propios. |

**Cómo funciona.**

1. La app envía usuario y contraseña a `POST /api/v1/auth/login/`, los mismos
   que se usan en la web.
2. Si son correctos y es un **técnico habilitado**, el servidor responde con un
   **token** y el perfil del técnico.
3. La app guarda el token y lo envía en cada petición siguiente, en la cabecera
   `Authorization: Token <token>`.
4. `POST /api/v1/auth/logout/` borra el token: deja de servir.
5. `GET /api/v1/auth/perfil/` devuelve los datos del técnico.

**Técnico habilitado** (`api/permissions.py`) significa que se cumplen las tres
condiciones: la cuenta está activa, el rol es TECNICO y el perfil de técnico no
está INACTIVO.

**Decisiones.**

- **Token y no sesión del navegador.** El celular no maneja cookies como un
  navegador; el token es el método estándar para apps. Además, la API ignora la
  sesión web, así que no depende de cookies ni de CSRF.
- **Mismo mensaje de error** si el usuario no existe o si la contraseña está mal:
  así nadie puede averiguar qué usuarios existen.
- **403 para otros roles.** La app es solo para técnicos; el resto usa la web.
- **Un token por usuario.** Si el técnico inicia sesión dos veces, recibe el
  mismo token.

**Pruebas (16 nuevas).** Login correcto, contraseña incorrecta, usuario
inexistente, datos faltantes, otros roles, técnico inactivo, rol técnico sin
perfil, cuenta desactivada, perfil con y sin token, token falso, logout y que la
sesión web no sirva para la API.

---

## Parte 2: ofertas disponibles (commit `0d85325`)

**Objetivo.** Que la sección Ofertas de la app muestre los trabajos que el
técnico puede tomar.

**Qué se agregó.**

| Archivo | Para qué |
|---|---|
| `ofertas/services.py` | Función nueva `ofertas_disponibles_para(tecnico)`. |
| `api/serializers.py` | `OfertaSerializer`: qué datos de la oferta recibe la app. |
| `api/views.py` | `OfertasDisponiblesView` (listado) y `OfertaDetalleView` (detalle). |
| `api/urls.py` | `GET ofertas/` y `GET ofertas/<id>/`. |

**Cómo funciona.** Una oferta aparece en la app si cumple las tres condiciones:

1. Está DISPONIBLE (antes se expiran las vencidas, igual que en la web).
2. La categoría del ticket tiene una especialidad definida.
3. El técnico tiene esa especialidad.

En el detalle, el técnico también puede ver las ofertas que ya tomó. Cualquier
otra oferta responde 404.

**Decisiones.**

- **Solo las de su especialidad** (historia HU-09). Hallazgo: la web muestra
  todas las disponibles y valida la especialidad recién al tomar. La web **no**
  se cambió; queda como decisión del equipo.
- **404 y no 403** para ofertas ajenas: no se revela que existen.
- **Sin número interno del ticket** (por ejemplo, `SEMAXEL-00001`), igual que la
  web lo oculta al técnico.

**Pruebas (10 nuevas).** Filtra por especialidad, oculta las tomadas, expira las
vencidas, no expone el número del ticket, detalle propio y ajeno, sin token y
otro rol.

---

## Parte 3: tomar una oferta (commit `17ebc38`)

**Objetivo.** Que el técnico tome una oferta desde la app, usando **exactamente
la misma regla** que la web.

**Qué se agregó o cambió.**

| Archivo | Para qué |
|---|---|
| `ofertas/services.py` | `tomar_oferta()` y el error `OfertaNoTomable`. La regla sale de la vista web y queda aquí. |
| `ofertas/views.py` | La vista web `tomar` ahora llama al servicio (bajó de ~90 a ~40 líneas). |
| `api/views.py` y `api/urls.py` | `POST ofertas/<id>/tomar/`. |
| `ofertas/tests.py` | Pruebas del servicio (antes estaba vacío). |

**Cómo funciona.** `tomar_oferta(oferta, tecnico, usuario)` revisa, en este
orden:

| Si pasa esto | Código |
|---|---|
| Ya no está disponible (por ejemplo, otro la tomó) | `no_disponible` |
| Venció (queda marcada EXPIRADA) | `vencida` |
| El ticket no puede pasar a ejecución | `ticket_no_permite` |
| La categoría no tiene especialidad | `sin_especialidad` |
| El técnico no tiene la especialidad | `especialidad_no_coincide` |

Si algo falla, lanza `OfertaNoTomable` y no cambia nada. Si todo está bien: la
oferta queda TOMADA, se crea la orden ASIGNADA, el ticket pasa a EN_EJECUCION
(con su entrada en el historial) y el técnico queda OCUPADO.

- La **web** traduce el error a un mensaje y redirige como antes.
- La **API** responde `201` con la orden creada, `409` con `detail` y `codigo` si
  no se puede tomar, o `404` si no existe.

**Decisiones.**

- **Una sola regla para la web y la API.** Es el cambio técnico que pedía el
  Documento B (sección 3.2): evita que las dos versiones dejen de coincidir.
- **Bloqueo contra tomas simultáneas** (`select_for_update`): si dos técnicos
  toman la misma oferta al mismo tiempo, el segundo espera y recibe
  `no_disponible`. Antes, los dos podían quedarse con ella. Mejora también la
  web. Ojo: SQLite no ejercita este bloqueo; se comprobará con MySQL.
- **Solo POST en la API.** Tomar una oferta modifica datos, así que un `GET`
  responde 405.

**Pruebas (12 nuevas).** 6 del servicio (toma exitosa y cada código de error) y
6 de la API. Las 3 pruebas web que ya existían sobre tomar ofertas siguen
pasando sin cambios: así se demuestra que la web se comporta igual.

---

## Parte 4: Mis trabajos (commit `cce1d41`)

**Objetivo.** Que la sección Mis trabajos de la app liste las órdenes del
técnico y le permita **iniciar** y **resolver** el trabajo, con las mismas
reglas que la web.

**Qué se agregó o cambió.**

| Archivo | Para qué |
|---|---|
| `tickets/services.py` (nuevo) | `cambiar_estado_orden()`, `transiciones_permitidas()` y el error `TransicionNoPermitida`. Las reglas salen de `tickets/ordenes_views.py`. |
| `tickets/ordenes_views.py` | La web usa el servicio (el archivo bajó unas 120 líneas). |
| `api/serializers.py` | `OrdenSerializer`, `IniciarOrdenSerializer` y `ResolverOrdenSerializer`. |
| `api/views.py` y `api/urls.py` | Listado, detalle, iniciar y resolver. |
| `tickets/tests.py` | Pruebas del servicio y de la corrección de Gerencia (antes estaba vacío). |

**Cómo funciona.** La orden sigue esta máquina de estados:

```
ASIGNADA ──iniciar──► EN_EJECUCION ──resolver──► RESUELTA ──cerrar──► CERRADA
    └──────────── cancelar ────────────┘              (encargado, en la web)
```

| Quién | Qué puede hacer |
|---|---|
| Técnico de la orden | Iniciar (exige diagnóstico) y resolver (exige el trabajo realizado). |
| Admin, Gestor, Encargado | Todo, incluido cerrar (exige calificación de 1 a 5) y cancelar. |
| Gerencia | Nada: solo consulta. |

`cambiar_estado_orden(orden, destino, usuario, datos)` revisa en orden: que no
sea el mismo estado (`sin_cambio`), que la transición exista
(`transicion_invalida`), que el usuario pueda aplicarla (`sin_permiso`) y que
vengan los datos obligatorios (`falta_diagnostico`, `falta_trabajo`,
`falta_calificacion`). Si todo está bien, guarda los datos de trabajo, fija las
fechas de inicio o fin, mueve el ticket al estado equivalente con su entrada en
el historial, libera al técnico si no tiene otras órdenes activas y, al cerrar,
registra la calificación.

En la API, cada orden trae el campo `acciones` (`["iniciar"]`, `["resolver"]` o
`[]`) para que la app sepa qué botón mostrar sin repetir la máquina de estados.

**Decisiones.**

- **Endpoints con nombre de acción** (`iniciar/`, `resolver/`) en vez de uno
  genérico "cambiar estado": cada uno pide solo sus datos y es más fácil de usar
  desde la app y de explicar.
- **El técnico no cierra ni cancela desde la app**: cerrar exige la calificación
  del encargado, que sigue usando la web. Reabrir (de RESUELTA a EN_EJECUCION)
  tampoco está en la app por ahora.
- **Corrección del bug de Gerencia (H3).** Antes, Gerencia podía cerrar o
  cancelar órdenes aunque su perfil es de solo lectura. Ahora no ve el
  formulario de transición y, si intenta enviarlo igual, recibe 403. Es el único
  cambio de comportamiento de la web en esta parte.
- **Bloqueo de la fila** (`select_for_update`), igual que al tomar ofertas, para
  que dos cambios simultáneos no se pisen.
- **Errores por tipo**: 400 si faltan datos o son inválidos (por ejemplo, costo
  negativo), 404 si la orden no es suya y 409 si el estado actual no permite la
  acción.

**Pruebas (25 nuevas).** 13 del servicio (iniciar, resolver, cerrar, cancelar,
datos obligatorios, permisos, técnico que sigue ocupado con otra orden y
Gerencia), 3 de la web (Gerencia ve sin poder cambiar, recibe 403 al enviar y el
encargado sí puede) y 9 de la API.

---

## Referencia rápida de la API

Todas las rutas empiezan con `/api/v1/` y responden JSON. Salvo el login, todas
exigen la cabecera `Authorization: Token <token>`.

| Método | Ruta | Qué hace | Respuestas |
|---|---|---|---|
| POST | `auth/login/` | Entrega el token | 200, 400, 403 |
| POST | `auth/logout/` | Borra el token | 204, 401 |
| GET | `auth/perfil/` | Perfil del técnico | 200, 401, 403 |
| GET | `ofertas/` | Ofertas que puede tomar | 200, 401, 403 |
| GET | `ofertas/<id>/` | Detalle de una oferta | 200, 401, 403, 404 |
| POST | `ofertas/<id>/tomar/` | Toma la oferta | 201, 401, 403, 404, 409 |
| GET | `ordenes/` | Sus órdenes (filtro opcional `?estado=`) | 200, 400, 401, 403 |
| GET | `ordenes/<id>/` | Detalle de una orden suya | 200, 401, 403, 404 |
| POST | `ordenes/<id>/iniciar/` | Inicia el trabajo (`diagnostico`, `costo_estimado`) | 200, 400, 401, 403, 404, 409 |
| POST | `ordenes/<id>/resolver/` | Marca como resuelta (`trabajo_realizado`, `observaciones`, `costo_final`) | 200, 400, 401, 403, 404, 409 |

Significado de los códigos: 200/201/204 correcto; 400 datos inválidos; 401 falta
el token o no es válido; 403 no es un técnico habilitado; 404 no existe o no le
corresponde; 409 la acción no se puede hacer en el estado actual.

## Probarlo a mano

Con el servidor corriendo (`python manage.py runserver`) y los datos de
demostración cargados (`python manage.py seed_demo`, que crea técnicos como
`cdiaz` con la clave definida en la constante `PASS` de ese comando):

```bash
# 1. Iniciar sesión (reemplaza CLAVE por la del técnico de prueba)
curl -X POST http://localhost:8000/api/v1/auth/login/ -H "Content-Type: application/json" -d "{\"username\": \"cdiaz\", \"password\": \"CLAVE\"}"

# 2. Copiar el token de la respuesta y usarlo en las siguientes llamadas
curl http://localhost:8000/api/v1/ofertas/ -H "Authorization: Token PEGAR_TOKEN"

# 3. Tomar la oferta con id 1 (la respuesta trae el orden_id)
curl -X POST http://localhost:8000/api/v1/ofertas/1/tomar/ -H "Authorization: Token PEGAR_TOKEN"

# 4. Ver mis trabajos
curl http://localhost:8000/api/v1/ordenes/ -H "Authorization: Token PEGAR_TOKEN"

# 5. Iniciar y resolver la orden con id 1
curl -X POST http://localhost:8000/api/v1/ordenes/1/iniciar/ -H "Authorization: Token PEGAR_TOKEN" -H "Content-Type: application/json" -d "{\"diagnostico\": \"Enchufe derretido\"}"
curl -X POST http://localhost:8000/api/v1/ordenes/1/resolver/ -H "Authorization: Token PEGAR_TOKEN" -H "Content-Type: application/json" -d "{\"trabajo_realizado\": \"Cambio de enchufe\"}"
```

---

## Hallazgos y pendientes

Cosas encontradas durante el trabajo que quedan registradas para decidir:

| # | Hallazgo | Estado |
|---|---|---|
| H1 | La web muestra al técnico todas las ofertas, no solo las de su especialidad (HU-09). | Por decidir |
| H2 | En la web, "tomar oferta" se ejecuta con un enlace `GET`: un enlace malicioso podría hacer que un técnico tome una oferta sin querer. Arreglarlo exige cambiar el botón del template. | Por decidir |
| H3 | Gerencia podía cerrar o cancelar una orden de trabajo aunque es de solo lectura. | Corregido en la parte 4 |
| H4 | Este equipo no tiene MySQL; las pruebas se corren con SQLite. | Parte 12 |
| H5 | Los tokens de la API no vencen; si se pierde un celular, hay que borrar el token desde el admin. | Evaluar vencimiento |
| H6 | El registro de requisitos dice 95 pruebas (RNF-15), pero había 97 antes de este trabajo. | Corregir al actualizar requisitos |
| H7 | El traspaso decía que las fotos completan el RF-11, pero el RF-11 es "Asignación de encargados a sucursales". | Consultar al PO |
