"""
Modelos de BarberHub - Estructura Modularizada.

Este archivo importa todos los modelos de los submódulos para mantener
la compatibilidad y facilitar los imports desde otras partes del proyecto.
"""

# Modelos de usuarios
from .usuarios import PerfilUsuario

# Modelos de barberos y servicios
from .barberos import Barbero, Servicio

# Modelos de citas
from .citas import Cita, Calificacion, Horario

# Modelos de notificaciones
from .notificaciones import Notificacion

# Modelos de configuración
from .configuracion import ConfiguracionBarberia


__all__ = [
    # Usuarios
    'PerfilUsuario',
    # Barberos y servicios
    'Barbero',
    'Servicio',
    # Citas
    'Cita',
    'Calificacion',
    'Horario',
    # Notificaciones
    'Notificacion',
    # Configuración
    'ConfiguracionBarberia',
]
