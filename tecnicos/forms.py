from django import forms

from .models import Especialidad, Tecnico


class TecnicoForm(forms.ModelForm):
    """Formulario de creación/edición de técnicos."""

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
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "+56 9 1234 5678"}),
            "documento": forms.TextInput(attrs={"class": "form-control", "placeholder": "RUT o documento"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "especialidades": forms.SelectMultiple(attrs={"class": "form-select"}),
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