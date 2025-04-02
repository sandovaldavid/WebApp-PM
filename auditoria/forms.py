from django import forms
from dashboard.models import Actividad


class ActividadForm(forms.ModelForm):
    # Campo de visualización para la fecha (solo lectura)
    fecha_visualizacion = forms.DateTimeField(
        label="Fecha de creación",
        required=False,
        widget=forms.DateTimeInput(
            attrs={"readonly": "readonly", "class": "form-control"}
        ),
    )

    class Meta:
        model = Actividad
        exclude = ["fechacreacion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es edición, mostrar la fecha actual
        if self.instance.pk:
            self.fields["fecha_visualizacion"].initial = self.instance.fechacreacion
