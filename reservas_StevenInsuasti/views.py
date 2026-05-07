"""
Vistas basadas en clases (CBV) para el CRUD de reservas.
Aplicación: reservas_StevenInsuasti

Mixins utilizados:
- LoginRequiredMixin: exige que el usuario esté autenticado.
- UserPassesTestMixin: permite definir una condición personalizada de acceso.
"""

import csv
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.http import HttpResponse
from django.db.models import Count, Q
from django.views import View

from .models import Reserva
from .forms import ReservaForm, ReservaFiltroForm


# ─────────────────────────────────────────────────────────────
# LISTVIEW — Lista reservas con filtros por fecha y laboratorio
# ─────────────────────────────────────────────────────────────
class ReservaListView(LoginRequiredMixin, ListView):
    """
    Muestra el listado de reservas con filtros de búsqueda.

    - Docente: solo ve sus propias reservas.
    - Administrador (is_staff): ve todas las reservas.
    - Filtro por fecha: coincidencia exacta con el campo 'fecha'.
    - Filtro por laboratorio: búsqueda parcial (icontains).
    """

    model = Reserva
    template_name = 'reservas/reserva_list.html'
    context_object_name = 'reservas'
    paginate_by = 10

    def get_queryset(self):
        """
        Construye el queryset aplicando:
        1. Restricción por rol (docente vs administrador).
        2. Filtro por fecha exacta si se proporcionó.
        3. Filtro por laboratorio (búsqueda parcial) si se proporcionó.
        """
        qs = Reserva.objects.select_related('usuario').order_by('-fecha', 'hora_inicio')

        # Administrador ve todo; docente solo sus reservas
        if not self.request.user.is_staff:
            qs = qs.filter(usuario=self.request.user)

        # Validar y limpiar los parámetros GET con el formulario de filtros
        self.filtro_form = ReservaFiltroForm(self.request.GET)

        if self.filtro_form.is_valid():
            fecha = self.filtro_form.cleaned_data.get('fecha')
            laboratorio = self.filtro_form.cleaned_data.get('laboratorio')

            # ── Filtro por fecha exacta ──
            # Usa el ORM: Reserva.objects.filter(fecha=fecha)
            if fecha:
                qs = qs.filter(fecha=fecha)

            # ── Filtro por laboratorio (parcial, sin importar mayúsculas) ──
            if laboratorio:
                qs = qs.filter(laboratorio__icontains=laboratorio)

        return qs

    def get_context_data(self, **kwargs):
        """
        Agrega al contexto:
        - filtro_form: el formulario de filtros con los valores actuales.
        - filtro_fecha / filtro_laboratorio: valores para mantener en paginación.
        - laboratorios_disponibles: lista de laboratorios únicos para el datalist.
        """
        ctx = super().get_context_data(**kwargs)
        ctx['filtro_form'] = self.filtro_form
        # Valores planos para construir URLs de paginación en el template
        ctx['filtro_fecha'] = self.request.GET.get('fecha', '')
        ctx['filtro_laboratorio'] = self.request.GET.get('laboratorio', '')
        # Lista de laboratorios únicos registrados (para sugerencias en el filtro)
        # El administrador ve todos; el docente solo los suyos
        if self.request.user.is_staff:
            ctx['laboratorios_disponibles'] = (
                Reserva.objects.values_list('laboratorio', flat=True)
                .distinct()
                .order_by('laboratorio')
            )
        else:
            ctx['laboratorios_disponibles'] = (
                Reserva.objects.filter(usuario=self.request.user)
                .values_list('laboratorio', flat=True)
                .distinct()
                .order_by('laboratorio')
            )
        return ctx


