# INFORME DE AVANCE — Sistema de Gestión de Mantenimiento de Infraestructura

**Proyecto:** Capstone-SEMAXEL
**Asignatura:** Proyecto de título de Ingeniería en Informática
**Fecha del informe:** 21/09/2026

---

## 1. Resumen general

Se está desarrollando una aplicación web para la gestión del mantenimiento de la
infraestructura física de sucursales. Permite administrar sucursales, técnicos,
especialidades, tickets de incidencias, ofertas de trabajo, órdenes de trabajo,
SLA y mantenimiento preventivo, e incluye un dashboard con indicadores.

El proyecto se basa en **Django 5.2** con **MySQL 8.0**. A la fecha se ha
completado la **instalación del framework**, la **estructura base**, el
**modelado del dominio de datos** completo, un **prototipo visual navegable**
con datos de demostración y la **Fase 4 (Conexión al ORM y CRUD persistente)**:
todas las vistas principales consultan ahora la base de datos real, los
formularios guardan en MySQL y existe un comando `seed_demo` para sembrar
datos. El siguiente hito es **autenticación y permisos por rol** (Fase 5) y la
**lógica de negocio del ciclo completo** (Fase 6).

> Estado de verificación técnica (21/09/2026):
> - `python manage.py check` → **sin problemas** (0 silenced).
> - Migraciones `showmigrations` → **todas aplicadas** `[X]` (base de datos MySQL operativa).
> - El servidor de desarrollo levanta sin errores.

---

## 2. Stack tecnológico

- **Python** 3.10.11
- **Django** 5.2.17
- **MySQL** 8.0 + **mysqlclient** 2.2.8
- **python-dotenv** 1.2.3 (variables de entorno)
- **HTML5 / CSS3 / Bootstrap 5 / Bootstrap Icons / Chart.js** (vía CDN)
- **JavaScript** (interacción del sidebar)
- **Git / GitHub** (control de versiones)

---

## 3. Estructura del proyecto

```text
Capstone-SEMAXEL/
├── config/            # Configuración del proyecto Django (settings, urls, wsgi, asgi, demo_data)
├── accounts/          # Perfil de usuario y roles
├── sucursales/        # Sucursales
├── tecnicos/          # Técnicos y especialidades
├── tickets/           # Tickets, órdenes de trabajo, calificaciones, evidencias, historial
├── ofertas/           # Ofertas de trabajo para técnicos (marketplace)
├── sla/               # Políticas de Acuerdo de Nivel de Servicio (SLA)
├── mantenimiento/     # Mantenimiento preventivo (sin marcos aún)
├── dashboard/         # Dashboard con indicadores y reportes
├── templates/         # Plantillas globales y por app (20 archivos)
├── static/css/        # style.css (337 líneas)
├── media/             # Archivos subidos (vacío)
├── manage.py
├── requirements.txt
├── .env               # Variables de entorno (no versionado)
└── .gitignore
```

---

## 4. Historial de commits

| Fecha | Commit | Fase | Descripción |
|-------|--------|------|-------------|
| 20/08/2026 | `instalacion de django` | Inicial | Instalación de Django y configuración base. |
| 27/08/2026 | `FASE 1 estructura base` | Fase 1 | Reestructuración: 8 aplicaciones, settings, plantillas base, MySQL. |
| 27/08/2026 | `Fase 2.1` | Fase 2.1 | Modelos de datos completos con migraciones (935 líneas). |
| 02/09/2026 | `prototipado` | Fase 3 | Prototipo visual navegable: templates, urls, views, demo_data (2.721 líneas). |
| 02/09/2026 | `detalles` | Fase 3 | Ajustes visuales y actualización del informe. |

---

## 5. Lo que YA está hecho

### 5.1 Infraestructura y configuración
- Proyecto Django 5.2 bajo el paquete `config/` (settings, urls, wsgi, asgi).
- Conexión a **MySQL** mediante variables de entorno (`python-dotenv`), charset `utf8mb4`.
- Localización `es-cl` y zona horaria `America/Santiago`.
- Estáticos (`STATIC_URL/DIRS/ROOT`) y medios (`MEDIA_URL/ROOT`) configurados.
- `.gitignore` y `.env` fuera del control de versiones.
- **Verificado:** `manage.py check` sin errores; migraciones aplicadas a la BD.

