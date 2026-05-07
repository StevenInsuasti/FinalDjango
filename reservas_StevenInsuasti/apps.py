"""
Configuración de la aplicación reservas_StevenInsuasti.
"""

from django.apps import AppConfig


class ReservasStevenInsuastiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservas_StevenInsuasti'
    verbose_name = 'Gestión de Reservas de Laboratorios'

    def ready(self):
        """Registra los signals al iniciar la aplicación."""
        import reservas_StevenInsuasti.signals  # noqa: F401
