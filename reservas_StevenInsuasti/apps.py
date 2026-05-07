"""
Configuración de la aplicación reservas_StevenInsuasti.
"""

from django.apps import AppConfig


class ReservasStevenInsuastiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservas_StevenInsuasti'
    verbose_name = 'Gestión de Reservas de Laboratorios'

    def ready(self):
        from . import signals  # noqa: F401
