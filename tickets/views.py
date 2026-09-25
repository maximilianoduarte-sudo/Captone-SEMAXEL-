from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Usuario
from accounts.roles import puede_ver_ticket, rol_requerido, tickets_visibles
from ofertas.forms import OfertaForm
from ofertas.models import OfertaTicket
from tecnicos.models import Tecnico

from .forms import CambiarEstadoForm, TicketForm
from .models import Categoria, EvidenciaTicket, Ticket, TicketHistorial


def _proximo_numero(sucursal):
    """Siguiente número de ticket, con secuencia independiente por empresa.

    Formato: <codigo_empresa>-<correlativo> (p. ej. SEMAXEL-00001). Como el
    código de empresa es único, los números no colisionan entre empresas.
    """
    empresa = sucursal.empresa
    prefix = f"{empresa.codigo}-"
    ultimo = (
        Ticket.objects.filter(sucursal__empresa=empresa, numero__startswith=prefix)
        .order_by("-numero")
        .first()
    )
    if not ultimo or not ultimo.numero.split("-")[-1].isdigit():
        return f"{prefix}00001"
    numero_siguiente = int(ultimo.numero.split("-")[-1]) + 1
    return f"{prefix}{numero_siguiente:05d}"


def _registrar_historial(ticket, usuario, estado_anterior, estado_nuevo, comentario=""):
    TicketHistorial.objects.create(
        ticket=ticket,
        usuario=usuario or ticket.creador,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        comentario=comentario,
    )


@login_required
@rol_requerido(
    Usuario.Rol.ADMIN,
    Usuario.Rol.GESTOR,
    Usuario.Rol.ENCARGADO,
    Usuario.Rol.GERENCIA,
)
def lista(request):
    """Listado paginado de tickets con búsqueda y filtros (alcance por rol).

    No accesible para el rol TECNICO: el técnico llega a los trabajos vía
    ofertas y a los tickets asociados a sus órdenes, no al listado general.
    """
    query = request.GET.get("q", "")
    estado = request.GET.get("estado", "")
    prioridad = request.GET.get("prioridad", "")
    categoria = request.GET.get("categoria", "")

    qs = tickets_visibles(request.user).select_related("sucursal", "categoria", "creador")
    if query:
        qs = qs.filter(
            Q(titulo__icontains=query)
            | Q(numero__icontains=query)
            | Q(sucursal__nombre__icontains=query)
        )
    if estado:
        qs = qs.filter(estado=estado)
    if prioridad:
        qs = qs.filter(prioridad=prioridad)
    if categoria:
        qs = qs.filter(categoria__nombre=categoria)

    paginator = Paginator(qs, 10)
    tickets = paginator.get_page(request.GET.get("page"))

    context = {
        "tickets": tickets,
        "query": query,
        "estado_seleccionado": estado,
        "prioridad_seleccionada": prioridad,
        "categoria_seleccionada": categoria,
        "estados": dict(Ticket.Estado.choices),
        "prioridades": dict(Ticket.Prioridad.choices),
        "categorias": Categoria.objects.filter(activo=True),
    }
    return render(request, "tickets/lista.html", context)


