from django.db import models


class OfertaTicket(models.Model):
    """
    Oferta de trabajo asociada a un ticket, publicada para que los técnicos
    elegibles puedan visualizarla y tomarla (modelo tipo marketplace).

    Al crearse, el técnico es nulo (estado DISPONIBLE). Cuando un técnico la
    toma, se registra el técnico, pasa a TOMADA y se guarda la fecha.
    """

    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        TOMADA = "TOMADA", "Tomada"
        EN_EJECUCION = "EN_EJECUCION", "En ejecución"
        COMPLETADA = "COMPLETADA", "Completada"
        CANCELADA = "CANCELADA", "Cancelada"
        EXPIRADA = "EXPIRADA", "Expirada"

    ticket = models.OneToOneField(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="oferta",
        verbose_name="Ticket",
        help_text="Cada ticket puede tener como máximo una oferta.",
    )
    tecnico = models.ForeignKey(
        "tecnicos.Tecnico",
        on_delete=models.SET_NULL,
        related_name="ofertas_tomadas",
        verbose_name="Técnico que tomó la oferta",
        null=True,
        blank=True,
        help_text="Se asigna cuando un técnico toma la oferta; puede ser nulo al publicarla.",
    )
    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.DISPONIBLE,
    )
    fecha_publicacion = models.DateTimeField(
        "Fecha de publicación",
        auto_now_add=True,
    )
    fecha_vencimiento = models.DateTimeField(
        "Fecha de vencimiento",
        null=True,
        blank=True,
    )
    fecha_respuesta = models.DateTimeField(
        "Fecha de respuesta",
        null=True,
        blank=True,
    )
    fecha_tomada = models.DateTimeField(
        "Fecha en que fue tomada",
        null=True,
        blank=True,
    )
    observaciones = models.TextField("Observaciones", blank=True)

    class Meta:
        verbose_name = "Oferta de ticket"
        verbose_name_plural = "Ofertas de ticket"
        ordering = ["-fecha_publicacion"]
        indexes = [
            models.Index(fields=["estado"], name="idx_oferta_estado"),
        ]

    def __str__(self):
        return f"Oferta {self.ticket.numero if hasattr(self.ticket, 'numero') else self.ticket_id} - {self.get_estado_display()}"
