from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Categoria(models.Model):
    """
    Categoría de mantenimiento (p. ej. Fuga de agua). Es configurable y puede
    asociarse opcionalmente a una especialidad.
    """

    nombre = models.CharField("Nombre", max_length=100, unique=True)
    descripcion = models.TextField("Descripción", blank=True)
    especialidad = models.ForeignKey(
        "tecnicos.Especialidad",
        on_delete=models.SET_NULL,
        related_name="categorias",
        verbose_name="Especialidad",
        null=True,
        blank=True,
    )
    activo = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Ticket(models.Model):
    """
    Reporte de incidencia o mantenimiento de una sucursal. Es la entidad
    central del sistema y desde la cual puede generarse una oferta de trabajo.
    """

    class Prioridad(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"
        CRITICA = "CRITICA", "Crítica"

    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        EN_REVISION = "EN_REVISION", "En revisión"
        PUBLICADO = "PUBLICADO", "Publicado"
        EN_EJECUCION = "EN_EJECUCION", "En ejecución"
        RESUELTO = "RESUELTO", "Resuelto"
        CERRADO = "CERRADO", "Cerrado"
        CANCELADO = "CANCELADO", "Cancelado"

    class Tipo(models.TextChoices):
        INCIDENCIA = "INCIDENCIA", "Incidencia"
        PREVENTIVO = "PREVENTIVO", "Preventivo"

    numero = models.CharField("Número", max_length=30, unique=True)
    sucursal = models.ForeignKey(
        "sucursales.Sucursal",
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="Sucursal",
    )
    creador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tickets_creados",
        verbose_name="Usuario que reporta",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="Categoría",
    )
    prioridad = models.CharField(
        "Prioridad",
        max_length=20,
        choices=Prioridad.choices,
        default=Prioridad.MEDIA,
    )
    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.ABIERTO,
    )
    tipo = models.CharField(
        "Tipo",
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.INCIDENCIA,
    )
    titulo = models.CharField("Título", max_length=200)
    descripcion = models.TextField("Descripción de la falla")
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de actualización", auto_now=True)
    fecha_limite_sla = models.DateTimeField(
        "Fecha límite según SLA",
        null=True,
        blank=True,
    )
    fecha_cierre = models.DateTimeField("Fecha de cierre", null=True, blank=True)
    informacion_adicional = models.TextField("Información adicional", blank=True)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["estado"], name="idx_ticket_estado"),
            models.Index(fields=["prioridad"], name="idx_ticket_prioridad"),
            models.Index(fields=["sucursal"], name="idx_ticket_sucursal"),
        ]

    def __str__(self):
        return f"{self.numero} - {self.titulo}"


class EvidenciaTicket(models.Model):
    """
    Evidencia (imagen u otro archivo) asociada a un ticket para documentar
    el estado de la falla o el trabajo realizado.
    """

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="evidencias",
        verbose_name="Ticket",
    )
    archivo = models.FileField("Archivo", upload_to="evidencias/")
    nombre = models.CharField("Nombre", max_length=255, blank=True)
    fecha_subida = models.DateTimeField("Fecha de subida", auto_now_add=True)

    class Meta:
        verbose_name = "Evidencia de ticket"
        verbose_name_plural = "Evidencias de ticket"
        ordering = ["-fecha_subida"]

    def __str__(self):
        return self.nombre or f"Evidencia {self.pk}"


class OrdenTrabajo(models.Model):
    """
    Orden de trabajo generada cuando un técnico toma la oferta asociada a un
    ticket. Registra el proceso de ejecución del mantenimiento.
    """

    class Estado(models.TextChoices):
        ASIGNADA = "ASIGNADA", "Asignada"
        EN_EJECUCION = "EN_EJECUCION", "En ejecución"
        RESUELTA = "RESUELTA", "Resuelta"
        CERRADA = "CERRADA", "Cerrada"
        CANCELADA = "CANCELADA", "Cancelada"

    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name="orden_trabajo",
        verbose_name="Ticket",
    )
    tecnico = models.ForeignKey(
        "tecnicos.Tecnico",
        on_delete=models.PROTECT,
        related_name="ordenes_trabajo",
        verbose_name="Técnico",
    )
    oferta = models.ForeignKey(
        "ofertas.OfertaTicket",
        on_delete=models.SET_NULL,
        related_name="ordenes",
        verbose_name="Oferta",
        null=True,
        blank=True,
    )
    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.ASIGNADA,
    )
    fecha_inicio = models.DateTimeField("Fecha de inicio", null=True, blank=True)
    fecha_fin = models.DateTimeField("Fecha de finalización", null=True, blank=True)
    diagnostico = models.TextField("Diagnóstico", blank=True)
    trabajo_realizado = models.TextField("Trabajo realizado", blank=True)
    observaciones = models.TextField("Observaciones", blank=True)
    costo_estimado = models.DecimalField(
        "Costo estimado",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    costo_final = models.DecimalField(
        "Costo final",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de actualización", auto_now=True)

    class Meta:
        verbose_name = "Orden de trabajo"
        verbose_name_plural = "Órdenes de trabajo"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["estado"], name="idx_orden_estado"),
        ]

    def __str__(self):
        return f"Orden {self.pk} - Ticket {self.ticket.numero}"


class Calificacion(models.Model):
    """
    Calificación que el encargado de sucursal otorga al técnico al cerrar
    la orden de trabajo. Una orden puede tener como máximo una calificación.
    """

    orden_trabajo = models.OneToOneField(
        OrdenTrabajo,
        on_delete=models.CASCADE,
        related_name="calificacion",
        verbose_name="Orden de trabajo",
    )
    tecnico = models.ForeignKey(
        "tecnicos.Tecnico",
        on_delete=models.CASCADE,
        related_name="calificaciones",
        verbose_name="Técnico",
    )
    puntuacion = models.PositiveSmallIntegerField(
        "Puntuación (1 a 5)",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comentario = models.TextField("Comentario", blank=True)
    fecha_calificacion = models.DateTimeField("Fecha de calificación", auto_now_add=True)

    class Meta:
        verbose_name = "Calificación"
        verbose_name_plural = "Calificaciones"
        ordering = ["-fecha_calificacion"]

    def __str__(self):
        return f"Calificación {self.puntuacion} - {self.tecnico}"


class TicketHistorial(models.Model):
    """
    Registro del cambio de estado de un ticket. Permite conocer quién cambió
    el estado, desde cuál hacia cuál y cuándo. No se automatiza en esta fase.
    """

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="historial",
        verbose_name="Ticket",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cambios_tickets",
        verbose_name="Usuario",
    )
    estado_anterior = models.CharField(
        "Estado anterior",
        max_length=30,
        null=True,
        blank=True,
    )
    estado_nuevo = models.CharField("Estado nuevo", max_length=30)
    comentario = models.TextField("Comentario", blank=True)
    fecha_cambio = models.DateTimeField("Fecha del cambio", auto_now_add=True)

    class Meta:
        verbose_name = "Historial de ticket"
        verbose_name_plural = "Historial de tickets"
        ordering = ["-fecha_cambio"]

    def __str__(self):
        return f"#{self.ticket.numero}: {self.estado_anterior} -> {self.estado_nuevo}"
