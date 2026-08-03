"""
Utilidades y helpers para BarberHub.
Funciones reutilizables en toda la aplicación.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


# ===========================================================================
# HELPERS DE PERMISOS
# ===========================================================================

def es_admin(user):
    """Verifica si el usuario tiene rol de ADMIN."""
    return hasattr(user, 'perfil') and user.perfil.rol == 'ADMIN'


def es_barbero(user):
    """Verifica si el usuario tiene rol de BARBERO."""
    return hasattr(user, 'perfil') and user.perfil.rol == 'BARBERO'


def es_cliente(user):
    """Verifica si el usuario tiene rol de CLIENTE."""
    return hasattr(user, 'perfil') and user.perfil.rol == 'CLIENTE'


# ===========================================================================
# DECORADORES
# ===========================================================================

def admin_required(view_func):
    """Decorador que restringe acceso solo a administradores."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not es_admin(request.user):
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def barbero_required(view_func):
    """Decorador que restringe acceso solo a barberos."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not es_barbero(request.user):
            messages.error(request, 'Acceso restringido a barberos.')
            return redirect('dashboard')
        # Verificar que tenga objeto Barbero asociado
        try:
            _ = request.user.perfil.barbero
        except Exception:
            messages.error(request, 'Tu cuenta de barbero no está configurada. Contacta al administrador.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def cliente_required(view_func):
    """Decorador que restringe acceso solo a clientes."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not es_cliente(request.user):
            messages.error(request, 'Acceso restringido a clientes.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
