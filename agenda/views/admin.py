"""
Vistas del módulo ADMINISTRADOR - BarberHub.
Gestión de servicios, horarios, citas, reportes y configuración.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone

from ..forms import ServicioForm, HorarioForm, ConfiguracionBarberiaForm
from ..models import (
    Barbero, Servicio, Cita, Horario, ConfiguracionBarberia,
    PerfilUsuario, Calificacion,
)
from ..utils import admin_required


# ===========================================================================
# GESTIÓN DE BARBEROS
# ===========================================================================

@login_required
@admin_required
def barberos_view(request):
    """Lista y gestión de barberos. Solo accesible para ADMIN."""
    barberos = Barbero.objects.select_related(
        'perfil__usuario'
    ).prefetch_related('servicios').all()

    contexto = {
        'barberos': barberos,
        'total_barberos': barberos.count(),
        'barberos_activos': barberos.filter(estado='ACTIVO').count(),
        # Barbero con más citas finalizadas
        'top_barbero': Cita.objects.filter(estado='FINALIZADA').values(
            'barbero__perfil__usuario__first_name',
            'barbero__perfil__usuario__last_name',
        ).annotate(total=Count('id')).order_by('-total').first(),
        # Citas pendientes totales
        'citas_pendientes': Cita.objects.filter(estado='PENDIENTE').count(),
    }
    return render(request, 'agenda/barberos.html', contexto)


# ===========================================================================
# GESTIÓN DE SERVICIOS
# ===========================================================================

@login_required
@admin_required
def servicios_view(request):
    """Lista todos los servicios."""
    servicios = Servicio.objects.annotate(total_citas=Count('citas_servicio')).order_by('nombre')
    return render(request, 'agenda/admin/servicios.html', {'servicios': servicios})


@login_required
@admin_required
def servicio_crear(request):
    """Crear un nuevo servicio."""
    form = ServicioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servicio creado correctamente.')
        return redirect('servicios')
    return render(request, 'agenda/admin/servicio_form.html', {'form': form, 'accion': 'Crear'})


@login_required
@admin_required
def servicio_editar(request, pk):
    """Editar servicio existente."""
    servicio = get_object_or_404(Servicio, pk=pk)
    form = ServicioForm(request.POST or None, instance=servicio)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servicio actualizado correctamente.')
        return redirect('servicios')
    return render(request, 'agenda/admin/servicio_form.html', {'form': form, 'accion': 'Editar', 'servicio': servicio})


@login_required
@admin_required
def servicio_toggle(request, pk):
    """Activar / desactivar servicio."""
    servicio = get_object_or_404(Servicio, pk=pk)
    servicio.activo = not servicio.activo
    servicio.save()
    estado = 'activado' if servicio.activo else 'desactivado'
    messages.success(request, f'Servicio "{servicio.nombre}" {estado}.')
    return redirect('servicios')


@login_required
@admin_required
def servicio_eliminar(request, pk):
    """Eliminar servicio (solo si no tiene citas asociadas)."""
    servicio = get_object_or_404(Servicio, pk=pk)
    if servicio.citas_servicio.exists():
        messages.error(request, f'No se puede eliminar "{servicio.nombre}" porque tiene citas asociadas. Desactívalo en su lugar.')
        return redirect('servicios')
    if request.method == 'POST':
        servicio.delete()
        messages.success(request, 'Servicio eliminado.')
        return redirect('servicios')
    return render(request, 'agenda/admin/confirmar_eliminar.html', {'objeto': servicio, 'tipo': 'servicio'})


# ===========================================================================
# GESTIÓN DE CITAS (Admin)
# ===========================================================================

@login_required
@admin_required
def citas_admin_view(request):
    """Lista todas las citas con filtros."""
    citas = Cita.objects.select_related(
        'cliente__usuario', 'barbero__perfil__usuario', 'servicio'
    ).order_by('-fecha', '-hora_inicio')

    # Filtros GET
    fecha = request.GET.get('fecha', '').strip()
    estado = request.GET.get('estado', '').strip()
    barbero = request.GET.get('barbero', '').strip()
    cliente = request.GET.get('cliente', '').strip()

    if fecha:
        citas = citas.filter(fecha=fecha)
    if estado:
        citas = citas.filter(estado=estado)
    if barbero:
        citas = citas.filter(barbero__id=barbero)
    if cliente:
        citas = citas.filter(
            Q(cliente__usuario__first_name__icontains=cliente) |
            Q(cliente__usuario__last_name__icontains=cliente) |
            Q(cliente__usuario__username__icontains=cliente)
        )

    contexto = {
        'citas': citas,
        'barberos_lista': Barbero.objects.select_related('perfil__usuario').filter(estado='ACTIVO'),
        'estados': Cita.ESTADO_CHOICES,
        'filtros': {'fecha': fecha, 'estado': estado, 'barbero': barbero, 'cliente': cliente},
        'total': citas.count(),
    }
    return render(request, 'agenda/admin/citas_admin.html', contexto)


@login_required
@admin_required
def cita_cambiar_estado(request, pk):
    """Cambiar el estado de una cita vía POST."""
    cita = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado', '')
        estados_validos = [e[0] for e in Cita.ESTADO_CHOICES]
        if nuevo_estado in estados_validos:
            cita.estado = nuevo_estado
            cita.save()
            messages.success(request, f'Cita #{cita.pk} → {cita.get_estado_display()}')
        else:
            messages.error(request, 'Estado inválido.')
    return redirect(request.META.get('HTTP_REFERER', 'citas_admin'))


# ===========================================================================
# GESTIÓN DE HORARIOS
# ===========================================================================

@login_required
@admin_required
def horarios_view(request):
    """Lista horarios semanales y días especiales."""
    horarios_semana = Horario.objects.filter(
        fecha_especifica__isnull=True
    ).order_by('dia_semana')

    horarios_especiales = Horario.objects.filter(
        fecha_especifica__isnull=False
    ).order_by('-fecha_especifica')

    return render(request, 'agenda/admin/horarios.html', {
        'horarios_semana': horarios_semana,
        'horarios_especiales': horarios_especiales,
    })


@login_required
@admin_required
def horario_crear(request):
    """Crear horario o bloqueo de día."""
    form = HorarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Horario guardado correctamente.')
        return redirect('horarios')
    return render(request, 'agenda/admin/horario_form.html', {'form': form, 'accion': 'Crear'})


@login_required
@admin_required
def horario_editar(request, pk):
    """Editar horario existente."""
    horario = get_object_or_404(Horario, pk=pk)
    form = HorarioForm(request.POST or None, instance=horario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Horario actualizado.')
        return redirect('horarios')
    return render(request, 'agenda/admin/horario_form.html', {'form': form, 'accion': 'Editar', 'horario': horario})


@login_required
@admin_required
def horario_eliminar(request, pk):
    """Eliminar horario."""
    horario = get_object_or_404(Horario, pk=pk)
    if request.method == 'POST':
        horario.delete()
        messages.success(request, 'Horario eliminado.')
        return redirect('horarios')
    return render(request, 'agenda/admin/confirmar_eliminar.html', {'objeto': horario, 'tipo': 'horario'})


# ===========================================================================
# REPORTES Y ESTADÍSTICAS
# ===========================================================================

@login_required
@admin_required
def reportes_view(request):
    """Panel de reportes con datos reales del ORM."""
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)

    # Totales generales
    total_citas = Cita.objects.count()
    citas_hoy = Cita.objects.filter(fecha=hoy).exclude(estado='CANCELADA').count()
    citas_mes = Cita.objects.filter(fecha__gte=inicio_mes).exclude(estado='CANCELADA').count()
    citas_finalizadas = Cita.objects.filter(estado='FINALIZADA').count()
    citas_canceladas = Cita.objects.filter(estado='CANCELADA').count()
    citas_pendientes = Cita.objects.filter(estado='PENDIENTE').count()
    total_clientes = PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count()
    total_barberos = Barbero.objects.filter(estado='ACTIVO').count()

    # Ingresos
    ingresos_total = Cita.objects.filter(
        estado='FINALIZADA'
    ).aggregate(total=Sum('precio'))['total'] or 0

    ingresos_mes = Cita.objects.filter(
        estado='FINALIZADA', fecha__gte=inicio_mes
    ).aggregate(total=Sum('precio'))['total'] or 0

    # Top 5 servicios más solicitados
    servicios_top = Cita.objects.filter(
        estado='FINALIZADA'
    ).values('servicio__nombre').annotate(
        total=Count('id'),
        ingresos=Sum('precio'),
    ).order_by('-total')[:5]

    # Top barberos por citas finalizadas
    barberos_top = Cita.objects.filter(
        estado='FINALIZADA'
    ).values(
        'barbero__perfil__usuario__first_name',
        'barbero__perfil__usuario__last_name',
    ).annotate(
        total=Count('id'),
        ingresos=Sum('precio'),
    ).order_by('-total')[:5]

    # Calificación promedio por barbero
    calificaciones_barbero = Calificacion.objects.values(
        'barbero__perfil__usuario__first_name',
        'barbero__perfil__usuario__last_name',
    ).annotate(promedio=Avg('puntuacion'), total=Count('id')).order_by('-promedio')

    # Citas por estado (para gráfica)
    citas_por_estado = {
        e[1]: Cita.objects.filter(estado=e[0]).count()
        for e in Cita.ESTADO_CHOICES
    }

    contexto = {
        'total_citas': total_citas,
        'citas_hoy': citas_hoy,
        'citas_mes': citas_mes,
        'citas_finalizadas': citas_finalizadas,
        'citas_canceladas': citas_canceladas,
        'citas_pendientes': citas_pendientes,
        'total_clientes': total_clientes,
        'total_barberos': total_barberos,
        'ingresos_total': ingresos_total,
        'ingresos_mes': ingresos_mes,
        'servicios_top': servicios_top,
        'barberos_top': barberos_top,
        'calificaciones_barbero': calificaciones_barbero,
        'citas_por_estado': citas_por_estado,
    }
    return render(request, 'agenda/admin/reportes.html', contexto)


# ===========================================================================
# GESTIÓN DE CLIENTES
# ===========================================================================

@login_required
@admin_required
def clientes_view(request):
    """Lista y gestión de clientes registrados."""
    clientes = PerfilUsuario.objects.filter(rol='CLIENTE').select_related('usuario').order_by(
        'usuario__first_name', 'usuario__last_name'
    )

    # Búsqueda
    q = request.GET.get('q', '').strip()
    if q:
        clientes = clientes.filter(
            Q(usuario__first_name__icontains=q) |
            Q(usuario__last_name__icontains=q) |
            Q(usuario__username__icontains=q) |
            Q(usuario__email__icontains=q) |
            Q(telefono__icontains=q)
        )

    # Filtro estado
    estado = request.GET.get('estado', '').strip()
    if estado == 'activo':
        clientes = clientes.filter(activo=True)
    elif estado == 'inactivo':
        clientes = clientes.filter(activo=False)

    # Anotar con total de citas
    clientes = clientes.annotate(total_citas=Count('citas_cliente'))

    contexto = {
        'clientes': clientes,
        'total_clientes': PerfilUsuario.objects.filter(rol='CLIENTE').count(),
        'clientes_activos': PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count(),
        'clientes_nuevos_mes': PerfilUsuario.objects.filter(
            rol='CLIENTE',
            creado_en__gte=timezone.localdate().replace(day=1)
        ).count(),
        'filtros': {'q': q, 'estado': estado},
    }
    return render(request, 'agenda/admin/clientes.html', contexto)


@login_required
@admin_required
def cliente_toggle(request, pk):
    """Activar / desactivar cuenta de cliente."""
    cliente = get_object_or_404(PerfilUsuario, pk=pk, rol='CLIENTE')
    cliente.activo = not cliente.activo
    cliente.save()
    nombre = cliente.usuario.get_full_name() or cliente.usuario.username
    estado = 'activado' if cliente.activo else 'desactivado'
    messages.success(request, f'Cliente "{nombre}" {estado}.')
    return redirect('clientes')


@login_required
@admin_required
def cliente_detalle(request, pk):
    """Detalle de un cliente: historial de citas y estadísticas."""
    cliente = get_object_or_404(PerfilUsuario, pk=pk, rol='CLIENTE')

    citas = Cita.objects.filter(cliente=cliente).select_related(
        'barbero__perfil__usuario', 'servicio'
    ).order_by('-fecha', '-hora_inicio')

    total_gastado = citas.filter(estado='FINALIZADA').aggregate(
        total=Sum('precio')
    )['total'] or 0

    contexto = {
        'cliente': cliente,
        'citas': citas,
        'total_citas': citas.count(),
        'citas_finalizadas': citas.filter(estado='FINALIZADA').count(),
        'citas_canceladas': citas.filter(estado='CANCELADA').count(),
        'total_gastado': total_gastado,
    }
    return render(request, 'agenda/admin/cliente_detalle.html', contexto)


# ===========================================================================
# VALIDAR COMPROBANTE (QR / CÓDIGO MANUAL)
# ===========================================================================

@login_required
@admin_required
def validar_comprobante_view(request):
    """
    Panel de validación de comprobantes.
    Permite buscar una cita por su código de reserva (manual o vía QR).
    No modifica el estado de la cita — solo muestra la información.
    """
    cita = None
    codigo_buscado = ''
    error = None

    if request.method == 'POST':
        codigo_buscado = request.POST.get('codigo', '').strip().upper()
        if codigo_buscado:
            try:
                cita = Cita.objects.select_related(
                    'cliente__usuario', 'barbero__perfil__usuario', 'servicio'
                ).get(codigo_reserva=codigo_buscado)
            except Cita.DoesNotExist:
                error = f'No se encontró ninguna reserva con el código "{codigo_buscado}".'
        else:
            error = 'Ingresa un código de reserva.'

    return render(request, 'agenda/admin/validar_comprobante.html', {
        'cita': cita,
        'codigo_buscado': codigo_buscado,
        'error': error,
    })


# ===========================================================================
# CONFIGURACIÓN DE BARBERÍA
# ===========================================================================

@login_required
@admin_required
def configuracion_view(request):
    """Ver y editar configuración de la barbería (singleton)."""
    config, _ = ConfiguracionBarberia.objects.get_or_create(
        pk=1,
        defaults={'nombre': 'BarberHub'}
    )
    form = ConfiguracionBarberiaForm(
        request.POST or None,
        request.FILES or None,
        instance=config
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Configuración guardada correctamente.')
        return redirect('configuracion')

    return render(request, 'agenda/admin/configuracion.html', {'form': form, 'config': config})
