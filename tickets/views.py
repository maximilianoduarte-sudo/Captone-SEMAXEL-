from django.shortcuts import get_object_or_404, redirect, render

from config import demo_data


def lista(request):
    """Listado de tickets con buscador y filtros (prototipo visual)."""
    query = request.GET.get("q", "")
    estado = request.GET.get("estado", "")
    prioridad = request.GET.get("prioridad", "")
    categoria = request.GET.get("categoria", "")

    tickets = demo_data.TICKETS
    if query:
        tickets = [t for t in tickets if query.lower() in t["titulo"].lower() or query.lower() in t["numero"].lower() or query.lower() in t["sucursal"].lower()]
    if estado:
        tickets = [t for t in tickets if t["estado"] == estado]
    if prioridad:
        tickets = [t for t in tickets if t["prioridad"] == prioridad]
    if categoria:
        tickets = [t for t in tickets if t["categoria"] == categoria]

    context = {
        "tickets": tickets,
        "query": query,
        "estado_seleccionado": estado,
        "prioridad_seleccionada": prioridad,
        "categoria_seleccionada": categoria,
        "estados": demo_data.ESTADOS,
        "prioridades": demo_data.PRIORIDADES,
        "categorias": demo_data.CATEGORIAS,
        "sucursales": demo_data.SUCURSALES,
    }
    return render(request, "tickets/lista.html", context)


def detalle(request, numero):
    """Detalle completo de un ticket (prototipo visual)."""
    ticket = demo_data.get_ticket(numero)
    if ticket is None:
        ticket = demo_data.TICKETS[0]
    historial = demo_data.HISTORIAL.get(numero, [])
    evidencias = demo_data.EVIDENCIAS.get(numero, [])
    tiene_oferta = numero in [o["ticket"] for o in demo_data.OFERTAS]

    context = {
        "ticket": ticket,
        "historial": historial,
        "evidencias": evidencias,
        "tiene_oferta": tiene_oferta,
        "estados": demo_data.ESTADOS,
        "prioridades": demo_data.PRIORIDADES,
    }
    return render(request, "tickets/detalle.html", context)


def crear(request):
    """Formulario de creación de ticket (prototipo visual)."""
    if request.method == "POST":
        return redirect("tickets:detalle", numero="TK-00001")
    context = {
        "sucursales": demo_data.SUCURSALES,
        "categorias": demo_data.CATEGORIAS,
        "prioridades": demo_data.PRIORIDADES,
    }
    return render(request, "tickets/crear.html", context)


def publicar_oferta(request, numero):
    """Interfaz para publicar una oferta asociada a un ticket (prototipo visual)."""
    ticket = demo_data.get_ticket(numero)
    if ticket is None:
        ticket = demo_data.TICKETS[0]
    context = {
        "ticket": ticket,
        "tecnicos_elegibles": demo_data.TECNICOS[:3],
    }
    return render(request, "tickets/publicar_oferta.html", context)
