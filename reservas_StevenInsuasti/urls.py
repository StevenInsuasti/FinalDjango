"""
URLs de la aplicación reservas_StevenInsuasti.
CRUD completo + autenticación + aprobar/rechazar + dashboard + exportación CSV.
"""

from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    # ── Listado principal con filtros ──
    path('', views.ReservaListView.as_view(), name='lista'),

    # ── CRUD de reservas ──
    path('crear/', views.ReservaCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.ReservaUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.ReservaDeleteView.as_view(), name='eliminar'),

    # ── Acciones de administrador ──
    path('<int:pk>/aprobar/', views.AprobarReservaView.as_view(), name='aprobar'),
    path('<int:pk>/rechazar/', views.RechazarReservaView.as_view(), name='rechazar'),

    # ── Dashboard de estadísticas ──
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # ── Exportación CSV ──
    path('exportar-csv/', views.ExportarReservasCSVView.as_view(), name='exportar_csv'),
]
