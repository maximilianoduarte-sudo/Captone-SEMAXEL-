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
con datos de demostración, la **Fase 4 (ORM y CRUD persistente)** y la
**Fase 5 (autenticación y permisos por rol)**: login/logout reales con
`django.contrib.auth`, todas las vistas protegidas con `@login_required`,
acceso controlado por rol (decorador `rol_requerido`), alcance por rol
(encargado ve solo sus sucursales, técnico solo sus órdenes), gestión de
usuarios completa para ADMIN/GESTOR y sidebar dinámico. El siguiente hito es la
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
├── mantenimiento/     # Mantenimiento preventivo (planes y programaciones)
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
- **sla::SLAPolicy** — política con tiempos máximos de respuesta/resolución por prioridad; **por empresa** (específica) con política global de respaldo (única por empresa+prioridad).
- Migraciones `0001_initial` / `0002_initial` **generadas y aplicadas** en todas las apps.
- **mantenimiento::PlanMantenimiento / ProgramacionMantenimiento** — planes preventivos por sucursal con frecuencia, próxima ejecución y programaciones vinculadas a sus tickets generados; `dashboard` sin modelos (solo vistas).

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

### 5.5 Autenticación y permisos por rol (Fase 5)
- **Login/logout reales** con `django.contrib.auth` (`accounts/views.LoginView` + `LogoutView` propio): credenciales validadas, error mostrado, anónimos redirigidos a `/login/`.
- **`@login_required`** en todas las vistas de negocio (dashboard, reportes, tickets, órdenes, ofertas, sucursales, técnicos, mantenimiento, perfil).
- **`accounts/roles.py`**: decorador `rol_requerido(*roles)`, helper `rol_usuario(user)` y `sucursales_visibles(user)` (alcance por rol).
  - ADMIN/GESTOR: acceso total + gestión de usuarios.
  - ENCARGADO: crea/cambia tickets y ve solo sus sucursales/tickets/órdenes.
  - TECNICO: ofertas (publicadas y tomar), sus órdenes, tickets en lectura y perfil.
  - GERENCIA: lectura global (tickets, órdenes, sucursales, reportes, mantenimiento).
- **Gestión de usuarios** (`accounts/urls.py`): listado, alta y edición (rol, teléfono, contraseña opcional, activo) para ADMIN/GESTOR.
- **Perfil editable** del usuario autenticado (nombre, apellido, correo, teléfono).
- **Sidebar por rol** y página `403.html` personalizada (`handler403`).
- **Verificado:** smoke test de 43 casos (login válido/inválido, anónimo→302, alcance de encargado/técnico, 403 por rol, creación de usuario, logout) con 0 fallos; BD restaurada al estado demo.

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
- ✅ **Login/logout reales** con `django.contrib.auth` (`LoginView` en `accounts`), ya no hay vista que oculte la estándar.
- ✅ **`@login_required`** en todas las vistas de negocio; un anónimo es redirigido a `/login/`.
- ✅ **Permisos por rol** con el decorador `rol_requerido(*roles)` (`accounts/roles.py`):
  - ADMIN: gestión global (empresas, sucursales, tickets, técnicos, usuarios, ofertas, reportes).
  - GESTOR: trabaja solo con su Empresa y sus sucursales (tickets, publicar/ofrecer trabajos), ve sus órdenes, mantenimiento y reportes; **no** administra usuarios ni técnicos globalmente ni toma ofertas.
  - ENCARGADO: crea/cambia tickets, ve sus sucursales y sus tickets, ofertas y órdenes.
  - TECNICO: accede directo a **Ofertas** (tomar), sus órdenes, tickets de su trabajo y perfil; **sin** dashboard ni listado general de tickets/sucursales/empresas.
  - GERENCIA: lectura global (tickets, órdenes, sucursales, reportes, mantenimiento) y su empresa.
