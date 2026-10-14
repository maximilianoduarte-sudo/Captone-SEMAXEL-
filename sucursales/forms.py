from django import forms
from django.contrib.auth.models import User

from accounts.roles import ROLES_ENCARGADOS

from .models import Sucursal


class SucursalForm(forms.ModelForm):
    """Formulario de creación/edición de sucursales.

    Recibe `empresa` para acotar los encargados a usuarios de esa empresa y
    validar el código único dentro de la misma.
    """

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._empresa = empresa or getattr(self.instance, "empresa", None)
        if self._empresa:
            self.fields["encargados"].queryset = (
                User.objects.filter(
                    perfil__empresa=self._empresa,
                    perfil__rol__in=ROLES_ENCARGADOS,
                )
                .select_related("perfil")
                .order_by("username")
            )

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

    def clean_codigo(self):
        """El código debe ser único dentro de la empresa."""
        codigo = self.cleaned_data.get("codigo")
        if codigo and self._empresa:
            qs = Sucursal.objects.filter(empresa=self._empresa, codigo=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "Ya existe una sucursal con este código en la empresa."
                )
        return codigo

    def clean_encargados(self):
        """Los encargados deben ser usuarios de la misma empresa."""
        encargados = self.cleaned_data.get("encargados")
        if encargados is None:
            return encargados
        if self._empresa:
            invalidos = encargados.exclude(
                perfil__empresa=self._empresa,
                perfil__rol__in=ROLES_ENCARGADOS,
            )
            if invalidos.exists():
                raise forms.ValidationError(
                    "Solo pueden ser encargados usuarios de esta empresa."
                )
        return encargados