# Roles y permisos del sistema

Documento que define las responsabilidades de cada usuario y las acciones que
puede realizar en la plataforma SEMAXEL: qué puede **registrar, consultar,
modificar, aprobar/asignar y cerrar**, y cómo funciona el control de permisos.

## 1. Modelo de autorización

La seguridad se aplica en tres capas, de modo que la interfaz y las URLs nunca
son la única defensa:

1. **Autenticación.** Django `auth` con sesión (`login`/`logout`). Toda vista
   operativa exige `@login_required`.
2. **Autorización por rol (acceso a la vista).** El decorador
   `@rol_requerido(...)` limita qué roles entran a cada sección; el superusuario
   siempre pasa. Ejemplo: la gestión de usuarios es solo `ADMIN`; tomar ofertas
   es solo `TECNICO`.
3. **Autorización por alcance (fila/objeto).** Aunque un rol acceda, solo ve y
   opera lo que le corresponde. Se implementa en `accounts/roles.py`:
   - **Querysets filtrados:** `empresas_visibles`, `sucursales_visibles`,
     `tickets_visibles`, `ofertas_visibles`, `ordenes_visibles`.
   - **Predicados de lectura:** `puede_ver_ticket`, `puede_ver_sucursal`,
     `puede_ver_oferta`, `es_encargado_de`, `pertenece_a_empresa`.
   - **Predicados de escritura (separados de la lectura):**
     `puede_gestionar_ticket` (ver una oferta publicada no habilita cambiar el
     estado del ticket).

Reglas adicionales:

- **Aislamiento multi-empresa:** todo se filtra por la Empresa del usuario; el
  Encargado, además, solo por sus **sucursales asignadas**.
- **Admin de Django con alcance:** el Encargado **no** entra a `/admin/` (su
  espacio de trabajo es el portal).
- **Máquina de estados:** cada entidad tiene transiciones válidas y el rol
  determina qué transiciones puede aplicar.

## 2. Definición de perfiles

### Administrador (ADMIN)

Administración de la plataforma dentro de su empresa.

- **Responsabilidad:** configurar y mantener usuarios y sucursales, y supervisar
  toda la operación de su empresa.
- **Registrar:** usuarios de su empresa (rol, teléfono, empresa); sucursales.
- **Consultar:** todo lo de su empresa (empresas, sucursales, técnicos, tickets,
  ofertas, órdenes, planes, dashboard y reportes).
- **Modificar:** usuarios, sucursales, planes de mantenimiento, estados de
  tickets y datos de órdenes.
- **Aprobar/Asignar:** publica ofertas de trabajo.
- **Cerrar:** tickets (Resuelto/Cerrado/Cancelado) y órdenes (Cerrar/Cancelar).
- **Límite:** no administra técnicos (recurso global del marketplace; eso es del
  superusuario).

### Gestor (GESTOR)

Gestión operativa del mantenimiento.

- **Responsabilidad:** operar el ciclo correctivo y preventivo de su empresa.
- **Registrar:** tickets; sucursales; planes de mantenimiento preventivo.
- **Consultar:** sucursales, tickets, ofertas, órdenes, planes, dashboard y
  reportes de su empresa.
- **Modificar:** sucursales, planes y estados de tickets/órdenes.
- **Aprobar/Asignar:** publica ofertas (habilita el trabajo para los técnicos).
- **Cerrar:** tickets y órdenes.
- **Límite:** no crea ni edita usuarios.

### Encargado de local (ENCARGADO)

Responsable de la(s) sucursal(es) asignada(s).

- **Responsabilidad:** reportar y dar seguimiento a las incidencias de sus
  locales.
- **Registrar:** tickets de sus sucursales.
- **Consultar:** únicamente sus sucursales (tickets, ofertas, órdenes, planes y
  dashboard acotado). Sin reportes, empresas ni usuarios.
- **Modificar:** estados de tickets y ejecución de órdenes de sus sucursales.
- **Aprobar/Asignar:** publica ofertas de sus tickets.
- **Cerrar:** tickets y órdenes de sus sucursales.
- **Límite:** no accede al admin de Django.

### Gerencia de operaciones (GERENCIA)

Supervisión y análisis.

