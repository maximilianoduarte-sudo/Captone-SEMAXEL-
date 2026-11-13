from django.apps import AppConfig


class ApiConfig(AppConfig):
    """API REST que usa la app móvil del técnico.

    No tiene modelos propios: expone los datos de las demás aplicaciones
    (técnicos, ofertas, órdenes) con las mismas reglas de permisos que la web.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
