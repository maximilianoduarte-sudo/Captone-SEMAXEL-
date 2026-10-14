from django.contrib.admin.apps import AdminConfig
from django.contrib.admin.sites import AdminSite


class SEMAXELAdminSite(AdminSite):
    """Sitio de administración con el alcance del sistema.

    El rol ENCARGADO no ingresa al admin: su espacio de trabajo es el portal y
    sólo puede operar sobre las sucursales que tiene asignadas. Quedan fuera
    tanto la lista de modelos como el acceso directo por URL.
    """

    def has_permission(self, request):
        # Importaciones diferidas: este módulo se carga al construir INSTALLED_APPS.
        from accounts.models import Usuario
        from accounts.roles import rol_usuario

        if not super().has_permission(request):
            return False
        if request.user.is_superuser:
            return True
        return rol_usuario(request.user) != Usuario.Rol.ENCARGADO


class SEMAXELAdminConfig(AdminConfig):
    default_site = "accounts.admin_site.SEMAXELAdminSite"
