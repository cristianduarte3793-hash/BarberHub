"""
Vistas del módulo CLIENTE - BarberHub.
Agendar citas, ver citas, cancelar y slots disponibles.
"""

import base64
import io
from datetime import datetime as dt, time as dtime, timedelta

import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from ..models import Servicio, Barbero, Cita, Horario
from ..utils import es_barbero, es_cliente


def _generar_qr_base64(texto):
    """Genera un QR y lo devuelve como string base64 para incrustar en HTML."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#121414', back_color='#e9c349')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# ===========================================================================
# MIS CITAS
# ===========================================================================

@login_required
def mis_citas_view(request):
    """Vista de todas las citas del cliente autenticado."""
    if not es_cliente(request.user):
        return redirect('dashboard')

    perfil = request.user.perfil
    hoy = timezone.localdate()

    proximas = (
        Cita.objects.filter(cliente=perfil, fecha__gte=hoy)
        .exclude(estado='CANCELADA')
        .select_related('barbero__perfil__usuario', 'servicio')
        .order_by('fecha', 'hora_inicio')
    )
    historial = (
        Cita.objects.filter(cliente=perfil, fecha__lt=hoy)
        .select_related('barbero__perfil__usuario', 'servicio')
        .order_by('-fecha', '-hora_inicio')
    )
    canceladas = (
        Cita.objects.filter(cliente=perfil, estado='CANCELADA')
        .select_related('barbero__perfil__usuario', 'servicio')
        .order_by('-fecha')[:10]
    )

    total_realizadas = Cita.objects.filter(cliente=perfil, estado='FINALIZADA').count()
    total_proximas = proximas.count()

    return render(request, 'agenda/mis_citas.html', {
        'proximas': proximas,
        'historial': historial,
        'canceladas': canceladas,
        'total_realizadas': total_realizadas,
        'total_proximas': total_proximas,
        'hoy': hoy,
    })


# ===========================================================================
# CANCELAR CITA
# ===========================================================================

@login_required
def cancelar_cita_view(request, pk):
    """Permite al cliente cancelar una cita propia que aún no ha pasado."""
    if not es_cliente(request.user):
        return redirect('dashboard')

    cita = get_object_or_404(Cita, pk=pk, cliente=request.user.perfil)

    if request.method == 'POST':
        if cita.estado in ['PENDIENTE', 'CONFIRMADA']:
            cita.estado = 'CANCELADA'
            cita.save()
            messages.success(request, f'Cita #{cita.pk} cancelada correctamente.')
        else:
            messages.error(request, 'Esta cita no puede cancelarse.')

    return redirect('mis_citas')


# ===========================================================================
# AGENDAR CITA
# ===========================================================================

@login_required
def agendar_cita_view(request):
    """Formulario para agendar una cita."""
    if es_barbero(request.user):
        messages.error(request, 'Los barberos no pueden agendar citas desde este módulo.')
        return redirect('dashboard')

    if request.method == 'POST':
        # Procesar creación de cita
        servicio_id = request.POST.get('servicio_id')
        barbero_id = request.POST.get('barbero_id')
        fecha_str = request.POST.get('fecha')
        hora_str = request.POST.get('hora_inicio')

        errores = []
        if not servicio_id:
            errores.append('Selecciona un servicio.')
        if not barbero_id:
            errores.append('Selecciona un barbero.')
        if not fecha_str:
            errores.append('Selecciona una fecha.')
        if not hora_str:
            errores.append('Selecciona una hora.')

        if not errores:
            try:
                servicio = Servicio.objects.get(pk=servicio_id, activo=True)
                barbero = Barbero.objects.get(pk=barbero_id, estado='ACTIVO')
                fecha = dt.strptime(fecha_str, '%Y-%m-%d').date()
                hora_ini = dtime.fromisoformat(hora_str)
                fin_dt = dt.combine(fecha, hora_ini) + timedelta(minutes=servicio.duracion)
                hora_fin = fin_dt.time()

                # Verificar solapamiento
                solapamiento = Cita.objects.filter(
                    barbero=barbero, fecha=fecha,
                    hora_inicio__lt=hora_fin, hora_fin__gt=hora_ini
                ).exclude(estado='CANCELADA').exists()

                if solapamiento:
                    errores.append('Ese horario ya está ocupado. Elige otra hora.')
                else:
                    Cita.objects.create(
                        cliente=request.user.perfil,
                        barbero=barbero,
                        servicio=servicio,
                        fecha=fecha,
                        hora_inicio=hora_ini,
                        hora_fin=hora_fin,
                        precio=servicio.precio,
                        estado='PENDIENTE',
                    )
                    messages.success(request, f'¡Cita reservada! Te esperamos el {fecha.strftime("%d/%m/%Y")} a las {hora_ini.strftime("%H:%M")}.')
                    return redirect('mis_citas')
            except (Servicio.DoesNotExist, Barbero.DoesNotExist, ValueError):
                errores.append('Datos inválidos. Intenta de nuevo.')

        for e in errores:
            messages.error(request, e)

    servicios = Servicio.objects.filter(activo=True).order_by('nombre')
    barberos = Barbero.objects.filter(
        estado='ACTIVO', disponibilidad__in=['DISPONIBLE', 'OCUPADO']
    ).select_related('perfil__usuario').prefetch_related('servicios')

    dias_abiertos = list(
        Horario.objects.filter(
            abierto=True,
            fecha_especifica__isnull=True,
            dia_semana__isnull=False
        ).values_list('dia_semana', flat=True).distinct()
    )

    return render(request, 'agenda/agendar_cita.html', {
        'servicios': servicios,
        'barberos': barberos,
        'dias_abiertos': dias_abiertos,
    })


# ===========================================================================
# SLOTS DISPONIBLES (AJAX)
# ===========================================================================

@login_required
def slots_disponibles_view(request):
    """AJAX: devuelve los slots libres para un barbero en una fecha."""
    barbero_id = request.GET.get('barbero')
    servicio_id = request.GET.get('servicio')
    fecha_str = request.GET.get('fecha')

    if not (barbero_id and servicio_id and fecha_str):
        return JsonResponse({'slots': []})

    try:
        barbero = Barbero.objects.get(pk=barbero_id, estado='ACTIVO')
        servicio = Servicio.objects.get(pk=servicio_id, activo=True)
        fecha = dt.strptime(fecha_str, '%Y-%m-%d').date()
    except (Barbero.DoesNotExist, Servicio.DoesNotExist, ValueError):
        return JsonResponse({'slots': []})

    # Horario del día
    dia_semana = fecha.weekday()
    horario = Horario.objects.filter(
        dia_semana=dia_semana,
        fecha_especifica__isnull=True,
        abierto=True
    ).first()
    if not horario:
        return JsonResponse({'slots': []})

    # Citas ya ocupadas
    citas_ocupadas = Cita.objects.filter(
        barbero=barbero, fecha=fecha
    ).exclude(estado='CANCELADA').values_list('hora_inicio', 'hora_fin')

    # Generar slots cada 30 min dentro del horario
    slots = []
    cursor = dt.combine(fecha, horario.hora_inicio)
    fin = dt.combine(fecha, horario.hora_fin)
    duracion = timedelta(minutes=servicio.duracion)
    ahora = dt.now()

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

    return JsonResponse({'slots': slots})


# ===========================================================================
# COMPROBANTE DE CITA (RECIBO + QR)
# ===========================================================================

@login_required
def comprobante_view(request, pk):
    """Muestra el comprobante de reserva con QR para una cita del cliente."""
    cita = get_object_or_404(
        Cita.objects.select_related(
            'cliente__usuario', 'barbero__perfil__usuario', 'servicio'
        ),
        pk=pk,
        cliente=request.user.perfil,
    )

    # El QR solo contiene el código de reserva
    qr_base64 = _generar_qr_base64(cita.codigo_reserva)

    return render(request, 'agenda/comprobante.html', {
        'cita': cita,
        'qr_base64': qr_base64,
    })
