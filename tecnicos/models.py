from django.conf import settings
from django.db import models


class Especialidad(models.Model):
    """
    Especialidad técnica configurable (p. ej. Electricidad, Gasfitería,
    Infraestructura). No se encuentra hardcodeada: se administra por registros.
    """

    nombre = models.CharField("Nombre", max_length=100, unique=True)
    descripcion = models.TextField("Descripción", blank=True)
    activo = models.BooleanField("Activo", default=True)

    class Meta:
        verbose_name = "Especialidad"
        verbose_name_plural = "Especialidades"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Tecnico(models.Model):
    """
    Técnico de mantenimiento. Se relaciona uno a uno con un usuario de Django.
    Un técnico puede tener varias especialidades (relación muchos a muchos).
    """

    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        OCUPADO = "OCUPADO", "Ocupado"
        NO_DISPONIBLE = "NO_DISPONIBLE", "No disponible"
        INACTIVO = "INACTIVO", "Inactivo"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tecnico",
        verbose_name="Usuario",
    )
    telefono = models.CharField("Teléfono", max_length=30, blank=True)
    documento = models.CharField(
        "Documento de identificación",
        max_length=30,
        blank=True,
        unique=True,
    )
    descripcion = models.TextField(
        "Información adicional",
        blank=True,
        help_text="Experiencia, notas u otra información relevante.",
    )
    especialidades = models.ManyToManyField(
        Especialidad,
        verbose_name="Especialidades",
        related_name="tecnicos",
        blank=True,
    )
    estado = models.CharField(
        "Estado / Disponibilidad",
        max_length=20,
        choices=Estado.choices,
        default=Estado.NO_DISPONIBLE,
    )
    fecha_registro = models.DateTimeField("Fecha de registro", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de actualización", auto_now=True)

    class Meta:
        verbose_name = "Técnico"
        verbose_name_plural = "Técnicos"
        ordering = ["usuario__username"]
        indexes = [
            models.Index(fields=["estado"], name="idx_tecnico_estado"),
        ]

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.get_estado_display()}"