@login_required
def detalle(request, numero):
    """Detalle completo de un ticket con historial y evidencias."""
    ticket = get_object_or_404(
        Ticket.objects.select_related("sucursal", "categoria", "creador"),
        numero=numero,
    )
    if not puede_ver_ticket(request.user, ticket):
        raise PermissionDenied
    context = {
        "ticket": ticket,
        "historial": ticket.historial.select_related("usuario").order_by("fecha_cambio")[:20],
        "evidencias": ticket.evidencias.all()[:10],
        "form_estado": CambiarEstadoForm(
            initial={"estado": ticket.estado}, estado_actual=ticket.estado
        ),
        "estados": dict(Ticket.Estado.choices),
        "prioridades": dict(Ticket.Prioridad.choices),
    }
    return render(request, "tickets/detalle.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.ENCARGADO)
def crear(request):
    """Formulario de creación de ticket (persistente, genera número e historial)."""
    form = TicketForm(request.POST or None, user=request.user)
    if form.is_valid():
        ticket = form.save(commit=False)
        creador = request.user
        if creador is None:
            messages.error(request, "No hay usuarios disponibles para registrar el ticket. Cree un usuario primero.")
            return render(request, "tickets/crear.html", {"form": form})
        ticket.creador = creador
        ticket.numero = _proximo_numero(ticket.sucursal)
        ticket.estado = Ticket.Estado.ABIERTO
        ticket.save()
        _registrar_historial(
            ticket,
            creador,
            estado_anterior=None,
            estado_nuevo=Ticket.Estado.ABIERTO,
            comentario="Creación del ticket por incidencia.",
        )
        for archivo in request.FILES.getlist("evidencia"):
            EvidenciaTicket.objects.create(ticket=ticket, archivo=archivo, nombre=archivo.name)
        messages.success(request, f"Ticket {ticket.numero} creado correctamente.")
        return redirect("tickets:detalle", numero=ticket.numero)

    context = {"form": form}
    return render(request, "tickets/crear.html", context)


@login_required
@rol_requerido(Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.ENCARGADO)
def publicar_oferta(request, numero):
    """Publica (o reactiva) la oferta asociada a un ticket."""
    ticket = get_object_or_404(Ticket, numero=numero)
    if not puede_ver_ticket(request.user, ticket):
        raise PermissionDenied
    if not (ticket.estado in (Ticket.Estado.ABIERTO, Ticket.Estado.EN_REVISION, Ticket.Estado.PUBLICADO)):
        messages.error(
            request,
            "No se puede publicar una oferta para un ticket en su estado actual.",
        )
        return redirect("tickets:detalle", numero=numero)
    oferta, _ = OfertaTicket.objects.get_or_create(ticket=ticket)
    form = OfertaForm(request.POST or None, instance=oferta)

    if form.is_valid():
        oferta = form.save(commit=False)
        oferta.estado = OfertaTicket.Estado.DISPONIBLE
        oferta.save()
        if ticket.estado != Ticket.Estado.PUBLICADO:
            _registrar_historial(
                ticket,
                request.user,
                ticket.estado,
                Ticket.Estado.PUBLICADO,
                "Se publicó la oferta para técnicos.",
            )
            ticket.estado = Ticket.Estado.PUBLICADO
            ticket.save()
        messages.success(request, "Oferta publicada correctamente.")
        return redirect("ofertas:detalle", oid=oferta.pk)

    tecnicos_elegibles = Tecnico.objects.filter(estado=Tecnico.Estado.DISPONIBLE).select_related("usuario").prefetch_related("especialidades")[:5]
    context = {"ticket": ticket, "form": form, "tecnicos_elegibles": tecnicos_elegibles}
    return render(request, "tickets/publicar_oferta.html", context)


@login_required
@rol_requerido(
    Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.ENCARGADO, Usuario.Rol.TECNICO
)
def cambiar_estado(request, numero):
    """Cambia el estado de un ticket y registra el cambio en el historial."""
    ticket = get_object_or_404(Ticket, numero=numero)
    if not puede_ver_ticket(request.user, ticket):
        raise PermissionDenied
    if request.method == "POST":
        estado_anterior = ticket.estado
        form = CambiarEstadoForm(
            request.POST, instance=ticket, estado_actual=ticket.estado
        )
        if form.is_valid():
            estado_nuevo = form.cleaned_data["estado"]
            if estado_anterior != estado_nuevo:
                form.save()
                if estado_nuevo in (
                    Ticket.Estado.RESUELTO,
                    Ticket.Estado.CERRADO,
                    Ticket.Estado.CANCELADO,
                ):
                    ticket.fecha_cierre = timezone.now()
                    ticket.save(update_fields=["fecha_cierre"])
                _registrar_historial(
                    ticket,
                    request.user,
                    estado_anterior,
                    estado_nuevo,
                    form.cleaned_data["comentario"],
                )
                messages.success(request, "Estado del ticket actualizado.")
            else:
                messages.info(request, "El ticket ya se encuentra en ese estado.")
        else:
            messages.error(request, "No se pudo actualizar el estado.")
    return redirect("tickets:detalle", numero=numero)