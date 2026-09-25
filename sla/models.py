from django.db import models

from empresas.models import Empresa


class SLAPolicy(models.Model):
    """
    Política de Acuerdo de Nivel de Servicio (SLA).

    Define los tiempos máximos de respuesta y resolución según prioridad.
    Es posible definir políticas específicas por empresa; si una empresa no
    tiene política para una prioridad se usa la política global de respaldo
    (empresa vacía).
    """

    class Prioridad(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"
        CRITICA = "CRITICA", "Crítica"

    nombre = models.CharField("Nombre", max_length=100)
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
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="sla_policies",
        verbose_name="Empresa",
        null=True,
        blank=True,
        help_text="Empresa a la que aplica esta política. Vacío = política "
        "global de respaldo para todas las empresas.",
    )
    activo = models.BooleanField("Activo", default=True)
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de actualización", auto_now=True)

    class Meta:
        verbose_name = "Política SLA"
        verbose_name_plural = "Políticas SLA"
        ordering = ["empresa__nombre", "prioridad", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "prioridad"],
                name="uniq_sla_empresa_prioridad",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.get_prioridad_display()}"

    @classmethod
    def obtener(cls, empresa, prioridad):
        """Política efectiva: la específica de la empresa o la global de respaldo."""
        if empresa is not None:
            especifica = cls.objects.filter(
                empresa=empresa, prioridad=prioridad, activo=True
            ).first()
            if especifica:
                return especifica
        return cls.objects.filter(
            empresa__isnull=True, prioridad=prioridad, activo=True
        ).first()