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
    """Dashboard principal con datos reales según el rol."""
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

    return render(request, 'perfil.html', {'form': form, 'perfil': perfil})


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
