"""Reglas de la orden de trabajo, compartidas por la web y la API.

La máquina de estados de la orden es:

    ASIGNADA     -> EN_EJECUCION, CANCELADA
    EN_EJECUCION -> RESUELTA, CANCELADA
    RESUELTA     -> CERRADA, EN_EJECUCION
    CERRADA, CANCELADA: terminales

Quién puede aplicar cada transición:
- El técnico de la orden: iniciar (EN_EJECUCION) y resolver (RESUELTA).
- ADMIN, GESTOR y ENCARGADO (y el superusuario): cualquiera, incluido
  cerrar y cancelar.
- GERENCIA: ninguna. Su perfil es de solo lectura.
"""
import math

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import Usuario
from accounts.roles import rol_usuario
from tecnicos.models import Tecnico

from .models import (
    Calificacion,
    EvidenciaOrden,
    FirmaConformidad,
    OrdenTrabajo,
    Ticket,
    TicketHistorial,
)

CAMPOS_DE_TRABAJO = (
    "diagnostico",
    "trabajo_realizado",
    "observaciones",
    "costo_estimado",
    "costo_final",
)

ESTADOS_TERMINO = (OrdenTrabajo.Estado.CERRADA, OrdenTrabajo.Estado.CANCELADA)


class ReglaNoCumplida(Exception):
    """Una operación sobre la orden no cumple una regla de negocio.

    `mensaje` es para la persona; `codigo`, para el programa (la app decide
    qué hacer según el código). No se cambia nada cuando se lanza.
    """

    def __init__(self, mensaje, codigo):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


class TransicionNoPermitida(ReglaNoCumplida):
    """No se puede aplicar la transición de estado.

    Códigos posibles:
    - "sin_cambio": la orden ya está en ese estado.
    - "transicion_invalida": la máquina de estados no permite ese paso.
    - "sin_permiso": el usuario no puede aplicar esa transición.
    - "falta_diagnostico": iniciar exige diagnóstico.
    - "falta_trabajo": resolver exige el trabajo realizado.
    - "falta_calificacion": cerrar exige una calificación de 1 a 5.
    """


class OperacionNoPermitida(ReglaNoCumplida):
    """No se puede registrar la llegada, una evidencia o la firma.

    Códigos posibles:
    - "sin_permiso": la orden no es del técnico (o la evidencia no es suya).
    - "orden_no_activa": el estado de la orden no permite la operación.
    - "llegada_ya_registrada": la llegada se registra una sola vez.
    - "limite_evidencias": se alcanzó el máximo de fotos por orden.
    - "firma_ya_registrada": la orden ya tiene firma de conformidad.
    """


def puede_aplicar_transicion(user, orden, destino):
    """True si el usuario puede llevar la orden al estado `destino`."""
    if user.is_superuser:
        return True
    rol = rol_usuario(user)
    if rol == Usuario.Rol.GERENCIA:
        return False
    if rol == Usuario.Rol.TECNICO:
        if destino in ESTADOS_TERMINO:
            return False
        return orden.tecnico.usuario_id == user.id
    return True


def transiciones_permitidas(user, orden):
    """Estados a los que este usuario puede llevar la orden ahora mismo."""
    return {
        destino
        for destino in orden.transiciones_validas()
        if puede_aplicar_transicion(user, orden, destino)
    }