### 5.2 Modelos de datos (Fase 2.1) — 6 de 8 apps con modelos
- **accounts::Usuario** — perfil 1-a-1 con `auth.User`, rol (ADMIN, GESTOR, ENCARGADO, TECNICO, GERENCIA) y teléfono.
- **sucursales::Sucursal** — datos de ubicación, encargados (M2M) y estado Activa/Inactiva.
- **tecnicos::Especialidad / Tecnico** — especialidades configurables; técnico 1-a-1 con usuario, documento único, M2M de especialidades y estados de disponibilidad.
- **tickets::Categoria / Ticket / EvidenciaTicket / OrdenTrabajo / Calificacion / TicketHistorial** — entidad central con número único, prioridad, estado, tipo, fechas y SLA; índices por estado/prioridad/sucursal; orden de trabajo 1-a-1 con ticket; calificación máxima una por orden; historial de cambios de estado.
- **ofertas::OfertaTicket** — marketplace 1-a-1 con ticket; técnico nulo al publicar; estados Disponible → Tomada → ... → Expirada y fechas.
- **sla::SLAPolicy** — política con tiempos máximos de respuesta/resolución por prioridad (prioridad única).
- Migraciones `0001_initial` / `0002_initial` **generadas y aplicadas** en todas las apps.
- **Pendiente de modelado:** `mantenimiento` y `dashboard` (archivos vacíos de placeholder).

### 5.3 Prototipo visual navegable (Fase 3) — con datos ficticios
- **20 templates HTML** + `base.html` con sidebar, topbar, breadcrumbs, mensajes flash, Bootstrap 5, Bootstrap Icons y Chart.js.
- **config/demo_data.py** — datos de demostración (sucursales, especialidades, categorías, tickets, historial, evidencias, ofertas, órdenes, técnicos y planes de mantenimiento).
- **Views funcionales (con demo_data):**
  - `dashboard`: indicadores, gráficos, login, perfil, reportes.
  - `tickets`: listado con búsqueda/filtros, detalle, crear, publicar oferta.
  - `tickets/ordenes_views`: listado y detalle de órdenes.
  - `ofertas`: disponibles, detalle y "tomar" (simulado).
  - `sucursales`: lista, formulario y detalle.
  - `tecnicos`: lista con filtro y detalle.
  - `mantenimiento`: lista de planes preventivos.
- **dashboard/templatetags/demo_extras.py** — filtros de etiquetas (estado, prioridad, disponibilidad).
- **static/css/style.css** (337 líneas) — estilos del prototipo (sidebar, tarjetas, badges por estado/prioridad).
- **Verificado:** todas las URLs resuelven; navegación completa funciona con datos ficticios.

### 5.4 Conexión al modelo real (Fase 4) — CRUD persistente con ORM
- **forms.py (ModelForm)** creados en `sucursales`, `tecnicos`, `tickets` y `ofertas`.
- **Vistas reescritas a ORM** en `dashboard`, `tickets` (lista/detalle/crear/publicar oferta/cambiar estado), `tickets/ordenes_views`, `ofertas`, `sucursales` y `tecnicos`.
- **CRUD persistente:** crear/editar sucursales y técnicos guardan en MySQL; creación de tickets genera número único (`TK-XXXXX`), registra el historial inicial y soporta evidencias multipart.
- **Cambio de estado** de tickets vía `TicketHistorial`; **toma de oferta** crea la `OrdenTrabajo`, asigna técnico y avanza los estados de ticket/oferta/orden de forma consistente.
- **admin.py** con todos los modelos registrados en `accounts`, `sucursales`, `tecnicos`, `tickets`, `ofertas` y `sla`.
- **Comando `python manage.py seed_demo`** — datos iniciales reales (usuarios con rol, 4 sucursales, 5 especialidades, 5 categorías, 4 políticas SLA, 9 tickets, 6 ofertas, 3 órdenes, 1 calificación + historial). Idempotente; todos los usuarios usan la contraseña `Semaxel2026!`.
- **Paginación** en listados (dash, tickets, órdenes, sucursales, técnicos) vía template `includes/paginacion.html`.
- **Dashboard real**: métricas calculadas sobre la BD y datos para gráficos Chart.js (por estado y por prioridad) mediante `json_script`.
- **Topbar y perfil dinámicos** con el usuario autenticado; `logout` funcional.
- **Verificado:** `manage.py check` sin problemas; `makemigrations --check` sin cambios (solo propiedades, sin migraciones); smoke test del cliente Django: 17 páginas en 200 y flujos POST (crear ticket, cambiar estado, tomar oferta, crear sucursal) en 302, con 0 fallos.

---

## 6. Lo que FALTA (diagnóstico por área)

