from django import template

register = template.Library()

@register.filter(name="sub")
def sub(value, arg):
    """Resta el argumento del valor."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name="mul")
def mul(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0