def cambiar_estado_orden(orden, destino, usuario, datos=None):
    """Aplica una transición a la orden y sincroniza todo lo relacionado.

    `datos` puede traer: diagnostico, trabajo_realizado, observaciones,
    costo_estimado, costo_final, puntuacion y comentario_calificacion.

    Si algo impide la transición, lanza TransicionNoPermitida y no cambia
    nada. Si se aplica:
    - guarda los datos de trabajo (solo al iniciar o resolver, sin pisar
      valores existentes con blancos);
    - fija fecha_inicio o fecha_fin según corresponda;
    - mueve el ticket al estado equivalente y lo registra en el historial;
    - libera al técnico si ya no tiene órdenes activas;
    - al cerrar, registra la calificación.

    Devuelve la orden actualizada.
    """
    datos = datos or {}
    with transaction.atomic():
        orden = (
            OrdenTrabajo.objects.select_for_update()
            .select_related("ticket", "tecnico")
            .get(pk=orden.pk)
        )
        _validar(orden, destino, usuario, datos)
        _aplicar_campos(orden, destino, datos)
        _sincronizar_ticket_y_tecnico(orden, destino, usuario)
        if destino == OrdenTrabajo.Estado.CERRADA:
            Calificacion.objects.update_or_create(
                orden_trabajo=orden,
                defaults={
                    "tecnico": orden.tecnico,
                    "puntuacion": datos["puntuacion"],
                    "comentario": datos.get("comentario_calificacion") or "",
                },
            )
    return orden


def _validar(orden, destino, usuario, datos):
    if destino == orden.estado:
        raise TransicionNoPermitida("La orden ya se encuentra en ese estado.", "sin_cambio")
    if not orden.puede_transicionar_a(destino):
        raise TransicionNoPermitida(
            f"Transición de la orden no permitida: {orden.estado} → {destino}.",
            "transicion_invalida",
        )
    if not puede_aplicar_transicion(usuario, orden, destino):
        raise TransicionNoPermitida(
            "No tienes permiso para aplicar esta transición.", "sin_permiso"
        )
    if destino == OrdenTrabajo.Estado.EN_EJECUCION and not (
        datos.get("diagnostico") or orden.diagnostico
    ):
        raise TransicionNoPermitida(
            "Ingresa el diagnóstico para iniciar el trabajo.", "falta_diagnostico"
        )
    if destino == OrdenTrabajo.Estado.RESUELTA and not (
        datos.get("trabajo_realizado") or orden.trabajo_realizado
    ):
        raise TransicionNoPermitida(
            "Registra el trabajo realizado antes de resolver la orden.", "falta_trabajo"
        )
    if destino == OrdenTrabajo.Estado.CERRADA and not datos.get("puntuacion"):
        raise TransicionNoPermitida(
            "La calificación (1 a 5) es obligatoria al cerrar la orden.",
            "falta_calificacion",
        )


def _aplicar_campos(orden, destino, datos):
    """Guarda el nuevo estado y, al iniciar o resolver, los datos de trabajo.

    Al cerrar o cancelar no se tocan los datos de trabajo.
    """
    campos = ["estado"]
    if destino in (OrdenTrabajo.Estado.EN_EJECUCION, OrdenTrabajo.Estado.RESUELTA):
        for campo in CAMPOS_DE_TRABAJO:
            valor = datos.get(campo)
            if valor not in (None, ""):
                setattr(orden, campo, valor)
                campos.append(campo)
    orden.estado = destino
    orden.save(update_fields=campos)


def _sincronizar_ticket_y_tecnico(orden, destino, usuario):
    """Fechas de la orden, estado del ticket (con historial) y disponibilidad del técnico."""
    ahora = timezone.now()

    if destino == OrdenTrabajo.Estado.EN_EJECUCION and not orden.fecha_inicio:
        orden.fecha_inicio = ahora
        orden.save(update_fields=["fecha_inicio"])
    elif destino in (OrdenTrabajo.Estado.RESUELTA, *ESTADOS_TERMINO):
        if not orden.fecha_fin:
            orden.fecha_fin = ahora
            orden.save(update_fields=["fecha_fin"])
        _liberar_tecnico(orden)

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
    elif (
        destino == OrdenTrabajo.Estado.EN_EJECUCION
        and ticket.estado != Ticket.Estado.EN_EJECUCION
        and ticket.puede_transicionar_a(Ticket.Estado.EN_EJECUCION)
    ):
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


