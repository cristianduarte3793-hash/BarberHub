"""
URLs de la app agenda (BarberHub).
"""

from django.urls import path
from . import views  # Importa desde el módulo views/ restructurado

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
    path('barberos/',                             views.barberos_view,          name='barberos'),
    path('admin/barberos/crear/',                 views.barbero_crear_view,     name='barbero_crear'),
    path('admin/barberos/<int:pk>/editar/',        views.barbero_editar_view,    name='barbero_editar'),
    path('admin/barberos/<int:pk>/eliminar/',      views.barbero_eliminar_view,  name='barbero_eliminar'),
    path('admin/barberos/<int:pk>/toggle/',        views.barbero_toggle_estado,  name='barbero_toggle'),

    # --- Citas ---
    path('citas/agendar/',    views.agendar_cita_view,       name='agendar_cita'),
    path('citas/',            views.mis_citas_view,          name='mis_citas'),
    path('citas/<int:pk>/cancelar/', views.cancelar_cita_view, name='cancelar_cita'),
    path('citas/slots/',      views.slots_disponibles_view,  name='slots_disponibles'),

    # -----------------------------------------------------------------------
    # MÓDULO ADMINISTRADOR
    # -----------------------------------------------------------------------

    # Comprobante / recibo de cita — usa código de reserva, no PK interno
    path('citas/<str:codigo>/comprobante/',        views.comprobante_view,          name='comprobante_cita'),

    # Validación de comprobante (Admin)
    path('admin/validar/',                        views.validar_comprobante_view,  name='validar_comprobante'),

    # Clientes
    path('admin/clientes/',                       views.clientes_view,       name='clientes'),
    path('admin/clientes/<int:pk>/toggle/',        views.cliente_toggle,      name='cliente_toggle'),
    path('admin/clientes/<int:pk>/',               views.cliente_detalle,     name='cliente_detalle'),

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

    # -----------------------------------------------------------------------
    # MÓDULO BARBERO
    # -----------------------------------------------------------------------
    path('barbero/',                              views.barbero_dashboard,     name='barbero_dashboard'),
    path('barbero/agenda/',                       views.barbero_agenda,        name='barbero_agenda'),
    path('barbero/agenda/<int:pk>/',              views.barbero_cita_detalle,  name='barbero_cita_detalle'),
    path('barbero/agenda/<int:pk>/accion/',       views.barbero_cita_accion,   name='barbero_cita_accion'),
    path('barbero/historial/',                    views.barbero_historial,     name='barbero_historial'),
    path('barbero/disponibilidad/',               views.barbero_disponibilidad,name='barbero_disponibilidad'),
    path('barbero/estado/',                       views.barbero_cambiar_estado,name='barbero_cambiar_estado'),
    path('barbero/perfil/',                       views.barbero_perfil,        name='barbero_perfil'),
]
