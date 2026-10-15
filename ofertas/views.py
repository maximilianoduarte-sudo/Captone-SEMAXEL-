from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import Usuario
from accounts.roles import (
    ofertas_visibles,
    puede_ver_oferta,
    rol_requerido,
    rol_usuario,
)
from tecnicos.models import Tecnico
from tickets.models import OrdenTrabajo, Ticket, TicketHistorial

from .models import OfertaTicket
from .services import expirar_ofertas_vencidas


def _ocultar_numero(request):
    """True si el usuario no debe ver el identificador del ticket (p. ej. SEMAXEL-00001).

    Los técnicos trabajan con las ofertas como marketplace, no como
    administración de tickets: no necesitan el número correlativo interno.
    Los roles de gestión (y el superusuario) sí lo ven para poder rastrearlo.
    """
    if request.user.is_superuser:
        return False
    return rol_usuario(request.user) == Usuario.Rol.TECNICO


def _tecnico_actual(request):
    """
    Técnico asociado al usuario autenticado.

    Para usuarios con perfil de técnico se devuelve su propio registro.
    El superusuario (que toma a nombre de un técnico) usa el primer
    técnico disponible como respaldo.
    Returns None solo si: usuario es TECNICO pero no tiene registro Tecnico.
    """
    if request.user.is_authenticated and hasattr(request.user, "tecnico"):
        return request.user.tecnico
    if rol_usuario(request.user) == Usuario.Rol.TECNICO:
        return None
    return Tecnico.objects.filter(estado=Tecnico.Estado.DISPONIBLE).first()


@login_required
def disponibles(request):
    """Ofertas de trabajo disponibles para técnicos (datos reales)."""
    expirar_ofertas_vencidas(usuario=request.user)
    qs = ofertas_visibles(request.user).filter(estado=OfertaTicket.Estado.DISPONIBLE)
    ofertas = (
        qs.select_related("ticket__sucursal__empresa", "ticket__categoria")
        .order_by("-fecha_publicacion")
    )
    context = {
        "ofertas": ofertas,
        "prioridades": dict(Ticket.Prioridad.choices),
        "ocultar_numero": _ocultar_numero(request),
    }
    return render(request, "tickets/ofertas/disponibles.html", context)


@login_required
def detalle(request, oid):
    """Detalle de una oferta con opción de tomarla."""
    oferta = get_object_or_404(
        OfertaTicket.objects.select_related(
            "ticket__sucursal__empresa", "ticket__categoria"
        ),
        pk=oid,
    )
    if not puede_ver_oferta(request.user, oferta):
        raise PermissionDenied
    context = {
        "oferta": oferta,
        "prioridades": dict(Ticket.Prioridad.choices),
        "tomada": request.GET.get("tomada", "") == "1",
        "ocultar_numero": _ocultar_numero(request),
    }
    return render(request, "tickets/ofertas/detalle.html", context)


@login_required
@rol_requerido(Usuario.Rol.TECNICO)
def tomar(request, oid):
    """Toma la oferta: asigna técnico, crea la orden de trabajo y avanza estados.

    Solo el rol TECNICO puede tomar ofertas: el GESTOR las publica y
    administra pero no las toma (el superusuario queda habilitado por
    convención del sistema de permisos).
    """
    oferta = get_object_or_404(
        OfertaTicket.objects.select_related("ticket__categoria__especialidad"),
        pk=oid,
    )

    if not puede_ver_oferta(request.user, oferta):
        raise PermissionDenied

    if oferta.estado != OfertaTicket.Estado.DISPONIBLE:
        messages.warning(request, "Esta oferta ya no está disponible.")
        return redirect("ofertas:detalle", oid=oferta.pk)

    if oferta.fecha_vencimiento and oferta.fecha_vencimiento <= timezone.now():
        expirar_ofertas_vencidas(usuario=request.user)
        messages.warning(request, "Esta oferta venció y ya no está disponible.")
        return redirect("ofertas:detalle", oid=oferta.pk)

    tecnico = _tecnico_actual(request)
    if tecnico is None:
        messages.error(
            request,
            "Tu usuario tiene rol Técnico pero no tiene un perfil de técnico "
            "asociado. Pídele a un administrador que lo registre en la sección "
            "Técnicos para poder tomar ofertas.",
        )
        return redirect("ofertas:detalle", oid=oferta.pk)

    ticket = oferta.ticket

    if not ticket.puede_transicionar_a(Ticket.Estado.EN_EJECUCION):
        messages.warning(request, "El ticket ya no permite tomar la oferta.")
        return redirect("ofertas:disponibles")

    # La categoría del ticket debe definir una especialidad: sin ella no hay
    # forma de verificar la idoneidad del técnico que toma el trabajo.
    especialidad = ticket.categoria.especialidad_id
    if especialidad is None:
        messages.warning(
            request,
            "La categoría del ticket no tiene especialidad definida. "
            "Contacta a un administrador para que la configure antes de tomar la oferta.",
        )
        return redirect("ofertas:detalle", oid=oferta.pk)

    if not tecnico.especialidades.filter(pk=especialidad).exists():
        messages.warning(
            request,
            "Esta oferta requiere la especialidad "
            f"“{ticket.categoria.especialidad.nombre}”, que no está en tu perfil.",
        )
        return redirect("ofertas:detalle", oid=oferta.pk)

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

    messages.success(
        request,
        f"Oferta tomada. Se generó la orden de trabajo #{orden.pk:05d}.",
    )
    return redirect(f"{reverse('ofertas:detalle', args=[oferta.pk])}?tomada=1")