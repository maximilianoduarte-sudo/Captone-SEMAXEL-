from django.shortcuts import redirect, render

from config import demo_data


def tomar(request, oid):
    """Confirma la toma de la oferta (prototipo visual, sin transacción real)."""
    return redirect("ofertas:detalle", oid=oid) + "?tomada=1"


def disponibles(request):
    """Ofertas de trabajo disponibles para técnicos (prototipo visual)."""
    ofertas = [o for o in demo_data.OFERTAS if o["estado"] == "PUBLICADO"]
    context = {"ofertas": ofertas, "prioridades": demo_data.PRIORIDADES}
    return render(request, "ofertas/disponibles.html", context)


def detalle(request, oid):
    """Detalle de una oferta con opción de tomarla (prototipo visual)."""
    oferta = demo_data.get_oferta(oid)
    if oferta is None:
        oferta = demo_data.OFERTAS[0]
    context = {"oferta": oferta, "prioridades": demo_data.PRIORIDADES, "tomada": request.GET.get("tomada", "") == "1"}
    return render(request, "ofertas/detalle.html", context)
