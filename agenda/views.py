"""
Vistas de BarberHub.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg

from .forms import RegistroForm, EditarPerfilForm, CambiarPasswordForm
from .models import PerfilUsuario, Barbero, Servicio, Cita, Horario, Calificacion


# ---------------------------------------------------------------------------
# Helpers de permisos
# ---------------------------------------------------------------------------

def es_admin(user):
    return hasattr(user, 'perfil') and user.perfil.rol == 'ADMIN'

def es_barbero(user):
    return hasattr(user, 'perfil') and user.perfil.rol == 'BARBERO'

def es_cliente(user):
    return hasattr(user, 'perfil') and user.perfil.rol == 'CLIENTE'


# ---------------------------------------------------------------------------
# Landing page (pública)
# ---------------------------------------------------------------------------

def landing_view(request):
    """Landing page pública de BarberHub."""
    servicios = Servicio.objects.filter(activo=True)
    barberos  = Barbero.objects.filter(estado='ACTIVO').select_related('perfil__usuario')

    # Stats reales
    total_clientes = PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count()
    total_barberos_activos = barberos.count()
    total_citas = Cita.objects.filter(estado='FINALIZADA').count()
    promedio_calificacion = Calificacion.objects.aggregate(
        prom=Avg('puntuacion'))['prom']
    if promedio_calificacion:
        promedio_calificacion = round(promedio_calificacion, 1)

    # Calificaciones reales para testimonios (máx 3, solo con comentario)
    testimonios = Calificacion.objects.filter(
        comentario__isnull=False
    ).exclude(comentario='').select_related(
        'cliente__usuario'
    ).order_by('-creado_en')[:3]

    # Datos de ejemplo para barberos cuando la BD está vacía
    barberos_ejemplo = [
        ('Marco Rossi',  'Master Barber',     'https://lh3.googleusercontent.com/aida-public/AB6AXuCZ9Pdv_2dj8fz1b-WARHb8ii5mlXjLiPzFRcSf06bbUFcTgtwMf18gL1VEqdKDVIF_V_L18O_bY2-r4JWF-eVv6FUiWSq_HchdOJDxUZmGVSWxW6EkuLMz5hj6BJYDhKDbX186ox0_1HMfbtI0sKhu1fIw97s8hKx9OcVAWXVsnW7rnUyN1iMwsjCrOunsn8kjqoJYAD3HOTrxC_siLKepx9bTzeOiliBRTtQ0tEMUC8K50wj1B5en'),
        ('Alex Chen',   'Fading Expert',      'https://lh3.googleusercontent.com/aida-public/AB6AXuDSYeJ7WZl_8_8_amU8MiqqVx6wmbvkc0NTZWZnzKyjGU3iAiLeuqxEk8pWFCLh9OI5DPn_P_9TSdH9vl44pHXPfNTf8OtYQKmSD07Osod8-G3B8dYEWRv_1W2tjdbemx-apGERs-5Mq_6GOTKJsEZzSKBBTUVb1xqnxTGXWKcrfAkVsqAFOkc5wUzYGwwScJFfTVo3FlpJ4FrYpAmMCmnMPwG1_vUKBRcRGZ5LilzbGVRy1eSlr9yF'),
        ('Julian Mora', 'Classic Specialist', 'https://lh3.googleusercontent.com/aida-public/AB6AXuA7Xc84lWf2f2QW-hofJFdYeiDLU7vhG6giDhmn_WUpG4FcAcz0A2XsXgkV48QeiNS_t0kzDs-xjg1zErZTyuJ76-tOGw6K7TjGTI87OxfX6YNcQpAnGAM-G5jochtpexS1U_gn-rUZVYq98ACMhZZXLexNZL63fv6_V14KIT3ANq0kzJN5RvjaRCVw6Hn-U5Ymz-0EEDTcNcRXTxtJBKveNtPBCOsdP7pP-7lDd5UUerHbRw1urRIs'),
        ('Santi Ruiz',  'Creative Stylist',   'https://lh3.googleusercontent.com/aida-public/AB6AXuDNSz1oDcIhJ7afLxHvejHbSc-apDwmXQLKMQyPOogcI4zliGW7PxPIANNhXG5oMfQXSUABG2_TL8Er47Ct4qDZxGsLbKDi3mZ_uz4Xp3B-i8r9_f1smwK5kSdetKkypwJhqnMQVq7lPGeCAg5JfGZgY4JVKztJ5-fIpDj-Gy-JanFO7I6e6lf18qsDWkRwx6eDi3YsFTU5cGN2aYdMke2UwxIhMmMmUo2GlYYrhfJWUxQK7Xjx6f1S'),
    ]

    return render(request, 'landing.html', {
        'servicios': servicios,
        'barberos': barberos,
        'barberos_ejemplo': barberos_ejemplo,
        'testimonios': testimonios,
        'total_clientes': total_clientes,
        'total_barberos_activos': total_barberos_activos,
        'total_citas': total_citas,
        'promedio_calificacion': promedio_calificacion,
    })


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def login_view(request):
    """Página de inicio de sesión."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if hasattr(user, 'perfil') and not user.perfil.activo:
                messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
                return render(request, 'login.html')
            login(request, user)
            messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'login.html')


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

