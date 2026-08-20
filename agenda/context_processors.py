from .models import ConfiguracionBarberia, Notificacion


def config_barberia(request):
    """Inyecta la configuración de la barbería en todos los templates."""
    try:
        config = ConfiguracionBarberia.objects.get(pk=1)
    except ConfiguracionBarberia.DoesNotExist:
        config = None
    return {'config_barberia': config}


def notificaciones(request):
    """Inyecta las notificaciones no leídas del usuario autenticado en todos los templates."""
    if not request.user.is_authenticated:
        return {'notificaciones_no_leidas': [], 'total_no_leidas': 0}
    try:
        perfil = request.user.perfil
    except Exception:
        return {'notificaciones_no_leidas': [], 'total_no_leidas': 0}

    notifs = Notificacion.objects.filter(
        destinatario=perfil, leida=False
    ).select_related('cita').order_by('-creada_en')[:10]

    return {
        'notificaciones_no_leidas': notifs,
        'total_no_leidas': notifs.count(),
    }
