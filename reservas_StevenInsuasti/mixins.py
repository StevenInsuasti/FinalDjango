"""
Mixins de control de acceso para la aplicación reservas_StevenInsuasti.
Implementa los roles: Docente y Administrador usando grupos de Django.
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Reserva


class GroupRequiredMixin(UserPassesTestMixin):
    """
    Mixin base que verifica que el usuario pertenezca a un grupo específico.
    Los superusuarios siempre tienen acceso.
    """
    required_group = None

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name=self.required_group).exists()

    def handle_no_permission(self):
        raise PermissionDenied('No tienes permisos para acceder a esta vista.')


class DocenteRequiredMixin(GroupRequiredMixin):
    """Solo usuarios del grupo 'Docente' pueden acceder."""
    required_group = 'Docente'


class AdminRequiredMixin(GroupRequiredMixin):
    """Solo usuarios del grupo 'Administrador' pueden acceder."""
    required_group = 'Administrador'


class ReservaVisibleMixin(UserPassesTestMixin):
    """
    Permite el acceso a usuarios con rol Docente o Administrador.
    Usado en vistas de listado.
    """

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(
            name__in=['Docente', 'Administrador']
        ).exists()

    def handle_no_permission(self):
        raise PermissionDenied('Tu usuario no tiene un rol asignado para el sistema de reservas.')


class DocenteOwnerPendienteMixin(UserPassesTestMixin):
    """
    Permite el acceso solo si:
    - El usuario es del grupo 'Docente'.
    - La reserva le pertenece.
    - La reserva está en estado 'pendiente'.
    """

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if not self.request.user.groups.filter(name='Docente').exists():
            return False
        reserva = get_object_or_404(Reserva, pk=self.kwargs.get('pk'))
        return reserva.usuario_id == self.request.user.id and reserva.es_pendiente

    def handle_no_permission(self):
        raise PermissionDenied(
            'Solo puedes modificar o eliminar tus propias reservas en estado Pendiente.'
        )
