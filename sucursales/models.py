from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Sucursal(models.Model):
    """
    Sucursal de la empresa donde se realiza mantenimiento de infraestructura.
    """

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        INACTIVA = "INACTIVA", "Inactiva"

    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.PROTECT,
        related_name="sucursales",
        verbose_name="Empresa",
        help_text="Empresa a la que pertenece la sucursal.",
    )
    nombre = models.CharField("Nombre", max_length=150)
    codigo = models.CharField(
        "Código",
        max_length=20,
        help_text="Identificador corto de la sucursal, único dentro de su empresa.",
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
    # Coordenadas de la entrada del local. Las usa la app del técnico para
    # validar su llegada con GPS (Documento A, flujo 2).
    latitud = models.DecimalField(
        "Latitud",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text="Ejemplo: -33.437800",
    )
    longitud = models.DecimalField(
        "Longitud",
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text="Ejemplo: -70.650400",
    )
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de actualización", auto_now=True)

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_sucursal_codigo_por_empresa",
            ),
        ]

    def __str__(self):
        return self.nombre

    @property
    def tiene_coordenadas(self):
        return self.latitud is not None and self.longitud is not None

    def clean(self):
        super().clean()
        if (self.latitud is None) != (self.longitud is None):
            raise ValidationError(
                "Ingresa la latitud y la longitud juntas, o deja ambas vacías."
            )

    @property
    def encargado(self):
        """Primer encargado (para mostrar en listados y detalle)."""
        encargado = self.encargados.first()
        if encargado:
            return encargado.get_full_name() or encargado.username
        return "Sin encargado"


class HorarioSucursal(models.Model):
    """Horario de atención de una sucursal para un día de la semana.

    Un día sin registro se considera cerrado. La app del técnico lo muestra
    antes de ir al local.
    """

    class Dia(models.IntegerChoices):
        LUNES = 0, "Lunes"
        MARTES = 1, "Martes"
        MIERCOLES = 2, "Miércoles"
        JUEVES = 3, "Jueves"
        VIERNES = 4, "Viernes"
        SABADO = 5, "Sábado"
        DOMINGO = 6, "Domingo"

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.CASCADE,
        related_name="horarios",
        verbose_name="Sucursal",
    )
    dia_semana = models.PositiveSmallIntegerField("Día", choices=Dia.choices)
    hora_apertura = models.TimeField("Apertura")
    hora_cierre = models.TimeField("Cierre")

    class Meta:
        verbose_name = "Horario de sucursal"
        verbose_name_plural = "Horarios de sucursal"
        ordering = ["sucursal", "dia_semana"]
        constraints = [
            models.UniqueConstraint(
                fields=["sucursal", "dia_semana"],
                name="uniq_horario_sucursal_dia",
            ),
        ]

    def __str__(self):
        return f"{self.get_dia_semana_display()} {self.hora_apertura:%H:%M}-{self.hora_cierre:%H:%M}"

    def clean(self):
        super().clean()
        if self.hora_apertura and self.hora_cierre and self.hora_apertura >= self.hora_cierre:
            raise ValidationError("La hora de apertura debe ser anterior a la de cierre.")
