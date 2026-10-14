from django import forms
from django.contrib.auth.models import User

from accounts.validators import TelefonoField

from .models import Especialidad, Tecnico


class TecnicoForm(forms.ModelForm):
    """Formulario de creación/edición de técnicos."""

    telefono = TelefonoField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "+56 9 1234 5678"}
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = User.objects.filter(perfil__rol="TECNICO")
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.usuario.pk)
        self.fields["usuario"].queryset = qs.exclude(tecnico__isnull=False)

    class Meta:
        model = Tecnico
        fields = [
            "usuario",
            "telefono",
            "documento",
            "descripcion",
            "especialidades",
            "estado",
        ]
        widgets = {
            "usuario": forms.Select(attrs={"class": "form-select"}),
            "documento": forms.TextInput(attrs={"class": "form-control", "placeholder": "RUT o documento"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "especialidades": forms.SelectMultiple(
                attrs={"class": "form-select", "size": 5}
            ),
            "estado": forms.Select(attrs={"class": "form-select"}),
        }


class EspecialidadForm(forms.ModelForm):
    """Formulario de creación/edición de especialidades."""

    class Meta:
        model = Especialidad
        fields = ["nombre", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }