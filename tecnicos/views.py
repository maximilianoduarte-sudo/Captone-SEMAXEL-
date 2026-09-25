from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Usuario
from accounts.roles import rol_requerido
from tickets.models import OrdenTrabajo

from .forms import TecnicoForm
from .models import Tecnico


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.ENCARGADO)
def lista(request):
    """Listado paginado de técnicos con filtro por estado."""
    estado = request.GET.get("estado", "")
    qs = Tecnico.objects.select_related("usuario").prefetch_related("especialidades").all()
    if estado:
        qs = qs.filter(estado=estado)

    paginator = Paginator(qs, 12)
    tecnicos = paginator.get_page(request.GET.get("page"))

    context = {"tecnicos": tecnicos, "estado_seleccionado": estado}
    return render(request, "tecnicos/lista.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.ENCARGADO)
def detalle(request, pk):
    """Detalle de un técnico con sus órdenes de trabajo reales."""
    tecnico = get_object_or_404(
        Tecnico.objects.select_related("usuario").prefetch_related("especialidades"),
        pk=pk,
    )
    ordenes = tecnico.ordenes_trabajo.select_related("ticket__sucursal").order_by("-fecha_creacion")[:5]
    context = {"tecnico": tecnico, "ordenes": ordenes}
    return render(request, "tecnicos/detalle.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN)
def crear(request):
    """Formulario de nuevo técnico (persistente)."""
    form = TecnicoForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Técnico registrado correctamente.")
        return redirect("tecnicos:lista")
    context = {"form": form, "titulo": "Nuevo técnico"}
    return render(request, "tecnicos/form.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN)
def editar(request, pk):
    """Formulario de edición de técnico (persistente)."""
    tecnico = get_object_or_404(Tecnico, pk=pk)
    form = TecnicoForm(request.POST or None, instance=tecnico)
    if form.is_valid():
        form.save()
        messages.success(request, "Técnico actualizado correctamente.")
        return redirect("tecnicos:detalle", pk=tecnico.pk)
    context = {"form": form, "titulo": "Editar técnico", "tecnico": tecnico}
    return render(request, "tecnicos/form.html", context)