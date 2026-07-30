"""
URLs principales del proyecto BarberHub.
Todas las rutas de la app se definen en agenda/urls.py
y se incluyen aquí con include().
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel admin de Django (lo dejamos por si acaso, pero no lo usaremos en el frontend)
    path('admin/', admin.site.urls),
    # Todas las URLs de nuestra app
    path('', include('agenda.urls')),
]

# Servir archivos media en desarrollo (fotos, logos, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
