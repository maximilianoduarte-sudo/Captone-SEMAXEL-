from django.db import transaction
from django.utils import timezone

from tickets.models import Ticket, TicketHistorial

from .models import OfertaTicket


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