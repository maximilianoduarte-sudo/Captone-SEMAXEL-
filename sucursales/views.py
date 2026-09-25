from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Usuario
from accounts.roles import (
    empresa_usuario,
    empresas_visibles,
    puede_ver_sucursal,
    rol_requerido,
    sucursales_visibles,
)
from tickets.models import Ticket

from .forms import SucursalForm
from .models import Sucursal


@login_required
@rol_requerido(
    Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.ENCARGADO, Usuario.Rol.GERENCIA
)
def lista(request):
    """Listado paginado de sucursales (según el alcance del rol)."""
    estado = request.GET.get("estado", "")
    qs = sucursales_visibles(request.user)
    if estado:
        qs = qs.filter(estado=estado)

    paginator = Paginator(qs, 10)
    sucursales = paginator.get_page(request.GET.get("page"))

    context = {
        "sucursales": sucursales,
        "estado_seleccionado": estado,
    }
    return render(request, "sucursales/lista.html", context)


@login_required
@rol_requerido(
    Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.ENCARGADO, Usuario.Rol.GERENCIA
)
def detalle(request, suc_id):
    """Detalle de una sucursal con indicadores reales."""
    sucursal = get_object_or_404(Sucursal, pk=suc_id)
    if not puede_ver_sucursal(request.user, sucursal):
        raise PermissionDenied
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


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.GESTOR)
def crear(request):
    """Formulario de nueva sucursal (persistente). La empresa se toma del usuario."""
    empresa = empresa_usuario(request.user) or empresas_visibles(request.user).first()
    form = SucursalForm(request.POST or None, empresa=empresa)
    if form.is_valid():
        sucursal = form.save(commit=False)
        sucursal.empresa = empresa
        sucursal.save()
        form.save_m2m()
        messages.success(request, "Sucursal creada correctamente.")
        return redirect("sucursales:lista")
    context = {"form": form, "titulo": "Nueva sucursal"}
    return render(request, "sucursales/form.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.GESTOR)
def editar(request, suc_id):
    """Formulario de edición de sucursal (persistente)."""
    sucursal = get_object_or_404(Sucursal, pk=suc_id)
    if not puede_ver_sucursal(request.user, sucursal):
        raise PermissionDenied
    form = SucursalForm(request.POST or None, instance=sucursal, empresa=sucursal.empresa)
    if form.is_valid():
        form.save()
        messages.success(request, "Sucursal actualizada correctamente.")
        return redirect("sucursales:detalle", suc_id=sucursal.pk)
    context = {"form": form, "titulo": "Editar sucursal", "sucursal": sucursal}
    return render(request, "sucursales/form.html", context)