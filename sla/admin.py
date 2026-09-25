from django.contrib import admin

from .models import SLAPolicy


@admin.register(SLAPolicy)
class SLAPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "empresa_mostrar",
        "prioridad",
        "tiempo_maximo_respuesta",
        "tiempo_maximo_resolucion",
        "activo",
    )
    list_filter = ("prioridad", "activo", "empresa")
    list_select_related = ("empresa",)

    @admin.display(description="Empresa")
    def empresa_mostrar(self, obj):
        return obj.empresa.codigo if obj.empresa else "Global"