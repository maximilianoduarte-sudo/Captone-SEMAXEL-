from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Usuario
from accounts.roles import (
    es_encargado_de,
    ordenes_visibles,
    pertenece_a_empresa,
    rol_usuario,
)
from tecnicos.models import Tecnico

from .forms import CambioEstadoOrdenForm
from .models import OrdenTrabajo
from .services import (
    TransicionNoPermitida,
    cambiar_estado_orden,
    transiciones_permitidas,
)


@login_required
def lista(request):
    """Listado paginado de órdenes de trabajo con filtros y alcance por rol."""
    estado = request.GET.get("estado", "")
    tecnico_id = request.GET.get("tecnico", "")

    qs = ordenes_visibles(request.user).select_related("ticket__sucursal", "tecnico__usuario", "oferta")
    if estado:
        qs = qs.filter(estado=estado)
    if tecnico_id:
        qs = qs.filter(tecnico_id=tecnico_id)

    paginator = Paginator(qs, 10)
    ordenes = paginator.get_page(request.GET.get("page"))

    context = {
        "ordenes": ordenes,
        "estado_seleccionado": estado,
        "tecnico_seleccionado": tecnico_id,
        "estados": dict(OrdenTrabajo.Estado.choices),
        "tecnicos": Tecnico.objects.select_related("usuario").all(),
    }
    return render(request, "tickets/ordenes_lista.html", context)


@login_required
def detalle(request, oid):
    """Detalle de una orden de trabajo (alcance según rol)."""
    orden = get_object_or_404(
        OrdenTrabajo.objects.select_related("ticket__sucursal", "tecnico__usuario", "oferta"),
        pk=oid,
    )
    if not _acceso_orden(request.user, orden):
        raise PermissionDenied
    # Solo se ofrecen las transiciones que este usuario puede aplicar
    # (el técnico no cierra ni cancela; Gerencia no aplica ninguna).
    permitidos = transiciones_permitidas(request.user, orden)
    context = {
        "orden": orden,
        "estados": dict(OrdenTrabajo.Estado.choices),
        "form_estado": CambioEstadoOrdenForm(instance=orden, estados_permitidos=permitidos),
        "puede_cerrar": OrdenTrabajo.Estado.CERRADA in permitidos,
        "puede_cancelar": OrdenTrabajo.Estado.CANCELADA in permitidos,
        "orden_terminal": orden.estado in (
            OrdenTrabajo.Estado.CERRADA,
            OrdenTrabajo.Estado.CANCELADA,
        ),
    }
    return render(request, "tickets/orden_detalle.html", context)


@login_required
def cambiar_estado(request, oid):
    """Aplica una transición de la orden desde la web.

    Las reglas viven en tickets.services.cambiar_estado_orden, que también
    usa la API de la app móvil; esta vista lee el formulario y traduce el
    resultado a mensajes y redirecciones.
    """
    orden = get_object_or_404(
        OrdenTrabajo.objects.select_related("ticket", "tecnico"), pk=oid
    )
    if not _acceso_orden(request.user, orden):
        raise PermissionDenied
    if request.method != "POST":
        return redirect("ordenes:detalle", oid=orden.pk)

    form = CambioEstadoOrdenForm(request.POST, instance=orden)
    if not form.is_valid():
        messages.error(request, "No se pudo aplicar la transición a la orden.")
        return redirect("ordenes:detalle", oid=orden.pk)

    destino = form.cleaned_data["estado"]
    try:
        cambiar_estado_orden(orden, destino, request.user, datos=form.cleaned_data)
    except TransicionNoPermitida as error:
        if error.codigo == "sin_permiso":
            raise PermissionDenied
        if error.codigo == "sin_cambio":
            messages.info(request, error.mensaje)
        else:
            messages.error(request, error.mensaje)
        return redirect("ordenes:detalle", oid=orden.pk)

    if destino == OrdenTrabajo.Estado.CERRADA:
        messages.success(request, "Orden cerrada con calificación registrada.")
    else:
        etiqueta = dict(OrdenTrabajo.Estado.choices)[destino]
        messages.success(request, f"Orden actualizada: {etiqueta}.")
    return redirect("ordenes:detalle", oid=orden.pk)


def _acceso_orden(user, orden):
    """True si el usuario puede ver la orden según su rol y empresa."""
    rol = rol_usuario(user)
    if user.is_superuser:
        return True
    if rol in (Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.GERENCIA):
        return pertenece_a_empresa(user, orden.ticket.sucursal.empresa_id)
    if rol == Usuario.Rol.TECNICO:
        return orden.tecnico.usuario == user
    if rol == Usuario.Rol.ENCARGADO:
        return es_encargado_de(user, orden.ticket.sucursal)
    return False