- ✅ **Alcance por rol**: `sucursales_visibles()` filtra sucursales/tickets/órdenes (encargado solo las suyas; técnico solo sus órdenes; gestor solo su empresa).
- ✅ **Sidebar dinámico** por rol y URL por rol (el menú y las vistas quedan protegidos según rol, no solo ocultos).
- ✅ **Perfil real** del usuario autenticado, editable (nombre, apellido, correo, teléfono) y topbar dinámica.
- ✅ **Gestión de usuarios**: listar, crear y editar usuarios (rol, teléfono, contraseña, activo) restringida a **ADMIN**; página de error **403** personalizada (el enlace "volver al inicio" apunta a Ofertas para TECNICO).
- ✅ Al crear/editar un usuario con rol **TECNICO** se genera automáticamente su perfil de técnico (`Tecnico`); si un usuario TECNICO no tiene ese perfil, la toma de oferta lo advierte y no asigna la orden a otro técnico.
- ✅ **Registro público** (`/registro/`, `/registro/gestor/`, `/registro/tecnico/`): una empresa se registra con su usuario **GESTOR** (crea la Empresa activa asociada) y un técnico se registra como **TECNICO** creando su perfil de técnico (con especialidades opcionales). **El registro nunca permite elegir rol ni otorga privilegios de ADMIN/staff/superusuario**; duplicados (usuario, RUT, código) se rechazan y un usuario ya autenticado no puede volver a registrarse.
- ✅ **Badges de estado** (`static/css/style.css`): corregido el estado **Resuelta** de las órdenes (texto/borde blanco sobre blanco) y completados los estados faltantes del mismo sistema (CERRADA, CANCELADA y DISPONIBLE/TOMADA/COMPLETADA/EXPIRADA de ofertas) con contraste suficiente; se mantienen los demás estados.
- ⚠️ Pendiente opcional: roles implementados a nivel de app (no con grupos/permisos de Django); suficiente para el alcance, grupos se pueden adoptar en la Fase 8.

### 6.3 Lógica de negocio (ciclo de vida)
- ✅ **TicketHistorial** ya se registra en la creación, cambio de estado y toma de oferta (desde Fase 4).
- ✅ **Toma de oferta** ya crea la `OrdenTrabajo`, asigna técnico y actualiza estados de forma consistente (Fase 4/5).
- ✅ **Transiciones de estado de ticket validadas** (máquina de estados en `Ticket.TRANSICIONES_VALIDAS` + `CambiarEstadoForm`, `publicar_oferta` y `tomar`): destino terminal CERRADO/CANCELADO no admite más cambios.
- ✅ **SLA automático**: `fecha_limite_sla` se calcula al crear un ticket según la política efectiva (`SLAPolicy.obtener`: específica de la empresa o global de respaldo); el cumplimiento en dashboard/reportes mide tickets cerrados/resueltos dentro del plazo.
- ✅ **Órdenes de trabajo con ciclo completo**: máquina de estados (Asignada → En ejecución → Resuelta → Cerrada, o Cancelada), captura de diagnóstico, trabajo realizado, observaciones, costos estimado/final y fechas (inicio/fin); sincroniza ticket (estado + historial), libera automáticamente al técnico si no tiene otras órdenes activas y registra la **calificación** (1 a 5, una por orden) al cerrar. El técnico solo ejecuta su propia orden (no puede cerrar/cancelar); estados terminales no admiten más cambios.
- ⚠️ **Evidencias**: la creación de tickets ya acepta archivos multipart, pero sin validación de tipos/tamaño.
- ✅ **Vencimiento de ofertas**: servicio `expirar_ofertas_vencidas` (lazy-check en el listado/detalle y en el dashboard + comando `python manage.py expirar_ofertas`) marca EXPIRADA las ofertas vencidas y devuelve el ticket PUBLICADO a EN_REVISION con registro en el histórico; tomar una oferta vencida no crea la orden.

### 6.4 Mantenimiento preventivo y reportes
- ✅ **Modelos de mantenimiento preventivo**: `PlanMantenimiento` (sucursal, categoría, frecuencia, próxima ejecución, activo) y `ProgramacionMantenimiento` (historial y ticket generado por ejecución).
- ✅ **Generación automática de tickets preventivos** desde los planes vencidos: servicio `generar_tickets_preventivos`, comando `python manage.py generar_preventivos` y acción "Generar preventivos" desde la vista (idempotente: no duplica preventivos abiertos; el ticket hereda el SLA de la empresa automáticamente al crearse).
- ✅ **Reportes reales** con agregaciones del ORM: tickets por sucursal, por categoría, órdenes por técnico, por estado y por prioridad; cumplimiento SLA y calificación promedio.
- ✅ **Gráficos Chart.js dinámicos** alimentados desde la BD (por sucursal, categoría, técnico, estado y prioridad).
- ✅ Dashboard con métricas reales.

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

