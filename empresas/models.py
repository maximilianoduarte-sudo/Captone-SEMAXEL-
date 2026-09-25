from django.db import models


class Empresa(models.Model):
    """
    Empresa cliente del sistema de gestión de mantenimiento.

    Las sucursales pertenecen a una empresa y el aislamiento de datos entre
    empresas se implementa de forma lógica sobre una única base de datos.
    """

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        INACTIVA = "INACTIVA", "Inactiva"

    nombre = models.CharField("Nombre", max_length=150)
    rut = models.CharField(
        "RUT",
        max_length=20,
        unique=True,
        help_text="Identificador tributario único de la empresa.",
    )
    codigo = models.CharField(
        "Código",
        max_length=20,
        unique=True,
        help_text="Identificador único y corto de la empresa.",
    )
    direccion = models.CharField("Dirección", max_length=255, blank=True)
    comuna = models.CharField("Comuna", max_length=100, blank=True)
    ciudad = models.CharField("Ciudad", max_length=100, blank=True)
    region = models.CharField("Región", max_length=100, blank=True)
    telefono = models.CharField("Teléfono", max_length=30, blank=True)
    correo = models.EmailField("Correo", blank=True)
    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVA,
    )
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de actualización", auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre