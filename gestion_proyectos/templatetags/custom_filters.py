from django import template

register = template.Library()


@register.filter
def sub(value, arg):
    """Resta el argumento del valor."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
