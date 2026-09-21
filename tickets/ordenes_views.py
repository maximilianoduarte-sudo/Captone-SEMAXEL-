from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from tecnicos.models import Tecnico

from .models import OrdenTrabajo


def lista(request):
    """Listado paginado de órdenes de trabajo con filtros."""
    estado = request.GET.get("estado", "")
    tecnico_id = request.GET.get("tecnico", "")

    qs = OrdenTrabajo.objects.select_related("ticket__sucursal", "tecnico__usuario", "oferta").all()
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


def detalle(request, oid):
    """Detalle de una orden de trabajo."""
    orden = get_object_or_404(
        OrdenTrabajo.objects.select_related("ticket__sucursal", "tecnico__usuario", "oferta"),
        pk=oid,
    )
    context = {"orden": orden, "estados": dict(OrdenTrabajo.Estado.choices)}
    return render(request, "tickets/orden_detalle.html", context)