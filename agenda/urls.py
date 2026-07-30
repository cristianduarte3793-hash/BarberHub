"""
URLs de la app agenda (BarberHub).
"""

from django.urls import path
from . import views

urlpatterns = [
    # --- Raíz → landing page ---
    path('', views.landing_view, name='home'),

    # --- Autenticación ---
    path('login/',            views.login_view,           name='login'),
    path('logout/',           views.logout_view,          name='logout'),
    path('registro/',         views.registro_view,        name='registro'),

    # --- Dashboard ---
    path('dashboard/',        views.dashboard_view,       name='dashboard'),

    # --- Perfil ---
    path('perfil/',           views.perfil_view,          name='perfil'),
    path('perfil/password/',  views.cambiar_password_view, name='cambiar_password'),

    # --- Módulos ---
    path('barberos/',         views.barberos_view,        name='barberos'),
    path('citas/agendar/',    views.agendar_cita_view,    name='agendar_cita'),
]
