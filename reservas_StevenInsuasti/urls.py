"""
URLs de la aplicación reservas_StevenInsuasti.
Preparadas para recibir las vistas basadas en clases (CBV)
que serán implementadas por los demás integrantes del equipo.
"""

from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('', views.ReservaListView.as_view(), name='lista'),
    path('crear/', views.ReservaCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.ReservaUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.ReservaDeleteView.as_view(), name='eliminar'),
    path('<int:pk>/aprobar/', views.AprobarReservaView.as_view(), name='aprobar'),
    path('<int:pk>/rechazar/', views.RechazarReservaView.as_view(), name='rechazar'),
]
