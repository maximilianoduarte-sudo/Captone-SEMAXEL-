from django.shortcuts import render

from config import demo_data


def lista(request):
    """Listado de planes de mantenimiento preventivo (prototipo visual)."""
    context = {"planes": demo_data.PLANES_MANTENIMIENTO}
    return render(request, "mantenimiento/lista.html", context)
