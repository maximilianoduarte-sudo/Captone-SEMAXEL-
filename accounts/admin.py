from django.contrib import admin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "rol", "empresa", "telefono")
    list_filter = ("rol", "empresa")
    search_fields = ("user__username", "user__first_name", "user__last_name")