from django.conf import settings
from django.db import models


class Sucursal(models.Model):
    """
    Sucursal de la empresa donde se realiza mantenimiento de infraestructura.
    """

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        INACTIVA = "INACTIVA", "Inactiva"

    nombre = models.CharField("Nombre", max_length=150)
    codigo = models.CharField(
        "Código",
        max_length=20,
        unique=True,
        help_text="Identificador único y corto de la sucursal.",
    )
    direccion = models.CharField("Dirección", max_length=255)
    comuna = models.CharField("Comuna", max_length=100, blank=True)
    ciudad = models.CharField("Ciudad", max_length=100, blank=True)
    region = models.CharField("Región", max_length=100, blank=True)
    telefono = models.CharField("Teléfono", max_length=30, blank=True)
    correo = models.EmailField("Correo", blank=True)
    encargados = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name="Encargados",
        related_name="sucursales_encargadas",
        blank=True,
        help_text="Usuarios encargados de la sucursal.",
    )
    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVA,
    )
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de actualización", auto_now=True)

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
