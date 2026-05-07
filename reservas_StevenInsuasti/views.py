"""
Vistas basadas en clases (CBV) para el CRUD de reservas.
Aplicación: reservas_StevenInsuasti

Integra:
- feature/crud-reservas   : CRUD completo con filtros, dashboard y exportación CSV
- feature/validaciones-filtros : Filtros avanzados y validaciones de horario
- feature/auth-roles      : Autenticación, roles (Docente/Administrador) y mixins
"""

import csv

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView, DeleteView, ListView, TemplateView, UpdateView
)

from .forms import ReservaFiltroForm, ReservaForm
from .mixins import (
    AdminRequiredMixin,
    DocenteOwnerPendienteMixin,
    DocenteRequiredMixin,
    ReservaVisibleMixin,
)
from .models import Reserva


# ─────────────────────────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────────────────────────

class AppLoginView(LoginView):
    """Vista de login personalizada."""
    template_name = 'registration/login.html'
    redirect_authenticated_user = True


class AppLogoutView(LogoutView):
    """Vista de logout."""
    next_page = reverse_lazy('login')


# ─────────────────────────────────────────────────────────────
# LISTVIEW — Lista reservas con filtros por fecha y laboratorio
# ─────────────────────────────────────────────────────────────

class ReservaListView(LoginRequiredMixin, ReservaVisibleMixin, ListView):
    """
    Muestra el listado de reservas con filtros de búsqueda.

    - Docente: solo ve sus propias reservas.
    - Administrador: ve todas las reservas.
    - Filtro por fecha, laboratorio y estado.
    """

    model = Reserva
    template_name = 'reservas/reserva_list.html'
    context_object_name = 'reservas'
    paginate_by = 10

    def get_queryset(self):
        qs = Reserva.objects.select_related('usuario').order_by('-fecha', 'hora_inicio')

        # Administrador ve todo; docente solo sus reservas
        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        if not es_admin:
            qs = qs.filter(usuario=self.request.user)

        # Validar y limpiar los parámetros GET con el formulario de filtros
        self.filtro_form = ReservaFiltroForm(self.request.GET)

        if self.filtro_form.is_valid():
            fecha = self.filtro_form.cleaned_data.get('fecha')
            laboratorio = self.filtro_form.cleaned_data.get('laboratorio')

            if fecha:
                qs = qs.filter(fecha=fecha)
            if laboratorio:
                qs = qs.filter(laboratorio__icontains=laboratorio)

        # Filtro por estado (viene directo del GET)
        estado = self.request.GET.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtro_form'] = self.filtro_form
        ctx['filtro_fecha'] = self.request.GET.get('fecha', '')
        ctx['filtro_laboratorio'] = self.request.GET.get('laboratorio', '')
        ctx['estados'] = Reserva.ESTADO_CHOICES

        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        ctx['es_admin'] = es_admin
        ctx['es_docente'] = self.request.user.groups.filter(name='Docente').exists()

        # Lista de laboratorios únicos para sugerencias en el filtro
        base_qs = Reserva.objects if es_admin else Reserva.objects.filter(usuario=self.request.user)
        ctx['laboratorios_disponibles'] = (
            base_qs.values_list('laboratorio', flat=True)
            .distinct()
            .order_by('laboratorio')
        )
        return ctx


# ─────────────────────────────────────────────────────────────
# CREATEVIEW — Crea una nueva reserva
# ─────────────────────────────────────────────────────────────

