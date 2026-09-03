# INFORME DE AVANCE — Sistema de Gestión de Mantenimiento de Infraestructura

**Proyecto:** Capstone-SEMAXEL
**Asignatura:** Proyecto de título de Ingeniería en Informática
**Fecha del informe:** 02/09/2026

---

## 1. Resumen general

Se está desarrollando una aplicación web para la gestión del mantenimiento de la
infraestructura física de sucursales. Permite administrar sucursales, técnicos,
especialidades, tickets de incidencias, ofertas de trabajo, órdenes de trabajo,
SLA y mantenimiento preventivo, e incluye un dashboard con indicadores.

El proyecto se basa en **Django 5.2** con **MySQL 8.0** y hasta el momento se ha
completado la **instalación del framework**, la **estructura base del proyecto**
y el **modelado del dominio de datos** (Fase 1 y Fase 2.1).

---

## 2. Stack tecnológico

- **Python** 3.10
- **Django** 5.2.17
- **MySQL** 8.0 + **mysqlclient** 2.2.8
- **python-dotenv** 1.2.3 (variables de entorno)
- **HTML5 / CSS3 / Bootstrap 5 / JavaScript / Chart.js** (frontend, planificado)
- **Git / GitHub** (control de versiones)

---

## 3. Estructura del proyecto

```text
Capstone-SEMAXEL/
├── config/            # Configuración del proyecto Django (settings, urls, wsgi, asgi)
├── accounts/          # Usuarios y roles
├── sucursales/        # Sucursales
├── tecnicos/          # Técnicos y especialidades
├── tickets/           # Tickets, órdenes de trabajo, calificaciones, evidencias
├── ofertas/           # Ofertas de trabajo para técnicos
├── sla/               # Políticas de Acuerdo de Nivel de Servicio (SLA)
├── mantenimiento/     # Mantenimiento preventivo
├── dashboard/         # Dashboard con indicadores
├── templates/         # Plantillas globales (base.html, home.html)
├── static/            # CSS, JS
├── media/             # Archivos subidos
├── manage.py
├── requirements.txt
├── .env               # Variables de entorno (no versionado)
└── .gitignore
```

---

## 4. Historial de commits y fases avanzadas

| Fecha | Commit | Fase | Descripción |
|-------|--------|------|-------------|
| 20/08/2026 | `instalacion de django` | Inicial | Instalación de Django y configuración base (`sistema_mantenimiento/`). |
| 27/08/2026 | `FASE 1 estructura base` | Fase 1 | Reestructuración del proyecto: creación de las 8 aplicaciones, settings, plantillas base y configuración MySQL. |
| 27/08/2026 | `Fase 2.1` | Fase 2.1 | Definición completa de los modelos de datos (935 líneas agregadas). |
| 02/09/2026 | `prototipado` | Fase 3 | Prototipo visual navegable: templates, urls, views y datos ficticios (2.721 líneas agregadas). |

---

## 5. Detalle por fase

### 5.1 Instalación de Django
- Instalación y configuración del framework Django.
- Archivos base del proyecto: `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`, `manage.py`.

