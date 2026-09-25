from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import PlanMantenimiento, ProgramacionMantenimiento


@admin.register(PlanMantenimiento)
class PlanMantenimientoAdmin(admin.ModelAdmin):
    @admin.display(description="Empresa", ordering="sucursal__empresa__codigo")
    def empresa(self, obj):
        return obj.sucursal.empresa

    @admin.display(description="Próxima ejecución")
    def proxima(self, obj):
        if obj.fecha_proxima <= timezone.now():
            return format_html(
                '<span style="color:#d63384;font-weight:600">{}</span>', obj.fecha_proxima
            )
        return obj.fecha_proxima

    list_display = ("nombre", "empresa", "sucursal", "categoria", "frecuencia", "proxima", "activo")
    list_filter = ("sucursal__empresa", "activo", "frecuencia")
    search_fields = ("nombre", "sucursal__nombre", "categoria__nombre")
    list_select_related = ("sucursal__empresa", "categoria")


@admin.register(ProgramacionMantenimiento)
class ProgramacionMantenimientoAdmin(admin.ModelAdmin):
    list_display = ("plan", "fecha_programada", "estado", "ticket")
    list_filter = ("estado",)
    search_fields = ("plan__nombre", "ticket__numero")
    list_select_related = ("plan", "ticket")
    date_hierarchy = "fecha_programada"