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

    # --- Barberos (admin) ---
    path('barberos/',         views.barberos_view,        name='barberos'),

    # --- Citas ---
    path('citas/agendar/',    views.agendar_cita_view,    name='agendar_cita'),

    # -----------------------------------------------------------------------
    # MÓDULO ADMINISTRADOR
    # -----------------------------------------------------------------------

    # Servicios
    path('admin/servicios/',                  views.servicios_view,      name='servicios'),
    path('admin/servicios/crear/',            views.servicio_crear,      name='servicio_crear'),
    path('admin/servicios/<int:pk>/editar/',  views.servicio_editar,     name='servicio_editar'),
    path('admin/servicios/<int:pk>/toggle/',  views.servicio_toggle,     name='servicio_toggle'),
    path('admin/servicios/<int:pk>/eliminar/',views.servicio_eliminar,   name='servicio_eliminar'),

    # Citas admin
    path('admin/citas/',                      views.citas_admin_view,    name='citas_admin'),
    path('admin/citas/<int:pk>/estado/',      views.cita_cambiar_estado, name='cita_cambiar_estado'),

    # Horarios
    path('admin/horarios/',                   views.horarios_view,       name='horarios'),
    path('admin/horarios/crear/',             views.horario_crear,       name='horario_crear'),
    path('admin/horarios/<int:pk>/editar/',   views.horario_editar,      name='horario_editar'),
    path('admin/horarios/<int:pk>/eliminar/', views.horario_eliminar,    name='horario_eliminar'),

    # Reportes
    path('admin/reportes/',                   views.reportes_view,       name='reportes'),

    # Configuración
    path('admin/configuracion/',              views.configuracion_view,  name='configuracion'),
]
