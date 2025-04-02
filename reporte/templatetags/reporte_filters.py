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


@register.filter(name="subtract")
def subtract(value, arg):
    """Resta arg de value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name="percentage")
def percentage(value, total):
    """Calcula el porcentaje de value respecto a total"""
    try:
        if not total:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter(name="format_duration")
def format_duration(value):
    """Formatea un valor numérico de horas en formato legible"""
    try:
        hours = int(value)
        minutes = int((value - hours) * 60)
        
        if hours == 0:
            return f"{minutes} min"
        elif minutes == 0:
            return f"{hours} h"
        else:
            return f"{hours} h {minutes} min"
    except (ValueError, TypeError):
        return "N/A"


@register.filter(name="currency")
def currency(value):
    """Formatea un valor como moneda"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"
