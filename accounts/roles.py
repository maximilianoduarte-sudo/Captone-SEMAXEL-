from functools import wraps

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q

from .models import Usuario


def rol_usuario(user):
    """Rol del usuario autenticado (o None si no tiene perfil)."""
    perfil = getattr(user, "perfil", None)
    return perfil.rol if perfil else None


def empresa_usuario(user):
    """Empresa del usuario autenticado (o None si no tiene)."""
    perfil = getattr(user, "perfil", None)
    return perfil.empresa if perfil else None


def pertenece_a_empresa(user, empresa_id):
    """True si el usuario autenticado pertenece a la empresa indicada."""
    perfil = getattr(user, "perfil", None)
    return bool(perfil) and perfil.empresa_id == empresa_id


def empresas_visibles(user):
    """Empresas que un usuario puede ver según su rol."""
    from empresas.models import Empresa

    if user.is_superuser:
        return Empresa.objects.all()
    perfil = getattr(user, "perfil", None)
    if perfil and perfil.empresa_id:
        return Empresa.objects.filter(pk=perfil.empresa_id)
    return Empresa.objects.none()


def rol_requerido(*roles):
    """Permite el acceso solo a los roles indicados (o superusuarios)."""

    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser or rol_usuario(request.user) in roles:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper

    return decorador


def sucursales_visibles(user):
    """Sucursales que un usuario puede ver según su rol (acotadas a su empresa)."""
    from sucursales.models import Sucursal

    rol = rol_usuario(user)
    empresas = empresas_visibles(user)
    if user.is_superuser or rol in (
        Usuario.Rol.ADMIN,
        Usuario.Rol.GESTOR,
        Usuario.Rol.GERENCIA,
    ):
        return Sucursal.objects.filter(empresa__in=empresas)
    if rol == Usuario.Rol.ENCARGADO:
        return Sucursal.objects.filter(encargados=user, empresa__in=empresas)
    return Sucursal.objects.none()


def tickets_visibles(user):
    """QuerySet de tickets que el usuario puede ver, según su rol y empresa."""
    from tickets.models import Ticket

    if user.is_superuser:
        return Ticket.objects.all()
    rol = rol_usuario(user)
    if rol in (
        Usuario.Rol.ADMIN,
        Usuario.Rol.GESTOR,
        Usuario.Rol.GERENCIA,
        Usuario.Rol.ENCARGADO,
    ):
        return Ticket.objects.filter(sucursal__in=sucursales_visibles(user))
    if rol == Usuario.Rol.TECNICO:
        from ofertas.models import OfertaTicket

        return Ticket.objects.filter(
            Q(oferta__estado=OfertaTicket.Estado.DISPONIBLE)
            | Q(orden_trabajo__tecnico__usuario=user)
        ).distinct()
    return Ticket.objects.none()


def ofertas_visibles(user):
    """QuerySet de ofertas que el usuario puede ver, según su rol y empresa."""
    from ofertas.models import OfertaTicket

    if user.is_superuser or rol_usuario(user) == Usuario.Rol.TECNICO:
        return OfertaTicket.objects.all()
    rol = rol_usuario(user)
    if rol in (
        Usuario.Rol.ADMIN,
        Usuario.Rol.GESTOR,
        Usuario.Rol.GERENCIA,
        Usuario.Rol.ENCARGADO,
    ):
        return OfertaTicket.objects.filter(ticket__sucursal__in=sucursales_visibles(user))
    return OfertaTicket.objects.none()


def ordenes_visibles(user):
    """QuerySet de órdenes de trabajo que el usuario puede ver, según su rol y empresa."""
    from tickets.models import OrdenTrabajo

    if user.is_superuser:
        return OrdenTrabajo.objects.all()
    rol = rol_usuario(user)
    if rol == Usuario.Rol.TECNICO:
        return OrdenTrabajo.objects.filter(tecnico__usuario=user)
    if rol in (
        Usuario.Rol.ADMIN,
        Usuario.Rol.GESTOR,
        Usuario.Rol.GERENCIA,
        Usuario.Rol.ENCARGADO,
    ):
        return OrdenTrabajo.objects.filter(ticket__sucursal__in=sucursales_visibles(user))
    return OrdenTrabajo.objects.none()


def puede_ver_sucursal(user, sucursal):
    """Acceso a una sucursal según rol y empresa."""
    if user.is_superuser:
        return True
    rol = rol_usuario(user)
    if rol in (Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.GERENCIA):
        return pertenece_a_empresa(user, sucursal.empresa_id)
    if rol == Usuario.Rol.ENCARGADO:
        return sucursal.encargados.filter(pk=user.pk).exists()
    return False


def puede_ver_ticket(user, ticket):
    """Acceso a un ticket según rol y empresa.

    - SUPERUSER: todo.
    - ADMIN/GESTOR/GERENCIA: tickets de su empresa.
    - ENCARGADO: tickets de sus sucursales.
    - TECNICO: tickets con oferta pública (de cualquier empresa) o tickets
      de sus propias órdenes de trabajo.
    """
    if user.is_superuser:
        return True
    rol = rol_usuario(user)
    if rol in (Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.GERENCIA):
        return pertenece_a_empresa(user, ticket.sucursal.empresa_id)
    if rol == Usuario.Rol.ENCARGADO:
        return ticket.sucursal.encargados.filter(pk=user.pk).exists()
    if rol == Usuario.Rol.TECNICO:
        from ofertas.models import OfertaTicket
        try:
            oferta = ticket.oferta
        except ObjectDoesNotExist:
            oferta = None
        if oferta and oferta.estado == OfertaTicket.Estado.DISPONIBLE:
            return True
        from tickets.models import OrdenTrabajo
        return OrdenTrabajo.objects.filter(
            ticket=ticket, tecnico__usuario=user
        ).exists()
    return False


def puede_ver_oferta(user, oferta):
    """Acceso a una oferta según rol y empresa.

    - SUPERUSER: todo.
    - ADMIN/GESTOR/GERENCIA: ofertas de su empresa.
    - ENCARGADO: ofertas de sus sucursales.
    - TECNICO: ofertas disponibles (marketplace global) o las que ha tomado.
    """
    if user.is_superuser:
        return True
    rol = rol_usuario(user)
    if rol in (Usuario.Rol.ADMIN, Usuario.Rol.GESTOR, Usuario.Rol.GERENCIA):
        return pertenece_a_empresa(user, oferta.ticket.sucursal.empresa_id)
    if rol == Usuario.Rol.ENCARGADO:
        return oferta.ticket.sucursal.encargados.filter(pk=user.pk).exists()
    if rol == Usuario.Rol.TECNICO:
        from ofertas.models import OfertaTicket
        if oferta.estado == OfertaTicket.Estado.DISPONIBLE:
            return True
        return OfertaTicket.objects.filter(
            pk=oferta.pk, tecnico__usuario=user
        ).exists()
    return False