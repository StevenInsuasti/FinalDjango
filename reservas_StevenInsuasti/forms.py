"""
Formularios de la aplicación reservas_StevenInsuasti.
Define el formulario principal para crear y editar reservas.
"""

from django import forms
from .models import Reserva


class ReservaForm(forms.ModelForm):
    """
    Formulario para crear y editar una Reserva.

    El campo 'usuario' y 'estado' se excluyen del formulario
    porque se asignan automáticamente en las vistas:
    - usuario: se toma del request.user
    - estado: por defecto 'pendiente' al crear
    """

    class Meta:
        model = Reserva
        fields = ['laboratorio', 'fecha', 'hora_inicio', 'hora_fin', 'motivo']
        widgets = {
            'laboratorio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Laboratorio de Redes',
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
