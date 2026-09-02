from django.shortcuts import render

from config import demo_data


def lista(request):
    """Listado de técnicos (prototipo visual)."""
    estado = request.GET.get("estado", "")
    tecnicos = demo_data.TECNICOS
    if estado:
        tecnicos = [t for t in tecnicos if t["estado"] == estado]
    context = {"tecnicos": tecnicos, "estado_seleccionado": estado}
    return render(request, "tecnicos/lista.html", context)


def detalle(request, nombre):
    """Detalle visual de un técnico (prototipo)."""
    tecnico = demo_data.get_tecnico(nombre)
    if tecnico is None:
        tecnico = demo_data.TECNICOS[0]
    context = {"tecnico": tecnico}
    return render(request, "tecnicos/detalle.html", context)
