"""
Servicio de Horarios - BarberHub.

Contiene la lógica de negocio relacionada con horarios:
- Verificación de días laborables
- Validación de horarios especiales
"""

from ..models import Horario


class HorariosService:
    """
    Servicio para gestión de horarios.
    """

    @staticmethod
    def get_dias_abiertos():
        """
        Obtiene los días de la semana en que la barbería está abierta.
        
        Returns:
            list - Lista de números de días (0=Lunes, 6=Domingo)
        """
        return list(
            Horario.objects.filter(
                abierto=True,
                fecha_especifica__isnull=True,
                dia_semana__isnull=False
            ).values_list('dia_semana', flat=True).distinct()
        )

    @staticmethod
    def is_dia_disponible(fecha):
        """
        Verifica si una fecha específica está disponible.
        
        Primero revisa si hay un horario especial para esa fecha.
        Si no, revisa el horario semanal del día.
        
        Args:
            fecha: date - Fecha a verificar
            
        Returns:
            bool - True si está disponible, False si está bloqueado
        """
        # Verificar si hay un horario especial para esta fecha
        horario_especial = Horario.objects.filter(
            fecha_especifica=fecha
        ).first()
        
        if horario_especial:
            return horario_especial.abierto
        
        # Si no hay horario especial, verificar el horario semanal
        dia_semana = fecha.weekday()
        horario_semanal = Horario.objects.filter(
            dia_semana=dia_semana,
            fecha_especifica__isnull=True,
            abierto=True
        ).exists()
        
        return horario_semanal

    @staticmethod
    def get_horario_dia(fecha):
        """
        Obtiene el horario de atención para una fecha específica.
        
        Args:
            fecha: date - Fecha a consultar
            
        Returns:
            Horario o None - Instancia de Horario o None si no hay atención
        """
        # Primero buscar horario especial
        horario = Horario.objects.filter(
            fecha_especifica=fecha
        ).first()
        
        if horario:
            return horario if horario.abierto else None
        
        # Si no, buscar horario semanal
        dia_semana = fecha.weekday()
        return Horario.objects.filter(
            dia_semana=dia_semana,
            fecha_especifica__isnull=True,
            abierto=True
        ).first()
