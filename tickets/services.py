"""Reglas de la orden de trabajo, compartidas por la web y la API.

La máquina de estados de la orden es:

    ASIGNADA     -> EN_EJECUCION, CANCELADA
    EN_EJECUCION -> RESUELTA, CANCELADA
    RESUELTA     -> CERRADA, EN_EJECUCION
    CERRADA, CANCELADA: terminales

Quién puede aplicar cada transición:
- El técnico de la orden: iniciar (EN_EJECUCION) y resolver (RESUELTA).
- ADMIN, GESTOR y ENCARGADO (y el superusuario): cualquiera, incluido
  cerrar y cancelar.
- GERENCIA: ninguna. Su perfil es de solo lectura.
"""
from django.db import transaction
from django.utils import timezone

from accounts.models import Usuario
from accounts.roles import rol_usuario
from tecnicos.models import Tecnico

from .models import Calificacion, OrdenTrabajo, Ticket, TicketHistorial

CAMPOS_DE_TRABAJO = (
    "diagnostico",
    "trabajo_realizado",
    "observaciones",
    "costo_estimado",
    "costo_final",
)

ESTADOS_TERMINO = (OrdenTrabajo.Estado.CERRADA, OrdenTrabajo.Estado.CANCELADA)


class TransicionNoPermitida(Exception):
    """No se puede aplicar la transición. `mensaje` es para la persona; `codigo`, para el programa.

    Códigos posibles:
    - "sin_cambio": la orden ya está en ese estado.
    - "transicion_invalida": la máquina de estados no permite ese paso.
    - "sin_permiso": el usuario no puede aplicar esa transición.
    - "falta_diagnostico": iniciar exige diagnóstico.
    - "falta_trabajo": resolver exige el trabajo realizado.
    - "falta_calificacion": cerrar exige una calificación de 1 a 5.
    """

    def __init__(self, mensaje, codigo):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def puede_aplicar_transicion(user, orden, destino):
    """True si el usuario puede llevar la orden al estado `destino`."""
    if user.is_superuser:
        return True
    rol = rol_usuario(user)
    if rol == Usuario.Rol.GERENCIA:
        return False
    if rol == Usuario.Rol.TECNICO:
        if destino in ESTADOS_TERMINO:
            return False
        return orden.tecnico.usuario_id == user.id
    return True


def transiciones_permitidas(user, orden):
    """Estados a los que este usuario puede llevar la orden ahora mismo."""
    return {
        destino
        for destino in orden.transiciones_validas()
        if puede_aplicar_transicion(user, orden, destino)
    }


def cambiar_estado_orden(orden, destino, usuario, datos=None):
    """Aplica una transición a la orden y sincroniza todo lo relacionado.

    `datos` puede traer: diagnostico, trabajo_realizado, observaciones,
    costo_estimado, costo_final, puntuacion y comentario_calificacion.

    Si algo impide la transición, lanza TransicionNoPermitida y no cambia
    nada. Si se aplica:
    - guarda los datos de trabajo (solo al iniciar o resolver, sin pisar
      valores existentes con blancos);
    - fija fecha_inicio o fecha_fin según corresponda;
    - mueve el ticket al estado equivalente y lo registra en el historial;
    - libera al técnico si ya no tiene órdenes activas;
    - al cerrar, registra la calificación.

    Devuelve la orden actualizada.
    """
    datos = datos or {}
    with transaction.atomic():
        orden = (
            OrdenTrabajo.objects.select_for_update()
            .select_related("ticket", "tecnico")
            .get(pk=orden.pk)
        )
        _validar(orden, destino, usuario, datos)
        _aplicar_campos(orden, destino, datos)
        _sincronizar_ticket_y_tecnico(orden, destino, usuario)
        if destino == OrdenTrabajo.Estado.CERRADA:
            Calificacion.objects.update_or_create(
                orden_trabajo=orden,
                defaults={
                    "tecnico": orden.tecnico,
                    "puntuacion": datos["puntuacion"],
                    "comentario": datos.get("comentario_calificacion") or "",
                },
            )
    return orden


