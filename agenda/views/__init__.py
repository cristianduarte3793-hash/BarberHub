"""
Módulo de vistas de BarberHub - Estructura modularizada.

Este archivo importa todas las vistas de los submódulos para mantener
la compatibilidad con urls.py sin necesidad de cambiar imports.
"""

# Vistas de autenticación
from .auth import (
    landing_view,
    login_view,
    logout_view,
    registro_view,
)

# Vistas comunes (dashboard general, perfil)
from .comunes import (
    dashboard_view,
    perfil_view,
    cambiar_password_view,
)

# Vistas de cliente
from .cliente import (
    agendar_cita_view,
    mis_citas_view,
    cancelar_cita_view,
    slots_disponibles_view,
    comprobante_view,
)

# Vistas de administrador
from .admin import (
    barberos_view,
    servicios_view,
    servicio_crear,
    servicio_editar,
    servicio_toggle,
    servicio_eliminar,
    citas_admin_view,
    cita_cambiar_estado,
    horarios_view,
    horario_crear,
    horario_editar,
    horario_eliminar,
    reportes_view,
    configuracion_view,
    clientes_view,
    cliente_toggle,
    cliente_detalle,
    validar_comprobante_view,
)

# Vistas de barbero
from .barbero import (
    barbero_dashboard,
    barbero_agenda,
    barbero_cita_detalle,
    barbero_cita_accion,
    barbero_cambiar_estado,
    barbero_historial,
    barbero_disponibilidad,
    barbero_perfil,
)

__all__ = [
    # Auth
    'landing_view',
    'login_view',
    'logout_view',
    'registro_view',
    # Comunes
    'dashboard_view',
    'perfil_view',
    'cambiar_password_view',
    # Cliente
    'agendar_cita_view',
    'mis_citas_view',
    'cancelar_cita_view',
    'slots_disponibles_view',
    # Admin
    'barberos_view',
    'servicios_view',
    'servicio_crear',
    'servicio_editar',
    'servicio_toggle',
    'servicio_eliminar',
    'citas_admin_view',
    'cita_cambiar_estado',
    'horarios_view',
    'horario_crear',
    'horario_editar',
    'horario_eliminar',
    'reportes_view',
    'configuracion_view',
    # Clientes
    'clientes_view',
    'cliente_toggle',
    'cliente_detalle',
    # Comprobante
    'comprobante_view',
    'validar_comprobante_view',
    # Barbero
    'barbero_dashboard',
    'barbero_agenda',
    'barbero_cita_detalle',
    'barbero_cita_accion',
    'barbero_cambiar_estado',
    'barbero_historial',
    'barbero_disponibilidad',
    'barbero_perfil',
]
