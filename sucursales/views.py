from django.shortcuts import render

from config import demo_data


def lista(request):
    """Listado de sucursales (prototipo visual)."""
    context = {"sucursales": demo_data.SUCURSALES, "estado_seleccionado": request.GET.get("estado", "")}
    return render(request, "sucursales/lista.html", context)


def crear(request):
    """Formulario de nueva sucursal (prototipo visual)."""
    context = {"sucursales": demo_data.SUCURSALES, "usuarios": demo_data.TECNICOS}
    return render(request, "sucursales/form.html", context)


def detalle(request, suc_id):
    """Detalle de una sucursal (prototipo visual)."""
    sucursal = next((s for s in demo_data.SUCURSALES if s["id"] == int(suc_id)), demo_data.SUCURSALES[0])
    context = {"sucursal": sucursal}
    return render(request, "sucursales/detalle.html", context)