### Fase 5 — Autenticación y permisos por rol ✅ Completada
**Objetivo:** usuarios reales con acceso según rol.
- Login/logout con `django.contrib.auth`; renombrar `dashboard/views.login` para no ocultar la vista estándar.
- `@login_required` en las vistas de negocio y redirección correcta al login.
- Aplicar **roles**: decoradores/mixins por rol (ADMIN, GESTOR, ENCARGADO, TECNICO, GERENCIA), usar grupos o permisos de Django.
- Perfil real (datos del usuario autenticado) y topbar dinámica (quitar "Juan Pérez" hardcodeado).
- Gestión de usuarios (crear/editar usuarios y asignar rol + sucursales encargadas).
- **Criterio de salida:** un encargado solo ve sus sucursales, un técnico solo ofertas/órdenes, y un anónimo no puede entrar a ninguna sección.
- **Estado:** ✔ cumplido y verificado con smoke test de 43 casos (respuestas 200/302/403 esperadas, login inválido con error, alcance por rol, gestión de usuarios; 0 fallos).

### Fase 6 — Lógica de negocio del ciclo completo ✅ Completada
**Objetivo:** flujo ticket → oferta → orden → cierre con SLA y evidencias.
- ✅ **Máquina de estados de ticket** con transiciones válidas y registro automático en `TicketHistorial` (Cerrado/Cancelado terminales).
- ✅ **Publicar oferta** desde un ticket (marcar ticket PUBLICADO / oferta DISPONIBLE con vencimiento).
- ✅ **Tomar oferta**: validar técnico elegible, crear `OrdenTrabajo`, asignar técnico, actualizar estados ticket/oferta/orden de forma consistente.
- ✅ Avance de **órdenes de trabajo** (asignada → en ejecución → resuelta → cerrada) con diagnóstico, fechas y costos.
- ✅ **Calificación** del técnico al cierre (max. 1 por orden).
- ✅ **SLA automático**: al crear un ticket se calcula `fecha_limite_sla` según `SLAPolicy` efectiva de la empresa (o global) y existe indicador de cumplimiento real.
- ⚠️ Subida de **evidencias** (`EvidenciaTicket`) con validación de archivos (pendiente validación de tipos/tamaño).
- ✅ Lógica de **vencimiento** de ofertas (lazy-check al listar/detalle/dashboard + comando `expirar_ofertas`).
- **Criterio de salida:** se puede recorrer un ticket completo de principio a fin con persistencia y trazabilidad en historial.
- **Estado:** ✔ cumplido y verificado con test integral de 38 casos (transiciones de orden con permisos, sincronización ticket/técnico/calificación, expiración de ofertas, alcance multi-empresa; 0 fallos).

### Fase 7 — Mantenimiento preventivo y reportes reales ✅ Completada
**Objetivo:** dar vida a `mantenimiento` y `dashboard`.
- ✅ Modelos de **mantenimiento preventivo**: plan (nombre, frecuencia, sucursal), programaciones/historial de ejecuciones.
- ✅ Generación automática de **tickets preventivos** desde los planes (comando `generar_preventivos`, botón en la vista y generación idempotente integrada al seed).
- ✅ **Reportes reales** con agregaciones del ORM (`annotate`/`aggregate`): tickets por estado/prioridad/sucursal/categoría, órdenes por técnico, cumplimiento SLA y calificación promedio.
- ✅ Gráficos **Chart.js dinámicos** alimentados desde la BD (no hardcodeados).
- ✅ Dashboard con métricas reales.
- ✅ **Criterio de salida:** dashboard y reportes reflejan la BD; el mantenimiento preventivo genera tickets programados.

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
| 5 · Autenticación y roles | Medio | Muy alto | ✅ Completada |
| 6 · Ciclo de vida completo | Alto | Alto | ✅ Completada |
| 7 · Preventivo y reportes | Medio | Medio | ✅ Completada |
| 8 · Calidad y despliegue | Medio | Alto (soporte) | Al final |

**Recomendación:** con la **Fase 4** (ORM), **Fase 5** (autenticación y
roles), **Fase 6** (lógica de negocio del ciclo completo: transiciones de
ticket, SLA automático, ciclo completo de órdenes con calificación y
vencimiento de ofertas) y **Fase 7** (reportes detallados y mantenimiento
preventivo) completadas y verificadas, el siguiente paso es la **Fase 8
(calidad, robustez y despliegue)**: suite de tests, errores personalizados,
seguridad y documentación final.

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

Después de `python manage.py seed_demo`, los usuarios demo usan la contraseña
`Semaxel2026!` (`admin`, `gestor`, `jperez` = ENCARGADO, `cdiaz`/`atorres`/
`lfernandez` = TECNICO).