class ReservaCreateView(LoginRequiredMixin, DocenteRequiredMixin, CreateView):
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
        form.instance.usuario = self.request.user
        form.instance.estado = Reserva.ESTADO_PENDIENTE
        messages.success(
            self.request,
            '✅ Reserva creada exitosamente. Queda pendiente de aprobación.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ No se pudo crear la reserva. Revisa los errores indicados.'
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva Reserva'
        ctx['boton'] = 'Crear Reserva'
        return ctx


# ─────────────────────────────────────────────────────────────
# UPDATEVIEW — Edita una reserva existente
# ─────────────────────────────────────────────────────────────

class ReservaUpdateView(LoginRequiredMixin, DocenteOwnerPendienteMixin, UpdateView):
    """
    Permite editar una reserva.
    Solo si estado == 'pendiente' y el docente es el dueño.
    """

    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/reserva_form.html'
    success_url = reverse_lazy('reservas:lista')

    def form_valid(self, form):
        messages.success(self.request, '✅ Reserva actualizada correctamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            '❌ No se pudo actualizar la reserva. Revisa los errores indicados.'
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar Reserva'
        ctx['boton'] = 'Guardar Cambios'
        return ctx


# ─────────────────────────────────────────────────────────────
# DELETEVIEW — Elimina una reserva
# ─────────────────────────────────────────────────────────────

class ReservaDeleteView(LoginRequiredMixin, DocenteOwnerPendienteMixin, DeleteView):
    """
    Permite eliminar una reserva pendiente propia del docente.
    """

    model = Reserva
    template_name = 'reservas/reserva_confirm_delete.html'
    success_url = reverse_lazy('reservas:lista')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, '🗑 Reserva eliminada correctamente.')
        return super().delete(request, *args, **kwargs)


# ─────────────────────────────────────────────────────────────
# CAMBIAR ESTADO — Aprobar / Rechazar (solo Administrador)
# ─────────────────────────────────────────────────────────────

class CambiarEstadoReservaView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    Vista base para cambiar el estado de una reserva.
    Solo accesible por usuarios con rol Administrador.
    """
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
                '⛔ Solo se pueden cambiar reservas en estado Pendiente.'
            )
            return HttpResponseRedirect(reverse_lazy('reservas:lista'))

        reserva.estado = self.nuevo_estado
        reserva.save()
        messages.success(request, self.mensaje)
        return HttpResponseRedirect(reverse_lazy('reservas:lista'))


class AprobarReservaView(CambiarEstadoReservaView):
    nuevo_estado = Reserva.ESTADO_APROBADA
    mensaje = '✅ Reserva aprobada correctamente.'


class RechazarReservaView(CambiarEstadoReservaView):
    nuevo_estado = Reserva.ESTADO_RECHAZADA
    mensaje = '❌ Reserva rechazada correctamente.'


# ─────────────────────────────────────────────────────────────
# DASHBOARD — Estadísticas de uso
# ─────────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard con estadísticas de reservas.
    Administrador ve todo; docente solo sus propias reservas.
    """

    template_name = 'reservas/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        es_admin = self.request.user.groups.filter(name='Administrador').exists()
        reservas = Reserva.objects.all() if es_admin else Reserva.objects.filter(
            usuario=self.request.user
        )

        ctx['total_reservas'] = reservas.count()
        ctx['reservas_aprobadas'] = reservas.filter(estado=Reserva.ESTADO_APROBADA).count()
        ctx['reservas_rechazadas'] = reservas.filter(estado=Reserva.ESTADO_RECHAZADA).count()
        ctx['reservas_pendientes'] = reservas.filter(estado=Reserva.ESTADO_PENDIENTE).count()

        ctx['reservas_por_laboratorio'] = (
            reservas.values('laboratorio')
            .annotate(total=Count('id'))
            .order_by('-total')
        )

        if es_admin:
            ctx['reservas_por_usuario'] = (
                reservas.values(
                    'usuario__username',
                    'usuario__first_name',
                    'usuario__last_name'
                )
                .annotate(total=Count('id'))
                .order_by('-total')[:10]
            )

        ctx['ultimas_reservas'] = reservas.select_related('usuario').order_by('-fecha_creacion')[:5]
        return ctx


# ─────────────────────────────────────────────────────────────
# EXPORTAR CSV
# ─────────────────────────────────────────────────────────────

class ExportarReservasCSVView(LoginRequiredMixin, View):
    """
    Exporta las reservas a un archivo CSV.
    Docente exporta solo las suyas; Administrador exporta todas.
    """

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="reservas.csv"'
        response.write('\ufeff')  # BOM para Excel

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Usuario', 'Nombre Completo', 'Laboratorio',
            'Fecha', 'Hora Inicio', 'Hora Fin', 'Estado', 'Motivo', 'Fecha Creación'
        ])

        es_admin = request.user.groups.filter(name='Administrador').exists()
        reservas = Reserva.objects.all() if es_admin else Reserva.objects.filter(
            usuario=request.user
        )

        fecha = request.GET.get('fecha')
        laboratorio = request.GET.get('laboratorio')
        if fecha:
            reservas = reservas.filter(fecha=fecha)
        if laboratorio:
            reservas = reservas.filter(laboratorio__icontains=laboratorio)

        reservas = reservas.select_related('usuario').order_by('-fecha', 'hora_inicio')

        for r in reservas:
            writer.writerow([
                r.id,
                r.usuario.username,
                r.usuario.get_full_name() or '-',
                r.laboratorio,
                r.fecha.strftime('%Y-%m-%d'),
                r.hora_inicio.strftime('%H:%M'),
                r.hora_fin.strftime('%H:%M'),
                r.get_estado_display(),
                r.motivo,
                r.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            ])

        return response
