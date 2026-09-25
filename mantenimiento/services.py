from django.db import transaction
from django.utils import timezone

from tickets.models import Ticket, TicketHistorial
from tickets.views import _proximo_numero

from .models import PlanMantenimiento, ProgramacionMantenimiento


def _creador_por_defecto(empresa):
    """Usuario ADMIN de la empresa para tickets preventivos; superuser como respaldo."""
    from accounts.models import Usuario

    admin = empresa.usuarios.filter(rol=Usuario.Rol.ADMIN).select_related("user").first()
    if admin:
        return admin.user
    from django.contrib.auth.models import User

    return User.objects.filter(is_superuser=True, is_active=True).first()


def _ticket_preventivo_abierto(plan):
    """True si el plan ya tiene un preventivo generado y aún no cerrado."""
    abiertos = [
        Ticket.Estado.ABIERTO, Ticket.Estado.EN_REVISION, Ticket.Estado.PUBLICADO,
        Ticket.Estado.EN_EJECUCION, Ticket.Estado.RESUELTO,
    ]
    return plan.programaciones.filter(
        estado=ProgramacionMantenimiento.Estado.GENERADO, ticket__estado__in=abiertos
    ).exists()


@transaction.atomic
def generar_tickets_preventivos(usuario=None, limite=None):
    """Genera tickets PREVENTIVO para los planes cuya fecha de ejecución venció.

    Reposiciona primero la agenda a hoy (sin desbordar por atrasos largos) y
    genera un único ticket por plan y ciclo, salvo que ya exista un preventivo
    abierto del mismo plan. Devuelve la cantidad de tickets generados.
    """
    ahora = timezone.now()
    generados = 0
    planes = PlanMantenimiento.objects.filter(
        activo=True, fecha_proxima__lte=ahora
    ).select_related("sucursal__empresa", "categoria")
    if limite:
        planes = planes[:limite]

    for plan in planes:
        if _ticket_preventivo_abierto(plan):
            continue
        creador = usuario or _creador_por_defecto(plan.sucursal.empresa)
        if not creador:
            continue

        # Anticipa la agenda hasta la siguiente ejecución futura.
        while plan.fecha_proxima <= ahora:
            plan.fecha_proxima += timezone.timedelta(days=plan.frecuencia_dias)

        ticket = Ticket.objects.create(
            numero=_proximo_numero(plan.sucursal),
            sucursal=plan.sucursal,
            categoria=plan.categoria,
            prioridad=Ticket.Prioridad.MEDIA,
            estado=Ticket.Estado.ABIERTO,
            tipo=Ticket.Tipo.PREVENTIVO,
            titulo=f"Preventivo: {plan.nombre}",
            descripcion=plan.descripcion
            or f"Ejecución programada del plan {plan.nombre} en {plan.sucursal}.",
            creador=creador,
        )
        TicketHistorial.objects.create(
            ticket=ticket,
            usuario=creador,
            estado_nuevo=Ticket.Estado.ABIERTO,
            comentario="Ticket preventivo generado automáticamente desde su plan.",
        )
        ProgramacionMantenimiento.objects.create(
            plan=plan,
            fecha_programada=plan.fecha_proxima,
            ticket=ticket,
            estado=ProgramacionMantenimiento.Estado.GENERADO,
        )
        plan.save(update_fields=["fecha_proxima"])
        generados += 1
    return generados