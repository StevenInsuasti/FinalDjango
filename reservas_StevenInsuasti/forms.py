"""
Formularios de la aplicación reservas_StevenInsuasti.

- ReservaForm: formulario principal con validaciones de conflicto de horario.
- ReservaFiltroForm: formulario de búsqueda/filtrado de reservas.
"""

from django import forms
from .models import Reserva


class ReservaForm(forms.ModelForm):
    """
    Formulario para crear y editar una Reserva.

    Campos excluidos (se asignan en la vista):
    - usuario: se toma de request.user
    - estado: siempre 'pendiente' al crear

    Validaciones:
    1. hora_fin debe ser posterior a hora_inicio.
    2. No deben existir reservas superpuestas en el mismo laboratorio y fecha.
    """

    class Meta:
        model = Reserva
        fields = ['laboratorio', 'fecha', 'hora_inicio', 'hora_fin', 'motivo']
        widgets = {
            'laboratorio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Laboratorio de Redes',
                'autocomplete': 'off',
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'hora_fin': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describa el motivo de la reserva...',
            }),
        }
        labels = {
            'laboratorio': 'Laboratorio',
            'fecha': 'Fecha',
            'hora_inicio': 'Hora de inicio',
            'hora_fin': 'Hora de fin',
            'motivo': 'Motivo',
        }
        error_messages = {
            'laboratorio': {
                'required': 'Debe ingresar el nombre del laboratorio.',
                'max_length': 'El nombre no puede superar los 100 caracteres.',
            },
            'fecha': {
                'required': 'Debe seleccionar una fecha para la reserva.',
                'invalid': 'Ingrese una fecha válida (AAAA-MM-DD).',
            },
            'hora_inicio': {
                'required': 'Debe indicar la hora de inicio.',
                'invalid': 'Ingrese una hora válida (HH:MM).',
            },
            'hora_fin': {
                'required': 'Debe indicar la hora de finalización.',
                'invalid': 'Ingrese una hora válida (HH:MM).',
            },
            'motivo': {
                'required': 'Debe describir el motivo de la reserva.',
            },
        }

    def clean(self):
        """
        Validaciones cruzadas:
        1. hora_fin > hora_inicio.
        2. Sin solapamiento de horarios en el mismo laboratorio y fecha.
        """
        cleaned_data = super().clean()

        laboratorio = cleaned_data.get('laboratorio')
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')

        if not all([laboratorio, fecha, hora_inicio, hora_fin]):
            return cleaned_data

        # ── Validación 1: hora_fin > hora_inicio ──
        if hora_fin <= hora_inicio:
            raise forms.ValidationError(
                f'La hora de finalización debe ser posterior a la de inicio. '
                f'Recibido: inicio {hora_inicio.strftime("%H:%M")} — '
                f'fin {hora_fin.strftime("%H:%M")}.'
            )

        # ── Validación 2: Conflictos de horario ──
        reservas_en_conflicto = Reserva.objects.filter(
            laboratorio__iexact=laboratorio,
            fecha=fecha,
            estado__in=[Reserva.ESTADO_PENDIENTE, Reserva.ESTADO_APROBADA],
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio,
        )

        if self.instance and self.instance.pk:
            reservas_en_conflicto = reservas_en_conflicto.exclude(pk=self.instance.pk)

        if reservas_en_conflicto.exists():
            conflictos = ', '.join([
                f'{r.hora_inicio.strftime("%H:%M")}–{r.hora_fin.strftime("%H:%M")} '
                f'({r.get_estado_display()})'
                for r in reservas_en_conflicto
            ])
            raise forms.ValidationError(
                f'⚠ Conflicto de horario: "{laboratorio}" ya tiene reservas '
                f'el {fecha.strftime("%d/%m/%Y")} en: {conflictos}. '
                f'Por favor elija otro horario o laboratorio.'
            )

        return cleaned_data


class ReservaFiltroForm(forms.Form):
    """
    Formulario para filtrar el listado de reservas.
    No guarda datos; solo valida y limpia los parámetros GET.
    """

    fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        }),
        label='Fecha',
        error_messages={'invalid': 'Ingrese una fecha válida.'},
    )

    laboratorio = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar laboratorio...',
            'autocomplete': 'off',
        }),
        label='Laboratorio',
    )
