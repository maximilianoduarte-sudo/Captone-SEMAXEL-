from django import forms

from accounts.roles import sucursales_visibles
from tickets.models import Categoria

from .models import PlanMantenimiento


class PlanMantenimientoForm(forms.ModelForm):
    """Formulario de creación/edición de planes de mantenimiento preventivo.

    Recibe `user` para acotar las sucursales al alcance del rol (las
    categorías y la empresa derivan de la sucursal elegida).
    """

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["sucursal"].queryset = sucursales_visibles(user).select_related(
                "empresa"
            )
        self.fields["categoria"].queryset = Categoria.objects.filter(activo=True)

    class Meta:
        model = PlanMantenimiento
        fields = [
            "nombre",
            "descripcion",
            "sucursal",
            "categoria",
            "frecuencia",
            "fecha_proxima",
            "activo",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej.: Lubricación motores sala de máquinas"}
            ),
            "descripcion": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción de las tareas del plan"}
            ),
            "sucursal": forms.Select(attrs={"class": "form-select"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "frecuencia": forms.Select(attrs={"class": "form-select"}),
            "fecha_proxima": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }