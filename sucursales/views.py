from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from tickets.models import Ticket

from .forms import SucursalForm
from .models import Sucursal


def lista(request):
    """Listado paginado de sucursales."""
    estado = request.GET.get("estado", "")
    qs = Sucursal.objects.all()
    if estado:
        qs = qs.filter(estado=estado)

    paginator = Paginator(qs, 10)
    sucursales = paginator.get_page(request.GET.get("page"))

    context = {
        "sucursales": sucursales,
        "estado_seleccionado": estado,
    }
    return render(request, "sucursales/lista.html", context)


def detalle(request, suc_id):
    """Detalle de una sucursal con indicadores reales."""
    sucursal = get_object_or_404(Sucursal, pk=suc_id)
    tickets = sucursal.tickets.all()
    resueltos = tickets.filter(
        estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.RESUELTO]
    ).count()
    total = tickets.count()
    context = {
        "sucursal": sucursal,
        "total_tickets": total,
        "tickets_abiertos": tickets.exclude(
            estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.CANCELADO]
        ).count(),
        "sla": round(resueltos / total * 100) if total else 100,
        "tickets_recientes": tickets.order_by("-fecha_creacion")[:5],
    }
    return render(request, "sucursales/detalle.html", context)


def crear(request):
    """Formulario de nueva sucursal (persistente)."""
    form = SucursalForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Sucursal creada correctamente.")
        return redirect("sucursales:lista")
    context = {"form": form, "titulo": "Nueva sucursal"}
    return render(request, "sucursales/form.html", context)


def editar(request, suc_id):
    """Formulario de edición de sucursal (persistente)."""
    sucursal = get_object_or_404(Sucursal, pk=suc_id)
    form = SucursalForm(request.POST or None, instance=sucursal)
    if form.is_valid():
        form.save()
        messages.success(request, "Sucursal actualizada correctamente.")
        return redirect("sucursales:detalle", suc_id=sucursal.pk)
    context = {"form": form, "titulo": "Editar sucursal", "sucursal": sucursal}
    return render(request, "sucursales/form.html", context)