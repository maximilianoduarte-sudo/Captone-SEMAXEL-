from django.shortcuts import redirect, render

from config import demo_data


def login(request):
    """Pantalla de acceso (prototipo visual, sin autenticación real)."""
    if request.method == "POST":
        return redirect("dashboard")
    return render(request, "dashboard/login.html")


def dashboard(request):
    """Dashboard principal con indicadores y gráficos (datos ficticios)."""
    context = {
        "tickets_abiertos": 3,
        "tickets_criticos": 2,
        "tickets_ejecucion": 4,
        "tickets_resueltos": 12,
        "ofertas_disponibles": 4,
        "ordenes_trabajo": 6,
        "cumplimiento_sla": 92,
        "tickets_recientes": demo_data.TICKETS[:6],
        "estados": demo_data.ESTADOS,
    }
    return render(request, "dashboard/dashboard.html", context)


def perfil(request):
    """Pantalla de perfil del usuario actual (prototipo visual)."""
    return render(request, "dashboard/perfil.html")


def reportes(request):
    """Pantalla de reportes (prototipo visual)."""
    return render(request, "dashboard/reportes.html")