# ─────────────────────────────────────────────────────────────
# CREATEVIEW — Crea una nueva reserva
# ─────────────────────────────────────────────────────────────
class ReservaCreateView(LoginRequiredMixin, CreateView):
    """
    Permite a un docente autenticado crear una nueva reserva.

    El campo 'usuario' se asigna automáticamente al usuario actual.
    El estado inicial siempre es 'pendiente'.
    Las validaciones de conflicto se ejecutan en ReservaForm.clean().
    """

    model = Reserva
    form_class = ReservaForm
    template_name = 'reservas/reserva_form.html'
    success_url = reverse_lazy('reservas:lista')

    def form_valid(self, form):
        """Asigna el usuario actual y estado pendiente antes de guardar."""
        form.instance.usuario = self.request.user
        form.instance.estado = Reserva.ESTADO_PENDIENTE
        messages.success(
            self.request,
            '✅ Reserva creada exitosamente. Queda pendiente de aprobación.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """Muestra mensaje de error cuando el formulario no es válido."""
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
        reserva = self.get_object()
        if not reserva.es_pendiente:
            return False
        if self.request.user.is_staff:
            return True
        return reserva.usuario == self.request.user

    def handle_no_permission(self):
        messages.error(
            self.request,
            '⛔ No puedes editar esta reserva. '
            'Solo se pueden editar reservas en estado Pendiente.'
        )
        return super().handle_no_permission()

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
        reserva = self.get_object()
        if not reserva.es_pendiente:
            return False
        if self.request.user.is_staff:
            return True
        return reserva.usuario == self.request.user

    def handle_no_permission(self):
        messages.error(
            self.request,
            '⛔ No puedes eliminar esta reserva. '
            'Solo se pueden eliminar reservas en estado Pendiente.'
        )
        return super().handle_no_permission()

    def form_valid(self, form):
        messages.success(self.request, '🗑 Reserva eliminada correctamente.')
        return super().form_valid(form)


# ─────────────────────────────────────────────────────────────
# DASHBOARD — Vista de estadísticas y reportes
# ─────────────────────────────────────────────────────────────
class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard con estadísticas de reservas.
    
    Muestra:
    - Total de reservas
    - Reservas aprobadas
    - Reservas rechazadas
    - Reservas pendientes
    - Reservas por laboratorio
    - Reservas por usuario (solo para administradores)
    """
    
    template_name = 'reservas/dashboard.html'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Filtrar reservas según el rol del usuario
        if self.request.user.is_staff:
            # Administrador ve todas las reservas
            reservas = Reserva.objects.all()
        else:
            # Docente solo ve sus propias reservas
            reservas = Reserva.objects.filter(usuario=self.request.user)
        
        # ── Estadísticas generales ──
        ctx['total_reservas'] = reservas.count()
        ctx['reservas_aprobadas'] = reservas.filter(estado=Reserva.ESTADO_APROBADA).count()
        ctx['reservas_rechazadas'] = reservas.filter(estado=Reserva.ESTADO_RECHAZADA).count()
        ctx['reservas_pendientes'] = reservas.filter(estado=Reserva.ESTADO_PENDIENTE).count()
        
        # ── Reservas por laboratorio ──
        ctx['reservas_por_laboratorio'] = (
            reservas.values('laboratorio')
            .annotate(total=Count('id'))
            .order_by('-total')
        )
        
        # ── Reservas por estado y laboratorio (para gráficos) ──
        ctx['reservas_por_lab_estado'] = (
            reservas.values('laboratorio', 'estado')
            .annotate(total=Count('id'))
            .order_by('laboratorio', 'estado')
        )
        
        # ── Reservas por usuario (solo para administradores) ──
        if self.request.user.is_staff:
            ctx['reservas_por_usuario'] = (
                reservas.values('usuario__username', 'usuario__first_name', 'usuario__last_name')
                .annotate(total=Count('id'))
                .order_by('-total')[:10]  # Top 10 usuarios
            )
        
        # ── Últimas reservas ──
        ctx['ultimas_reservas'] = reservas.select_related('usuario').order_by('-fecha_creacion')[:5]
        
        return ctx


# ─────────────────────────────────────────────────────────────
# EXPORTAR CSV — Exporta reservas a formato CSV
# ─────────────────────────────────────────────────────────────
class ExportarReservasCSVView(LoginRequiredMixin, View):
    """
    Exporta las reservas a un archivo CSV.
    
    - Docente: exporta solo sus propias reservas.
    - Administrador: exporta todas las reservas.
    - Respeta los filtros de fecha y laboratorio si se proporcionan.
    """
    
    def get(self, request, *args, **kwargs):
        # Crear respuesta HTTP con tipo CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="reservas.csv"'
        
        # Agregar BOM para que Excel reconozca UTF-8
        response.write('\ufeff')
        
        # Crear escritor CSV
        writer = csv.writer(response)
        
        # Escribir encabezados
        writer.writerow([
            'ID',
            'Usuario',
            'Nombre Completo',
            'Laboratorio',
            'Fecha',
            'Hora Inicio',
            'Hora Fin',
            'Estado',
            'Motivo',
            'Fecha Creación'
        ])
        
        # Obtener reservas según el rol
        if request.user.is_staff:
            reservas = Reserva.objects.all()
        else:
            reservas = Reserva.objects.filter(usuario=request.user)
        
        # Aplicar filtros si existen
        fecha = request.GET.get('fecha')
        laboratorio = request.GET.get('laboratorio')
        
        if fecha:
            reservas = reservas.filter(fecha=fecha)
        
        if laboratorio:
            reservas = reservas.filter(laboratorio__icontains=laboratorio)
        
        # Ordenar por fecha descendente
        reservas = reservas.select_related('usuario').order_by('-fecha', 'hora_inicio')
        
        # Escribir datos
        for reserva in reservas:
            writer.writerow([
                reserva.id,
                reserva.usuario.username,
                reserva.usuario.get_full_name() or '-',
                reserva.laboratorio,
                reserva.fecha.strftime('%Y-%m-%d'),
                reserva.hora_inicio.strftime('%H:%M'),
                reserva.hora_fin.strftime('%H:%M'),
                reserva.get_estado_display(),
                reserva.motivo,
                reserva.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
