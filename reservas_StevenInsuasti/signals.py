"""
Signals de la aplicación reservas_StevenInsuasti.
- Crea automáticamente los grupos de roles al ejecutar las migraciones.
- Carga los usuarios iniciales desde el fixture usuarios_iniciales.json.
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


@receiver(post_migrate)
def cargar_usuarios_iniciales(sender, **kwargs):
    """
    Carga el fixture de usuarios iniciales automáticamente
    después de las migraciones, solo si aún no existen.

    Usuarios creados:
    - admin_reservas / Admin1234!  → Administrador (superuser)
    - docente1       / Docente1234! → Docente
    - docente2       / Docente1234! → Docente
    """
    if sender.name != 'reservas_StevenInsuasti':
        return

    from django.contrib.auth.models import User
    # Solo carga si no existe ninguno de los usuarios iniciales
    if User.objects.filter(username='admin_reservas').exists():
        return

    from django.core.management import call_command
    import os

    fixture_path = os.path.join(
        os.path.dirname(__file__),
        'fixtures',
        'usuarios_iniciales.json'
    )

    if os.path.exists(fixture_path):
        call_command('loaddata', fixture_path, verbosity=0)
