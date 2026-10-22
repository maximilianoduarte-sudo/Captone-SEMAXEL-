# Reglas de negocio

Este documento describe, de forma explícita y verificable en el código, qué
ocurre en cada punto clave del ciclo de mantenimiento: registro de incidencias,
conversión en orden de trabajo, asignación de técnico, cálculo del SLA,
incumplimiento del tiempo comprometido, cierre de la orden y contenido del
historial.

## 1. Registro de una incidencia (ticket)

**Quién puede registrar:** los roles que gestionan la incidencia
(`ROLES_GESTIONAN_TICKETS`): **Administrador, Gestor y Encargado de local**.
Gerencia y Técnico no registran tickets. El Encargado solo puede elegir
sucursales que tenga asignadas; el resto de roles, las de su empresa.

**Qué ocurre al registrar (regla paso a paso):**

1. Se valida que la sucursal elegida esté dentro del alcance del usuario
   (`TicketForm.clean_sucursal`); si no, se rechaza con
   "No tienes permisos para usar esta sucursal".
2. Se asigna el **número** con `_proximo_numero(sucursal)`, con formato
   `<codigo_empresa>-<correlativo de 5 dígitos>` (p. ej. `SEMAXEL-00001`). La
   secuencia es **independiente por empresa**, por lo que los números no
   colisionan entre empresas.
3. El **creador** queda registrado como el usuario autenticado.
4. El estado inicial es **ABIERTO** y el tipo, por defecto, **INCIDENCIA**.
5. En el primer guardado se calcula la **fecha límite de SLA** (ver sección 4).
6. Se crea la **primera entrada del historial**: `estado_anterior = None` →
   `ABIERTO`, con el comentario "Creación del ticket por incidencia.".
7. Cada archivo enviado se guarda como **EvidenciaTicket** (imagen u otro
   archivo que documenta la falla).

> Nota: además de la creación manual, el sistema genera tickets **PREVENTIVO**
> automáticamente (sección 8).

## 2. Conversión de la incidencia en orden de trabajo

La conversión **no la ejecuta directamente una persona**: el ticket se convierte
en orden de trabajo a través del flujo de **oferta y toma por un técnico**.

1. **Quién publica la oferta:** Administrador, Gestor o Encargado
   (`ROLES_GESTIONAN_TICKETS`) y solo si el ticket está en un estado publicable
   (**ABIERTO, EN_REVISION o PUBLICADO**).
2. Al publicar, se crea la **OfertaTicket** (estado **DISPONIBLE**) y el ticket
   pasa a **PUBLICADO**, registrando el historial "Se publicó la oferta para
   técnicos.".
3. **Quién convierte a orden:** el **Técnico** que **toma** la oferta (sección
   3). En ese momento se crea la **OrdenTrabajo** en estado **ASIGNADA**.

Regla de cardinalidad: cada ticket admite **una sola oferta** y **una sola
orden de trabajo** (relación uno a uno).

## 3. Asignación de técnico

La asignación es **por autoselección del técnico** sobre una oferta publicada
(modelo tipo marketplace), **no** por elección manual del gestor.

**Elegibilidad (condiciones para poder tomar la oferta):**

- La oferta debe estar **DISPONIBLE** y no vencida.
- La **categoría del ticket debe tener una especialidad definida**; si no, no se
  puede verificar la idoneidad y se bloquea la toma.
- El técnico debe tener esa **especialidad** en su perfil.
- Si el usuario tiene rol Técnico pero no tiene perfil de Técnico asociado, no
  puede tomar ofertas.

**Qué ocurre al tomar la oferta:**

1. La oferta pasa a **TOMADA** y se registra `fecha_tomada`.
2. Se crea la **OrdenTrabajo** (estado **ASIGNADA**) con ese técnico.
3. El ticket pasa a **EN_EJECUCION** y se registra el historial "Oferta tomada
   por el técnico {nombre}.".
4. El técnico pasa a estado **OCUPADO**.

## 4. Cálculo del SLA (cómo y con qué variables)

**Objetivo:** fijar el plazo máximo de resolución de un ticket y medir su
cumplimiento.

**Variables utilizadas:**

| Variable | Origen |
|---|---|
| Prioridad del ticket | `Ticket.prioridad` (BAJA, MEDIA, ALTA, CRITICA) |
| Empresa | La de la sucursal del ticket |
| Política SLA efectiva | `SLAPolicy.obtener(empresa, prioridad)` |
| Tiempo máximo de resolución | `SLAPolicy.tiempo_maximo_resolucion` (minutos) |
| Fecha de creación | `timezone.now()` al crear el ticket |

