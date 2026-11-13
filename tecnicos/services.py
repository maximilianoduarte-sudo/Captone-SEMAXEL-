from .models import Tecnico


class DisponibilidadNoPermitida(Exception):
    """El técnico no puede cambiar su disponibilidad ahora.

    Códigos posibles:
    - "estado_invalido": solo se puede elegir DISPONIBLE o NO_DISPONIBLE.
    - "tecnico_ocupado": tiene órdenes activas; el sistema lo libera al terminarlas.
    - "tecnico_inactivo": lo inactivó un administrador; no puede reactivarse solo.
    """

    def __init__(self, mensaje, codigo):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def cambiar_disponibilidad(tecnico, estado):
    """El propio técnico cambia entre DISPONIBLE y NO_DISPONIBLE.

    OCUPADO lo fija y lo libera el sistema (al tomar y terminar órdenes) e
    INACTIVO es administrativo, así que en esos casos no se permite el cambio.
    """
    if estado not in Tecnico.ESTADOS_DISPONIBILIDAD:
        raise DisponibilidadNoPermitida(
            "Solo puedes elegir Disponible o No disponible.", "estado_invalido"
        )
    if tecnico.estado == Tecnico.Estado.INACTIVO:
        raise DisponibilidadNoPermitida(
            "Tu cuenta está inactiva; un administrador debe reactivarla.",
            "tecnico_inactivo",
        )
    if tecnico.estado == Tecnico.Estado.OCUPADO:
        raise DisponibilidadNoPermitida(
            "Tienes órdenes activas: quedarás disponible al terminarlas.",
            "tecnico_ocupado",
        )
    if tecnico.estado != estado:
        tecnico.estado = estado
        tecnico.save(update_fields=["estado", "fecha_actualizacion"])
    return tecnico
