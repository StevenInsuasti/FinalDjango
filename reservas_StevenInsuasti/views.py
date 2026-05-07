"""
Vistas basadas en clases (CBV) para el CRUD de reservas.
Aplicación: reservas_StevenInsuasti

Mixins utilizados:
- LoginRequiredMixin: exige que el usuario esté autenticado.
- UserPassesTestMixin: permite definir una condición personalizada de acceso.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Reserva
from .forms import ReservaForm


# ─────────────────────────────────────────────────────────────
# LISTVIEW — Lista todas las reservas del usuario autenticado.
# Los administradores (is_staff) ven todas las reservas.
# ─────────────────────────────────────────────────────────────
class ReservaListView(LoginRequiredMixin, ListView):
    """
    Muestra el listado de reservas.

    - Docente: solo ve sus propias reservas.
    - Administrador (is_staff): ve todas las reservas.
    - Soporta filtros por fecha y laboratorio via GET params.
    """

    model = Reserva
    template_name = 'reservas/reserva_list.html'
    context_object_name = 'reservas'
    paginate_by = 10

    def get_queryset(self):
        """Filtra reservas según el rol del usuario y parámetros GET."""
        qs = Reserva.objects.select_related('usuario')

        # Administrador ve todo; docente solo sus reservas
        if not self.request.user.is_staff:
            qs = qs.filter(usuario=self.request.user)

        # Filtro por fecha
        fecha = self.request.GET.get('fecha')
        if fecha:
            qs = qs.filter(fecha=fecha)

        # Filtro por laboratorio
        laboratorio = self.request.GET.get('laboratorio')
        if laboratorio:
            qs = qs.filter(laboratorio__icontains=laboratorio)

        return qs

    def get_context_data(self, **kwargs):
        """Agrega los filtros activos al contexto para mostrarlos en el template."""
        ctx = super().get_context_data(**kwargs)
        ctx['filtro_fecha'] = self.request.GET.get('fecha', '')
        ctx['filtro_laboratorio'] = self.request.GET.get('laboratorio', '')
        return ctx


# ─────────────────────────────────────────────────────────────
# CREATEVIEW — Crea una nueva reserva.
# Solo usuarios autenticados pueden crear reservas.
# ─────────────────────────────────────────────────────────────
class ReservaCreateView(LoginRequiredMixin, CreateView):
    """
    Permite a un docente autenticado crear una nueva reserva.

    El campo 'usuario' se asigna automáticamente al usuario actual.
    El estado inicial siempre es 'pendiente'.
    """

    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/reserva_form.html'
    success_url = reverse_lazy('reservas:lista')

    def form_valid(self, form):
        """Asigna el usuario actual y estado pendiente antes de guardar."""
        form.instance.usuario = self.request.user
        form.instance.estado = Reserva.ESTADO_PENDIENTE
        messages.success(self.request, 'Reserva creada exitosamente. Queda pendiente de aprobación.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Reserva'
        ctx['boton'] = 'Crear Reserva'
        return ctx


# ─────────────────────────────────────────────────────────────
# UPDATEVIEW — Edita una reserva existente.
# Solo se permite editar si el estado es 'pendiente'.
# El docente solo puede editar sus propias reservas.
# ─────────────────────────────────────────────────────────────
class ReservaUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Permite editar una reserva.

    Restricciones:
    - Solo si estado == 'pendiente'.
    - El docente solo puede editar sus propias reservas.
    - El administrador puede editar cualquier reserva pendiente.
    """

    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/reserva_form.html'
    success_url = reverse_lazy('reservas:lista')

    def test_func(self):
        """
        UserPassesTestMixin: define quién puede acceder.
        Retorna True si el usuario tiene permiso de editar.
        """
        reserva = self.get_object()
        # Solo se puede editar si está pendiente
        if not reserva.es_pendiente:
            return False
        # Administrador puede editar cualquier reserva pendiente
        if self.request.user.is_staff:
            return True
        # Docente solo puede editar sus propias reservas
        return reserva.usuario == self.request.user

    def handle_no_permission(self):
        """Mensaje de error cuando no se tiene permiso."""
        messages.error(
            self.request,
            'No puedes editar esta reserva. Solo se pueden editar reservas en estado Pendiente.'
        )
        return super().handle_no_permission()

    def form_valid(self, form):
        messages.success(self.request, 'Reserva actualizada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Reserva'
        ctx['boton'] = 'Guardar Cambios'
        return ctx


# ─────────────────────────────────────────────────────────────
# DELETEVIEW — Elimina una reserva.
# Solo se permite eliminar si el estado es 'pendiente'.
# El docente solo puede eliminar sus propias reservas.
# ─────────────────────────────────────────────────────────────
class ReservaDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Permite eliminar una reserva.

    Restricciones:
    - Solo si estado == 'pendiente'.
    - El docente solo puede eliminar sus propias reservas.
    - El administrador puede eliminar cualquier reserva pendiente.
    """

    model = Reserva
    template_name = 'reservas/reserva_confirm_delete.html'
    success_url = reverse_lazy('reservas:lista')

    def test_func(self):
        """
        UserPassesTestMixin: define quién puede acceder.
        Retorna True si el usuario tiene permiso de eliminar.
        """
        reserva = self.get_object()
        # Solo se puede eliminar si está pendiente
        if not reserva.es_pendiente:
            return False
        # Administrador puede eliminar cualquier reserva pendiente
        if self.request.user.is_staff:
            return True
        # Docente solo puede eliminar sus propias reservas
        return reserva.usuario == self.request.user

    def handle_no_permission(self):
        """Mensaje de error cuando no se tiene permiso."""
        messages.error(
            self.request,
            'No puedes eliminar esta reserva. Solo se pueden eliminar reservas en estado Pendiente.'
        )
        return super().handle_no_permission()

    def form_valid(self, form):
        messages.success(self.request, 'Reserva eliminada correctamente.')
        return super().form_valid(form)
