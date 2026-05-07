"""
Modelos de la aplicación reservas_StevenInsuasti.
Define la entidad principal: Reserva de laboratorio.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Reserva(models.Model):
    """
    Modelo que representa una reserva de laboratorio.

    Un docente puede solicitar el uso de un laboratorio en una
    fecha y rango horario específico. El administrador aprueba
    o rechaza la solicitud.
    """

    # ─────────────────────────────────────────
    # CHOICES para el campo estado
    # ─────────────────────────────────────────
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_RECHAZADA = 'rechazada'

    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
    ]

    # ─────────────────────────────────────────
    # CAMPOS DEL MODELO
    # ─────────────────────────────────────────

    # Usuario que realiza la reserva (docente)
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservas',
        verbose_name='Usuario',
    )

    # Nombre del laboratorio solicitado
    laboratorio = models.CharField(
        max_length=100,
        verbose_name='Laboratorio',
    )

    # Fecha de la reserva
    fecha = models.DateField(
        verbose_name='Fecha',
    )

    # Hora de inicio de la reserva
    hora_inicio = models.TimeField(
        verbose_name='Hora de inicio',
    )

    # Hora de finalización de la reserva
    hora_fin = models.TimeField(
        verbose_name='Hora de fin',
    )

    # Estado actual de la reserva
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_PENDIENTE,
        verbose_name='Estado',
    )

    # Motivo o descripción de la reserva
    motivo = models.TextField(
        verbose_name='Motivo',
    )

    # Fecha y hora en que se creó la reserva (automática)
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación',
    )

    # ─────────────────────────────────────────
    # VALIDACIONES
    # ─────────────────────────────────────────

    def clean(self):
        """
        Validaciones de negocio:
        1. hora_fin debe ser mayor que hora_inicio.
        2. No deben existir conflictos de horario en el mismo laboratorio y fecha.
        """
        # Validar que hora_fin > hora_inicio
        if self.hora_inicio and self.hora_fin:
            if self.hora_fin <= self.hora_inicio:
                raise ValidationError(
                    'La hora de fin debe ser posterior a la hora de inicio.'
                )

        # Validar conflictos de horario en el mismo laboratorio y fecha
        conflictos = Reserva.objects.filter(
            laboratorio=self.laboratorio,
            fecha=self.fecha,
            estado__in=[self.ESTADO_PENDIENTE, self.ESTADO_APROBADA],
        ).exclude(pk=self.pk)

        for reserva in conflictos:
            # Hay conflicto si los rangos horarios se solapan
            if self.hora_inicio < reserva.hora_fin and self.hora_fin > reserva.hora_inicio:
                raise ValidationError(
                    f'Ya existe una reserva en "{self.laboratorio}" '
                    f'el {self.fecha} entre {reserva.hora_inicio} y {reserva.hora_fin}.'
                )

    def save(self, *args, **kwargs):
        """Ejecuta validaciones antes de guardar."""
        self.full_clean()
        super().save(*args, **kwargs)

    # ─────────────────────────────────────────
    # PROPIEDADES DE CONVENIENCIA
    # ─────────────────────────────────────────

    @property
    def es_pendiente(self):
        """Retorna True si la reserva está en estado pendiente."""
        return self.estado == self.ESTADO_PENDIENTE

    @property
    def es_aprobada(self):
        """Retorna True si la reserva está aprobada."""
        return self.estado == self.ESTADO_APROBADA

    # ─────────────────────────────────────────
    # METADATA
    # ─────────────────────────────────────────

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-fecha', 'hora_inicio']

    def __str__(self):
        return (
            f'{self.laboratorio} | {self.fecha} '
            f'{self.hora_inicio}-{self.hora_fin} | '
            f'{self.get_estado_display()} | {self.usuario.get_full_name() or self.usuario.username}'
        )
