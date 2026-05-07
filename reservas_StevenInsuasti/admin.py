"""
Registro de modelos en el panel de administración de Django.
Configuración avanzada para gestión de reservas.
"""

from django.contrib import admin
from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    """
    Configuración del panel admin para el modelo Reserva.
    Permite al administrador visualizar, filtrar y gestionar reservas.
    """

    # Columnas visibles en el listado
    list_display = (
        'id',
        'usuario',
        'laboratorio',
        'fecha',
        'hora_inicio',
        'hora_fin',
        'estado',
        'fecha_creacion',
    )

    # Filtros laterales
    list_filter = (
        'estado',
        'laboratorio',
        'fecha',
    )

    # Búsqueda por campos de texto
    search_fields = (
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
        'laboratorio',
        'motivo',
    )

    # Campos de solo lectura (no editables desde admin)
    readonly_fields = ('fecha_creacion',)

    # Ordenamiento por defecto
    ordering = ('-fecha', 'hora_inicio')

    # Campos editables directamente desde el listado
    list_editable = ('estado',)

    # Paginación
    list_per_page = 20

    # Agrupación de campos en el formulario de detalle
    fieldsets = (
        ('Información del solicitante', {
            'fields': ('usuario',)
        }),
        ('Detalles de la reserva', {
            'fields': ('laboratorio', 'fecha', 'hora_inicio', 'hora_fin', 'motivo')
        }),
        ('Estado y auditoría', {
            'fields': ('estado', 'fecha_creacion')
        }),
    )
