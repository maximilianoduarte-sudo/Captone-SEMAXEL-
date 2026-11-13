"""Disparadores de notificaciones push.

Se usan señales de Django para no tocar las vistas web: cuando una oferta
queda DISPONIBLE (publicada o republicada) o una orden se cierra o se
cancela, se avisa a los técnicos que corresponda. El envío se hace después
de confirmar la transacción (on_commit), para no avisar de algo que al final
no se guardó.
"""
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.models import Usuario
from ofertas.models import OfertaTicket
from tecnicos.models import Tecnico
from tickets.models import OrdenTrabajo

from .notificaciones import notificar


def _estado_anterior(sender, instance):
    if not instance.pk:
        return None
    return sender.objects.filter(pk=instance.pk).values_list("estado", flat=True).first()


@receiver(pre_save, sender=OfertaTicket)
@receiver(pre_save, sender=OrdenTrabajo)
def recordar_estado_anterior(sender, instance, **kwargs):
    instance._estado_anterior = _estado_anterior(sender, instance)


@receiver(post_save, sender=OfertaTicket)
def avisar_oferta_nueva(sender, instance, **kwargs):
    """Avisa a los técnicos con la especialidad requerida que hay una oferta nueva."""
    if instance.estado != OfertaTicket.Estado.DISPONIBLE:
        return
    if getattr(instance, "_estado_anterior", None) == OfertaTicket.Estado.DISPONIBLE:
        return  # ya estaba disponible: no es una publicación nueva

    def enviar():
        especialidad = instance.ticket.categoria.especialidad_id
        if especialidad is None:
            return
        usuarios = Usuario.objects.filter(
            rol=Usuario.Rol.TECNICO,
            user__is_active=True,
            user__tecnico__especialidades=especialidad,
        ).exclude(user__tecnico__estado=Tecnico.Estado.INACTIVO).values("user")
        notificar(
            usuarios,
            "Nueva oferta de trabajo",
            f"{instance.ticket.titulo} · {instance.ticket.sucursal.nombre}",
            {"tipo": "oferta_nueva", "oferta_id": instance.pk},
        )

    transaction.on_commit(enviar)


@receiver(post_save, sender=OrdenTrabajo)
def avisar_cierre_de_orden(sender, instance, **kwargs):
    """Avisa al técnico cuando el encargado cierra o cancela su orden."""
    anterior = getattr(instance, "_estado_anterior", None)
    if instance.estado == anterior or instance.estado not in (
        OrdenTrabajo.Estado.CERRADA,
        OrdenTrabajo.Estado.CANCELADA,
    ):
        return
    accion = "cerrada" if instance.estado == OrdenTrabajo.Estado.CERRADA else "cancelada"

    def enviar():
        notificar(
            [instance.tecnico.usuario_id],
            f"Orden {accion}",
            f"La orden de «{instance.ticket.titulo}» fue {accion}.",
            {"tipo": f"orden_{accion}", "orden_id": instance.pk},
        )

    transaction.on_commit(enviar)
