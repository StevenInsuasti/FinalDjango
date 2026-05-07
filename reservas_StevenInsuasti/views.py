from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import ReservaForm
from .mixins import (
    AdminRequiredMixin,
    DocenteOwnerPendienteMixin,
    DocenteRequiredMixin,
    ReservaVisibleMixin,
)
from .models import Reserva


class AppLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True


class AppLogoutView(LogoutView):
    next_page = reverse_lazy('login')


class ReservaListView(LoginRequiredMixin, ReservaVisibleMixin, ListView):
    model = Reserva
    template_name = 'reservas/reserva_list.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('usuario')

        if self.request.user.groups.filter(name='Administrador').exists():
            base_queryset = queryset
        else:
            base_queryset = queryset.filter(usuario=self.request.user)

        fecha = self.request.GET.get('fecha')
        laboratorio = self.request.GET.get('laboratorio')
        estado = self.request.GET.get('estado')

        if fecha:
            base_queryset = base_queryset.filter(fecha=fecha)
        if laboratorio:
            base_queryset = base_queryset.filter(
                laboratorio__icontains=laboratorio.strip()
            )
        if estado:
            base_queryset = base_queryset.filter(estado=estado)
        return base_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Reserva.ESTADO_CHOICES
        context['es_admin'] = self.request.user.groups.filter(
            name='Administrador'
        ).exists()
        context['es_docente'] = self.request.user.groups.filter(
            name='Docente'
        ).exists()
        return context


class ReservaCreateView(
    LoginRequiredMixin,
    DocenteRequiredMixin,
    CreateView,
):
    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/reserva_form.html'
    success_url = reverse_lazy('reservas:lista')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        form.instance.estado = Reserva.ESTADO_PENDIENTE
        messages.success(self.request, 'Reserva creada correctamente.')
        return super().form_valid(form)


class ReservaUpdateView(
    LoginRequiredMixin,
    DocenteOwnerPendienteMixin,
    UpdateView,
):
    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/reserva_form.html'
    success_url = reverse_lazy('reservas:lista')

    def form_valid(self, form):
        messages.success(self.request, 'Reserva actualizada correctamente.')
        return super().form_valid(form)


class ReservaDeleteView(
    LoginRequiredMixin,
    DocenteOwnerPendienteMixin,
    DeleteView,
):
    model = Reserva
    template_name = 'reservas/reserva_confirm_delete.html'
    success_url = reverse_lazy('reservas:lista')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Reserva eliminada correctamente.')
        return super().delete(request, *args, **kwargs)


class CambiarEstadoReservaView(
    LoginRequiredMixin,
    AdminRequiredMixin,
    View,
):
    nuevo_estado = None
    mensaje = ''

    def post(self, request, *args, **kwargs):
        reserva = Reserva.objects.filter(pk=kwargs['pk']).first()
        if not reserva:
            messages.error(request, 'La reserva no existe.')
            return HttpResponseRedirect(reverse_lazy('reservas:lista'))

        if reserva.estado != Reserva.ESTADO_PENDIENTE:
            messages.error(
                request,
                'Solo se pueden cambiar reservas en estado pendiente.',
            )
            return HttpResponseRedirect(reverse_lazy('reservas:lista'))

        reserva.estado = self.nuevo_estado
        reserva.save()
        messages.success(request, self.mensaje)
        return HttpResponseRedirect(reverse_lazy('reservas:lista'))


class AprobarReservaView(CambiarEstadoReservaView):
    nuevo_estado = Reserva.ESTADO_APROBADA
    mensaje = 'Reserva aprobada correctamente.'


class RechazarReservaView(CambiarEstadoReservaView):
    nuevo_estado = Reserva.ESTADO_RECHAZADA
    mensaje = 'Reserva rechazada correctamente.'
