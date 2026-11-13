from rest_framework.permissions import BasePermission

from accounts.models import Usuario
from tecnicos.models import Tecnico


def tecnico_habilitado(user):
    """Devuelve el perfil Tecnico si el usuario puede usar la app, o None.

    Puede usar la app quien cumple las tres condiciones:
    - su cuenta está activa (is_active),
    - su rol es TECNICO,
    - tiene perfil de técnico y ese perfil no está INACTIVO.
    """
    if not user or not user.is_active:
        return None
    perfil = getattr(user, "perfil", None)
    if perfil is None or perfil.rol != Usuario.Rol.TECNICO:
        return None
    tecnico = getattr(user, "tecnico", None)
    if tecnico is None or tecnico.estado == Tecnico.Estado.INACTIVO:
        return None
    return tecnico


class EsTecnicoHabilitado(BasePermission):
    """Permite el acceso solo a técnicos habilitados (ver tecnico_habilitado)."""

    message = "Esta app es solo para técnicos habilitados."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and tecnico_habilitado(request.user) is not None
        )