### 5.2 Fase 1 — Estructura base
- Configuración del proyecto con el paquete **config/**.
- Creación de las aplicaciones del sistema:
  - `accounts`, `sucursales`, `tecnicos`, `tickets`, `ofertas`, `sla`, `mantenimiento`, `dashboard`.
- Configuración de la conexión a **MySQL** mediante variables de entorno (`python-dotenv`).
- Localización en español de Chile (`es-cl`) y zona horaria `America/Santiago`.
- Plantillas base: `templates/base.html` y `templates/home.html`.
- Hoja de estilos inicial: `static/css/style.css`.
- Documentación del proyecto en `README.md` y archivo `.gitignore`.
- Configuración de `MEDIA_ROOT` y `STATIC_ROOT`.

### 5.3 Fase 2.1 — Modelado del dominio de datos
Definición completa de los modelos de Django en cada aplicación, con sus
migraciones correspondientes.

#### `accounts` — Usuarios y roles
- **Usuario**: perfil que extiende `auth.User` (relación uno a uno) y agrega:
  - `rol`: ADMIN, GESTOR, ENCARGADO, TECNICO, GERENCIA.
  - `telefono`.

#### `sucursales` — Sucursales
- **Sucursal**: datos de identificación y ubicación (nombre, código único,
  dirección, comuna, ciudad, región, teléfono, correo), estados Activa/Inactiva
  y relación muchos a muchos con los **encargados** (usuarios).

#### `tecnicos` — Técnicos y especialidades
- **Especialidad**: catálogo configurable (no hardcodeado), con nombre, descripción y estado activo.
- **Tecnico**: relacionado uno a uno con un usuario, con documento único, teléfono,
  descripción, muchas especialidades (M2M), estados de disponibilidad
  (Disponible/Ocupado/No disponible/Inactivo).

#### `tickets` — Entidad central del sistema
- **Categoria**: categoría de mantenimiento vinculable opcionalmente a una especialidad.
- **Ticket**: entidad central; número único, sucursal, creador, categoría,
  prioridad (Baja/Media/Alta/Crítica), estado (Abierto → … → Cerrado/Cancelado),
  tipo (Incidencia/Preventivo), fechas (creación, SLA, cierre), con índices de
  búsqueda por estado, prioridad y sucursal.
- **EvidenciaTicket**: archivos/evidencias por ticket.
- **OrdenTrabajo**: generada al tomar un técnico la oferta; estados (Asignada → …),
  diagnóstico, trabajo realizado, costos estimado/final y fechas.
- **Calificacion**: puntuación de 1 a 5 del encargado al técnico (máx. una por orden).
- **TicketHistorial**: registro del cambio de estados de un ticket (usuario, estado anterior/nuevo, comentario, fecha).

#### `ofertas` — Marketplace de trabajo
- **OfertaTicket**: oferta asociada a un ticket (uno a uno); técnico nulo al
  publicarse (estado Disponible) y se registra al ser tomada; estados
  (Disponible/Tomada/En ejecución/Completada/Cancelada/Expirada) y fechas de
  publicación, vencimiento, respuesta y toma.

#### `sla` — Acuerdo de Nivel de Servicio
- **SLAPolicy**: política SLA con tiempos máximos de respuesta y resolución por
  prioridad, con restricción de prioridad única. El cálculo automático de
  vencimientos no está implementado aún (fase posterior).

#### `mantenimiento` y `dashboard`
- Aplicaciones creadas como base (modelos a definir en fases posteriores).

### 5.4 Fase 3 — Prototipado visual navegable
Se crea y configura un prototipo funcional de la interfaz con **templates**,
**urls** y **views**, alimentado por **datos ficticios** (`config/demo_data.py`)
para visualizar el diseño y la navegación sin consultas reales a la base de
datos.

#### Rutas y views
- **config/urls.py**: rutas principales (dashboard, login, perfil, reportes) y
  `include` de las URLs de cada app (tickets, ofertas, órdenes, sucursales,
  técnicos, mantenimiento). Se sirven los medios en modo DEBUG.
- **config/demo_data.py**: conjunto de datos de demostración (sucursales,
  especialidades, categorías, tickets, historial, evidencias, ofertas, órdenes,
  técnicos y planes de mantenimiento) con funciones auxiliares de búsqueda.
- **dashboard/views.py**: dashboard con indicadores (tickets abiertos/críticos/
  en ejecución/resueltos, ofertas, órdenes y cumplimiento SLA) y pantallas de
  login, perfil y reportes (datos ficticios, sin autenticación real).
- **tickets/views.py**: listado con buscador y filtros por estado/prioridad/
  categoría, detalle con historial y evidencias, formulario de creación y
  publicación de oferta.
- **ofertas/views.py**: ofertas disponibles y detalle con opción de tomarlas.
- **tickets/ordenes_views.py**: listado de órdenes de trabajo con filtros y
  detalle de cada orden.
- **sucursales/views.py**: listado, formulario y detalle de sucursales.
- **tecnicos/views.py**: listado con filtro por estado y detalle.
- **mantenimiento/views.py**: listado de planes de mantenimiento preventivo.

#### Templates (33 archivos)
- **base.html**: layout con sidebar navegable, topbar con perfil de usuario,
  breadcrumbs, mensajes/flash y carga de Bootstrap 5, Bootstrap Icons y Chart.js.
- **dashboard/**: dashboard.html (indicadores, gráficos de barra, dona y SLA con
  Chart.js, actividad reciente), login.html, perfil.html y reportes.html.
- **tickets/**: lista, detalle, crear, publicar_oferta, ordenes_lista y orden_detalle.
- **ofertas/**: disponibles y detalle.
- **sucursales/**: lista, detalle y form.
- **tecnicos/**: lista y detalle.
- **mantenimiento/**: lista.

#### Extras
- **dashboard/templatetags/demo_extras.py**: filtros personalizados para etiquetas
  legibles de estado, prioridad y disponibilidad, y tag para obtener el nombre
  de un archivo.
- **static/css/style.css**: ampliado (+383 líneas) con estilos de la aplicación
  (sidebar, tarjetas de indicadores, badges por color de estado/prioridad, etc.).

---

## 6. Estado actual y pendientes

✅ **Completado:**
- Instalación de Django.
- Estructura base del proyecto y configuración MySQL.
- Modelos de datos de todas las aplicaciones principales con migraciones.
- **Prototipo visual navegable** de todas las secciones del sistema con datos
  de demostración (Fase 3).

⏳ **Pendiente (próximas fases):**
- **Conectar las vistas al modelo de datos real** (reemplazar `demo_data` por
  consultas al ORM y formularios Django).
- CRUD persistente de sucursales, técnicos, especialidades y categorías.
- Lógica de negocio real: creación de tickets, publicación/toma de ofertas.
- Cálculo automático de vencimientos de SLA.
- Sistema de autenticación y permisos por rol (actualmente el login es visual).
- Reportes con datos reales y gráficos dinámicos.
- Panel de administración avanzado y vistas de usuario definitivas.

---

## 7. Cómo ejecutar el proyecto

```bash
# 1. Crear y activar el entorno virtual (Windows PowerShell)
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables en .env (DB_NAME, DB_USER, DB_PASSWORD, SECRET_KEY, etc.)

# 4. Crear la base de datos MySQL (capstone_semaxel, utf8mb4)

# 5. Ejecutar migraciones
python manage.py makemigrations
python manage.py migrate

# 6. Crear superusuario (opcional)
python manage.py createsuperuser

# 7. Levantar el servidor
python manage.py runserver
```

Acceso: `http://127.0.0.1:8000/` · Admin: `http://127.0.0.1:8000/admin/`
