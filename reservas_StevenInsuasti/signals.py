"""
Signals de la aplicación reservas_StevenInsuasti.
Crea automáticamente los grupos de roles al ejecutar las migraciones.
"""

from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def crear_roles_base(sender, **kwargs):
    """
    Crea los grupos 'Docente' y 'Administrador' si no existen,
    cada vez que se ejecuta `python manage.py migrate`.
    """
    if sender.name != 'reservas_StevenInsuasti':
        return

    Group.objects.get_or_create(name='Docente')
    Group.objects.get_or_create(name='Administrador')
