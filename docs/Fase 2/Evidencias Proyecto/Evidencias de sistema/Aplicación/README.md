# Evidencia de sistema: aplicación

El código fuente de la aplicación SEMAXEL está en la raíz de este mismo
repositorio. No se copia aquí para no duplicarlo; el historial de commits del
repositorio es la evidencia del desarrollo.

## Dónde está cada parte

| Módulo | Carpeta | Contenido |
|---|---|---|
| Configuración | `config/` | Ajustes de Django, URLs y tareas |
| Usuarios y roles | `accounts/` | Autenticación, 5 roles y control de acceso (`roles.py`) |
| Empresas | `empresas/` | Empresas clientes (multi-empresa) |
| Sucursales | `sucursales/` | Sucursales y encargados |
| Técnicos | `tecnicos/` | Técnicos, especialidades y disponibilidad |
| Tickets | `tickets/` | Tickets, órdenes de trabajo, historial y calificaciones |
| Ofertas | `ofertas/` | Publicación y toma de ofertas de trabajo |
| SLA | `sla/` | Políticas SLA y cálculo de la fecha límite |
| Mantenimiento | `mantenimiento/` | Planes de mantenimiento preventivo |
| Dashboard | `dashboard/` | Indicadores y reportes |
| Interfaz | `templates/`, `static/` | Plantillas HTML, Bootstrap 5 y Chart.js |

## Pruebas automatizadas

```bash
python manage.py test
```

Resultado al 22/10/2026 (commit `dcdb638`): **97 pruebas, todas aprobadas**.

## Video

`Prototipo capstone.mp4`: video del prototipo del sistema.

La instalación y ejecución se describen en el `README.md` de la raíz del
repositorio.
