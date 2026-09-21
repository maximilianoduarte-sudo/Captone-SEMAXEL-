from django.contrib import admin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "rol", "telefono")
    list_filter = ("rol",)
    search_fields = ("user__username", "user__first_name", "user__last_name")