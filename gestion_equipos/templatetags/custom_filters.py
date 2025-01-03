from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name="replace")
def replace(value, old_new):
    """
    Replaces all occurrences of old with new in value
    Usage: {{ value|replace:" _" }}
    """
    if not value:
        return value
    return value.replace(" ", "_")
