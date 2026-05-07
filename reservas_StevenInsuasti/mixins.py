from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import Reserva


class GroupRequiredMixin(UserPassesTestMixin):
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
    required_group = 'Docente'


class AdminRequiredMixin(GroupRequiredMixin):
    required_group = 'Administrador'


class ReservaVisibleMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        return self.request.user.groups.filter(
            name__in=['Docente', 'Administrador']
        ).exists() or self.request.user.is_superuser

    def handle_no_permission(self):
        raise PermissionDenied('Tu usuario no tiene rol asignado para reservas.')


class DocenteOwnerPendienteMixin(UserPassesTestMixin):
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if not self.request.user.groups.filter(name='Docente').exists():
            return False
        reserva = get_object_or_404(Reserva, pk=self.kwargs.get('pk'))
        return reserva.usuario_id == self.request.user.id and reserva.es_pendiente

    def handle_no_permission(self):
        raise PermissionDenied(
            'Solo puedes modificar o eliminar tus reservas pendientes.'
        )