def _liberar_tecnico(orden):
    """Deja DISPONIBLE al técnico si no tiene otras órdenes activas."""
    tecnico = orden.tecnico
    if not tecnico or tecnico.estado != Tecnico.Estado.OCUPADO:
        return
    activas = OrdenTrabajo.objects.filter(
        tecnico=tecnico,
        estado__in=[OrdenTrabajo.Estado.ASIGNADA, OrdenTrabajo.Estado.EN_EJECUCION],
    ).exclude(pk=orden.pk)
    if not activas.exists():
        tecnico.estado = Tecnico.Estado.DISPONIBLE
        tecnico.save(update_fields=["estado"])


# ---------------------------------------------------------------------------
# Trabajo en terreno: llegada con GPS, fotos de evidencia y firma
# ---------------------------------------------------------------------------

ESTADOS_ACTIVOS = (OrdenTrabajo.Estado.ASIGNADA, OrdenTrabajo.Estado.EN_EJECUCION)
ESTADOS_CON_EVIDENCIA = (*ESTADOS_ACTIVOS, OrdenTrabajo.Estado.RESUELTA)
ESTADOS_PARA_FIRMAR = (OrdenTrabajo.Estado.EN_EJECUCION, OrdenTrabajo.Estado.RESUELTA)

RADIO_TIERRA_METROS = 6_371_000