def logout_view(request):
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('login')


# ---------------------------------------------------------------------------
# Registro de clientes
# ---------------------------------------------------------------------------

def registro_view(request):
    """Registro público — solo crea cuentas con rol CLIENTE."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegistroForm()

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            from django.contrib.auth.models import User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )
            PerfilUsuario.objects.create(
                usuario=user,
                telefono=form.cleaned_data.get('telefono', ''),
                rol='CLIENTE',
                activo=True,
            )
            login(request, user)
            messages.success(request, f'¡Cuenta creada! Bienvenido a BarberHub, {user.first_name}.')
            return redirect('dashboard')

    return render(request, 'registro.html', {'form': form})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    """Dashboard principal con datos reales según el rol.
    Los barberos son redirigidos a su panel dedicado."""
    if es_barbero(request.user):
        return redirect('barbero_dashboard')

    hoy = timezone.localdate()

    # Datos comunes
    proximas_citas = []

    if es_admin(request.user):
        # Citas de hoy
        citas_hoy = Cita.objects.filter(fecha=hoy).exclude(estado='CANCELADA').count()
        # Clientes registrados
        total_clientes = PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count()
        # Barberos activos
        barberos_activos = Barbero.objects.filter(estado='ACTIVO').count()
        # Próximas citas (hoy y futuras, pendientes o confirmadas)
        proximas_citas = Cita.objects.filter(
            fecha__gte=hoy,
            estado__in=['PENDIENTE', 'CONFIRMADA', 'EN_PROCESO']
        ).select_related(
            'cliente__usuario', 'barbero__perfil__usuario', 'servicio'
        ).order_by('fecha', 'hora_inicio')[:10]

        # Servicios más solicitados (top 5 por conteo de citas finalizadas)
        servicios_top_qs = Cita.objects.filter(
            estado='FINALIZADA'
        ).values('servicio__nombre').annotate(
            total=Count('id')
        ).order_by('-total')[:5]

        total_servicios = sum(s['total'] for s in servicios_top_qs) or 1
        servicios_top = [
            {
                'nombre': s['servicio__nombre'],
                'porcentaje': round(s['total'] / total_servicios * 100),
            }
            for s in servicios_top_qs
        ]

        contexto = {
            'citas_hoy': citas_hoy,
            'total_clientes': total_clientes,
            'barberos_activos': barberos_activos,
            'proximas_citas': proximas_citas,
            'servicios_top': servicios_top,
        }

    elif es_barbero(request.user):
        try:
            barbero = request.user.perfil.barbero
            citas_hoy = Cita.objects.filter(
                barbero=barbero, fecha=hoy
            ).exclude(estado='CANCELADA').count()
            proximas_citas = Cita.objects.filter(
                barbero=barbero,
                fecha__gte=hoy,
                estado__in=['PENDIENTE', 'CONFIRMADA', 'EN_PROCESO']
            ).select_related('cliente__usuario', 'servicio').order_by('fecha', 'hora_inicio')[:10]
        except Exception:
            citas_hoy = 0

        contexto = {
            'citas_hoy': citas_hoy,
            'proximas_citas': proximas_citas,
            'servicios_top': [],
        }

    else:  # CLIENTE
        citas_hoy = Cita.objects.filter(
            cliente=request.user.perfil,
            fecha=hoy
        ).exclude(estado='CANCELADA').count()
        proximas_citas = Cita.objects.filter(
            cliente=request.user.perfil,
            fecha__gte=hoy,
            estado__in=['PENDIENTE', 'CONFIRMADA']
        ).select_related('barbero__perfil__usuario', 'servicio').order_by('fecha', 'hora_inicio')[:5]

        contexto = {
            'citas_hoy': citas_hoy,
            'proximas_citas': proximas_citas,
            'servicios_top': [],
        }

    return render(request, 'dashboard.html', contexto)


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------

@login_required
def perfil_view(request):
    """Ver y editar perfil del usuario."""
    perfil = get_object_or_404(PerfilUsuario, usuario=request.user)

    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name  = form.cleaned_data['last_name']
            request.user.email      = form.cleaned_data['email']
            request.user.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name':  request.user.last_name,
            'email':      request.user.email,
        }
        form = EditarPerfilForm(instance=perfil, initial=initial)

    contexto = {'form': form, 'perfil': perfil}

    # Datos extra para barberos
    if perfil.rol == 'BARBERO':
        try:
            barbero = perfil.barbero
            from django.db.models import Avg, Count
            calificacion_resultado = Calificacion.objects.filter(
                barbero=barbero
            ).aggregate(prom=Avg('puntuacion'))
            contexto['calificacion_promedio'] = (
                round(calificacion_resultado['prom'], 1)
                if calificacion_resultado['prom'] else None
            )
            contexto['total_citas_realizadas'] = Cita.objects.filter(
                barbero=barbero, estado='FINALIZADA'
            ).count()
        except Exception:
            contexto['calificacion_promedio'] = None
            contexto['total_citas_realizadas'] = 0

    return render(request, 'perfil.html', contexto)


# ---------------------------------------------------------------------------
# Cambiar contraseña
# ---------------------------------------------------------------------------

@login_required
def cambiar_password_view(request):
    if request.method == 'POST':
        form = CambiarPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña cambiada correctamente.')
            return redirect('perfil')
    else:
        form = CambiarPasswordForm(request.user)

    return render(request, 'cambiar_password.html', {'form': form})


# ---------------------------------------------------------------------------
# Barberos (solo ADMIN)
# ---------------------------------------------------------------------------

@login_required
def barberos_view(request):
    """Lista y gestión de barberos. Solo accesible para ADMIN."""
    if not es_admin(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('dashboard')

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
    return render(request, 'barberos.html', contexto)


# ---------------------------------------------------------------------------
# Agendar Cita
# ---------------------------------------------------------------------------

@login_required
def agendar_cita_view(request):
    """Formulario para agendar una cita."""
    if es_barbero(request.user):
        messages.error(request, 'Los barberos no pueden agendar citas desde este módulo.')
        return redirect('dashboard')

    servicios = Servicio.objects.filter(activo=True)
    barberos = Barbero.objects.filter(
        estado='ACTIVO'
    ).select_related('perfil__usuario').prefetch_related('servicios')

    # Horarios de la semana (para marcar días disponibles en el calendario)
    dias_abiertos = list(
        Horario.objects.filter(
            abierto=True,
            fecha_especifica__isnull=True,
            dia_semana__isnull=False
        ).values_list('dia_semana', flat=True).distinct()
    )

    contexto = {
        'servicios': servicios,
        'barberos': barberos,
        'dias_abiertos': dias_abiertos,
    }
    return render(request, 'agendar_cita.html', contexto)


# ===========================================================================
# MÓDULO ADMINISTRADOR — vistas nuevas
# ===========================================================================

from .forms import ServicioForm, HorarioForm, ConfiguracionBarberiaForm
from .models import ConfiguracionBarberia
from django.db.models import Sum, Q
from django.http import JsonResponse


# ---------------------------------------------------------------------------
# Helper decorador admin
# ---------------------------------------------------------------------------
def admin_required(view_func):
    """Decorador que restringe acceso a administradores."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not es_admin(request.user):
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# 1. GESTIÓN DE SERVICIOS
# ---------------------------------------------------------------------------

