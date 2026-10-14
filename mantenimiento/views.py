from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Usuario
from accounts.roles import (
    puede_ver_sucursal,
    rol_requerido,
    rol_usuario,
    sucursales_visibles,
)

from .forms import PlanMantenimientoForm
from .models import PlanMantenimiento
from .services import generar_tickets_preventivos

ROL_PLANES = (
    Usuario.Rol.ADMIN,
    Usuario.Rol.GESTOR,
    Usuario.Rol.ENCARGADO,
    Usuario.Rol.GERENCIA,
)

ROLES_EDITAN_PLANES = (Usuario.Rol.ADMIN, Usuario.Rol.GESTOR)


def _planes_visibles(user):
    return PlanMantenimiento.objects.filter(
        sucursal__in=sucursales_visibles(user)
    ).select_related("sucursal__empresa", "categoria")


def _generar_preventivos(user):
    """Genera los preventivos vencidos que le corresponde operar al usuario.

    Solo el ENCARGADO queda acotado a sus sucursales: los demás roles mantienen
    el alcance global que ya tenían.
    """
    sucursales = None
    if not user.is_superuser and rol_usuario(user) == Usuario.Rol.ENCARGADO:
        sucursales = sucursales_visibles(user)
    return generar_tickets_preventivos(usuario=user, sucursales=sucursales)


@login_required
@rol_requerido(*ROL_PLANES)
def lista(request):
    """Listado de planes de mantenimiento. Al abrirlo, genera los preventivos vencidos."""
    generados = 0
    if request.method == "POST":
        generados = _generar_preventivos(request.user)
        if generados:
            messages.success(
                request, f"Se generaron {generados} ticket(s) preventivo(s) automáticamente."
            )
        else:
            messages.info(request, "No hay planes vencidos por generar.")

    paginator = Paginator(_planes_visibles(request.user), 10)
    planes = paginator.get_page(request.GET.get("page"))
    context = {
        "planes": planes,
        "generados": generados,
        "puede_editar": request.user.is_superuser
        or rol_usuario(request.user) in ROLES_EDITAN_PLANES,
    }
    return render(request, "mantenimiento/lista.html", context)


@login_required
@rol_requerido(*ROL_PLANES)
def detalle(request, pk):
    """Detalle de un plan con su historial de programaciones."""
    plan = get_object_or_404(
        _planes_visibles(request.user).prefetch_related("programaciones__ticket"), pk=pk
    )
    if not puede_ver_sucursal(request.user, plan.sucursal):
        raise PermissionDenied
    context = {
        "plan": plan,
        "programaciones": plan.programaciones.select_related("ticket")[:20],
        "puede_editar": request.user.is_superuser
        or rol_usuario(request.user) in ROLES_EDITAN_PLANES,
    }
    return render(request, "mantenimiento/detalle.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.GESTOR)
def crear(request):
    """Formulario de nuevo plan de mantenimiento."""
    form = PlanMantenimientoForm(request.POST or None, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Plan de mantenimiento creado correctamente.")
        return redirect("mantenimiento:detalle", pk=form.instance.pk)
    context = {"form": form, "titulo": "Nuevo plan de mantenimiento"}
    return render(request, "mantenimiento/form.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.GESTOR)
def editar(request, pk):
    """Formulario de edición de un plan de mantenimiento."""
    plan = get_object_or_404(_planes_visibles(request.user), pk=pk)
    if not puede_ver_sucursal(request.user, plan.sucursal):
        raise PermissionDenied
    form = PlanMantenimientoForm(request.POST or None, instance=plan, user=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Plan de mantenimiento actualizado correctamente.")
        return redirect("mantenimiento:detalle", pk=plan.pk)
    context = {"form": form, "titulo": "Editar plan de mantenimiento", "plan": plan}
    return render(request, "mantenimiento/form.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.GESTOR)
def generar(request):
    """Genera ahora los tickets preventivos vencidos (acción manual)."""
    generados = _generar_preventivos(request.user)
    if generados:
        messages.success(
            request, f"Se generaron {generados} ticket(s) preventivo(s) automáticamente."
        )
    else:
        messages.info(request, "No hay planes vencidos por generar.")
    return redirect("mantenimiento:lista")