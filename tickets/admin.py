from django.contrib import admin

from .models import Calificacion, Categoria, EvidenciaTicket, OrdenTrabajo, Ticket, TicketHistorial


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "especialidad", "activo")
    list_filter = ("activo", "especialidad")
    search_fields = ("nombre",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("numero", "titulo", "empresa", "sucursal", "prioridad", "estado", "fecha_creacion")
    list_filter = ("estado", "prioridad", "tipo", "sucursal__empresa")
    search_fields = ("numero", "titulo", "sucursal__nombre")
    ordering = ("-fecha_creacion",)
    list_select_related = ("sucursal__empresa", "categoria", "creador")

    @admin.display(description="Empresa", ordering="sucursal__empresa__codigo")
    def empresa(self, obj):
        return obj.sucursal.empresa.codigo


@admin.register(EvidenciaTicket)
class EvidenciaTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "nombre")
    list_filter = ("ticket",)


@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket", "empresa", "sucursal", "tecnico", "estado", "fecha_creacion")
    list_filter = ("estado", "ticket__sucursal__empresa")
    search_fields = ("ticket__numero", "tecnico__usuario__username")
    list_select_related = ("ticket__sucursal__empresa", "tecnico__usuario")

    @admin.display(description="Empresa", ordering="ticket__sucursal__empresa__codigo")
    def empresa(self, obj):
        return obj.ticket.sucursal.empresa.codigo


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ("id", "orden_trabajo", "tecnico", "puntuacion", "fecha_calificacion")
    list_filter = ("puntuacion",)


@admin.register(TicketHistorial)
class TicketHistorialAdmin(admin.ModelAdmin):
    list_display = ("ticket", "estado_anterior", "estado_nuevo", "usuario", "fecha_cambio")
    list_filter = ("estado_nuevo",)