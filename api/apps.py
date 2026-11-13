from django.apps import AppConfig


class ApiConfig(AppConfig):
    """API REST que usa la app móvil del técnico.

    Expone los datos de las demás aplicaciones (técnicos, ofertas, órdenes)
    con las mismas reglas de permisos que la web. Su único modelo propio es
    Dispositivo (celulares que reciben notificaciones push).
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Conecta los disparadores de notificaciones push.
        from . import signals  # noqa: F401
