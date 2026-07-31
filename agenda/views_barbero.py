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

from .forms import EditarPerfilForm
from .models import Barbero, Calificacion, Cita, PerfilUsuario


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

    # Total de clientes únicos atendidos (solo citas FINALIZADAS)
    total_clientes_atendidos = (
        Cita.objects.filter(barbero=barbero, estado='FINALIZADA')
        .values('cliente')
        .distinct()
        .count()
    )

    # Choices de disponibilidad
    disponibilidad_choices = Barbero.DISPONIBILIDAD_CHOICES

    from datetime import datetime as _dt
    now_time = timezone.localtime().time()

    return render(request, 'barbero/dashboard.html', {
        'barbero': barbero,
        'citas_hoy': citas_hoy,
        'citas_hoy_lista': citas_hoy_lista,
        'proxima_cita': proxima_cita,
        'citas_pendientes': citas_pendientes,
        'calificacion_promedio': calificacion_promedio,
        'total_clientes_atendidos': total_clientes_atendidos,
        'disponibilidad_choices': disponibilidad_choices,
        'now_time': now_time,
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
    dias_semana = []  # solo se puebla en vista semana

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
        citas_qs = (
            Cita.objects.filter(barbero=barbero, fecha__range=(inicio_semana, fin_semana))
            .exclude(estado='CANCELADA')
            .select_related('cliente__usuario', 'servicio')
            .order_by('fecha', 'hora_inicio')
        )
        citas = citas_qs  # para el template tabla mobile

        DIAS_NOMBRES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
        MESES_ES = ['', 'ene', 'feb', 'mar', 'abr', 'may', 'jun',
                    'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

        # Grid de la semana: lista de 7 días con sus citas y posición
        # La grilla empieza en 09:00 (540 min) y cada hora = 60px
        HORA_INICIO_GRID = 9 * 60   # 09:00 en minutos
        PX_POR_MINUTO = 1.0         # 60px por hora → 1px por minuto

        dias_semana = []
        for i in range(7):
            dia_fecha = inicio_semana + timedelta(days=i)
            citas_dia = [c for c in citas_qs if c.fecha == dia_fecha]
            # Calcular posición top y altura para cada cita
            citas_con_pos = []
            for c in citas_dia:
                minutos_inicio = c.hora_inicio.hour * 60 + c.hora_inicio.minute
                minutos_fin    = c.hora_fin.hour * 60 + c.hora_fin.minute
                top_px    = (minutos_inicio - HORA_INICIO_GRID) * PX_POR_MINUTO
                height_px = max((minutos_fin - minutos_inicio) * PX_POR_MINUTO, 36)
                # Adjuntar como atributos temporales al objeto
                c.top_px    = max(int(top_px), 0)
                c.height_px = int(height_px)
                citas_con_pos.append(c)
            dias_semana.append({
                'fecha': dia_fecha,
                'iso':   dia_fecha.isoformat(),
                'nombre': DIAS_NOMBRES[i],
                'dia':   dia_fecha.day,
                'es_hoy': dia_fecha == hoy,
                'citas': citas_con_pos,
            })

        titulo_periodo = (
            f"{inicio_semana.day} {MESES_ES[inicio_semana.month]} — "
            f"{fin_semana.day} {MESES_ES[fin_semana.month]} {fin_semana.year}"
        )
        total_citas_periodo = citas_qs.count()

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
        'dias_semana': dias_semana if vista == 'semana' else [],
        'horas_grid': list(range(9, 20)),  # 09:00 → 19:00
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


# ---------------------------------------------------------------------------
# 8. PERFIL DEL BARBERO (módulo dedicado)
# ---------------------------------------------------------------------------

@login_required
@barbero_required
def barbero_perfil(request):
    """Perfil propio del barbero — muestra y permite editar campos permitidos."""
    perfil = request.user.perfil
    barbero = perfil.barbero

    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name  = form.cleaned_data['last_name']
            request.user.email      = form.cleaned_data['email']
            request.user.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('barbero_perfil')
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name':  request.user.last_name,
            'email':      request.user.email,
        }
        form = EditarPerfilForm(instance=perfil, initial=initial)

    # Métricas del barbero
    resultado = Calificacion.objects.filter(barbero=barbero).aggregate(
        prom=Avg('puntuacion'), total=Count('id')
    )
    calificacion_promedio = round(resultado['prom'], 1) if resultado['prom'] else None
    total_calificaciones  = resultado['total'] or 0

    total_citas_realizadas = Cita.objects.filter(
        barbero=barbero, estado='FINALIZADA'
    ).count()

    total_clientes_unicos = (
        Cita.objects.filter(barbero=barbero, estado='FINALIZADA')
        .values('cliente')
        .distinct()
        .count()
    )

    # Servicio más realizado
    servicio_top_qs = (
        Cita.objects.filter(barbero=barbero, estado='FINALIZADA')
        .values('servicio__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')
        .first()
    )

    # Últimas 5 calificaciones con comentario
    ultimas_calificaciones = (
        Calificacion.objects.filter(barbero=barbero)
        .exclude(comentario='')
        .exclude(comentario__isnull=True)
        .select_related('cliente__usuario')
        .order_by('-creado_en')[:5]
    )

    return render(request, 'barbero/perfil.html', {
        'form': form,
        'perfil': perfil,
        'barbero': barbero,
        'calificacion_promedio': calificacion_promedio,
        'total_calificaciones': total_calificaciones,
        'total_citas_realizadas': total_citas_realizadas,
        'total_clientes_unicos': total_clientes_unicos,
        'servicio_top': servicio_top_qs,
        'ultimas_calificaciones': ultimas_calificaciones,
    })