- **Responsabilidad:** observar el desempeño y tomar decisiones con datos.
- **Registrar:** nada (perfil de solo consulta).
- **Consultar:** dashboard, reportes, empresas, sucursales, tickets, ofertas,
  órdenes y planes de su empresa.
- **Modificar / Aprobar / Cerrar:** no participa en la operación; su valor es el
  análisis y los indicadores (SLA, tiempos, carga por técnico/sucursal).

### Técnico de terreno (TECNICO)

Ejecución del trabajo.

- **Responsabilidad:** ejecutar los trabajos que toma y reportar su avance.
- **Registrar:** su propia cuenta (registro público con especialidades) y, en las
  órdenes, diagnóstico, trabajo realizado, observaciones y costos.
- **Consultar:** ofertas disponibles (marketplace global), sus órdenes y los
  tickets asociados, y su perfil (rol y especialidades visibles).
- **Modificar:** su **disponibilidad** (Disponible/No disponible) y datos básicos
  del perfil; el avance de **sus** órdenes (En ejecución → Resuelta).
- **Aprobar/Asignar:** toma ofertas disponibles (autoasignación), validando que
  su especialidad coincida con la categoría del ticket.
- **Cerrar:** **no** cierra órdenes ni tickets (el cierre/cancelación corresponde
  a ADMIN/GESTOR/ENCARGADO).
- **Límites:** no ve el listado general de tickets; no cambia el estado de
  tickets ajenos; no cambia su rol ni la disponibilidad de otros técnicos; no
  puede reactivarse si está Inactivo.

### Superusuario (Django)

Administrador global del sistema.

- Acceso total: todas las empresas, gestión de técnicos, admin de Django y
  cualquier operación del sistema. Es el único que administra los técnicos del
  marketplace.

## 3. Matriz de permisos por perfil

| Acción | ADMIN | GESTOR | ENCARGADO | GERENCIA | TECNICO |
|---|---|---|---|---|---|
| Crear usuario | Sí (su empresa) | No | No | No | No |
| Crear/editar sucursal | Sí | Sí | No | No | No |
| Gestionar técnicos | No (superusuario) | No | No | No | No |
| Crear ticket | Sí | Sí | Sí (sus sucursales) | No | No |
| Consultar tickets | Sí (su empresa) | Sí | Sí (solo suyas) | Sí | Solo los de sus órdenes |
| Cambiar estado de ticket | Sí | Sí | Sí (su sucursal) | No | Solo con orden viva |
| Publicar oferta | Sí | Sí | Sí | No | No |
| Tomar oferta | No | No | No | No | Sí (si especialidad coincide) |
| Crear/editar planes preventivos | Sí | Sí | No | No | No |
| Generar preventivos | Sí | Sí | Sí (sus sucursales) | No | No |
| Ejecutar orden (iniciar/avanzar) | Sí | Sí | Sí | Solo lectura | Sí (solo las suyas) |
| Cerrar/cancelar orden y ticket | Sí | Sí | Sí | No | No |
| Ver dashboard | Sí | Sí | Sí | Sí | No (usa Ofertas) |
| Ver reportes | Sí | Sí | No | Sí | No |
| Acceso al admin Django | Sí | Sí (staff) | No | Sí (staff) | No |

## 4. Reglas transversales

- **Consulta no es modificación:** cada acción sensible valida permisos de
  escritura aparte (por ejemplo, ver una oferta publicada no permite cerrar el
  ticket).
- **Alcance por objeto:** ninguna URL permite operar fuera de la empresa o
  sucursal del usuario; intentarlo responde 403.
- **Trazabilidad:** cada cambio de estado de ticket queda en el historial
  (usuario, estado anterior/nuevo, comentario y fecha).
- **Aprobación:** no existe un flujo formal de "aprobar"; su equivalente
  funcional es **publicar la oferta** (libera el trabajo) y **cerrar** ticket u
  orden (cierre formal con calificación).

## 5. Observación de precisión (Gerencia y órdenes)

En el código actual, el perfil GERENCIA queda incluido en el alcance de órdenes
de trabajo. Si el diseño define a Gerencia como estrictamente de solo lectura,
conviene restringir en esa vista las transiciones de orden para que coincida con
la intención: hoy el cierre/cancelación de órdenes está pensado para
ADMIN/GESTOR/ENCARGADO.
