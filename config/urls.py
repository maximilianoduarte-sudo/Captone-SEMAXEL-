"""
URL configuration for the Sistema de Gestión de Mantenimiento project.

En esta fase solo se define la página inicial de bienvenida y el acceso al
admin de Django. Las URLs de cada app (accounts, sucursales, tecnicos, etc.)
se incluirán en fases posteriores.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]

# Servir archivos de medios en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