### 6.1 Conexión al modelo real (lo más urgente)
- ✅ **Fase 4 completada**: todas las vistas principales usan el ORM; `config/demo_data.py` solo queda en `mantenimiento` (sin modelos aún, se aborda en Fase 7) y es candidato a eliminarse.
- ✅ **forms.py** creados (ModelForm) en `sucursales`, `tecnicos`, `tickets`, `ofertas`.
- ✅ **CRUD persistente**: sucursales, técnicos, tickets y cambio de estado guardan en MySQL.
- ✅ **Admin de Django** con todos los modelos registrados.
- ✅ **Datos de arranque**: comando `python manage.py seed_demo` (idempotente).
- ⚠️ Pendiente menor: fórmulas de especialidad/categoría todavía no tienen formulario propio de edición (se crean desde el admin).

### 6.2 Autenticación y permisos
- ❌ **Login solo visual**: `dashboard/views.login` redirige sin validar credenciales ni crear sesión. Además, ese nombre **oculta** la vista `login` de Django.
- ✅ Topbar y perfil **dinámicos** con el usuario autenticado y `logout` funcional.
- ❌ Ninguna vista exige `login_required` ni permisos por rol.
- ❌ El rol `Usuario.rol` existe en el modelo pero **no se aplica** en ninguna parte (sin decoradores, mixins ni asignación de grupos/permisos).
- ❌ Gestión de usuarios (crear/editar usuarios y asignar rol + sucursales encargadas) pendiente.

### 6.3 Lógica de negocio (ciclo de vida)
- ❌ **Transiciones de estado de ticket** no validadas (no hay máquina de estados).
- ❌ **TicketHistorial existe pero no se registra** nada en él.
- ❌ **Toma de oferta** no crea la `OrdenTrabajo` ni asigna técnico ni actualiza estados.
- ❌ **SLA sin cálculo**: `fecha_limite_sla` nunca se calcula a partir de `SLAPolicy`.
- ❌ **Órdenes de trabajo** (diagnóstico, costos, fechas, calificación) sin implementar la transición.
- ❌ **Evidencias**: `EvidenciaTicket` no se usa; no hay subida de archivos (carpeta `media/` vacía).
- ❌ **Vencimiento de ofertas** sin manejo (no hay contexto programado/`expiración`).

### 6.4 Mantenimiento preventivo y reportes
- ❌ **`mantenimiento` sin modelos**: los planes preventivos solo existen en `demo_data.PLANES_MANTENIMIENTO`.
- ✅ **Dashboard con métricas reales** de la BD, incluyendo datos para los gráficos Chart.js.
- ❌ **Reportes** parciales: la plantilla ya usa los indicadores globales calculados (`cumplimiento_sla`, `tickets_totales`, `calificacion_promedio`, `tecnicos_activos`), pero los gráficos dinámicos y reportes por sucursal/técnico/categoría quedan para la Fase 7.

### 6.5 Calidad y robustez
- ❌ **Sin tests** (los `tests.py` son placeholders), sin fixtures de prueba.
- ✅ Paginación en todos los listados; URLs de técnico/sucursal por `pk` (ya no frágiles).
- ❌ Sin manejo de errores personalizado (404/500), ni logging.
- ❌ `.env` no tiene `.env.example` versionado para replicar el entorno.
- ⚠️ Bootstrap/Chart.js se cargan por **CDN**: requiere internet (para producción conviene empaquetados localmente).

---

## 7. Roadmap: fases propuestas para seguir avanzando

Orden sugerido por **valor/riesgo** (del mayor impacto inmediato al refinamiento final).
Cada fase termina con un **entregable verificable** y un commit propio.

### Fase 4 — Conectar la interfaz al modelo real (CRUD persistente) ✅ Completada
**Objetivo:** reemplazar `demo_data` por consultas al ORM y formularios Django.
- Crear `forms.py` (ModelForm) en `sucursales`, `tecnicos`, `tickets`, `ofertas`.
- Reescribir **todas** las views para usar el ORM (`Ticket.objects.filter(...)`, `Q` para búsqueda).
- Implementar CRUD persistente: sucursales, especialidades, categorías, técnicos.
- Crear formulario de **creación de ticket** que guarde en BD, genere número único y registre el historial inicial.
- Registrar todos los modelos en `admin.py` de cada app.
- Crear comando `python manage.py seed_demo` (management command) o fixtures `*.json` con datos iniciales reales.
- Agregar paginación a los listados.
- **Criterio de salida:** los cambios hechos en la interfaz **persisten** en MySQL y se ven en listados/detalles y en el admin de Django.
- **Estado:** ✔ cumplido y verificado con smoke test completo (0 fallos).