**Resolución de la política efectiva** (`SLAPolicy.obtener`):

1. Si la empresa tiene una política **activa** para esa prioridad, se usa esa.
2. Si no, se usa la **política global** (empresa vacía) activa para esa
   prioridad.
3. Si no existe ninguna, **no se fija fecha límite** (`fecha_limite_sla = None`)
   y el ticket no entra en el cálculo de cumplimiento.

Restricción: existe una única política por combinación `(empresa, prioridad)`.

**Fórmula:**

```
fecha_limite_sla = fecha_creacion + timedelta(minutes = tiempo_maximo_resolucion)
```

La fecha límite se calcula **una sola vez**, al crear el ticket, y no se
recalcula si luego cambia la política.

**Medición del cumplimiento** (`_cumplimiento_sla`):

- Se consideran **solo** los tickets **CERRADO o RESUELTO** con
  `fecha_limite_sla` no nulo.
- `fecha_cierre` se fija al pasar a **RESUELTO, CERRADO o CANCELADO** y se
  limpia al reabrir.
- Cumplimiento (%) =

```
cumplidos = tickets con fecha_cierre <= fecha_limite_sla
cumplimiento = round(cumplidos / total * 100)
```

- Si no hay tickets evaluables, el cumplimiento es **100%**.

**Alcance actual del SLA (importante):**

- Solo se usa el **tiempo máximo de resolución**. El campo
  `tiempo_maximo_respuesta` existe y se muestra en el detalle de la empresa,
  pero **no** participa en ningún cálculo automático.
- El campo `fecha_respuesta` de la oferta existe pero **no se completa** en el
  flujo actual.
- El vencimiento de la **oferta** es un campo **manual** que ingresa el gestor
  al publicar (`fecha_vencimiento`); no se deriva del SLA.

## 5. Qué sucede cuando se incumple el tiempo comprometido

**Comportamiento actual (no hay acciones automáticas):**

- El sistema **no ejecuta penalizaciones, escalamientos, reasignaciones ni
  notificaciones** al vencer el plazo. El incumplimiento es **informativo**.
- El dashboard expone `cumplimiento_sla` y su complemento
  `no_cumplimiento_sla = 100 - cumplimiento_sla`, por lo que el incumplimiento
  se refleja en los **indicadores**.
- **Importante:** la métrica solo evalúa tickets **ya cerrados o resueltos**. Un
  ticket con `fecha_limite_sla` vencida pero **aún abierto** no aparece en el
  porcentaje hasta que se cierra o resuelve. No existe (aún) un indicador de
  "tickets abiertos vencidos".

**Recomendación (alcance futuro):** si el SLA es un pilar de la propuesta,
conviene añadir el marcado de tickets vencidos y vivos, alertas/notificaciones y
una política de consecuencias (p. ej. escalamiento), hoy fuera del MVP.

## 6. Registro del cierre de una orden de trabajo

**Quién puede cerrar:** los roles que **no** son Técnico y tienen acceso a la
orden (Administrador, Gestor, Encargado). El **Técnico queda excluido** de las
transiciones **CERRADA** y **CANCELADA**.

**Transiciones y responsables:**

- **ASIGNADA → EN_EJECUCION:** el técnico de la orden (exige registrar
  diagnóstico).
- **EN_EJECUCION → RESUELTA:** el técnico de la orden (exige registrar el trabajo
  realizado).
- **RESUELTA → CERRADA:** rol no-técnico con acceso (exige calificación 1–5).

**Efectos del cierre (orden → CERRADA):**

1. La orden pasa a **CERRADA** y se fija `fecha_fin` si no estaba.
2. Se **libera al técnico** (vuelve a **DISPONIBLE**) si no tiene otras órdenes
   activas (ASIGNADA/EN_EJECUCION).
3. El **ticket** pasa a **CERRADO** (si la transición es válida), se fija
   `fecha_cierre` y se registra el historial
   "Sincronizado desde la orden #{id} (CERRADA).".
4. Se registra la **Calificación** de la orden: técnico, puntuación (1–5) y
   comentario.

**Efectos de resolver (orden → RESUELTA):** igual que el cierre, pero el ticket
pasa a **RESUELTO** y el técnico se libera; no exige calificación.

