from django.contrib import admin

from .models import OfertaTicket


@admin.register(OfertaTicket)
class OfertaTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "empresa", "tecnico", "estado", "fecha_publicacion", "fecha_vencimiento")
    list_filter = ("estado", "ticket__sucursal__empresa")
    search_fields = ("ticket__numero", "tecnico__usuario__username")
    list_select_related = ("ticket__sucursal__empresa", "tecnico__usuario")

    @admin.display(description="Empresa", ordering="ticket__sucursal__empresa__codigo")
    def empresa(self, obj):
        return obj.ticket.sucursal.empresa.codigo