from django.db import models
from django.utils import timezone


class PlanMantenimiento(models.Model):
    """
    Plan de mantenimiento preventivo asociado a una sucursal.

    Cada plan define una frecuencia y el momento de su próxima ejecución.
    Cuando `fecha_proxima` vence se genera automáticamente un ticket de tipo
    PREVENTIVO (ver `mantenimiento.services.generar_tickets_preventivos`).
    """

    class Frecuencia(models.TextChoices):
        DIARIA = "DIARIA", "Diaria"
        SEMANAL = "SEMANAL", "Semanal"
        QUINCENAL = "QUINCENAL", "Quincenal"
        MENSUAL = "MENSUAL", "Mensual"
        BIMESTRAL = "BIMESTRAL", "Bimestral"
        TRIMESTRAL = "TRIMESTRAL", "Trimestral"
        SEMESTRAL = "SEMESTRAL", "Semestral"
        ANUAL = "ANUAL", "Anual"

    FRECUENCIA_DIAS = {
        Frecuencia.DIARIA: 1,
        Frecuencia.SEMANAL: 7,
        Frecuencia.QUINCENAL: 15,
        Frecuencia.MENSUAL: 30,
        Frecuencia.BIMESTRAL: 60,
        Frecuencia.TRIMESTRAL: 90,
        Frecuencia.SEMESTRAL: 180,
        Frecuencia.ANUAL: 365,
    }

    nombre = models.CharField("Nombre", max_length=150)
    descripcion = models.TextField("Descripción", blank=True)
    sucursal = models.ForeignKey(
        "sucursales.Sucursal",
        on_delete=models.CASCADE,
        related_name="planes_mantenimiento",
        verbose_name="Sucursal",
    )
    categoria = models.ForeignKey(
        "tickets.Categoria",
        on_delete=models.PROTECT,
        related_name="planes_mantenimiento",
        verbose_name="Categoría",
    )
    frecuencia = models.CharField(
        "Frecuencia",
        max_length=20,
        choices=Frecuencia.choices,
        default=Frecuencia.MENSUAL,
    )
    fecha_proxima = models.DateTimeField(
        "Próxima ejecución",
        default=timezone.now,
    )
    activo = models.BooleanField("Activo", default=True)
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de actualización", auto_now=True)

    class Meta:
        verbose_name = "Plan de mantenimiento"
        verbose_name_plural = "Planes de mantenimiento"
        ordering = ["sucursal__empresa__codigo", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.sucursal})"

    @property
    def empresa(self):
        return self.sucursal.empresa

    @property
    def frecuencia_dias(self):
        return self.FRECUENCIA_DIAS.get(self.frecuencia, 30)


class ProgramacionMantenimiento(models.Model):
    """
    Ejecución programada de un plan y su ticket preventivo generado.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        GENERADO = "GENERADO", "Ticket generado"
        COMPLETADO = "COMPLETADO", "Completado"
        OMITIDO = "OMITIDO", "Omitido"

    plan = models.ForeignKey(
        PlanMantenimiento,
        on_delete=models.CASCADE,
        related_name="programaciones",
        verbose_name="Plan",
    )
    fecha_programada = models.DateTimeField("Fecha programada", default=timezone.now)
    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="programaciones_preventivas",
        verbose_name="Ticket generado",
    )
    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    fecha_ejecucion = models.DateTimeField("Fecha de ejecución", null=True, blank=True)
    observaciones = models.TextField("Observaciones", blank=True)

    class Meta:
        verbose_name = "Programación de mantenimiento"
        verbose_name_plural = "Programaciones de mantenimiento"
        ordering = ["-fecha_programada"]

    def __str__(self):
        return f"{self.plan} · {self.fecha_programada:%d/%m/%Y}"