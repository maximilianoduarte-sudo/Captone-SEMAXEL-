# Stack tecnológico y arquitectura

Documento que describe con qué está construido el sistema SEMAXEL, cómo está
organizado el código y cómo se relacionan sus módulos. Refleja el estado real
del repositorio.

## 1. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.10 |
| Framework web | Django 5.2 |
| Base de datos | MySQL 8.0 (`mysqlclient`) |
| Acceso a datos | Django ORM |
| Configuración | `python-dotenv` (`.env`, no versionado) |
| Frontend | HTML5, CSS3, Bootstrap 5, Bootstrap Icons |
| Gráficos | Chart.js |
| JavaScript | Interacción del sidebar y componentes |
| Control de versiones | Git / GitHub |

Nota: Bootstrap, Bootstrap Icons y Chart.js se cargan por **CDN**, por lo que la
interfaz requiere conexión a internet (para producción conviene empaquetarlos
localmente).

## 2. Estructura del proyecto

```text
Capstone-SEMAXEL/
├── config/            # Configuración Django (settings, urls, wsgi, asgi)
├── accounts/          # Usuario (perfil, rol, empresa), roles y permisos
├── empresas/          # Empresas (aislamiento multiempresa)
├── sucursales/        # Sucursales y encargados asignados
├── tecnicos/          # Técnicos y especialidades
├── tickets/           # Tickets, órdenes de trabajo, calificaciones, historial
├── ofertas/           # Ofertas de trabajo para técnicos (marketplace)
├── sla/               # Políticas de SLA
├── mantenimiento/     # Mantenimiento preventivo (planes y programaciones)
├── dashboard/         # Dashboard, reportes y login/perfil
├── templates/         # Plantillas globales y por app
├── static/css/        # style.css
├── media/             # Archivos subidos (evidencias)
├── manage.py
├── requirements.txt
├── .env               # Variables de entorno (no versionado)
└── .gitignore
```

## 3. Configuración (`config/`)

- **settings.py**: base de datos MySQL por variables de entorno (`DB_NAME`,
  `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`), `SECRET_KEY` **obligatoria**
  (si falta, la aplicación no arranca), `DEBUG` por entorno, `ALLOWED_HOSTS`,
  localización `es-cl`, zona horaria `America/Santiago`, estáticos y medios.
- **urls.py**: enruta el admin, login/logout/registro/perfil, usuarios, reportes
  y las apps (`tickets`, `ofertas`, `ordenes`, `sucursales`, `empresas`,
  `tecnicos`, `mantenimiento`). Define `handler403`.
- **Validación de contraseñas**: longitud mínima 8, similitud con datos del
  usuario, contraseñas comunes, solo numéricas y un validador propio de
  complejidad (`accounts.validators.ComplejidadPasswordValidator`).

## 4. Aplicaciones y responsabilidad

| App | Responsabilidad | Modelos principales |
|---|---|---|
| `accounts` | Perfil de usuario (rol, empresa, teléfono), permisos y validadores | `Usuario` |
| `empresas` | Empresa cliente (unidad de aislamiento lógico) | `Empresa` |
| `sucursales` | Locales de la empresa y encargados asignados | `Sucursal` |
| `tecnicos` | Técnicos y especialidades | `Especialidad`, `Tecnico` |
| `tickets` | Entidad central del ciclo y su ejecución | `Categoria`, `Ticket`, `EvidenciaTicket`, `OrdenTrabajo`, `Calificacion`, `TicketHistorial` |
| `ofertas` | Marketplace: publicación y toma de ofertas | `OfertaTicket` |
| `sla` | Políticas de tiempo por prioridad (globales o por empresa) | `SLAPolicy` |
| `mantenimiento` | Planes preventivos y sus programaciones | `PlanMantenimiento`, `ProgramacionMantenimiento` |
| `dashboard` | Vistas de indicadores, reportes, login y perfil (sin modelos) | — |

## 5. Modelo de datos (relaciones clave)

- `Usuario` es un perfil **1‑a‑1** con `auth.User`; guarda `rol` y `empresa`
  (nula para técnicos del marketplace).
