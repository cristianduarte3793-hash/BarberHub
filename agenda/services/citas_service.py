"""
Servicio de Citas - BarberHub.

Contiene la lógica de negocio relacionada con las citas:
- Validaciones de disponibilidad
- Verificación de solapamientos
- Cálculo de horarios disponibles
"""

from datetime import datetime, timedelta
from django.db.models import Q
from ..models import Cita, Horario, Barbero, Servicio


class CitasService:
    """
    Servicio para gestión de citas.
    """

    @staticmethod
    def is_time_slot_available(barbero, fecha, hora_inicio, hora_fin, cita_id=None):
        """
        Verifica si un slot de tiempo está disponible para un barbero.
        
        Args:
            barbero: Instancia de Barbero
            fecha: date - Fecha de la cita
            hora_inicio: time - Hora de inicio
            hora_fin: time - Hora de fin
            cita_id: int (opcional) - ID de cita a excluir (para edición)
            
        Returns:
            bool - True si está disponible, False si hay solapamiento
        """
        # Buscar citas que se solapen con el horario propuesto
        query = Cita.objects.filter(
            barbero=barbero,
            fecha=fecha,
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio
        ).exclude(estado='CANCELADA')
        
        # Excluir la cita actual si estamos editando
        if cita_id:
            query = query.exclude(pk=cita_id)
        
        return not query.exists()

    @staticmethod
    def get_available_slots(barbero, servicio, fecha):
        """
        Obtiene los slots disponibles para un barbero en una fecha.
        
        Args:
            barbero: Instancia de Barbero
            servicio: Instancia de Servicio
            fecha: date - Fecha a consultar
            
        Returns:
            list - Lista de strings con horarios disponibles (formato "HH:MM")
        """
        # Obtener horario del día
        dia_semana = fecha.weekday()
        horario = Horario.objects.filter(
            dia_semana=dia_semana,
            fecha_especifica__isnull=True,
            abierto=True
        ).first()
        
        if not horario:
            return []
        
        # Obtener citas ya ocupadas
        citas_ocupadas = Cita.objects.filter(
            barbero=barbero,
            fecha=fecha
        ).exclude(estado='CANCELADA').values_list('hora_inicio', 'hora_fin')
        
        # Generar slots cada 30 minutos
        slots = []
        cursor = datetime.combine(fecha, horario.hora_inicio)
        fin = datetime.combine(fecha, horario.hora_fin)
        duracion = timedelta(minutes=servicio.duracion)
        ahora = datetime.now()
        
        while cursor + duracion <= fin:
            hora_s = cursor.time()
            hora_e = (cursor + duracion).time()
            
            # Saltar slots pasados
            if fecha == ahora.date() and cursor <= ahora:
                cursor += timedelta(minutes=30)
                continue
            
            # Verificar solapamiento con citas existentes
            ocupado = any(
                hora_s < c_fin and hora_e > c_ini
                for c_ini, c_fin in citas_ocupadas
            )
            
            if not ocupado:
                slots.append(hora_s.strftime('%H:%M'))
            
            cursor += timedelta(minutes=30)
        
        return slots

    @staticmethod
    def calcular_hora_fin(hora_inicio, duracion_minutos):
        """
        Calcula la hora de fin basándose en la hora de inicio y duración.
        
        Args:
            hora_inicio: time - Hora de inicio
            duracion_minutos: int - Duración en minutos
            
        Returns:
            time - Hora de fin calculada
        """
        from datetime import date
        dt_inicio = datetime.combine(date.today(), hora_inicio)
        dt_fin = dt_inicio + timedelta(minutes=duracion_minutos)
        return dt_fin.time()

    @staticmethod
    def validar_cita(barbero_id, servicio_id, fecha, hora_inicio):
        """
        Valida todos los aspectos de una cita antes de crearla.
        
        Args:
            barbero_id: int - ID del barbero
            servicio_id: int - ID del servicio
            fecha: date - Fecha de la cita
            hora_inicio: time - Hora de inicio
            
        Returns:
            tuple - (es_valido: bool, errores: list)
        """
        errores = []
        
        # Validar que el barbero existe y está activo
        try:
            barbero = Barbero.objects.get(pk=barbero_id, estado='ACTIVO')
        except Barbero.DoesNotExist:
            errores.append('El barbero seleccionado no está disponible.')
            return False, errores
        
        # Validar que el servicio existe y está activo
        try:
            servicio = Servicio.objects.get(pk=servicio_id, activo=True)
        except Servicio.DoesNotExist:
            errores.append('El servicio seleccionado no está disponible.')
            return False, errores
        
        # Validar que el barbero ofrece ese servicio
        if not barbero.servicios.filter(pk=servicio_id).exists():
            errores.append('El barbero no ofrece ese servicio.')
        
        # Validar que la fecha no sea en el pasado
        from django.utils import timezone
        if fecha < timezone.localdate():
            errores.append('No puedes agendar citas en fechas pasadas.')
        
        # Calcular hora de fin
        hora_fin = CitasService.calcular_hora_fin(hora_inicio, servicio.duracion)
        
        # Validar disponibilidad del slot
        if not CitasService.is_time_slot_available(barbero, fecha, hora_inicio, hora_fin):
            errores.append('El horario seleccionado ya está ocupado.')
        
        return len(errores) == 0, errores
