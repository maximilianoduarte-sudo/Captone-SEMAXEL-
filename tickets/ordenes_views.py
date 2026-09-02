from django.shortcuts import render

from config import demo_data


def lista(request):
    """Listado de órdenes de trabajo (prototipo visual)."""
    estado = request.GET.get("estado", "")
    tecnico = request.GET.get("tecnico", "")

    ordenes = demo_data.ORDENES
    if estado:
        ordenes = [o for o in ordenes if o["estado"] == estado]
    if tecnico:
        ordenes = [o for o in ordenes if o["tecnico"] == tecnico]

    estados = {
        "ASIGNADA": "Asignada",
        "EN_EJECUCION": "En ejecución",
        "RESUELTA": "Resuelta",
        "CERRADA": "Cerrada",
        "CANCELADA": "Cancelada",
    }
    context = {
        "ordenes": ordenes,
        "estado_seleccionado": estado,
        "tecnico_seleccionado": tecnico,
        "estados": estados,
        "tecnicos": demo_data.TECNICOS,
    }
    return render(request, "tickets/ordenes_lista.html", context)


def detalle(request, oid):
    """Detalle de una orden de trabajo (prototipo visual)."""
    orden = demo_data.get_orden(oid)
    if orden is None:
        orden = demo_data.ORDENES[0]
    estados = {
        "ASIGNADA": "Asignada",
        "EN_EJECUCION": "En ejecución",
        "RESUELTA": "Resuelta",
        "CERRADA": "Cerrada",
        "CANCELADA": "Cancelada",
    }
    context = {"orden": orden, "estados": estados}
    return render(request, "tickets/orden_detalle.html", context)
