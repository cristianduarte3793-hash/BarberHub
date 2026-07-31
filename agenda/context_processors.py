from .models import ConfiguracionBarberia


def config_barberia(request):
    """Inyecta la configuración de la barbería en todos los templates."""
    try:
        config = ConfiguracionBarberia.objects.get(pk=1)
    except ConfiguracionBarberia.DoesNotExist:
        config = None
    return {'config_barberia': config}
