from django.conf import settings
from django.db import models


class Dispositivo(models.Model):
    """Celular donde un técnico recibe notificaciones push.

    La app obtiene un token de Firebase Cloud Messaging (FCM) y lo registra
    aquí. Un técnico puede tener varios dispositivos; cada token es único.
    """

    class Plataforma(models.TextChoices):
        ANDROID = "ANDROID", "Android"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dispositivos",
        verbose_name="Usuario",
    )
    token = models.CharField("Token FCM", max_length=255, unique=True)
    plataforma = models.CharField(
        "Plataforma",
        max_length=20,
        choices=Plataforma.choices,
        default=Plataforma.ANDROID,
    )
    fecha_registro = models.DateTimeField("Fecha de registro", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Última actualización", auto_now=True)

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"
        ordering = ["-fecha_actualizacion"]

    def __str__(self):
        return f"{self.get_plataforma_display()} de {self.usuario}"
