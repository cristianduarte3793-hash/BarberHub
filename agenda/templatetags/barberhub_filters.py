from django import template

register = template.Library()


@register.filter
def cop(value):
    """Formatea un número como precio en pesos colombianos. Ej: 35000 → $35.000"""
    try:
        valor = int(float(value))
        # Formato: $ 35.000 COP
        return f'$ {valor:,}'.replace(',', '.') + ' COP'
    except (ValueError, TypeError):
        return value
