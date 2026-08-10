"""
Vistas de autenticación - BarberHub.
Login, logout, registro y landing page.
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from ..forms import RegistroForm
from ..models import (
    Barbero, Calificacion, Cita, ConfiguracionBarberia,
    PerfilUsuario, Servicio,
)


# ===========================================================================
# LANDING PAGE (Pública)
# ===========================================================================

def landing_view(request):
    """Landing page pública de BarberHub."""
    servicios = Servicio.objects.filter(activo=True)
    barberos  = Barbero.objects.filter(estado='ACTIVO').select_related(
        'perfil__usuario', 'perfil'
    )

    total_clientes        = PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count()
    total_barberos_activos = barberos.count()
    total_citas           = Cita.objects.filter(estado='FINALIZADA').count()

    resultado = Calificacion.objects.aggregate(prom=Avg('puntuacion'))
    promedio_calificacion = (
        round(resultado['prom'], 1) if resultado['prom'] else None
    )

    testimonios = (
        Calificacion.objects.filter(comentario__isnull=False)
        .exclude(comentario='')
        .select_related('cliente__usuario')
        .order_by('-creado_en')[:3]
    )

    # Solo se muestran barberos reales de la BD; sin datos de ejemplo falsos.

    return render(request, 'agenda/landing.html', {
        'servicios':              servicios,
        'barberos':               barberos,
        'testimonios':            testimonios,
        'total_clientes':         total_clientes,
        'total_barberos_activos': total_barberos_activos,
        'total_citas':            total_citas,
        'promedio_calificacion':  promedio_calificacion,
        'config_barberia':        ConfiguracionBarberia.objects.filter(pk=1).first(),
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
        user     = authenticate(request, username=username, password=password)

        if user is not None:
            # Verificar el flag de activación del perfil propio
            if hasattr(user, 'perfil') and not user.perfil.activo:
                messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
                return render(request, 'agenda/login.html')
            login(request, user)
            messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}.')
            return redirect('dashboard')

        messages.error(request, 'Usuario o contraseña incorrectos.')

    # config_barberia viene del context processor; se pasa explícitamente
    # solo aquí porque login.html no extiende base.html.
    config = ConfiguracionBarberia.objects.filter(pk=1).first()
    return render(request, 'agenda/login.html', {'config_barberia': config})


# ===========================================================================
# LOGOUT  — solo POST para evitar CSRF logout via GET
# ===========================================================================

@require_POST
def logout_view(request):
    """Cerrar sesión. Requiere POST para prevenir ataques de logout por GET."""
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
            # transaction.atomic garantiza que User y PerfilUsuario
            # se creen juntos o ninguno — sin usuarios huérfanos.
            with transaction.atomic():
                user = User.objects.create_user(
                    username   = form.cleaned_data['username'],
                    email      = form.cleaned_data['email'],
                    password   = form.cleaned_data['password1'],
                    first_name = form.cleaned_data['first_name'],
                    last_name  = form.cleaned_data['last_name'],
                )
                PerfilUsuario.objects.create(
                    usuario  = user,
                    telefono = form.cleaned_data.get('telefono', ''),
                    rol      = 'CLIENTE',
                    activo   = True,
                )
                # Sincronizar User.is_active con PerfilUsuario.activo
                # desde el inicio (ambos True al registrarse).
                user.is_active = True
                user.save(update_fields=['is_active'])

            login(request, user)
            messages.success(request, f'¡Cuenta creada! Bienvenido a BarberHub, {user.first_name}.')
            return redirect('dashboard')

    config = ConfiguracionBarberia.objects.filter(pk=1).first()
    return render(request, 'agenda/registro.html', {'form': form, 'config_barberia': config})
