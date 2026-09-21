from django import forms

from .models import Categoria, Ticket, TicketHistorial


class TicketForm(forms.ModelForm):
    """Formulario de creación de tickets (incidencia o preventivo)."""

    class Meta:
        model = Ticket
        fields = [
            "sucursal",
            "categoria",
            "prioridad",
            "tipo",
            "titulo",
            "descripcion",
            "informacion_adicional",
        ]
        widgets = {
            "sucursal": forms.Select(attrs={"class": "form-select"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "prioridad": forms.Select(attrs={"class": "form-select"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Fuga de agua en cocina"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Describe la falla o incidencia detectada..."}),
            "informacion_adicional": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Información adicional (opcional)"}),
        }


class CambiarEstadoForm(forms.ModelForm):
    """Formulario para cambiar el estado de un ticket (registra historial)."""

    comentario = forms.CharField(
        label="Comentario",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Motivo del cambio (opcional)"}),
    )

    class Meta:
        model = Ticket
        fields = ["estado"]
        widgets = {
            "estado": forms.Select(attrs={"class": "form-select"}),
        }