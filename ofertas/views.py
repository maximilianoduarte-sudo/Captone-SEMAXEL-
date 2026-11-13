from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.models import Usuario
from accounts.roles import (
    ofertas_visibles,
    puede_ver_oferta,
    rol_requerido,
    rol_usuario,
)
from tecnicos.models import Tecnico
from tickets.models import Ticket

from .models import OfertaTicket
from .services import OfertaNoTomable, expirar_ofertas_vencidas, tomar_oferta


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

    Las reglas viven en ofertas.services.tomar_oferta, que también usa la
    API de la app móvil; esta vista solo traduce el resultado a mensajes y
    redirecciones de la web.
    """
    oferta = get_object_or_404(OfertaTicket, pk=oid)

    if not puede_ver_oferta(request.user, oferta):
        raise PermissionDenied

    tecnico = _tecnico_actual(request)
    if tecnico is None:
        messages.error(
            request,
            "Tu usuario tiene rol Técnico pero no tiene un perfil de técnico "
            "asociado. Pídele a un administrador que lo registre en la sección "
            "Técnicos para poder tomar ofertas.",
        )
        return redirect("ofertas:detalle", oid=oferta.pk)

    try:
        orden = tomar_oferta(oferta, tecnico, usuario=request.user)
    except OfertaNoTomable as error:
        messages.warning(request, error.mensaje)
        if error.codigo == "ticket_no_permite":
            return redirect("ofertas:disponibles")
        return redirect("ofertas:detalle", oid=oferta.pk)

    messages.success(
        request,
        f"Oferta tomada. Se generó la orden de trabajo #{orden.pk:05d}.",
    )
    return redirect(f"{reverse('ofertas:detalle', args=[oferta.pk])}?tomada=1")
