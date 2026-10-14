"""Validadores y campos reutilizables de usuarios, teléfonos y contraseñas.

Se centralizan aquí para que los formularios de registro y edición compartan
las mismas reglas, sin repetir lógica ni depender de validaciones del navegador.
"""

import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

LETRA_MAYUSCULA = re.compile(r"[A-ZÁÉÍÓÚÜÑ]")
DIGITO = re.compile(r"\d")
SIMBOLO = re.compile(r"[^\w\s]")

PASSWORD_HELP_TEXT = _(
    "Mínimo 8 caracteres, con al menos una letra mayúscula, un número y un símbolo."
)


class TelefonoField(forms.CharField):
    """Teléfono obligatorio.

    Rechaza valores vacíos o formados únicamente por espacios. El recorte de
    espacios lo hace `CharField` (strip=True); aquí se valida antes para poder
    emitir un mensaje específico.
    """

    default_error_messages = {
        "required": _("El teléfono es obligatorio."),
        "vacio": _("El teléfono no puede estar vacío ni contener solo espacios."),
    }

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 30)
        kwargs.setdefault("label", "Teléfono")
        super().__init__(strip=True, **kwargs)

    def clean(self, value):
        if isinstance(value, str) and value and not value.strip():
            raise ValidationError(self.error_messages["vacio"], code="vacio")
        value = super().clean(value)
        return value.strip() if isinstance(value, str) else value


class ComplejidadPasswordValidator:
    """Exige al menos una mayúscula, un número y un símbolo en la contraseña.

    Complementa a los validadores estándar de Django (longitud mínima,
    contraseñas comunes, similitud con datos del usuario y contraseñas
    enteramente numéricas), que se configuran en `AUTH_PASSWORD_VALIDATORS`.
    """

    def __init__(
        self,
        exige_mayuscula=True,
        exige_numero=True,
        exige_simbolo=True,
    ):
        self.exige_mayuscula = exige_mayuscula
        self.exige_numero = exige_numero
        self.exige_simbolo = exige_simbolo

    def _errores(self, password):
        errores = []
        if self.exige_mayuscula and not LETRA_MAYUSCULA.search(password):
            errores.append(
                ValidationError(
                    _("La contraseña debe incluir al menos una letra mayúscula."),
                    code="password_sin_mayuscula",
                )
            )
        if self.exige_numero and not DIGITO.search(password):
            errores.append(
                ValidationError(
                    _("La contraseña debe incluir al menos un número."),
                    code="password_sin_numero",
                )
            )
        if self.exige_simbolo and not SIMBOLO.search(password):
            errores.append(
                ValidationError(
                    _(
                        "La contraseña debe incluir al menos un símbolo "
                        "(por ejemplo: !, @, #, $, %)."
                    ),
                    code="password_sin_simbolo",
                )
            )
        return errores

    def validate(self, password, user=None):
        errores = self._errores(password)
        if errores:
            raise ValidationError(errores)

    def get_help_text(self):
        return _(
            "Debe incluir al menos una letra mayúscula, un número y un símbolo."
        )


def usuario_para_validar(cleaned, instancia=None):
    """Construye un `User` (sin guardar) para la validación de similitud.

    `UserAttributeSimilarityValidator` compara la contraseña con los datos del
    usuario, por lo que necesita un objeto con esos atributos ya cargados.
    """
    username = cleaned.get("username") or getattr(instancia, "username", "")
    first_name = cleaned.get("first_name") or getattr(instancia, "first_name", "")
    last_name = cleaned.get("last_name") or getattr(instancia, "last_name", "")
    email = cleaned.get("email") or getattr(instancia, "email", "")
    return User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
    )


def validar_password(password, cleaned, instancia=None):
    """Ejecuta los validadores configurados sobre `password`.

    No hace nada si la contraseña está vacía: en la edición, dejar el campo en
    blanco significa conservar la contraseña actual, y las contraseñas
    existentes no se revalidan.
    """
    if not password:
        return
    validate_password(password, user=usuario_para_validar(cleaned, instancia))
