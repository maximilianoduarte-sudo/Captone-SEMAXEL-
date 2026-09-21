from django.contrib import admin

from .models import SLAPolicy


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = ("nombre", "prioridad", "tiempo_maximo_respuesta", "tiempo_maximo_resolucion", "activo")
    list_filter = ("prioridad", "activo")