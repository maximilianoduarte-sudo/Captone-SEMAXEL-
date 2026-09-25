from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from accounts.models import Usuario
from accounts.roles import empresas_visibles, rol_requerido
from sla.models import SLAPolicy
from tickets.models import Ticket

from .models import Empresa


@login_required
@rol_requerido(Usuario.Rol.ADMIN)
def lista(request):
    """Listado de empresas visibles para el usuario (superuser: todas)."""
    empresas = empresas_visibles(request.user)
    context = {"empresas": empresas}
    return render(request, "empresas/lista.html", context)


@login_required
@rol_requerido(
    Usuario.Rol.ADMIN,
    Usuario.Rol.GESTOR,
    Usuario.Rol.GERENCIA,
)
def detalle(request, pk):
    """Detalle de una empresa con sus sucursales, usuarios y tickets."""
    empresa = get_object_or_404(Empresa, pk=pk)
    if not request.user.is_superuser:
        if not empresas_visibles(request.user).filter(pk=empresa.pk).exists():
            raise PermissionDenied

    tickets = Ticket.objects.filter(sucursal__empresa=empresa)
    cantidades = {
        item["estado"]: item["cantidad"]
        for item in tickets.values("estado").annotate(cantidad=Count("id"))
    }
    estado_tickets = [
        {"etiqueta": etiqueta, "cantidad": cantidades.get(valor, 0)}
        for valor, etiqueta in Ticket.Estado.choices
    ]

    especificas = {p.prioridad: p for p in empresa.sla_policies.all()}
    globales = {p.prioridad: p for p in SLAPolicy.objects.filter(empresa__isnull=True)}
    politicas_sla = []
    for valor, etiqueta in SLAPolicy.Prioridad.choices:
        p = especificas.get(valor) or globales.get(valor)
        if p and p.activo:
            politicas_sla.append(
                {
                    "etiqueta": etiqueta,
                    "respuesta": p.tiempo_maximo_respuesta,
                    "resolucion": p.tiempo_maximo_resolucion,
                    "especifica": valor in especificas,
                }
            )

    context = {
        "empresa": empresa,
        "sucursales": empresa.sucursales.order_by("nombre"),
        "usuarios": empresa.usuarios.select_related("user").order_by("user__username"),
        "total_tickets": tickets.count(),
        "estado_tickets": estado_tickets,
        "politicas_sla": politicas_sla,
    }
    return render(request, "empresas/detalle.html", context)