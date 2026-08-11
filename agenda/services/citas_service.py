"""
Servicio de Citas - BarberHub.

Toda la lógica de negocio de citas vive aquí.
Las vistas solo orquestan; este servicio valida y decide.
"""

import re
from datetime import datetime, time, timedelta, date as date_type

from django.utils import timezone

from ..models import Cita, Horario, Barbero, Servicio

# ── Constantes de negocio ────────────────────────────────────────────────────
MAX_DIAS_ANTICIPACION  = 60  # No se puede agendar a más de 60 días
MAX_CITAS_POR_DIA      = 2   # Máximo de citas activas por cliente en el mismo día
MIN_MIN_ANTICIPACION   = 30  # Mínimo 30 minutos de anticipación
PATRON_CODIGO         = re.compile(r'^BH-\d{6}$')  # Formato válido: BH-000001

# Bloqueo diario por almuerzo — ningún slot puede comenzar ni solaparse con esta franja
ALMUERZO_INICIO = time(12, 0)  # 12:00 PM
ALMUERZO_FIN    = time(14, 0)  # 2:00 PM


class CitasService:

    # ── Disponibilidad ───────────────────────────────────────────────────────

    @staticmethod
    def _solapa_almuerzo(hora_inicio, hora_fin):
        """
        Devuelve True si el slot [hora_inicio, hora_fin) se solapa con
        la franja de almuerzo [ALMUERZO_INICIO, ALMUERZO_FIN).
        Un slot solapa si empieza antes de que termine el almuerzo
        Y termina después de que empiece el almuerzo.
        """
        return hora_inicio < ALMUERZO_FIN and hora_fin > ALMUERZO_INICIO

    @staticmethod
    def is_time_slot_available(barbero, fecha, hora_inicio, hora_fin, cita_id=None):
        """
        Verifica si el barbero tiene ese slot libre.
        Excluye citas canceladas y, opcionalmente, la cita que se está editando.
        """
        query = Cita.objects.filter(
            barbero=barbero,
            fecha=fecha,
            hora_inicio__lt=hora_fin,
            hora_fin__gt=hora_inicio,
        ).exclude(estado='CANCELADA')

        if cita_id:
            query = query.exclude(pk=cita_id)

        return not query.exists()

    @staticmethod
    def calcular_hora_fin(hora_inicio, duracion_minutos):
        """Calcula la hora de fin sumando la duración a la hora de inicio."""
        dt_inicio = datetime.combine(date_type.today(), hora_inicio)
        return (dt_inicio + timedelta(minutes=duracion_minutos)).time()

    @staticmethod
    def get_available_slots(barbero, servicio, fecha):
        """
        Devuelve lista de strings 'HH:MM' con slots libres para ese barbero/día.
        Respeta el horario de la barbería y descuenta citas ya existentes.
        """
        from .horarios_service import HorariosService

        horario = HorariosService.get_horario_dia(fecha)
        if not horario:
            return []

        citas_ocupadas = list(
            Cita.objects.filter(barbero=barbero, fecha=fecha)
            .exclude(estado='CANCELADA')
            .values_list('hora_inicio', 'hora_fin')
        )

        slots  = []
        cursor = datetime.combine(fecha, horario.hora_inicio)
        fin    = datetime.combine(fecha, horario.hora_fin)
        dur    = timedelta(minutes=servicio.duracion)
        ahora  = datetime.now()

        while cursor + dur <= fin:
            hora_s = cursor.time()
            hora_e = (cursor + dur).time()

            # Descartar slots en el pasado o dentro del margen mínimo
            limite = ahora + timedelta(minutes=MIN_MIN_ANTICIPACION)
            if fecha == ahora.date() and datetime.combine(fecha, hora_s) < limite:
                cursor += timedelta(minutes=30)
                continue

            # Descartar slots que se solapan con la franja de almuerzo
            if CitasService._solapa_almuerzo(hora_s, hora_e):
                cursor += timedelta(minutes=30)
                continue

            ocupado = any(
                hora_s < c_fin and hora_e > c_ini
                for c_ini, c_fin in citas_ocupadas
            )
            if not ocupado:
                slots.append(hora_s.strftime('%H:%M'))

            cursor += timedelta(minutes=30)

        return slots

    # ── Validación completa antes de crear ──────────────────────────────────

    @staticmethod
    def validar_cita(barbero_id, servicio_id, fecha, hora_inicio, cliente=None):
        """
        Valida todos los requisitos de negocio antes de crear una cita.

        Args:
            barbero_id:  ID del barbero
            servicio_id: ID del servicio
            fecha:       date
            hora_inicio: time
            cliente:     PerfilUsuario opcional — activa validaciones del cliente

        Returns:
            (bool, list)  — (es_válido, lista_de_errores_en_español)
        """
        from .horarios_service import HorariosService

        errores = []
        hoy     = timezone.localdate()

        # 1. Fecha no en el pasado
        if fecha < hoy:
            errores.append('No puedes agendar citas en fechas pasadas.')
            return False, errores   # Sin fecha válida no tiene sentido seguir

        # 2. Fecha dentro del límite de anticipación
        if (fecha - hoy).days > MAX_DIAS_ANTICIPACION:
            errores.append(
                f'Solo puedes agendar con un máximo de {MAX_DIAS_ANTICIPACION} días de anticipación.'
            )

        # 3. Barbero existe, activo y disponible
        try:
            barbero = Barbero.objects.get(pk=barbero_id, estado='ACTIVO')
        except Barbero.DoesNotExist:
            errores.append('El barbero seleccionado no está disponible.')
            return False, errores

        if barbero.disponibilidad == 'NO_DISPONIBLE':
            errores.append('El barbero no está disponible en este momento.')

        # 4. Servicio existe y está activo
        try:
            servicio = Servicio.objects.get(pk=servicio_id, activo=True)
        except Servicio.DoesNotExist:
            errores.append('El servicio seleccionado no está disponible.')
            return False, errores

        # 5. El barbero ofrece ese servicio
        if not barbero.servicios.filter(pk=servicio_id).exists():
            errores.append('El barbero seleccionado no ofrece ese servicio.')

        # 6. La barbería atiende ese día
        if not HorariosService.is_dia_disponible(fecha):
            errores.append('La barbería no atiende ese día.')
            return False, errores

        # 7. La hora está dentro del horario de atención
        horario = HorariosService.get_horario_dia(fecha)
        if horario:
            hora_fin = CitasService.calcular_hora_fin(hora_inicio, servicio.duracion)
            if hora_inicio < horario.hora_inicio or hora_fin > horario.hora_fin:
                errores.append(
                    f'El horario de atención es de '
                    f'{horario.hora_inicio.strftime("%H:%M")} a '
                    f'{horario.hora_fin.strftime("%H:%M")}.'
                )
        else:
            errores.append('No hay horario configurado para ese día.')
            return False, errores

        # 7b. La cita no cae en la franja de almuerzo (12:00 - 14:00)
        hora_fin_tentativa = CitasService.calcular_hora_fin(hora_inicio, servicio.duracion)
        if CitasService._solapa_almuerzo(hora_inicio, hora_fin_tentativa):
            errores.append(
                f'El horario de {ALMUERZO_INICIO.strftime("%H:%M")} a '
                f'{ALMUERZO_FIN.strftime("%H:%M")} está reservado para el almuerzo.'
            )

        # 8. Mínimo de anticipación
        ahora_local = timezone.localtime()
        dt_cita     = datetime.combine(fecha, hora_inicio)
        # Comparación naive — ambos sin tzinfo para evitar error de tipos
        ahora_naive = datetime(
            ahora_local.year, ahora_local.month, ahora_local.day,
            ahora_local.hour, ahora_local.minute, ahora_local.second
        )
        if dt_cita < ahora_naive + timedelta(minutes=MIN_MIN_ANTICIPACION):
            errores.append(
                f'Debes agendar con al menos {MIN_MIN_ANTICIPACION} minutos de anticipación.'
            )

        # 9. Slot del barbero libre
        hora_fin = CitasService.calcular_hora_fin(hora_inicio, servicio.duracion)
        if not CitasService.is_time_slot_available(barbero, fecha, hora_inicio, hora_fin):
            errores.append('El horario seleccionado ya está ocupado para ese barbero.')

        # ── Validaciones del cliente (opcionales) ──────────────────────────
        if cliente:
            # 10. Límite de citas activas por día (máximo 2 en el mismo día)
            citas_hoy = Cita.objects.filter(
                cliente=cliente,
                fecha=fecha,
                estado__in=['PENDIENTE', 'CONFIRMADA'],
            ).count()
            if citas_hoy >= MAX_CITAS_POR_DIA:
                errores.append(
                    f'Ya tienes {citas_hoy} cita(s) para ese día. '
                    f'El máximo permitido es {MAX_CITAS_POR_DIA} citas por día.'
                )

            # 11. El cliente no tiene otra cita activa en ese mismo horario
            conflicto = Cita.objects.filter(
                cliente=cliente,
                fecha=fecha,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio,
            ).exclude(estado='CANCELADA').exists()
            if conflicto:
                errores.append('Ya tienes una cita activa en ese horario.')

        return len(errores) == 0, errores

    # ── Validación de código de reserva ─────────────────────────────────────

    @staticmethod
    def es_codigo_valido(codigo):
        """
        Verifica que el código tenga el formato correcto BH-XXXXXX.
        No consulta la BD — solo valida el formato.
        """
        return bool(PATRON_CODIGO.match(codigo)) if codigo else False
