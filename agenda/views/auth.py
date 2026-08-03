"""
Vistas de autenticación - BarberHub.
Login, logout, registro y landing page.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count, Avg

from ..forms import RegistroForm
from ..models import (
    PerfilUsuario, Barbero, Servicio, Calificacion,
    ConfiguracionBarberia,
)


# ===========================================================================
# LANDING PAGE (Pública)
# ===========================================================================

def landing_view(request):
    """Landing page pública de BarberHub."""
    servicios = Servicio.objects.filter(activo=True)
    barberos = Barbero.objects.filter(estado='ACTIVO').select_related('perfil__usuario')

    # Stats reales
    total_clientes = PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count()
    total_barberos_activos = barberos.count()
    
    from ..models import Cita
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
        ('Marco Rossi', 'Master Barber', 'https://lh3.googleusercontent.com/aida-public/AB6AXuCZ9Pdv_2dj8fz1b-WARHb8ii5mlXjLiPzFRcSf06bbUFcTgtwMf18gL1VEqdKDVIF_V_L18O_bY2-r4JWF-eVv6FUiWSq_HchdOJDxUZmGVSWxW6EkuLMz5hj6BJYDhKDbX186ox0_1HMfbtI0sKhu1fIw97s8hKx9OcVAWXVsnW7rnUyN1iMwsjCrOunsn8kjqoJYAD3HOTrxC_siLKepx9bTzeOiliBRTtQ0tEMUC8K50wj1B5en'),
        ('Alex Chen', 'Fading Expert', 'https://lh3.googleusercontent.com/aida-public/AB6AXuDSYeJ7WZl_8_8_amU8MiqqVx6wmbvkc0NTZWZnzKyjGU3iAiLeuqxEk8pWFCLh9OI5DPn_P_9TSdH9vl44pHXPfNTf8OtYQKmSD07Osod8-G3B8dYEWRv_1W2tjdbemx-apGERs-5Mq_6GOTKJsEZzSKBBTUVb1xqnxTGXWKcrfAkVsqAFOkc5wUzYGwwScJFfTVo3FlpJ4FrYpAmMCmnMPwG1_vUKBRcRGZ5LilzbGVRy1eSlr9yF'),
        ('Julian Mora', 'Classic Specialist', 'https://lh3.googleusercontent.com/aida-public/AB6AXuA7Xc84lWf2f2QW-hofJFdYeiDLU7vhG6giDhmn_WUpG4FcAcz0A2XsXgkV48QeiNS_t0kzDs-xjg1zErZTyuJ76-tOGw6K7TjGTI87OxfX6YNcQpAnGAM-G5jochtpexS1U_gn-rUZVYq98ACMhZZXLexNZL63fv6_V14KIT3ANq0kzJN5RvjaRCVw6Hn-U5Ymz-0EEDTcNcRXTxtJBKveNtPBCOsdP7pP-7lDd5UUerHbRw1urRIs'),
        ('Santi Ruiz', 'Creative Stylist', 'https://lh3.googleusercontent.com/aida-public/AB6AXuDNSz1oDcIhJ7afLxHvejHbSc-apDwmXQLKMQyPOogcI4zliGW7PxPIANNhXG5oMfQXSUABG2_TL8Er47Ct4qDZxGsLbKDi3mZ_uz4Xp3B-i8r9_f1smwK5kSdetKkypwJhqnMQVq7lPGeCAg5JfGZgY4JVKztJ5-fIpDj-Gy-JanFO7I6e6lf18qsDWkRwx6eDi3YsFTU5cGN2aYdMke2UwxIhMmMmUo2GlYYrhfJWUxQK7Xjx6f1S'),
    ]

    return render(request, 'agenda/landing.html', {
        'servicios': servicios,
        'barberos': barberos,
        'barberos_ejemplo': barberos_ejemplo,
        'testimonios': testimonios,
        'total_clientes': total_clientes,
        'total_barberos_activos': total_barberos_activos,
        'total_citas': total_citas,
        'promedio_calificacion': promedio_calificacion,
        'config_barberia': ConfiguracionBarberia.objects.filter(pk=1).first(),
    })


# ===========================================================================
# LOGIN
# ===========================================================================

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
                return render(request, 'agenda/login.html')
            login(request, user)
            messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    config = ConfiguracionBarberia.objects.filter(pk=1).first()
    return render(request, 'agenda/login.html', {'config_barberia': config})


# ===========================================================================
# LOGOUT
# ===========================================================================

def logout_view(request):
    """Cerrar sesión."""
    logout(request)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('login')


# ===========================================================================
# REGISTRO DE CLIENTES
# ===========================================================================

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

    config = ConfiguracionBarberia.objects.filter(pk=1).first()
    return render(request, 'agenda/registro.html', {'form': form, 'config_barberia': config})
