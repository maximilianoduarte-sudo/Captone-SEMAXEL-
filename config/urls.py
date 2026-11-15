"""
URL configuration for the Sistema de Gestión de Mantenimiento project.

Fase 5: autenticación con django.contrib.auth (login/logout reales),
gestión de usuarios por rol y acceso según permisos.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from accounts import views as accounts_views
from dashboard import views as dashboard_views

handler403 = dashboard_views.handler403

admin.site.site_header = "SEMAXEL · Administración"
admin.site.site_title = "SEMAXEL Admin"
admin.site.index_title = "Gestión del sistema de mantenimiento"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_views.dashboard, name='dashboard'),
    path('login/', accounts_views.login, name='login'),
    path('logout/', accounts_views.logout, name='logout'),
    path('registro/', accounts_views.registro, name='registro'),
    path('registro/gestor/', accounts_views.registro_gestor, name='registro_gestor'),
    path('registro/tecnico/', accounts_views.registro_tecnico, name='registro_tecnico'),
    path('perfil/', accounts_views.perfil, name='perfil'),
    path('usuarios/', include('accounts.urls')),
    path('reportes/', dashboard_views.reportes, name='reportes'),

    path('tickets/', include('tickets.urls')),
    path('ofertas/', include('ofertas.urls')),
    path('ordenes/', include('tickets.ordenes_urls')),
    path('sucursales/', include('sucursales.urls')),
    path('empresas/', include('empresas.urls')),
    path('tecnicos/', include('tecnicos.urls')),
    path('mantenimiento/', include('mantenimiento.urls')),

    # API REST de la app móvil del técnico (versión 1)
    path('api/v1/', include('api.urls')),
]

# Servir archivos de medios en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SEMAXEL_SERVIR_MEDIA:
    # Servidor de demostración sin un servidor web aparte (Nginx, IIS): Django
    # entrega las fotos subidas aunque DEBUG=False. En producción real lo
    # debe hacer el servidor web. Se activa con SEMAXEL_SERVIR_MEDIA=True.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
