"""
Vistas del módulo CLIENTE - BarberHub.
"""

import base64
import io
from datetime import datetime as dt, time as dtime

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import Barbero, Cita, Horario, Servicio
from ..services import CitasService, HorariosService
from ..utils import es_barbero, es_cliente


def _generar_qr_base64(texto):
    """Genera un QR con solo el código de reserva y lo devuelve en base64."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=2,
    )
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#121414', back_color='#e9c349')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


# ===========================================================================
# MIS CITAS
# ===========================================================================

@login_required
def mis_citas_view(request):
    if not es_cliente(request.user):
        return redirect('dashboard')

    perfil = request.user.perfil
    hoy    = timezone.localdate()

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

    return render(request, 'agenda/mis_citas.html', {
        'proximas':        proximas,
        'historial':       historial,
        'canceladas':      canceladas,
        'total_realizadas': Cita.objects.filter(cliente=perfil, estado='FINALIZADA').count(),
        'total_proximas':  proximas.count(),
        'hoy':             hoy,
    })


# ===========================================================================
# CANCELAR CITA
# ===========================================================================

@login_required
def cancelar_cita_view(request, pk):
    if not es_cliente(request.user):
        return redirect('dashboard')

    # Ownership check: solo puede cancelar sus propias citas
    cita = get_object_or_404(Cita, pk=pk, cliente=request.user.perfil)

    if request.method == 'POST':
        if cita.estado in ['PENDIENTE', 'CONFIRMADA']:
            cita.estado = 'CANCELADA'
            cita.save()
            messages.success(request, f'Cita {cita.codigo_reserva} cancelada correctamente.')
        else:
            messages.error(request, 'Esta cita no puede cancelarse en su estado actual.')

    return redirect('mis_citas')


# ===========================================================================
# AGENDAR CITA
# ===========================================================================

@login_required
def agendar_cita_view(request):
    if es_barbero(request.user):
        messages.error(request, 'Los barberos no pueden agendar citas desde este módulo.')
        return redirect('dashboard')

    if request.method == 'POST':
        servicio_id = request.POST.get('servicio_id', '').strip()
        barbero_id  = request.POST.get('barbero_id', '').strip()
        fecha_str   = request.POST.get('fecha', '').strip()
        hora_str    = request.POST.get('hora_inicio', '').strip()

        errores = []
        if not servicio_id: errores.append('Selecciona un servicio.')
        if not barbero_id:  errores.append('Selecciona un barbero.')
        if not fecha_str:   errores.append('Selecciona una fecha.')
        if not hora_str:    errores.append('Selecciona una hora.')

        fecha    = None
        hora_ini = None

        if not errores:
            try:
                fecha    = dt.strptime(fecha_str, '%Y-%m-%d').date()
                hora_ini = dtime.fromisoformat(hora_str)
            except ValueError:
                errores.append('Formato de fecha u hora inválido.')

        if not errores:
            # Toda la lógica de negocio en el servicio, incluyendo validaciones del cliente
            es_valido, errores_srv = CitasService.validar_cita(
                barbero_id, servicio_id, fecha, hora_ini,
                cliente=request.user.perfil,
            )
            errores.extend(errores_srv)

            if es_valido:
                barbero  = Barbero.objects.get(pk=barbero_id, estado='ACTIVO')
                servicio = Servicio.objects.get(pk=servicio_id, activo=True)
                hora_fin = CitasService.calcular_hora_fin(hora_ini, servicio.duracion)

                cita = Cita.objects.create(
                    cliente     = request.user.perfil,
                    barbero     = barbero,
                    servicio    = servicio,
                    fecha       = fecha,
                    hora_inicio = hora_ini,
                    hora_fin    = hora_fin,
                    precio      = servicio.precio,
                    estado      = 'PENDIENTE',
                )
                messages.success(
                    request,
                    f'¡Cita reservada! Código: {cita.codigo_reserva}. '
                    f'Te esperamos el {fecha.strftime("%d/%m/%Y")} a las {hora_ini.strftime("%H:%M")}.'
                )
                # Redirige al comprobante usando el código, no el PK
                return redirect('comprobante_cita', codigo=cita.codigo_reserva)

        for e in errores:
            messages.error(request, e)

    servicios = Servicio.objects.filter(activo=True).order_by('nombre')
    barberos  = Barbero.objects.filter(
        estado='ACTIVO',
        disponibilidad__in=['DISPONIBLE', 'OCUPADO'],
    ).select_related('perfil__usuario').prefetch_related('servicios')

    dias_abiertos = list(
        Horario.objects.filter(
            abierto=True,
            fecha_especifica__isnull=True,
            dia_semana__isnull=False,
        ).values_list('dia_semana', flat=True).distinct()
    )

    return render(request, 'agenda/agendar_cita.html', {
        'servicios':    servicios,
        'barberos':     barberos,
        'dias_abiertos': dias_abiertos,
    })


# ===========================================================================
# SLOTS DISPONIBLES (AJAX)
# ===========================================================================

@login_required
def slots_disponibles_view(request):
    barbero_id  = request.GET.get('barbero', '').strip()
    servicio_id = request.GET.get('servicio', '').strip()
    fecha_str   = request.GET.get('fecha', '').strip()

    if not (barbero_id and servicio_id and fecha_str):
        return JsonResponse({'slots': [], 'error': 'Faltan parámetros.'})

    try:
        barbero  = Barbero.objects.get(pk=barbero_id, estado='ACTIVO')
        servicio = Servicio.objects.get(pk=servicio_id, activo=True)
        fecha    = dt.strptime(fecha_str, '%Y-%m-%d').date()
    except (Barbero.DoesNotExist, Servicio.DoesNotExist, ValueError):
        return JsonResponse({'slots': [], 'error': 'Datos inválidos.'})

    if not HorariosService.is_dia_disponible(fecha):
        return JsonResponse({'slots': [], 'error': 'La barbería no atiende ese día.'})

    if barbero.disponibilidad == 'NO_DISPONIBLE':
        return JsonResponse({'slots': [], 'error': 'El barbero no está disponible.'})

    slots = CitasService.get_available_slots(barbero, servicio, fecha)
    return JsonResponse({'slots': slots})


# ===========================================================================
# COMPROBANTE — usa código de reserva en URL, no PK interno
# ===========================================================================

@login_required
def comprobante_view(request, codigo):
    """
    Muestra el comprobante con QR.
    - Solo accesible para el cliente dueño de la cita.
    - Usa el código de reserva en la URL para no exponer PKs.
    - Devuelve 404 si el código no existe o no pertenece al usuario.
    """
    if not CitasService.es_codigo_valido(codigo):
        raise Http404

    try:
        cita = Cita.objects.select_related(
            'cliente__usuario', 'barbero__perfil__usuario', 'servicio'
        ).get(codigo_reserva=codigo)
    except Cita.DoesNotExist:
        raise Http404

    # Ownership check — el cliente solo ve sus propias citas
    if cita.cliente != request.user.perfil:
        raise Http404

    qr_base64 = _generar_qr_base64(cita.codigo_reserva)

    return render(request, 'agenda/comprobante.html', {
        'cita':      cita,
        'qr_base64': qr_base64,
    })