@login_required
@admin_required
def servicios_view(request):
    """Lista todos los servicios."""
    servicios = Servicio.objects.annotate(total_citas=Count('citas_servicio')).order_by('nombre')
    return render(request, 'admin/servicios.html', {'servicios': servicios})


@login_required
@admin_required
def servicio_crear(request):
    """Crear un nuevo servicio."""
    form = ServicioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servicio creado correctamente.')
        return redirect('servicios')
    return render(request, 'admin/servicio_form.html', {'form': form, 'accion': 'Crear'})


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
    return render(request, 'admin/servicio_form.html', {'form': form, 'accion': 'Editar', 'servicio': servicio})


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
    return render(request, 'admin/confirmar_eliminar.html', {'objeto': servicio, 'tipo': 'servicio'})


# ---------------------------------------------------------------------------
# 2. GESTIÓN DE CITAS (Admin)
# ---------------------------------------------------------------------------

@login_required
@admin_required
def citas_admin_view(request):
    """Lista todas las citas con filtros."""
    citas = Cita.objects.select_related(
        'cliente__usuario', 'barbero__perfil__usuario', 'servicio'
    ).order_by('-fecha', '-hora_inicio')

    # Filtros GET
    fecha    = request.GET.get('fecha', '').strip()
    estado   = request.GET.get('estado', '').strip()
    barbero  = request.GET.get('barbero', '').strip()
    cliente  = request.GET.get('cliente', '').strip()

    if fecha:
        citas = citas.filter(fecha=fecha)
    if estado:
        citas = citas.filter(estado=estado)
    if barbero:
        citas = citas.filter(barbero__id=barbero)
    if cliente:
        citas = citas.filter(
            Q(cliente__usuario__first_name__icontains=cliente) |
            Q(cliente__usuario__last_name__icontains=cliente)  |
            Q(cliente__usuario__username__icontains=cliente)
        )

    contexto = {
        'citas': citas,
        'barberos_lista': Barbero.objects.select_related('perfil__usuario').filter(estado='ACTIVO'),
        'estados': Cita.ESTADO_CHOICES,
        'filtros': {'fecha': fecha, 'estado': estado, 'barbero': barbero, 'cliente': cliente},
        'total': citas.count(),
    }
    return render(request, 'admin/citas_admin.html', contexto)


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


