from django.db import models


class SLAPolicy(models.Model):
    """
    Política de Acuerdo de Nivel de Servicio (SLA).

    Define los tiempos máximos de respuesta y resolución según prioridad.
    No se implementa todavía el cálculo automático de vencimientos.
    """

    class Prioridad(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"
        CRITICA = "CRITICA", "Crítica"

    nombre = models.CharField("Nombre", max_length=100, unique=True)
    prioridad = models.CharField(
        "Prioridad",
        max_length=20,
        choices=Prioridad.choices,
        default=Prioridad.MEDIA,
    )
    tiempo_maximo_respuesta = models.PositiveIntegerField(
        "Tiempo máximo de respuesta (minutos)"
    )
    tiempo_maximo_resolucion = models.PositiveIntegerField(
        "Tiempo máximo de resolución (minutos)"
    )
    activo = models.BooleanField("Activo", default=True)
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de actualización", auto_now=True)

    class Meta:
        verbose_name = "Política SLA"
        verbose_name_plural = "Políticas SLA"
        ordering = ["prioridad", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["prioridad"],
                name="uniq_sla_prioridad",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.get_prioridad_display()}"
