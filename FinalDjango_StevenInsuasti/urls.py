"""
URLs principales del proyecto FinalDjango_StevenInsuasti.
Aquí se incluyen las rutas de cada aplicación.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from reservas_StevenInsuasti.views import AppLoginView, AppLogoutView

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),

    # URLs de autenticación de la aplicación
    path('auth/login/', AppLoginView.as_view(), name='login'),
    path('auth/logout/', AppLogoutView.as_view(), name='logout'),

    # URLs de la aplicación de reservas
    path('reservas/', include('reservas_StevenInsuasti.urls')),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
