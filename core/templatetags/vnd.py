from django import template

register = template.Library()


@register.filter
def vnd(value):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "0 VND"
    return f"{n:,.0f} VND".replace(",", ".")


@register.filter
def lookup(dictionary, key):
    """Template filter to lookup a key in a dictionary"""
    try:
        return dictionary[key]
    except (KeyError, TypeError):
        return None


