from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Usuario
from accounts.roles import ordenes_visibles, pertenece_a_empresa, rol_usuario, sucursales_visibles
from tecnicos.models import Tecnico

from .forms import CambioEstadoOrdenForm
from .models import Calificacion, OrdenTrabajo, Ticket, TicketHistorial


@login_required
def lista(request):
    """Listado paginado de órdenes de trabajo con filtros y alcance por rol."""
    estado = request.GET.get("estado", "")
    tecnico_id = request.GET.get("tecnico", "")

    qs = ordenes_visibles(request.user).select_related("ticket__sucursal", "tecnico__usuario", "oferta")
    if estado:
        qs = qs.filter(estado=estado)
    if tecnico_id:
        qs = qs.filter(tecnico_id=tecnico_id)

    paginator = Paginator(qs, 10)
    ordenes = paginator.get_page(request.GET.get("page"))

    context = {
        "ordenes": ordenes,
        "estado_seleccionado": estado,
        "tecnico_seleccionado": tecnico_id,
        "estados": dict(OrdenTrabajo.Estado.choices),
        "tecnicos": Tecnico.objects.select_related("usuario").all(),
    }
    return render(request, "tickets/ordenes_lista.html", context)


@login_required
def detalle(request, oid):
    """Detalle de una orden de trabajo (alcance según rol)."""
    orden = get_object_or_404(
        OrdenTrabajo.objects.select_related("ticket__sucursal", "tecnico__usuario", "oferta"),
        pk=oid,
    )
    if not _acceso_orden(request.user, orden):
        raise PermissionDenied
    permitidos = set(orden.transiciones_validas())
    if (
        not request.user.is_superuser
        and rol_usuario(request.user) == Usuario.Rol.TECNICO
    ):
        permitidos -= {
            OrdenTrabajo.Estado.CERRADA,
            OrdenTrabajo.Estado.CANCELADA,
        }
    context = {
        "orden": orden,
        "estados": dict(OrdenTrabajo.Estado.choices),
        "form_estado": CambioEstadoOrdenForm(instance=orden, estados_permitidos=permitidos),
        "puede_cerrar": OrdenTrabajo.Estado.CERRADA in permitidos,
        "puede_cancelar": OrdenTrabajo.Estado.CANCELADA in permitidos,
        "orden_terminal": orden.estado in (
            OrdenTrabajo.Estado.CERRADA,
            OrdenTrabajo.Estado.CANCELADA,
        ),
    }
    return render(request, "tickets/orden_detalle.html", context)


@login_required
def cambiar_estado(request, oid):
    """Ejecuta una transición de la máquina de estados de la orden y sincroniza
    ticket (estado + historial), técnico (disponibilidad) y calificación."""
    orden = get_object_or_404(
        OrdenTrabajo.objects.select_related("ticket", "tecnico"), pk=oid
    )
    if not _acceso_orden(request.user, orden):
        raise PermissionDenied
    if request.method != "POST":
        return redirect("ordenes:detalle", oid=orden.pk)

    estado_anterior = orden.estado

    form = CambioEstadoOrdenForm(request.POST, instance=orden)
    if not form.is_valid():
        messages.error(request, "No se pudo aplicar la transición a la orden.")
        return redirect("ordenes:detalle", oid=orden.pk)

    destino = form.cleaned_data["estado"]
    if destino == estado_anterior:
        messages.info(request, "La orden ya se encuentra en ese estado.")
        return redirect("ordenes:detalle", oid=orden.pk)

    if not _puede_aplicar_transicion(request.user, orden, destino):
        raise PermissionDenied

    _aplicar_campos(orden, form, destino)
    _sincronizar_ticket_y_tecnico(orden, form, request.user)

    if destino == OrdenTrabajo.Estado.CERRADA:
        puntuacion = form.cleaned_data["puntuacion"]
        if puntuacion:
            Calificacion.objects.update_or_create(
                orden_trabajo=orden,
                defaults={
                    "tecnico": orden.tecnico,
                    "puntuacion": puntuacion,
                    "comentario": form.cleaned_data["comentario_calificacion"],
                },
            )
        messages.success(request, "Orden cerrada con calificación registrada.")
    else:
        etiqueta = dict(OrdenTrabajo.Estado.choices)[destino]
        messages.success(request, f"Orden actualizada: {etiqueta}.")
    return redirect("ordenes:detalle", oid=orden.pk)


