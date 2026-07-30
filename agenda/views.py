"""
Vistas de BarberHub.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import RegistroForm, EditarPerfilForm, CambiarPasswordForm
from .models import PerfilUsuario


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
# Login
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Landing page (pública)
# ---------------------------------------------------------------------------

def landing_view(request):
    """Landing page pública de BarberHub."""
    from .models import Servicio, Barbero

    servicios = Servicio.objects.filter(activo=True)
    barberos  = Barbero.objects.filter(estado='ACTIVO').select_related('perfil__usuario')

    # Datos de ejemplo para barberos cuando la BD está vacía
    barberos_ejemplo = [
        ('Marco Rossi',  'Master Barber',      'https://lh3.googleusercontent.com/aida-public/AB6AXuCZ9Pdv_2dj8fz1b-WARHb8ii5mlXjLiPzFRcSf06bbUFcTgtwMf18gL1VEqdKDVIF_V_L18O_bY2-r4JWF-eVv6FUiWSq_HchdOJDxUZmGVSWxW6EkuLMz5hj6BJYDhKDbX186ox0_1HMfbtI0sKhu1fIw97s8hKx9OcVAWXVsnW7rnUyN1iMwsjCrOunsn8kjqoJYAD3HOTrxC_siLKepx9bTzeOiliBRTtQ0tEMUC8K50wj1B5en'),
        ('Alex Chen',    'Fading Expert',       'https://lh3.googleusercontent.com/aida-public/AB6AXuDSYeJ7WZl_8_8_amU8MiqqVx6wmbvkc0NTZWZnzKyjGU3iAiLeuqxEk8pWFCLh9OI5DPn_P_9TSdH9vl44pHXPfNTf8OtYQKmSD07Osod8-G3B8dYEWRv_1W2tjdbemx-apGERs-5Mq_6GOTKJsEZzSKBBTUVb1xqnxTGXWKcrfAkVsqAFOkc5wUzYGwwScJFfTVo3FlpJ4FrYpAmMCmnMPwG1_vUKBRcRGZ5LilzbGVRy1eSlr9yF'),
        ('Julian Mora',  'Classic Specialist',  'https://lh3.googleusercontent.com/aida-public/AB6AXuA7Xc84lWf2f2QW-hofJFdYeiDLU7vhG6giDhmn_WUpG4FcAcz0A2XsXgkV48QeiNS_t0kzDs-xjg1zErZTyuJ76-tOGw6K7TjGTI87OxfX6YNcQpAnGAM-G5jochtpexS1U_gn-rUZVYq98ACMhZZXLexNZL63fv6_V14KIT3ANq0kzJN5RvjaRCVw6Hn-U5Ymz-0EEDTcNcRXTxtJBKveNtPBCOsdP7pP-7lDd5UUerHbRw1urRIs'),
        ('Santi Ruiz',   'Creative Stylist',    'https://lh3.googleusercontent.com/aida-public/AB6AXuDNSz1oDcIhJ7afLxHvejHbSc-apDwmXQLKMQyPOogcI4zliGW7PxPIANNhXG5oMfQXSUABG2_TL8Er47Ct4qDZxGsLbKDi3mZ_uz4Xp3B-i8r9_f1smwK5kSdetKkypwJhqnMQVq7lPGeCAg5JfGZgY4JVKztJ5-fIpDj-Gy-JanFO7I6e6lf18qsDWkRwx6eDi3YsFTU5cGN2aYdMke2UwxIhMmMmUo2GlYYrhfJWUxQK7Xjx6f1S'),
    ]

    return render(request, 'landing.html', {
        'servicios': servicios,
        'barberos': barberos,
        'barberos_ejemplo': barberos_ejemplo,
    })


def login_view(request):
    """Página de inicio de sesión."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Verificar que el perfil esté activo
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
    """Cierra sesión."""
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
            # Crear el usuario de Django
            user = form.save(commit=False) if hasattr(form, 'save') else None

            # Como usamos un Form normal (no ModelForm de User), creamos manualmente
            from django.contrib.auth.models import User
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
            )
            # Crear el perfil asociado con rol CLIENTE
            PerfilUsuario.objects.create(
                usuario=user,
                telefono=form.cleaned_data.get('telefono', ''),
                rol='CLIENTE',
                activo=True,
            )
            # Iniciar sesión automáticamente
            login(request, user)
            messages.success(request, f'¡Cuenta creada! Bienvenido a BarberHub, {user.first_name}.')
            return redirect('dashboard')

    return render(request, 'registro.html', {'form': form})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    """Dashboard principal. Muestra contenido según el rol."""
    return render(request, 'dashboard.html')


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------

@login_required
def perfil_view(request):
    """Ver y editar perfil del usuario."""
    perfil = get_object_or_404(PerfilUsuario, usuario=request.user)

    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=perfil)
        # Actualizar campos del User (nombre, email)
        if form.is_valid():
            form.save()
            # Actualizar first_name, last_name y email en auth_user
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name  = form.cleaned_data['last_name']
            request.user.email      = form.cleaned_data['email']
            request.user.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
    else:
        # Pre-llenar campos del User en el form
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
    """Cambiar contraseña del usuario."""
    if request.method == 'POST':
        form = CambiarPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Mantener la sesión activa después de cambiar contraseña
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

    from .models import Barbero
    barberos = Barbero.objects.select_related('perfil__usuario').prefetch_related('servicios').all()

    contexto = {
        'barberos': barberos,
        'total_barberos': barberos.count(),
        'barberos_activos': barberos.filter(estado='ACTIVO').count(),
    }
    return render(request, 'barberos.html', contexto)


# ---------------------------------------------------------------------------
# Agendar Cita
# ---------------------------------------------------------------------------

@login_required
def agendar_cita_view(request):
    """Formulario para agendar una cita. Accesible para CLIENTE y ADMIN."""
    if es_barbero(request.user):
        messages.error(request, 'Los barberos no pueden agendar citas desde este módulo.')
        return redirect('dashboard')

    from .models import Servicio, Barbero
    servicios = Servicio.objects.filter(activo=True)
    barberos = Barbero.objects.filter(estado='ACTIVO').select_related('perfil__usuario')

    contexto = {
        'servicios': servicios,
        'barberos': barberos,
    }
    return render(request, 'agendar_cita.html', contexto)
