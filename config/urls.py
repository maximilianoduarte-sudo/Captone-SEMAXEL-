"""
URL configuration for the Sistema de Gestión de Mantenimiento project.

Fase 3: prototipo visual navegable. Se definen las rutas principales y se
incluyen las URLs de cada app.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_views.dashboard, name='dashboard'),
    path('login/', dashboard_views.login, name='login'),
    path('perfil/', dashboard_views.perfil, name='perfil'),
    path('reportes/', dashboard_views.reportes, name='reportes'),

    path('tickets/', include('tickets.urls')),
    path('ofertas/', include('ofertas.urls')),
    path('ordenes/', include('tickets.ordenes_urls')),
    path('sucursales/', include('sucursales.urls')),
    path('tecnicos/', include('tecnicos.urls')),
    path('mantenimiento/', include('mantenimiento.urls')),
]

# Servir archivos de medios en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