def distancia_metros(lat1, lon1, lat2, lon2):
    """Distancia en metros entre dos puntos GPS (fórmula de haversine).

    Considera la Tierra como una esfera; para distancias de cientos de metros
    el error es despreciable.
    """
    lat1, lon1, lat2, lon2 = (math.radians(float(v)) for v in (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * RADIO_TIERRA_METROS * math.asin(math.sqrt(a))


def _exigir_tecnico_de_la_orden(orden, usuario):
    if orden.tecnico.usuario_id != usuario.id:
        raise OperacionNoPermitida("Esta orden no está asignada a ti.", "sin_permiso")


def registrar_llegada(orden, usuario, latitud, longitud, precision_m=None):
    """Registra que el técnico llegó al local, con su posición GPS.

    - Solo el técnico de la orden, con la orden ASIGNADA o EN_EJECUCION.
    - Se registra una sola vez.
    - Si la sucursal tiene coordenadas, calcula la distancia y marca la
      llegada como verificada cuando está dentro del radio permitido
      (SEMAXEL_RADIO_LLEGADA_METROS). Si no tiene, queda "no verificable".
    - Completa la fecha de respuesta de la oferta (dato del SLA de
      respuesta, que antes nunca se llenaba) y deja constancia en el
      historial del ticket.
    """
    with transaction.atomic():
        orden = (
            OrdenTrabajo.objects.select_for_update()
            .select_related("ticket__sucursal", "tecnico", "oferta")
            .get(pk=orden.pk)
        )
        _exigir_tecnico_de_la_orden(orden, usuario)
        if orden.estado not in ESTADOS_ACTIVOS:
            raise OperacionNoPermitida(
                "Solo se registra la llegada en órdenes asignadas o en ejecución.",
                "orden_no_activa",
            )
        if orden.fecha_llegada:
            raise OperacionNoPermitida(
                "La llegada ya fue registrada.", "llegada_ya_registrada"
            )

        ahora = timezone.now()
        sucursal = orden.ticket.sucursal
        orden.fecha_llegada = ahora
        orden.llegada_latitud = round(float(latitud), 6)
        orden.llegada_longitud = round(float(longitud), 6)
        orden.llegada_precision_m = precision_m
        if sucursal.tiene_coordenadas:
            distancia = distancia_metros(latitud, longitud, sucursal.latitud, sucursal.longitud)
            orden.llegada_distancia_m = round(distancia)
            orden.llegada_verificada = distancia <= settings.SEMAXEL_RADIO_LLEGADA_METROS
        else:
            orden.llegada_distancia_m = None
            orden.llegada_verificada = None
        orden.save(update_fields=[
            "fecha_llegada", "llegada_latitud", "llegada_longitud",
            "llegada_precision_m", "llegada_distancia_m", "llegada_verificada",
        ])

        if orden.oferta and not orden.oferta.fecha_respuesta:
            orden.oferta.fecha_respuesta = ahora
            orden.oferta.save(update_fields=["fecha_respuesta"])

        if orden.llegada_verificada is None:
            detalle = "no verificable: la sucursal no tiene coordenadas"
        elif orden.llegada_verificada:
            detalle = f"verificada a {orden.llegada_distancia_m} m de la sucursal"
        else:
            detalle = f"fuera del radio: a {orden.llegada_distancia_m} m de la sucursal"
        ticket = orden.ticket
        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=usuario,
            estado_anterior=ticket.estado,
            estado_nuevo=ticket.estado,
            comentario=f"Llegada del técnico {orden.tecnico.nombre} al local ({detalle}).",
        )
    return orden


def agregar_evidencia(orden, usuario, imagen, descripcion=""):
    """Agrega una foto de evidencia a la orden.

    Solo el técnico de la orden, mientras esté asignada, en ejecución o
    resuelta (antes del cierre), y hasta SEMAXEL_MAX_EVIDENCIAS_POR_ORDEN fotos.
    """
    with transaction.atomic():
        orden = OrdenTrabajo.objects.select_for_update().select_related("tecnico").get(pk=orden.pk)
        _exigir_tecnico_de_la_orden(orden, usuario)
        if orden.estado not in ESTADOS_CON_EVIDENCIA:
            raise OperacionNoPermitida(
                "La orden ya está cerrada o cancelada; no admite nuevas evidencias.",
                "orden_no_activa",
            )
        maximo = settings.SEMAXEL_MAX_EVIDENCIAS_POR_ORDEN
        if orden.evidencias.count() >= maximo:
            raise OperacionNoPermitida(
                f"La orden ya tiene el máximo de {maximo} fotos.", "limite_evidencias"
            )
        return EvidenciaOrden.objects.create(
            orden=orden, imagen=imagen, descripcion=descripcion or "", subida_por=usuario
        )


def eliminar_evidencia(evidencia, usuario):
    """Elimina una foto subida por error (solo quien la subió, antes del cierre)."""
    orden = evidencia.orden
    _exigir_tecnico_de_la_orden(orden, usuario)
    if evidencia.subida_por_id != usuario.id:
        raise OperacionNoPermitida("Solo puedes eliminar tus propias fotos.", "sin_permiso")
    if orden.estado not in ESTADOS_CON_EVIDENCIA:
        raise OperacionNoPermitida(
            "La orden ya está cerrada o cancelada; sus evidencias no se modifican.",
            "orden_no_activa",
        )
    evidencia.imagen.delete(save=False)
    evidencia.delete()


def registrar_firma(orden, usuario, imagen, nombre_firmante):
    """Guarda la firma de conformidad del encargado, capturada en la app.

    Solo el técnico de la orden, con la orden en ejecución o resuelta, y una
    sola vez por orden. Queda registrada en el historial del ticket.
    """
    with transaction.atomic():
        orden = (
            OrdenTrabajo.objects.select_for_update()
            .select_related("ticket", "tecnico")
            .get(pk=orden.pk)
        )
        _exigir_tecnico_de_la_orden(orden, usuario)
        if orden.estado not in ESTADOS_PARA_FIRMAR:
            raise OperacionNoPermitida(
                "La firma se registra con la orden en ejecución o resuelta.",
                "orden_no_activa",
            )
        if FirmaConformidad.objects.filter(orden=orden).exists():
            raise OperacionNoPermitida(
                "La orden ya tiene firma de conformidad.", "firma_ya_registrada"
            )
        firma = FirmaConformidad.objects.create(
            orden=orden, imagen=imagen, nombre_firmante=nombre_firmante, registrada_por=usuario
        )
        ticket = orden.ticket
        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=usuario,
            estado_anterior=ticket.estado,
            estado_nuevo=ticket.estado,
            comentario=f"Firma de conformidad de {nombre_firmante} registrada en terreno.",
        )
    return firma
