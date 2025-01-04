from django import template
import json

register = template.Library()


@register.filter(name="to_json")
def to_json(value):
    """Convierte un valor de Python a string JSON"""
    try:
        return json.dumps(value)
    except:
        return "{}"