def _validar(orden, destino, usuario, datos):
    if destino == orden.estado:
        raise TransicionNoPermitida("La orden ya se encuentra en ese estado.", "sin_cambio")
    if not orden.puede_transicionar_a(destino):
        raise TransicionNoPermitida(
            f"Transición de la orden no permitida: {orden.estado} → {destino}.",
            "transicion_invalida",
        )
    if not puede_aplicar_transicion(usuario, orden, destino):
        raise TransicionNoPermitida(
            "No tienes permiso para aplicar esta transición.", "sin_permiso"
        )
    if destino == OrdenTrabajo.Estado.EN_EJECUCION and not (
        datos.get("diagnostico") or orden.diagnostico
    ):
        raise TransicionNoPermitida(
            "Ingresa el diagnóstico para iniciar el trabajo.", "falta_diagnostico"
        )
    if destino == OrdenTrabajo.Estado.RESUELTA and not (
        datos.get("trabajo_realizado") or orden.trabajo_realizado
    ):
        raise TransicionNoPermitida(
            "Registra el trabajo realizado antes de resolver la orden.", "falta_trabajo"
        )
    if destino == OrdenTrabajo.Estado.CERRADA and not datos.get("puntuacion"):
        raise TransicionNoPermitida(
            "La calificación (1 a 5) es obligatoria al cerrar la orden.",
            "falta_calificacion",
        )


def _aplicar_campos(orden, destino, datos):
    """Guarda el nuevo estado y, al iniciar o resolver, los datos de trabajo.

    Al cerrar o cancelar no se tocan los datos de trabajo.
    """
    campos = ["estado"]
    if destino in (OrdenTrabajo.Estado.EN_EJECUCION, OrdenTrabajo.Estado.RESUELTA):
        for campo in CAMPOS_DE_TRABAJO:
            valor = datos.get(campo)
            if valor not in (None, ""):
                setattr(orden, campo, valor)
                campos.append(campo)
    orden.estado = destino
    orden.save(update_fields=campos)


def _sincronizar_ticket_y_tecnico(orden, destino, usuario):
    """Fechas de la orden, estado del ticket (con historial) y disponibilidad del técnico."""
    ahora = timezone.now()

    if destino == OrdenTrabajo.Estado.EN_EJECUCION and not orden.fecha_inicio:
        orden.fecha_inicio = ahora
        orden.save(update_fields=["fecha_inicio"])
    elif destino in (OrdenTrabajo.Estado.RESUELTA, *ESTADOS_TERMINO):
        if not orden.fecha_fin:
            orden.fecha_fin = ahora
            orden.save(update_fields=["fecha_fin"])
        _liberar_tecnico(orden)

    destino_ticket = {
        OrdenTrabajo.Estado.RESUELTA: Ticket.Estado.RESUELTO,
        OrdenTrabajo.Estado.CERRADA: Ticket.Estado.CERRADO,
        OrdenTrabajo.Estado.CANCELADA: Ticket.Estado.CANCELADO,
    }.get(destino)
    ticket = orden.ticket
    if destino_ticket and ticket.puede_transicionar_a(destino_ticket):
        estado_anterior = ticket.estado
        ticket.estado = destino_ticket
        ticket.fecha_cierre = ahora
        ticket.save(update_fields=["estado", "fecha_cierre"])
        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=destino_ticket,
            comentario=f"Sincronizado desde la orden #{orden.pk} ({destino}).",
        )
    elif (
        destino == OrdenTrabajo.Estado.EN_EJECUCION
        and ticket.estado != Ticket.Estado.EN_EJECUCION
        and ticket.puede_transicionar_a(Ticket.Estado.EN_EJECUCION)
    ):
        estado_anterior = ticket.estado
        ticket.estado = Ticket.Estado.EN_EJECUCION
        ticket.save(update_fields=["estado"])
        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=Ticket.Estado.EN_EJECUCION,
            comentario=f"Inicio de trabajo registrado desde la orden #{orden.pk}.",
        )


def _liberar_tecnico(orden):
    """Deja DISPONIBLE al técnico si no tiene otras órdenes activas."""
    tecnico = orden.tecnico
    if not tecnico or tecnico.estado != Tecnico.Estado.OCUPADO:
        return
    activas = OrdenTrabajo.objects.filter(
        tecnico=tecnico,
        estado__in=[OrdenTrabajo.Estado.ASIGNADA, OrdenTrabajo.Estado.EN_EJECUCION],
    ).exclude(pk=orden.pk)
    if not activas.exists():
        tecnico.estado = Tecnico.Estado.DISPONIBLE
        tecnico.save(update_fields=["estado"])
