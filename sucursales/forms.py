from django import forms

from .models import Sucursal


class SucursalForm(forms.ModelForm):
    """Formulario de creación/edición de sucursales."""

    class Meta:
        model = Sucursal
        fields = [
            "nombre",
            "codigo",
            "direccion",
            "comuna",
            "ciudad",
            "region",
            "telefono",
            "correo",
            "encargados",
            "estado",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la sucursal"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "PRO"}),
            "direccion": forms.TextInput(attrs={"class": "form-control", "placeholder": "Av. Principal 123"}),
            "comuna": forms.TextInput(attrs={"class": "form-control", "placeholder": "Comuna"}),
            "ciudad": forms.TextInput(attrs={"class": "form-control"}),
            "region": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "+56 2 2345 1000"}),
            "correo": forms.EmailInput(attrs={"class": "form-control", "placeholder": "sucursal@semaxel.cl"}),
            "encargados": forms.SelectMultiple(attrs={"class": "form-select"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
        }