def _aplicar_campos(orden, form, destino):
    """Aplica los datos de ejecución sin pisar valores existentes por blancos.

    Los campos de trabajo/costos solo se actualizan en transiciones de
    ejecución (iniciar/avanzar); al cerrar o cancelar no se tocan.
    """
    datos = form.cleaned_data
    es_transicion_trabajo = destino in (
        OrdenTrabajo.Estado.EN_EJECUCION,
        OrdenTrabajo.Estado.RESUELTA,
    )
    if es_transicion_trabajo:
        for campo in (
            "diagnostico",
            "trabajo_realizado",
            "observaciones",
            "costo_estimado",
            "costo_final",
        ):
            valor = datos.get(campo)
            if valor not in (None, ""):
                setattr(orden, campo, valor)
    orden.estado = destino
    orden.save(update_fields=["estado"] + (
        ["diagnostico", "trabajo_realizado", "observaciones", "costo_estimado", "costo_final"]
        if es_transicion_trabajo else []
    ))


def _puede_aplicar_transicion(user, orden, destino):
    """Quién puede aplicar cada transición: el técnico de la orden para la
    ejecución; ADMIN/GESTOR/ENCARGADO para cerrar o cancelar."""
    rol = rol_usuario(user)
    es_tecnico = not user.is_superuser and rol == Usuario.Rol.TECNICO
    if destino in (
        OrdenTrabajo.Estado.CERRADA,
        OrdenTrabajo.Estado.CANCELADA,
    ):
        return not es_tecnico
    if es_tecnico:
        return orden.tecnico.usuario_id == user.id
    return True


def _sincronizar_ticket_y_tecnico(orden, form, usuario):
    """Sincroniza fechas de la orden, estado del ticket (con historial) y
    libera al técnico cuando la orden ya no está activa."""
    destino = form.cleaned_data["estado"]
    ahora = timezone.now()

    if destino == OrdenTrabajo.Estado.EN_EJECUCION and not orden.fecha_inicio:
        orden.fecha_inicio = ahora
        orden.save(update_fields=["fecha_inicio"])
    elif destino == OrdenTrabajo.Estado.RESUELTA:
        if not orden.fecha_fin:
            orden.fecha_fin = ahora
            orden.save(update_fields=["fecha_fin"])
        _liberar_tecnico(orden, orden.tecnico)
    elif destino in (
        OrdenTrabajo.Estado.CERRADA,
        OrdenTrabajo.Estado.CANCELADA,
    ):
        if not orden.fecha_fin:
            orden.fecha_fin = ahora
            orden.save(update_fields=["fecha_fin"])
        _liberar_tecnico(orden, orden.tecnico)

    destino_ticket = {
        OrdenTrabajo.Estado.RESUELTA: Ticket.Estado.RESUELTO,
        OrdenTrabajo.Estado.CERRADA: Ticket.Estado.CERRADO,
        OrdenTrabajo.Estado.CANCELADA: Ticket.Estado.CANCELADO,
    }.get(destino)
    ticket = orden.ticket
    if destino_ticket and ticket.puede_transicionar_a(destino_ticket):
        estado_anterior = ticket.estado
        ticket.estado = destino_ticket
        ticket.fecha_cierre = ahora
        ticket.save(update_fields=["estado", "fecha_cierre"])
        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=usuario,
            estado_anterior=estado_anterior,
            estado_nuevo=destino_ticket,
            comentario=f"Sincronizado desde la orden #{orden.pk} ({destino}).",
        )
    elif destino == OrdenTrabajo.Estado.EN_EJECUCION and ticket.estado != Ticket.Estado.EN_EJECUCION:
        if ticket.puede_transicionar_a(Ticket.Estado.EN_EJECUCION):
            estado_anterior = ticket.estado
            ticket.estado = Ticket.Estado.EN_EJECUCION
            ticket.save(update_fields=["estado"])
            TicketHistorial.objects.create(
                ticket=ticket,
                usuario=usuario,
                estado_anterior=estado_anterior,
                estado_nuevo=Ticket.Estado.EN_EJECUCION,
                comentario=f"Inicio de trabajo registrado desde la orden #{orden.pk}.",
            )


def _liberar_tecnico(orden, tecnico):
    """Libera al técnico si no tiene otras órdenes activas."""
    if not tecnico or tecnico.estado != Tecnico.Estado.OCUPADO:
        return
    activas = OrdenTrabajo.objects.filter(
        tecnico=tecnico,
        estado__in=[OrdenTrabajo.Estado.ASIGNADA, OrdenTrabajo.Estado.EN_EJECUCION],
    ).exclude(pk=orden.pk)
    if not activas.exists():
        tecnico.estado = Tecnico.Estado.DISPONIBLE
        tecnico.save(update_fields=["estado"])


def _acceso_orden(user, orden):
    """True si el usuario puede ver la orden según su rol y empresa."""
    rol = rol_usuario(user)
    if user.is_superuser:
        return True
    if rol in (Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.GERENCIA):
        return pertenece_a_empresa(user, orden.ticket.sucursal.empresa_id)
    if rol == Usuario.Rol.TECNICO:
        return orden.tecnico.usuario == user
    if rol == Usuario.Rol.ENCARGADO:
        return orden.ticket.sucursal in list(sucursales_visibles(user))
    return False