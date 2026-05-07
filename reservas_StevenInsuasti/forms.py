"""
Formularios de la aplicación reservas_StevenInsuasti.

Responsabilidad de este módulo (feature/validaciones-filtros):
- ReservaForm: formulario principal con validaciones de conflicto de horario.
- ReservaFiltroForm: formulario de búsqueda/filtrado de reservas.
"""

from django import forms
from .models import Reserva


class ReservaForm(forms.ModelForm):
    """
    Formulario para crear y editar una Reserva.

    Campos excluidos del formulario (se asignan en la vista):
    - usuario: se toma de request.user
    - estado: siempre 'pendiente' al crear

    Validaciones implementadas:
    1. hora_fin debe ser posterior a hora_inicio.
    2. No deben existir reservas superpuestas en el mismo laboratorio y fecha.
       Se verifica cruce de horas con ORM: inicio < fin_existente AND fin > inicio_existente.
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
                'max_length': 'El nombre del laboratorio no puede superar los 100 caracteres.',
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

    # ─────────────────────────────────────────
    # VALIDACIÓN: hora_fin > hora_inicio
    # ─────────────────────────────────────────

    def clean(self):
        """
        Validaciones a nivel de formulario (cross-field):

        1. Verifica que hora_fin sea posterior a hora_inicio.
        2. Detecta conflictos de horario en el mismo laboratorio y fecha
           usando una consulta ORM que comprueba solapamiento de rangos.

        La lógica de solapamiento es:
            nueva.hora_inicio < existente.hora_fin
            AND
            nueva.hora_fin > existente.hora_inicio

        Si ambas condiciones se cumplen, los rangos se cruzan.
        """
        cleaned_data = super().clean()

        laboratorio = cleaned_data.get('laboratorio')
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')

        # Solo validar si todos los campos necesarios están presentes
        if not all([laboratorio, fecha, hora_inicio, hora_fin]):
            return cleaned_data

        # ── Validación 1: hora_fin debe ser posterior a hora_inicio ──
        if hora_fin <= hora_inicio:
            raise forms.ValidationError(
                'La hora de finalización debe ser posterior a la hora de inicio. '
                f'Recibido: inicio {hora_inicio.strftime("%H:%M")} — '
                f'fin {hora_fin.strftime("%H:%M")}.'
            )

        # ── Validación 2: Detectar conflictos de horario ──
        # Busca reservas en el mismo laboratorio y fecha que no estén rechazadas
        # y cuyo rango horario se solape con el nuevo.
        reservas_en_conflicto = Reserva.objects.filter(
            laboratorio__iexact=laboratorio,   # mismo laboratorio (sin importar mayúsculas)
            fecha=fecha,                        # misma fecha
            estado__in=[                        # solo pendientes y aprobadas
                Reserva.ESTADO_PENDIENTE,
                Reserva.ESTADO_APROBADA,
            ],
            hora_inicio__lt=hora_fin,           # la existente empieza ANTES de que termine la nueva
            hora_fin__gt=hora_inicio,           # la existente termina DESPUÉS de que empiece la nueva
        )

        # Si estamos editando, excluir la reserva actual del chequeo
        if self.instance and self.instance.pk:
            reservas_en_conflicto = reservas_en_conflicto.exclude(pk=self.instance.pk)

        if reservas_en_conflicto.exists():
            # Construir mensaje detallado con todas las reservas en conflicto
            conflictos_detalle = []
            for r in reservas_en_conflicto:
                conflictos_detalle.append(
                    f'{r.hora_inicio.strftime("%H:%M")}–{r.hora_fin.strftime("%H:%M")} '
                    f'({r.get_estado_display()})'
                )
            detalle = ', '.join(conflictos_detalle)

            raise forms.ValidationError(
                f'⚠ Conflicto de horario: el laboratorio "{laboratorio}" ya tiene '
                f'reservas el {fecha.strftime("%d/%m/%Y")} en los siguientes horarios: '
                f'{detalle}. Por favor elija otro horario o laboratorio.'
            )

        return cleaned_data


# ─────────────────────────────────────────────────────────────
# FORMULARIO DE FILTROS
# ─────────────────────────────────────────────────────────────

class ReservaFiltroForm(forms.Form):
    """
    Formulario para filtrar el listado de reservas.

    Campos:
    - fecha: filtra reservas de una fecha específica.
    - laboratorio: filtra por nombre de laboratorio (búsqueda parcial).

    Este formulario NO guarda datos; solo se usa para validar
    y limpiar los parámetros GET de la URL.
    """

    fecha = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'Filtrar por fecha',
        }),
        label='Fecha',
        error_messages={
            'invalid': 'Ingrese una fecha válida.',
        },
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
