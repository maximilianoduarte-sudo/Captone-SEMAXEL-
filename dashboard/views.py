from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F
from django.shortcuts import render

from accounts.models import Usuario
from accounts.roles import (
    ofertas_visibles,
    ordenes_visibles,
    rol_requerido,
    tickets_visibles,
)
from ofertas.models import OfertaTicket
from ofertas.services import expirar_ofertas_vencidas
from tecnicos.models import Tecnico
from tickets.models import Calificacion, OrdenTrabajo, Ticket


def handler403(request, exception=None):
    """Página de acceso denegado (403)."""
    return render(request, "403.html", status=403)


def _cumplimiento_sla(tickets):
    """% de tickets cerrados/resueltos dentro de su fecha_limite_sla."""
    cerrados = tickets.filter(
        estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.RESUELTO],
        fecha_limite_sla__isnull=False,
    )
    total = cerrados.count()
    if not total:
        return 100
    cumplidos = cerrados.filter(fecha_cierre__lte=F("fecha_limite_sla")).count()
    return round(cumplidos / total * 100)


@login_required
@rol_requerido(
    Usuario.Rol.ADMIN,
    Usuario.Rol.GESTOR,
    Usuario.Rol.ENCARGADO,
    Usuario.Rol.GERENCIA,
)
def dashboard(request):
    """Dashboard con indicadores y gráficos según el alcance del usuario.

    No accesible para el rol TECNICO (su espacio de trabajo es Ofertas).
    """
    expirar_ofertas_vencidas(usuario=request.user)
    tickets = tickets_visibles(request.user)
    ticket_estados = [
        {
            "estado": estado,
            "label": label,
            "cantidad": tickets.filter(estado=estado).count(),
        }
        for estado, label in dict(Ticket.Estado.choices).items()
    ]
    ticket_prioridades = [
        {
            "prioridad": prioridad,
            "label": label,
            "cantidad": tickets.filter(prioridad=prioridad).count(),
        }
        for prioridad, label in dict(Ticket.Prioridad.choices).items()
    ]

    cerrados_resueltos = tickets.filter(
        estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.RESUELTO]
    ).count()
    total = tickets.count()
    cumplimiento_sla = _cumplimiento_sla(tickets)

    ofertas = ofertas_visibles(request.user).filter(
        estado=OfertaTicket.Estado.DISPONIBLE
    )

    context = {
        "tickets_abiertos": tickets.exclude(
            estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.CANCELADO]
        ).count(),
        "tickets_criticos": tickets.filter(prioridad=Ticket.Prioridad.CRITICA).count(),
        "tickets_ejecucion": tickets.filter(estado=Ticket.Estado.EN_EJECUCION).count(),
        "tickets_resueltos": cerrados_resueltos,
        "ofertas_disponibles": ofertas.count(),
        "ordenes_trabajo": ordenes_visibles(request.user).count(),
        "cumplimiento_sla": cumplimiento_sla,
        "no_cumplimiento_sla": 100 - cumplimiento_sla,
        "tickets_recientes": tickets.select_related("sucursal").order_by("-fecha_creacion")[:6],
        "estado_labels": [e["label"] for e in ticket_estados],
        "estado_values": [e["cantidad"] for e in ticket_estados],
        "estado_colors": ["#0d6efd", "#f59e0b", "#8b5cf6", "#4f46e5", "#10b981", "#6b7280", "#dc2626"],
        "prioridad_labels": [p["label"] for p in ticket_prioridades],
        "prioridad_values": [p["cantidad"] for p in ticket_prioridades],
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.GERENCIA)
def reportes(request):
    """Reportes con indicadores reales y gráficos, según el alcance del usuario."""
    tickets = tickets_visibles(request.user)
    ordenes = ordenes_visibles(request.user)
    promedio_calificaciones = (
        Calificacion.objects.filter(orden_trabajo__in=ordenes).aggregate(
            avg=Avg("puntuacion")
        )["avg"]
        or 0
    )

    por_sucursal = (
        tickets.values("sucursal__nombre")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    por_categoria = (
        tickets.values("categoria__nombre")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    por_tecnico = (
        ordenes.exclude(tecnico__isnull=True)
        .values("tecnico__usuario__username")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    por_estado = [
        {
            "label": label,
            "total": tickets.filter(estado=estado).count(),
        }
        for estado, label in dict(Ticket.Estado.choices).items()
    ]
    por_prioridad = [
        {
            "label": label,
            "total": tickets.filter(prioridad=prioridad).count(),
        }
        for prioridad, label in dict(Ticket.Prioridad.choices).items()
    ]

    context = {
        "cumplimiento_sla": _cumplimiento_sla(tickets),
        "tickets_totales": tickets.count(),
        "calificacion_promedio": round(promedio_calificaciones, 2),
        "tecnicos_activos": Tecnico.objects.filter(estado__in=[
            Tecnico.Estado.DISPONIBLE, Tecnico.Estado.OCUPADO
        ]).count(),
        "sucursal_labels": [r["sucursal__nombre"] for r in por_sucursal],
        "sucursal_values": [r["total"] for r in por_sucursal],
        "sucursal_rows": [
            {"label": r["sucursal__nombre"], "total": r["total"]} for r in por_sucursal
        ],
        "categoria_labels": [r["categoria__nombre"] for r in por_categoria],
        "categoria_values": [r["total"] for r in por_categoria],
        "tecnico_labels": [r["tecnico__usuario__username"] for r in por_tecnico],
        "tecnico_values": [r["total"] for r in por_tecnico],
        "estado_labels": [e["label"] for e in por_estado],
        "estado_values": [e["total"] for e in por_estado],
        "prioridad_labels": [p["label"] for p in por_prioridad],
        "prioridad_values": [p["total"] for p in por_prioridad],
    }
    return render(request, "dashboard/reportes.html", context)