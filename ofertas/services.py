from django.db import transaction
from django.utils import timezone

from tecnicos.models import Tecnico
from tickets.models import OrdenTrabajo, Ticket, TicketHistorial

from .models import OfertaTicket


class OfertaNoTomable(Exception):
    """La oferta no se puede tomar. `mensaje` es para la persona; `codigo`, para el programa.

    Códigos posibles:
    - "no_disponible": ya la tomó otro técnico o dejó de estar disponible.
    - "vencida": pasó su fecha de vencimiento (se marca EXPIRADA).
    - "ticket_no_permite": el estado del ticket no permite pasar a ejecución.
    - "sin_especialidad": la categoría del ticket no tiene especialidad definida.
    - "especialidad_no_coincide": el técnico no tiene la especialidad requerida.
    """

    def __init__(self, mensaje, codigo):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


@transaction.atomic
def expirar_ofertas_vencidas(usuario=None):
    """Marca EXPIRADA a las ofertas DISPONIBLE cuyo vencimiento llegó.

    Si el ticket asociado está PUBLICADO y puede volver a EN_REVISION, se
    revierte a revisión (registrando el cambio en el historial) para que un
    administrador pueda republicar la oferta con nuevas condiciones.
    Devuelve la cantidad de ofertas expiradas.
    """
    ahora = timezone.now()
    vencidas = (
        OfertaTicket.objects.filter(
            estado=OfertaTicket.Estado.DISPONIBLE,
            fecha_vencimiento__isnull=False,
            fecha_vencimiento__lte=ahora,
        )
        .select_related("ticket")
    )
    expiradas = 0
    for oferta in vencidas:
        oferta.estado = OfertaTicket.Estado.EXPIRADA
        oferta.save(update_fields=["estado"])

        ticket = oferta.ticket
        if (
            ticket.estado == Ticket.Estado.PUBLICADO
            and ticket.puede_transicionar_a(Ticket.Estado.EN_REVISION)
        ):
            estado_anterior = ticket.estado
            ticket.estado = Ticket.Estado.EN_REVISION
            ticket.save(update_fields=["estado"])
            TicketHistorial.objects.create(
                ticket=ticket,
                usuario=usuario or ticket.creador,
                estado_anterior=estado_anterior,
                estado_nuevo=Ticket.Estado.EN_REVISION,
                comentario="Oferta expirada; ticket devuelto a revisión para republicar.",
            )
        expiradas += 1
    return expiradas

def ofertas_disponibles_para(tecnico, usuario=None):
    """Ofertas que un técnico puede tomar ahora (regla HU-09).

    Una oferta aparece solo si cumple todo lo siguiente:
    - está DISPONIBLE (antes se expiran las vencidas, igual que en la web);
    - la categoría de su ticket tiene una especialidad definida;
    - esa especialidad está en el perfil del técnico.

    Así el técnico no ve trabajos que el sistema le impediría tomar.
    La usa la API de la app móvil; la web todavía muestra todas las
    disponibles y valida la especialidad recién al tomar la oferta.
    """
    expirar_ofertas_vencidas(usuario=usuario)
    return (
        OfertaTicket.objects.filter(
            estado=OfertaTicket.Estado.DISPONIBLE,
            ticket__categoria__especialidad__isnull=False,
            ticket__categoria__especialidad__in=tecnico.especialidades.all(),
        )
        .select_related(
            "ticket__sucursal__empresa",
            "ticket__categoria__especialidad",
        )
        .order_by("-fecha_publicacion")
    )


def tomar_oferta(oferta, tecnico, usuario):
    """Asigna la oferta al técnico y crea su orden de trabajo.

    Es la única implementación de "tomar oferta": la usan la web y la API.
    Si algo impide tomarla, lanza OfertaNoTomable y no cambia nada (salvo
    marcar EXPIRADA una oferta vencida). Si todo está bien:

    1. La oferta pasa a TOMADA, con el técnico y la fecha.
    2. Se crea la orden de trabajo en estado ASIGNADA.
    3. El ticket pasa a EN_EJECUCION y se registra en su historial.
    4. El técnico pasa a OCUPADO.

    Devuelve la orden de trabajo.
    """
    with transaction.atomic():
        # Bloquea la fila de la oferta hasta terminar: si dos técnicos la
        # toman al mismo tiempo, el segundo espera y luego la ve TOMADA.
        oferta = OfertaTicket.objects.select_for_update().get(pk=oferta.pk)

        if oferta.estado != OfertaTicket.Estado.DISPONIBLE:
            raise OfertaNoTomable("Esta oferta ya no está disponible.", "no_disponible")

        vencida = bool(
            oferta.fecha_vencimiento and oferta.fecha_vencimiento <= timezone.now()
        )
        if not vencida:
            _validar_idoneidad(oferta, tecnico)
            return _asignar(oferta, tecnico, usuario)

    # Fuera de la transacción, para que la expiración quede guardada aunque
    # después se informe el error.
    expirar_ofertas_vencidas(usuario=usuario)
    raise OfertaNoTomable("Esta oferta venció y ya no está disponible.", "vencida")


def _validar_idoneidad(oferta, tecnico):
    """Revisa que el ticket y el técnico permitan tomar la oferta."""
    ticket = oferta.ticket
    if not ticket.puede_transicionar_a(Ticket.Estado.EN_EJECUCION):
        raise OfertaNoTomable(
            "El ticket ya no permite tomar la oferta.", "ticket_no_permite"
        )

    # Sin especialidad en la categoría no hay forma de verificar la
    # idoneidad del técnico que toma el trabajo.
    especialidad = ticket.categoria.especialidad
    if especialidad is None:
        raise OfertaNoTomable(
            "La categoría del ticket no tiene especialidad definida. "
            "Contacta a un administrador para que la configure antes de tomar la oferta.",
            "sin_especialidad",
        )

    if not tecnico.especialidades.filter(pk=especialidad.pk).exists():
        raise OfertaNoTomable(
            f"Esta oferta requiere la especialidad “{especialidad.nombre}”, "
            "que no está en tu perfil.",
            "especialidad_no_coincide",
        )


def _asignar(oferta, tecnico, usuario):
    """Aplica los cambios de estado de una toma ya validada."""
    oferta.tecnico = tecnico
    oferta.estado = OfertaTicket.Estado.TOMADA
    oferta.fecha_tomada = timezone.now()
    oferta.save()

    ticket = oferta.ticket
    orden, _ = OrdenTrabajo.objects.get_or_create(
        ticket=ticket,
        defaults={
            "tecnico": tecnico,
            "oferta": oferta,
            "estado": OrdenTrabajo.Estado.ASIGNADA,
        },
    )

    if ticket.estado != Ticket.Estado.EN_EJECUCION:
        estado_anterior = ticket.estado
        ticket.estado = Ticket.Estado.EN_EJECUCION
        ticket.save()
        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=Ticket.Estado.EN_EJECUCION,
            comentario=f"Oferta tomada por el técnico {tecnico.nombre}.",
        )

    tecnico.estado = Tecnico.Estado.OCUPADO
    tecnico.save(update_fields=["estado"])
    return orden
