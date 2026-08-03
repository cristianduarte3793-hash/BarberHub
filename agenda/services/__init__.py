"""
Capa de Servicios - BarberHub.

Esta capa contiene la lógica de negocio del sistema.
Las vistas (controladores) llaman a estos servicios en lugar de
contener lógica compleja directamente.

Patrón Service Layer:
- Separa la lógica de negocio de los controladores
- Facilita testing y reutilización
- Hace el código más mantenible
"""

from .citas_service import CitasService
from .horarios_service import HorariosService

__all__ = [
    'CitasService',
    'HorariosService',
]