- `Empresa` **1‑a‑N** `Sucursal` (sucursal con empresa obligatoria).
- `Sucursal` **M‑a‑M** `auth.User` (encargados asignados).
- `Tecnico` es **1‑a‑1** con `auth.User` y **M‑a‑M** con `Especialidad`.
- `Ticket` pertenece a una `Sucursal`, una `Categoria` y un `creador`;
  **1‑a‑1** con `OfertaTicket` y **1‑a‑1** con `OrdenTrabajo`.
- `OrdenTrabajo` **1‑a‑N** `Calificacion` es en realidad **1‑a‑1** (una
  calificación por orden).
- `TicketHistorial` **1‑a‑N** con `Ticket`.
- `SLAPolicy` es única por `(empresa, prioridad)`; `empresa` nula = política
  global de respaldo.
- `PlanMantenimiento` pertenece a `Sucursal` + `Categoria`;
  `ProgramacionMantenimiento` vincula plan con el ticket generado.

## 6. Capas y patrón de organización

1. **Modelos** (`models.py`): estructuran el dominio e incluyen las **máquinas de
   estado** de `Ticket` y `OrdenTrabajo` (transiciones válidas como clase).
2. **Permisos centralizados** (`accounts/roles.py`): decorador `rol_requerido`,
   helpers de rol/empresa, querysets de visibilidad (`empresas_visibles`,
   `sucursales_visibles`, `tickets_visibles`, `ofertas_visibles`,
   `ordenes_visibles`) y predicados de acceso (`puede_ver_*`,
   `puede_gestionar_ticket`). Es el único punto donde vive el aislamiento por
   empresa/sucursal.
3. **Vistas** (`views.py`): `@login_required` + `@rol_requerido(...)` y validación
   de alcance por objeto (403 si corresponde). El backend nunca confía solo en
   la interfaz.
4. **Formularios** (`forms.py`): `ModelForm` con querysets acotados al alcance
   del usuario (p. ej. `TicketForm` limita las sucursales visibles).
5. **Servicios** (`services.py`): lógica reutilizable fuera de las vistas
   (`ofertas.expirar_ofertas_vencidas`,
   `mantenimiento.generar_tickets_preventivos`).
6. **Plantillas** (`templates/`): una base común con sidebar dinámico por rol.

## 7. Aislamiento multiempresa

- Una **única base de datos MySQL** con separación **lógica** por empresa.
- Todo el acceso se filtra por la empresa del usuario; el ENCARGADO además se
  limita a sus **sucursales asignadas**.
- El **superusuario** conserva acceso global.
- El **admin de Django** usa `SEMAXELAdminSite`, que impide el ingreso del rol
  ENCARGADO.
- Los técnicos son un **recurso global del marketplace**: no pertenecen a una
  empresa y ven ofertas disponibles de cualquier empresa.

## 8. Flujos principales

- **Incidencia:** alta de ticket (numeración por empresa `<codigo>-NNNNN`),
  cálculo de `fecha_limite_sla`, historial inicial y evidencias.
- **Oferta:** publicación de la oferta (ticket → PUBLICADO) para técnicos.
- **Ejecución:** el técnico toma la oferta (valida especialidad), se crea la
  orden (ASIGNADA) y el ticket pasa a EN_EJECUCION.
- **Cierre:** avance de la orden, sincronización del ticket, liberación del
  técnico y calificación al cerrar.
- **Preventivo:** los planes vencidos generan tickets PREVENTIVO automáticamente.

## 9. Comandos de utilidad

```bash
python manage.py check              # Verificación de configuración
python manage.py runserver          # Servidor de desarrollo
python manage.py seed_demo          # Datos iniciales (idempotente)
python manage.py expirar_ofertas    # Marca ofertas vencidas
python manage.py generar_preventivos # Genera tickets preventivos
python manage.py test               # Suite de pruebas
```

## 10. Seguridad y secretos

- `SECRET_KEY` y credenciales de BD viven en `.env` (fuera del repositorio).
- El registro público nunca permite elegir rol ni otorga privilegios de
  staff/superusuario.
- Se recomienda versionar un `.env.example` (hoy no existe) para replicar el
  entorno sin exponer secretos.
