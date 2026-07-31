"""
Vistas del módulo BARBERO — BarberHub.

Reglas:
- Solo accesibles por usuarios con rol BARBERO.
- Toda la información proviene de la base de datos (ORM).
- Un barbero solo ve sus propias citas y clientes.
"""

from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Barbero, Calificacion, Cita


# ---------------------------------------------------------------------------
# Decorador helper
# ---------------------------------------------------------------------------

def barbero_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (hasattr(request.user, 'perfil') and request.user.perfil.rol == 'BARBERO'):
            messages.error(request, 'Acceso restringido a barberos.')
            return redirect('dashboard')
        # Asegurar que tiene objeto Barbero asociado
        try:
            _ = request.user.perfil.barbero
        except Barbero.DoesNotExist:
            messages.error(request, 'Tu cuenta de barbero no está configurada. Contacta al administrador.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# 1. DASHBOARD
# ---------------------------------------------------------------------------

@login_required
@barbero_required
def barbero_dashboard(request):
    barbero = request.user.perfil.barbero
    hoy = timezone.localdate()

    # Citas del día (no canceladas)
    citas_hoy_lista = (
        Cita.objects.filter(barbero=barbero, fecha=hoy)
        .exclude(estado='CANCELADA')
        .select_related('cliente__usuario', 'servicio')
        .order_by('hora_inicio')
    )
    citas_hoy = citas_hoy_lista.count()

    # Próxima cita: la más próxima desde ahora (pendiente o confirmada)
    proxima_cita = (
        Cita.objects.filter(
            barbero=barbero,
            fecha__gte=hoy,
            estado__in=['PENDIENTE', 'CONFIRMADA'],
        )
        .select_related('cliente__usuario', 'servicio')
        .order_by('fecha', 'hora_inicio')
        .first()
    )

    # Citas pendientes totales (hoy y futuras)
    citas_pendientes = Cita.objects.filter(
        barbero=barbero,
        fecha__gte=hoy,
        estado__in=['PENDIENTE', 'CONFIRMADA'],
    ).count()

    # Calificación promedio
    resultado = Calificacion.objects.filter(barbero=barbero).aggregate(prom=Avg('puntuacion'))
    calificacion_promedio = round(resultado['prom'], 1) if resultado['prom'] else None

    # Choices de disponibilidad
    disponibilidad_choices = Barbero.DISPONIBILIDAD_CHOICES

    return render(request, 'barbero/dashboard.html', {
        'barbero': barbero,
        'citas_hoy': citas_hoy,
        'citas_hoy_lista': citas_hoy_lista,
        'proxima_cita': proxima_cita,
        'citas_pendientes': citas_pendientes,
        'calificacion_promedio': calificacion_promedio,
        'disponibilidad_choices': disponibilidad_choices,
    })


# ---------------------------------------------------------------------------
# 2. AGENDA
# ---------------------------------------------------------------------------

@login_required
@barbero_required
def barbero_agenda(request):
    barbero = request.user.perfil.barbero
    hoy = timezone.localdate()

    vista = request.GET.get('vista', 'dia')
    offset = int(request.GET.get('offset', 0))

    if vista == 'dia':
        fecha_base = hoy + timedelta(days=offset)
        citas = (
            Cita.objects.filter(barbero=barbero, fecha=fecha_base)
            .exclude(estado='CANCELADA')
            .select_related('cliente__usuario', 'servicio')
            .order_by('hora_inicio')
        )
        DIAS_ES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        MESES_ES = ['', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        titulo_periodo = (
            f"{DIAS_ES[fecha_base.weekday()]}, "
            f"{fecha_base.day} de {MESES_ES[fecha_base.month]} de {fecha_base.year}"
        )
        total_citas_periodo = citas.count()

    elif vista == 'semana':
        # Semana que empieza en lunes
        inicio_semana = hoy + timedelta(weeks=offset) - timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        citas = (
            Cita.objects.filter(barbero=barbero, fecha__range=(inicio_semana, fin_semana))
            .exclude(estado='CANCELADA')
            .select_related('cliente__usuario', 'servicio')
            .order_by('fecha', 'hora_inicio')
        )
        MESES_ES = ['', 'ene', 'feb', 'mar', 'abr', 'may', 'jun',
                    'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
        titulo_periodo = (
            f"{inicio_semana.day} {MESES_ES[inicio_semana.month]} — "
            f"{fin_semana.day} {MESES_ES[fin_semana.month]} {fin_semana.year}"
        )
        total_citas_periodo = citas.count()

    else:  # mes
        from calendar import monthrange
        mes_base = hoy.replace(day=1) + timedelta(days=offset * 32)
        mes_base = mes_base.replace(day=1)
        _, ultimo_dia = monthrange(mes_base.year, mes_base.month)
        inicio_mes = mes_base
        fin_mes = mes_base.replace(day=ultimo_dia)
        citas = (
            Cita.objects.filter(barbero=barbero, fecha__range=(inicio_mes, fin_mes))
            .exclude(estado='CANCELADA')
            .select_related('cliente__usuario', 'servicio')
            .order_by('fecha', 'hora_inicio')
        )
        MESES_ES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        titulo_periodo = f"{MESES_ES[mes_base.month]} {mes_base.year}"
        total_citas_periodo = citas.count()

    return render(request, 'barbero/agenda.html', {
        'barbero': barbero,
        'citas': citas,
        'vista': vista,
        'offset': offset,
        'offset_anterior': offset - 1,
        'offset_siguiente': offset + 1,
        'titulo_periodo': titulo_periodo,
        'total_citas_periodo': total_citas_periodo,
    })


# ---------------------------------------------------------------------------
# 3. DETALLE DE CITA
# ---------------------------------------------------------------------------

@login_required
@barbero_required
def barbero_cita_detalle(request, pk):
    barbero = request.user.perfil.barbero

    # Solo puede ver sus propias citas
    cita = get_object_or_404(
        Cita.objects.select_related('cliente__usuario', 'servicio', 'barbero'),
        pk=pk,
        barbero=barbero,
    )

    # Calificación si existe
    calificacion = getattr(cita, 'calificacion', None)

    # Total de citas previas del mismo cliente con este barbero
    total_citas_cliente = Cita.objects.filter(
        barbero=barbero,
        cliente=cita.cliente,
    ).exclude(pk=pk).count()

    return render(request, 'barbero/detalle_cita.html', {
        'cita': cita,
        'calificacion': calificacion,
        'total_citas_cliente': total_citas_cliente,
    })


# ---------------------------------------------------------------------------
# 4. ACCIÓN SOBRE CITA (cambiar estado)
# ---------------------------------------------------------------------------

@login_required
@barbero_required
def barbero_cita_accion(request, pk):
    """Permite al barbero marcar EN_PROCESO o FINALIZADA."""
    if request.method != 'POST':
        return redirect('barbero_agenda')

    barbero = request.user.perfil.barbero
    cita = get_object_or_404(Cita, pk=pk, barbero=barbero)

    accion = request.POST.get('accion', '')
    estados_permitidos = ['EN_PROCESO', 'FINALIZADA']

    if accion in estados_permitidos:
        cita.estado = accion
        cita.save()
        messages.success(request, f'Cita #{cita.pk} marcada como {cita.get_estado_display()}.')
    else:
        messages.error(request, 'Acción no válida.')

    return redirect('barbero_cita_detalle', pk=pk)


# ---------------------------------------------------------------------------
# 5. CAMBIAR DISPONIBILIDAD
# ---------------------------------------------------------------------------

@login_required
@barbero_required
def barbero_cambiar_estado(request):
    """Cambia el campo disponibilidad del barbero autenticado."""
    if request.method != 'POST':
        return redirect('barbero_disponibilidad')

    barbero = request.user.perfil.barbero
    nueva_disp = request.POST.get('disponibilidad', '')
    valores_validos = [v[0] for v in Barbero.DISPONIBILIDAD_CHOICES]

    if nueva_disp in valores_validos:
        barbero.disponibilidad = nueva_disp
        barbero.save(update_fields=['disponibilidad'])
        messages.success(request, f'Estado actualizado a: {barbero.get_disponibilidad_display()}.')
    else:
        messages.error(request, 'Estado no válido.')

    # Redirigir al origen (dashboard o disponibilidad)
    referer = request.META.get('HTTP_REFERER', '')
    if 'disponibilidad' in referer:
        return redirect('barbero_disponibilidad')
    return redirect('barbero_dashboard')


# ---------------------------------------------------------------------------
# 6. HISTORIAL
# ---------------------------------------------------------------------------

@login_required
@barbero_required
def barbero_historial(request):
    barbero = request.user.perfil.barbero

    # Solo citas finalizadas o canceladas (historial real)
    citas = (
        Cita.objects.filter(barbero=barbero, estado__in=['FINALIZADA', 'CANCELADA'])
        .select_related('cliente__usuario', 'servicio')
        .prefetch_related('calificacion')
        .order_by('-fecha', '-hora_inicio')
    )

    total_realizadas = Cita.objects.filter(barbero=barbero, estado='FINALIZADA').count()

    # Promedio calificación
    resultado = Calificacion.objects.filter(barbero=barbero).aggregate(prom=Avg('puntuacion'))
    promedio_calificacion = round(resultado['prom'], 1) if resultado['prom'] else None

    # Servicios más realizados (top 5)
    servicios_top = (
        Cita.objects.filter(barbero=barbero, estado='FINALIZADA')
        .values('servicio__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )
    servicio_top = servicios_top.first() if servicios_top else None

    return render(request, 'barbero/historial.html', {
        'barbero': barbero,
        'citas': citas,
        'total_realizadas': total_realizadas,
        'promedio_calificacion': promedio_calificacion,
        'servicios_top': servicios_top,
        'servicio_top': servicio_top,
    })


# ---------------------------------------------------------------------------
# 7. DISPONIBILIDAD (vista dedicada)
# ---------------------------------------------------------------------------

@login_required
@barbero_required
def barbero_disponibilidad(request):
    barbero = request.user.perfil.barbero
    return render(request, 'barbero/disponibilidad.html', {
        'barbero': barbero,
    })
