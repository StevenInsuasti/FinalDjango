"""
URLs de la aplicación reservas_StevenInsuasti.
CRUD completo de reservas usando vistas basadas en clases (CBV).
"""

from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    # Lista de reservas (con filtros opcionales por fecha y laboratorio)
    path('', views.ReservaListView.as_view(), name='lista'),

    # Crear nueva reserva
    path('crear/', views.ReservaCreateView.as_view(), name='crear'),

    # Editar reserva existente (solo si estado == pendiente)
    path('<int:pk>/editar/', views.ReservaUpdateView.as_view(), name='editar'),

    # Eliminar reserva (solo si estado == pendiente)
    path('<int:pk>/eliminar/', views.ReservaDeleteView.as_view(), name='eliminar'),
]
