from django.contrib import admin

from .models import Especialidad, Tecnico


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre",)


@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "usuario", "telefono", "estado", "fecha_registro")
    list_filter = ("estado", "especialidades")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name", "documento")
    filter_horizontal = ("especialidades",)
    list_select_related = ("usuario",)