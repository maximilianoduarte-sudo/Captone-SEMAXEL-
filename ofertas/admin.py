from django.contrib import admin

from .models import OfertaTicket


@admin.register(OfertaTicket)
class OfertaTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "tecnico", "estado", "fecha_publicacion", "fecha_vencimiento")
    list_filter = ("estado",)
    search_fields = ("ticket__numero",)