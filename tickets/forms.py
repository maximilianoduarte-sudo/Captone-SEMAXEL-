from django import forms

from .models import Categoria, OrdenTrabajo, Ticket, TicketHistorial


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

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            from accounts.roles import sucursales_visibles
            self.fields["sucursal"].queryset = sucursales_visibles(user)

    def clean_sucursal(self):
        """Solo se permiten sucursales visibles para el usuario."""
        sucursal = self.cleaned_data.get("sucursal")
        if sucursal is None:
            return sucursal
        if not self.fields["sucursal"].queryset.filter(pk=sucursal.pk).exists():
            raise forms.ValidationError("No tienes permisos para usar esta sucursal.")
        return sucursal


class CambiarEstadoForm(forms.ModelForm):
    """Formulario para cambiar el estado de un ticket (registra historial).

    Con ``estado_actual`` limita las opciones del desplegable a las
    transiciones válidas de la máquina de estados y valida la transición.
    """

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

    def __init__(self, *args, **kwargs):
        estado_actual = kwargs.pop("estado_actual", None)
        super().__init__(*args, **kwargs)
        if estado_actual is not None:
            validos = Ticket.transiciones_de(estado_actual)
            self.fields["estado"].choices = [
                (valor, etiqueta)
                for valor, etiqueta in Ticket.Estado.choices
                if valor in validos
            ]

    def clean_estado(self):
        estado = self.cleaned_data.get("estado")
        actual = getattr(self.instance, "estado", None)
        if (
            actual
            and estado
            and actual != estado
            and estado not in Ticket.transiciones_de(actual)
        ):
            raise forms.ValidationError(
                f"Transición de estado no permitida: {actual} → {estado}."
            )
        return estado


class CambioEstadoOrdenForm(forms.ModelForm):
    """Formulario para ejecutar la máquina de estados de una orden de trabajo.

    El estado es el único campo del modelo: los datos de ejecución
    (diagnóstico, trabajo, costos) se reciben como campos extra y solo se
    aplican cuando la transición es de trabajo (iniciar/avanzar), evitando
    pisar valores existentes al cerrar o cancelar.

    Con ``estados_permitidos`` se acota el desplegable según el rol (p. ej.
    un técnico no puede cerrar ni cancelar su propia orden).
    """

    diagnostico = forms.CharField(
        label="Diagnóstico",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 2, "placeholder": "Diagnóstico del técnico"}
        ),
    )
    trabajo_realizado = forms.CharField(
        label="Trabajo realizado",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 2, "placeholder": "Trabajo realizado"}
        ),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 2, "placeholder": "Observaciones (opcional)"}
        ),
    )
    costo_estimado = forms.DecimalField(
        label="Costo estimado",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    costo_final = forms.DecimalField(
        label="Costo final",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    puntuacion = forms.IntegerField(
        label="Calificación (1 a 5)",
        required=False,
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "min": 1, "max": 5}
        ),
    )
    comentario_calificacion = forms.CharField(
        label="Comentario de la calificación",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    class Meta:
        model = OrdenTrabajo
        fields = ["estado"]
        widgets = {
            "estado": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, estados_permitidos=None, **kwargs):
        super().__init__(*args, **kwargs)
        permitidos = estados_permitidos
        if permitidos is None:
            permitidos = self.instance.transiciones_validas()
        self.fields["estado"].choices = [
            (valor, etiqueta)
            for valor, etiqueta in OrdenTrabajo.Estado.choices
            if valor in permitidos
        ]

    def clean_estado(self):
        estado = self.cleaned_data.get("estado")
        actual = self.instance.estado
        if not estado:
            raise forms.ValidationError("Seleccione un estado destino.")
        if actual != estado and estado not in OrdenTrabajo.transiciones_de(actual):
            raise forms.ValidationError(
                f"Transición de la orden no permitida: {actual} → {estado}."
            )
        return estado

    def clean(self):
        cleaned = super().clean()
        estado = cleaned.get("estado")
        actual = self.instance.estado
        if estado == OrdenTrabajo.Estado.EN_EJECUCION and actual != OrdenTrabajo.Estado.EN_EJECUCION:
            if not (cleaned.get("diagnostico") or self.instance.diagnostico):
                self.add_error(
                    "diagnostico",
                    "Ingresa el diagnóstico para iniciar el trabajo.",
                )
        if estado == OrdenTrabajo.Estado.RESUELTA:
            if not (cleaned.get("trabajo_realizado") or self.instance.trabajo_realizado):
                self.add_error(
                    "trabajo_realizado",
                    "Registra el trabajo realizado antes de resolver la orden.",
                )
        if estado == OrdenTrabajo.Estado.CERRADA:
            if not cleaned.get("puntuacion"):
                self.add_error(
                    "puntuacion",
                    "La calificación (1 a 5) es obligatoria al cerrar la orden.",
                )
        return cleaned