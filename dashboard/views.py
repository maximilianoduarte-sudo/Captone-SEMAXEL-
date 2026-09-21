from django.contrib.auth import logout as auth_logout
from django.db.models import Avg, Count
from django.shortcuts import redirect, render

from ofertas.models import OfertaTicket
from tecnicos.models import Tecnico
from tickets.models import Calificacion, OrdenTrabajo, Ticket


def login(request):
    """Pantalla de acceso (autenticación real se integra en la Fase 5)."""
    if request.method == "POST":
        return redirect("dashboard")
    return render(request, "dashboard/login.html")


def logout(request):
    """Cierra la sesión del usuario y vuelve al login."""
    auth_logout(request)
    return redirect("login")


def dashboard(request):
    """Dashboard con indicadores y gráficos calculados desde la base de datos."""
    tickets = Ticket.objects.all()
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
    cumplimiento_sla = round(cerrados_resueltos / total * 100) if total else 100

    context = {
        "tickets_abiertos": tickets.exclude(
            estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.CANCELADO]
        ).count(),
        "tickets_criticos": tickets.filter(prioridad=Ticket.Prioridad.CRITICA).count(),
        "tickets_ejecucion": tickets.filter(estado=Ticket.Estado.EN_EJECUCION).count(),
        "tickets_resueltos": cerrados_resueltos,
        "ofertas_disponibles": OfertaTicket.objects.filter(
            estado=OfertaTicket.Estado.DISPONIBLE
        ).count(),
        "ordenes_trabajo": OrdenTrabajo.objects.count(),
        "cumplimiento_sla": cumplimiento_sla,
        "tickets_recientes": tickets.select_related("sucursal").order_by("-fecha_creacion")[:6],
        "estado_labels": [e["label"] for e in ticket_estados],
        "estado_values": [e["cantidad"] for e in ticket_estados],
        "estado_colors": ["#0d6efd", "#f59e0b", "#8b5cf6", "#4f46e5", "#10b981", "#6b7280", "#dc2626"],
        "prioridad_labels": [p["label"] for p in ticket_prioridades],
        "prioridad_values": [p["cantidad"] for p in ticket_prioridades],
    }
    return render(request, "dashboard/dashboard.html", context)


def perfil(request):
    """Perfil del usuario autenticado (datos reales)."""
    return render(request, "dashboard/perfil.html")


def reportes(request):
    """Reportes con indicadores calculados desde la base de datos."""
    tickets = Ticket.objects.all()
    promedio_calificaciones = (
        Calificacion.objects.aggregate(avg=Avg("puntuacion"))["avg"] or 0
    )
    context = {
        "cumplimiento_sla": round(
            tickets.filter(estado__in=[Ticket.Estado.CERRADO, Ticket.Estado.RESUELTO]).count()
            / tickets.count() * 100
        ) if tickets.count() else 100,
        "tickets_totales": tickets.count(),
        "calificacion_promedio": round(promedio_calificaciones, 2),
        "tecnicos_activos": Tecnico.objects.filter(estado__in=[
            Tecnico.Estado.DISPONIBLE, Tecnico.Estado.OCUPADO
        ]).count(),
    }
    return render(request, "dashboard/reportes.html", context)