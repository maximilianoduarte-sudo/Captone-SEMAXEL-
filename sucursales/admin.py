from django.contrib import admin

from .models import Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "empresa", "codigo", "ciudad", "telefono", "estado")
    list_filter = ("empresa", "estado", "ciudad")
    search_fields = ("nombre", "codigo", "ciudad", "empresa__nombre")
    filter_horizontal = ("encargados",)