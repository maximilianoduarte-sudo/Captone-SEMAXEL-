from django import forms

from .models import OfertaTicket


class OfertaForm(forms.ModelForm):
    """Formulario de publicación de una oferta para un ticket."""

    class Meta:
        model = OfertaTicket
        fields = ["fecha_vencimiento", "observaciones"]
        widgets = {
            "fecha_vencimiento": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "observaciones": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Requerimientos adicionales para el técnico"}
            ),
        }