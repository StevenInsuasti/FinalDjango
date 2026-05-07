from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def crear_roles_base(sender, **kwargs):
    if sender.name != 'reservas_StevenInsuasti':
        return

    Group.objects.get_or_create(name='Docente')
    Group.objects.get_or_create(name='Administrador')