**Cancelación:** una orden **ASIGNADA** o **EN_EJECUCION** puede pasar a
**CANCELADA** (rol no-técnico); el ticket se sincroniza a **CANCELADO**.

## 7. Información almacenada en el historial

El historial de un ticket (`TicketHistorial`) guarda, por cada cambio:

| Campo | Contenido |
|---|---|
| `usuario` | Quién realizó el cambio (o el creador si no hay usuario) |
| `estado_anterior` | Estado previo (nulo en la creación) |
| `estado_nuevo` | Estado resultante |
| `comentario` | Motivo o descripción del cambio |
| `fecha_cambio` | Marca de tiempo automática |

**Eventos que generan una entrada de historial:**

- Creación del ticket (None → ABIERTO).
- Publicación de la oferta (→ PUBLICADO).
- Toma de la oferta (→ EN_EJECUCION).
- Inicio de trabajo desde la orden (→ EN_EJECUCION).
- Resolución desde la orden (→ RESUELTO).
- Cierre desde la orden (→ CERRADO).
- Cancelación desde la orden (→ CANCELADO).
- Expiración de la oferta (PUBLICADO → EN_REVISION para republicar).
- Cambio manual de estado del ticket (con comentario del formulario).

**Información complementaria (fuera del historial, pero persistida):**

- **Evidencias** del ticket (archivos).
- **Orden de trabajo:** diagnóstico, trabajo realizado, observaciones, costo
  estimado y final, y fechas de inicio/fin.
- **Calificación:** puntuación y comentario al cerrar.
- **Oferta:** fechas de publicación, vencimiento y toma, observaciones.

## 8. Regla del mantenimiento preventivo (generación automática)

- Se generan tickets **PREVENTIVO** para los planes **activos** cuya
  `fecha_proxima` ya venció (`fecha_proxima <= ahora`).
- Antes de generar, la agenda se reposiciona a la **siguiente ejecución futura**
  sumando la frecuencia en días (sin desbordar por atrasos largos).
- Se genera **un único ticket por plan y ciclo**, salvo que ya exista un
  preventivo **abierto** del mismo plan (ABIERTO, EN_REVISION, PUBLICADO,
  EN_EJECUCION o RESUELTO), en cuyo caso se omite.
- Cada preventivo se crea en estado **ABIERTO**, prioridad **MEDIA** y con el
  historial "Ticket preventivo generado automáticamente desde su plan.".
- El **creador** es el usuario indicado; si no, el ADMIN de la empresa; en
  último caso, el superusuario.
- El Encargado solo genera preventivos de **sus sucursales**.

## 9. Máquinas de estado (referencia)

**Ticket:**

```
ABIERTO      -> EN_REVISION, PUBLICADO, EN_EJECUCION, CANCELADO
EN_REVISION  -> ABIERTO, PUBLICADO, EN_EJECUCION, CANCELADO
PUBLICADO    -> EN_EJECUCION, EN_REVISION, CANCELADO
EN_EJECUCION -> RESUELTO, CANCELADO
RESUELTO     -> CERRADO, EN_EJECUCION
CERRADO      -> (terminal)
CANCELADO    -> (terminal)
```

**Orden de trabajo:**

```
ASIGNADA     -> EN_EJECUCION, CANCELADA
EN_EJECUCION -> RESUELTA, CANCELADA
RESUELTA     -> CERRADA, EN_EJECUCION
CERRADA      -> (terminal)
CANCELADA    -> (terminal)
```

**Oferta:**

```
DISPONIBLE -> TOMADA
DISPONIBLE -> EXPIRADA   (al vencer fecha_vencimiento)
```

## 10. Resumen de reglas clave

| Pregunta | Regla |
|---|---|
| ¿Quién registra incidencias? | ADMIN, GESTOR, ENCARGADO (según sucursales visibles). |
| ¿Quién convierte en orden? | El TÉCNICO al tomar la oferta; el gestor publica la oferta. |
| ¿Quién asigna al técnico? | El propio técnico (autoselección), validando especialidad. |
| ¿Cómo se calcula el SLA? | `fecha_creacion + tiempo_maximo_resolucion` de la política efectiva. |
| ¿Qué pasa al incumplir? | Solo se refleja en métricas; no hay acciones ni penalizaciones automáticas. |
| ¿Quién cierra la orden? | ADMIN/GESTOR/ENCARGADO (no el TÉCNICO); exige calificación 1–5. |
| ¿Qué guarda el historial? | Usuario, estado anterior, estado nuevo, comentario y fecha. |
