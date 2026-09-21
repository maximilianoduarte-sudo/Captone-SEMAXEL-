from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from tecnicos.models import Tecnico
from tickets.models import OrdenTrabajo, Ticket, TicketHistorial

from .models import OfertaTicket


def _tecnico_actual(request):
    """Perfil de técnico del usuario autenticado (o el primero disponible)."""
    if request.user.is_authenticated and hasattr(request.user, "tecnico"):
        return request.user.tecnico
    return Tecnico.objects.filter(estado=Tecnico.Estado.DISPONIBLE).first()


def disponibles(request):
    """Ofertas de trabajo disponibles para técnicos (datos reales)."""
    ofertas = (
        OfertaTicket.objects.filter(estado=OfertaTicket.Estado.DISPONIBLE)
        .select_related("ticket__sucursal", "ticket__categoria")
        .order_by("-fecha_publicacion")
    )
    context = {"ofertas": ofertas, "prioridades": dict(Ticket.Prioridad.choices)}
    return render(request, "ofertas/disponibles.html", context)


def detalle(request, oid):
    """Detalle de una oferta con opción de tomarla."""
    oferta = get_object_or_404(OfertaTicket.objects.select_related("ticket__sucursal", "ticket__categoria"), pk=oid)
    context = {
        "oferta": oferta,
        "prioridades": dict(Ticket.Prioridad.choices),
        "tomada": request.GET.get("tomada", "") == "1",
    }
    return render(request, "ofertas/detalle.html", context)


def tomar(request, oid):
    """Toma la oferta: asigna técnico, crea la orden de trabajo y avanza estados."""
    oferta = get_object_or_404(OfertaTicket, pk=oid)

    if oferta.estado != OfertaTicket.Estado.DISPONIBLE:
        messages.warning(request, "Esta oferta ya no está disponible.")
        return redirect("ofertas:detalle", oid=oferta.pk)

    tecnico = _tecnico_actual(request)
    if tecnico is None:
        messages.error(request, "No existe un perfil de técnico disponible para tomar la oferta.")
        return redirect("ofertas:detalle", oid=oferta.pk)

    ticket = oferta.ticket

    oferta.tecnico = tecnico
    oferta.estado = OfertaTicket.Estado.TOMADA
    oferta.fecha_tomada = timezone.now()
    oferta.save()

    orden, creada = OrdenTrabajo.objects.get_or_create(
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
            usuario=request.user if request.user.is_authenticated else ticket.creador,
            estado_anterior=estado_anterior,
            estado_nuevo=Ticket.Estado.EN_EJECUCION,
            comentario=f"Oferta tomada por el técnico {tecnico.nombre}.",
        )

    tecnico.estado = Tecnico.Estado.OCUPADO
    tecnico.save(update_fields=["estado"])

    messages.success(request, f"Oferta tomada. Se generó la orden de trabajo #{orden.pk}.")
    return redirect(f"{reverse('ofertas:detalle', args=[oferta.pk])}?tomada=1")