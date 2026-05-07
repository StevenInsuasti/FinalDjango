"""
URLs de la aplicación reservas_StevenInsuasti.
Preparadas para recibir las vistas basadas en clases (CBV)
que serán implementadas por los demás integrantes del equipo.
"""

from django.urls import path

# Las vistas se importarán cuando sean implementadas
# from . import views

app_name = 'reservas'

urlpatterns = [
    # Las rutas serán añadidas por los integrantes responsables de las vistas:
    #
    # path('', views.ReservaListView.as_view(), name='lista'),
    # path('crear/', views.ReservaCreateView.as_view(), name='crear'),
    # path('<int:pk>/editar/', views.ReservaUpdateView.as_view(), name='editar'),
    # path('<int:pk>/eliminar/', views.ReservaDeleteView.as_view(), name='eliminar'),
    # path('<int:pk>/aprobar/', views.aprobar_reserva, name='aprobar'),
    # path('<int:pk>/rechazar/', views.rechazar_reserva, name='rechazar'),
    # path('exportar/csv/', views.exportar_csv, name='exportar_csv'),
]
