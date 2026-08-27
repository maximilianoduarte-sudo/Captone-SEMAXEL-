from django.conf import settings
from django.db import models


class Usuario(models.Model):
    """
    Perfil de usuario del sistema.

    Extiende el modelo User estándar de Django (auth.User) mediante una
    relación uno a uno. Guarda el rol del sistema y el teléfono, mientras
    que la autenticación, sesiones y permisos los maneja Django.
    """

    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        GESTOR = "GESTOR", "Gestor"
        ENCARGADO = "ENCARGADO", "Encargado"
        TECNICO = "TECNICO", "Técnico"
        GERENCIA = "GERENCIA", "Gerencia"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil",
        verbose_name="Usuario",
    )
    rol = models.CharField(
        "Rol",
        max_length=20,
        choices=Rol.choices,
        default=Rol.ENCARGADO,
    )
    telefono = models.CharField(
        "Teléfono",
        max_length=30,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_rol_display()}"