### Fase 5 — Autenticación y permisos por rol 🔵 Prioridad alta
**Objetivo:** usuarios reales con acceso según rol.
- Login/logout con `django.contrib.auth`; renombrar `dashboard/views.login` para no ocultar la vista estándar.
- `@login_required` en las vistas de negocio y redirección correcta al login.
- Aplicar **roles**: decoradores/mixins por rol (ADMIN, GESTOR, ENCARGADO, TECNICO, GERENCIA), usar grupos o permisos de Django.
- Perfil real (datos del usuario autenticado) y topbar dinámica (quitar "Juan Pérez" hardcodeado).
- Gestión de usuarios (crear/editar usuarios y asignar rol + sucursales encargadas).
- **Criterio de salida:** un encargado solo ve sus sucursales, un técnico solo ofertas/órdenes, y un anónimo no puede entrar a ninguna sección.

### Fase 6 — Lógica de negocio del ciclo completo 🟠 Prioridad media
**Objetivo:** flujo ticket → oferta → orden → cierre con SLA y evidencias.
- Máquina de estados de **ticket** con transiciones válidas y registro automático en `TicketHistorial`.
- **Publicar oferta** desde un ticket (marcar ticket PUBLICADO / oferta DISPONIBLE con vencimiento).
- **Tomar oferta**: validar técnico elegible, crear `OrdenTrabajo`, asignar técnico, actualizar estados ticket/oferta/orden de forma consistente.
- Avance de **órdenes de trabajo** (asignada → en ejecución → resuelta → cerrada) con diagnóstico, fechas y costos.
- **Calificación** del técnico al cierre (max. 1 por orden).
- **SLA automático**: al crear un ticket, calcular `fecha_limite_sla` según `SLAPolicy` por prioridad; indicador de cumplimiento.
- Subida de **evidencias** (`EvidenciaTicket`) con validación de archivos.
- Lógica de **vencimiento** de ofertas (tarea programada o lazy-check al listar).
- **Criterio de salida:** se puede recorrer un ticket completo de principio a fin con persistencia y trazabilidad en historial.

### Fase 7 — Mantenimiento preventivo y reportes reales 🟡 Prioridad media
**Objetivo:** dar vida a `mantenimiento` y `dashboard`.
- Modelos de **mantenimiento preventivo**: plan (nombre, frecuencia, sucursal), programaciones/historial de ejecuciones.
- Generación automática de **tickets preventivos** desde los planes (tarea programada con Django-cron o Celery, o al abrir el dashboard).
- **Reportes reales** con agregaciones del ORM (`annotate`/`aggregate`): tickets por estado/prioridad/sucursal/categoría, cumplimiento SLA, costos por técnico/sucursal.
- Gráficos **Chart.js dinámicos** alimentados desde la BD (no hardcodeados).
- Dashboard con métricas reales.
- **Criterio de salida:** dashboard y reportes reflejan la BD; el mantenimiento preventivo genera tickets programados.

### Fase 8 — Calidad, robustez y despliegue 🟢 Cierre
**Objetivo:** dejar el sistema estable, testeado y desplegable.
- Tests unitarios e integración (modelos, flujos, permisos, SLA).
- Páginas de error 404/500, logging, manejo de excepciones.
- Seguridad: validaciones, `DEBUG=False`, `ALLOWED_HOSTS` de producción, secretos en `.env`, `collectstatic`.
- Empacar Bootstrap/Chart.js localmente (opcional, para operar sin internet).
- Documentación final: manual de usuario, `.env.example`, instrucciones de despliegue.
- **Criterio de salida:** `python manage.py test` en verde, checklist de seguridad aplicado y despliegue documentado.

---

## 8. Prioridad sugerida y esfuerzos relativos

| Fase | Esfuerzo | Impacto | Debería hacerse |
|------|----------|---------|-----------------|
| 4 · Conexión al ORM y CRUD | Alto | Muy alto | ✅ Completada |
| 5 · Autenticación y roles | Medio | Muy alto | Ahora |
| 6 · Ciclo de vida completo | Alto | Alto | Después de Fase 5 |
| 7 · Preventivo y reportes | Medio | Medio | Después de Fase 6 |
| 8 · Calidad y despliegue | Medio | Alto (soporte) | Al final |

**Recomendación:** la **Fase 4** (ORM conectado y CRUD persistente) ya está
completada y verificada. El siguiente paso es la **Fase 5 (autenticación y
roles)**, imprescindible para restringir el acceso por rol antes de la lógica
de negocio del ciclo completo (Fase 6).

---

## 9. Cómo ejecutar el proyecto

```bash
# 1. Crear y activar el entorno virtual (Windows PowerShell)
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables en .env (DB_NAME, DB_USER, DB_PASSWORD, SECRET_KEY, etc.)

# 4. Crear la base de datos MySQL (capstone_semaxel, utf8mb4)

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Crear superusuario (opcional)
python manage.py createsuperuser

# 7. Levantar el servidor
python manage.py runserver
```

Acceso: `http://127.0.0.1:8000/` · Admin: `http://127.0.0.1:8000/admin/`