# ---------------------------------------------------------------------------
# 3. GESTIÓN DE HORARIOS
# ---------------------------------------------------------------------------

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

    return render(request, 'admin/horarios.html', {
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
    return render(request, 'admin/horario_form.html', {'form': form, 'accion': 'Crear'})


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
    return render(request, 'admin/horario_form.html', {'form': form, 'accion': 'Editar', 'horario': horario})


@login_required
@admin_required
def horario_eliminar(request, pk):
    """Eliminar horario."""
    horario = get_object_or_404(Horario, pk=pk)
    if request.method == 'POST':
        horario.delete()
        messages.success(request, 'Horario eliminado.')
        return redirect('horarios')
    return render(request, 'admin/confirmar_eliminar.html', {'objeto': horario, 'tipo': 'horario'})


# ---------------------------------------------------------------------------
# 4. REPORTES Y ESTADÍSTICAS
# ---------------------------------------------------------------------------

@login_required
@admin_required
def reportes_view(request):
    """Panel de reportes con datos reales del ORM."""
    from datetime import date
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)

    # Totales generales
    total_citas          = Cita.objects.count()
    citas_hoy            = Cita.objects.filter(fecha=hoy).exclude(estado='CANCELADA').count()
    citas_mes            = Cita.objects.filter(fecha__gte=inicio_mes).exclude(estado='CANCELADA').count()
    citas_finalizadas    = Cita.objects.filter(estado='FINALIZADA').count()
    citas_canceladas     = Cita.objects.filter(estado='CANCELADA').count()
    citas_pendientes     = Cita.objects.filter(estado='PENDIENTE').count()
    total_clientes       = PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count()
    total_barberos       = Barbero.objects.filter(estado='ACTIVO').count()

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
    return render(request, 'admin/reportes.html', contexto)


# ---------------------------------------------------------------------------
# 5. CONFIGURACIÓN DE BARBERÍA
# ---------------------------------------------------------------------------

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

    return render(request, 'admin/configuracion.html', {'form': form, 'config': config})
