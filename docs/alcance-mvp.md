# Alcance del MVP y funcionalidades fuera de la primera versión

Este documento delimita de forma explícita qué se compromete a implementar y
probar el proyecto (MVP) y qué queda fuera de esta primera versión. El criterio
de corte es **"implementable y demostrable"**: solo se declara dentro del MVP lo
que existe y funciona hoy en el sistema.

## 1. Objetivo del MVP

Centralizar el ciclo de vida del mantenimiento (correctivo y preventivo) en un
entorno multiempresa y multisucursal, permitiendo **reportar incidencias,
publicarlas como ofertas, asignar y ejecutar órdenes de trabajo, controlar
tiempos por SLA, programar mantenimiento preventivo y visualizar indicadores
gerenciales**.

## 2. Descripción honesta de la solución

La solución implementada es una **aplicación web multiusuario y multiempresa
(SaaS multi-tenant) y responsiva**. No es una PWA en sentido estricto: no
incluye `manifest`, *service worker*, funcionamiento offline ni notificaciones
push. Por lo tanto, **PWA pasa a ser alcance futuro** y no debe comprometerse en
el MVP (ver sección 4).

## 3. Funcionalidades incluidas en el MVP (implementadas)

### 3.1 Autenticación, roles y permisos
- Inicio/cierre de sesión y registro de cuentas (empresa gestora, técnico y
  encargado).
- Cinco roles con responsabilidades diferenciadas: Administrador, Gestor,
  Encargado de local, Gerencia y Técnico.
- Control de acceso por rol **y** por alcance (empresa/sucursal); admin de
  Django con alcance restringido.
- Perfil de usuario, especialidades del técnico y gestión de su disponibilidad.

### 3.2 Estructura organizacional
- **Empresas** (aislamiento de datos por empresa) y **sucursales** (estado
  activa/inactiva) con su indicadores.
- **Categorías** de mantenimiento configurables, vinculables a una especialidad.

### 3.3 Gestión de técnicos
- Alta de técnicos, **especialidades**, estado operativo y calificaciones
  recibidas.

### 3.4 Reporte de incidencias (tickets)
- Creación de tickets con numeración por empresa, categoría, prioridad,
  descripción, información adicional y **evidencias** (archivos adjuntos).
- **Máquina de estados** del ticket e **historial** de cambios (quién, de qué
  estado a cuál y cuándo).

### 3.5 Asignación por marketplace de ofertas
- Publicación de una **oferta** a partir de un ticket.
- **Expiración automática** de ofertas vencidas.
- **Toma de la oferta por el técnico**, validando coincidencia de especialidad
  (asignación semi-automática basada en oferta + autoselección).

### 3.6 Órdenes de trabajo
- Generación de la orden al tomar la oferta y **ejecución** del trabajo
  (diagnóstico, trabajo realizado, observaciones, costo estimado y final).
- **Cierre/cancelación** de órdenes y **calificación** del técnico al cerrar.
- Sincronización automática del estado del ticket y de la disponibilidad del
  técnico.

### 3.7 SLA
- **Políticas de SLA** globales y por empresa, según prioridad (tiempos máximos
  de respuesta y resolución).
- Cálculo de la **fecha límite** del ticket y del **porcentaje de cumplimiento**.

### 3.8 Mantenimiento preventivo
- **Planes** por sucursal con frecuencia configurable y **programaciones** de
  ejecución.
- **Generación automática de tickets preventivos** cuando vence la fecha
  programada.
- Nota de alcance: la programación preventiva se presenta como listado de planes
  y programaciones; **no incluye una vista de calendario visual** (queda como
  alcance futuro, sección 4).

### 3.9 Dashboard gerencial y reportes
- **Dashboard** con indicadores (abiertos, críticos, en ejecución, resueltos,
  ofertas disponibles, órdenes y cumplimiento de SLA) y gráficos.
- **Reportes** por sucursal, categoría y técnico, con calificación promedio y
  técnicos activos, según el alcance del rol.

## 4. Funcionalidades fuera del MVP (alcance futuro)

| Funcionalidad | Motivo por el que queda fuera |
|---|---|
| PWA real (manifest, service worker, modo offline, push) | No implementada; la versión actual es web responsiva. |
| Notificaciones y recordatorios (email, push, in-app) | No implementadas. |
| Mensajería/chat entre encargado y técnico | No implementada. |
| Exportación de reportes (PDF, Excel, CSV) y envíos programados | No implementada. |
| Vista de calendario visual del mantenimiento preventivo | Hoy solo existen planes y programaciones en listado. |
| Motor de asignación automática/óptima de técnicos | Hoy la asignación es por oferta y autoselección del técnico. |
| Firma digital, geolocalización y check-in de evidencias | No implementada. |
| Gestión de inventario, repuestos y proveedores | Fuera del núcleo del ciclo de vida. |
| Facturación, pasarela de pago y multas por incumplimiento de SLA | Fuera del alcance operativo. |
| Integraciones (ERP, Google Calendar, SSO/MFA) | Fuera del alcance. |
| App móvil nativa | La web responsiva cubre la necesidad mínima. |
| Analítica avanzada / IA predictiva | Requiere datos y esfuerzo adicional. |
| Auditoría completa y permisos a nivel de campo / multi-idioma | Fuera del alcance. |

## 5. Criterios de éxito (definición de terminado)

El MVP se considera logrado cuando, en una demostración real y con datos
persistidos en la base de datos, se puede:

1. Iniciar sesión con cada rol y comprobar que **ve y opera solo lo que le
   corresponde** según empresa/sucursal.
2. **Registrar un ticket** con su prioridad y evidencia (con número asignado).
3. **Publicar la oferta** del ticket y ver su **expiración automática**.
4. Que un **técnico con la especialidad** correcta **tome la oferta** y ejecute
   la **orden de trabajo** hasta el cierre, con **calificación**.
5. Verificar el **cálculo del SLA** y el **historial** de estados del ticket.
6. **Crear un plan preventivo** y comprobar la **generación automática** del
   ticket preventivo al vencer.
7. Consultar el **dashboard** y los **reportes** con los indicadores reales.

## 6. Supuestos y restricciones

- Se mantiene la arquitectura actual (Django + MySQL) y la separación lógica por
  Empresa; no se recrea la base de datos ni se eliminan registros.
- La demostración se realiza sobre datos reales cargados en el entorno local.
- No se comprometen funcionalidades de la sección 4 dentro de esta versión.
- Las métricas de SLA son informativas; no derivan en penalizaciones ni cobros.
