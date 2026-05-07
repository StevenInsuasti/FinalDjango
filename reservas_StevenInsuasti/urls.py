"""
URLs de la aplicación reservas_StevenInsuasti.
CRUD completo de reservas usando vistas basadas en clases (CBV).
Incluye dashboard de estadísticas y exportación CSV.
"""

from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    # Dashboard con estadísticas
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Lista de reservas (con filtros opcionales por fecha y laboratorio)
    path('', views.ReservaListView.as_view(), name='lista'),

    # Crear nueva reserva
    path('crear/', views.ReservaCreateView.as_view(), name='crear'),

    # Editar reserva existente (solo si estado == pendiente)
    path('<int:pk>/editar/', views.ReservaUpdateView.as_view(), name='editar'),

    # Eliminar reserva (solo si estado == pendiente)
    path('<int:pk>/eliminar/', views.ReservaDeleteView.as_view(), name='eliminar'),
    
    # Exportar reservas a CSV
    path('exportar-csv/', views.ExportarReservasCSVView.as_view(), name='exportar_csv'),
]
