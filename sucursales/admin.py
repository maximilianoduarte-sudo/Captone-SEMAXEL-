from django.contrib import admin

from .models import Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "ciudad", "telefono", "estado")
    list_filter = ("estado",)
    search_fields = ("nombre", "codigo", "ciudad")
    filter_horizontal = ("encargados",)