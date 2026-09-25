from django.contrib import admin

from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "rut", "ciudad", "telefono", "estado")
    list_filter = ("estado",)
    search_fields = ("nombre", "codigo", "rut", "ciudad")