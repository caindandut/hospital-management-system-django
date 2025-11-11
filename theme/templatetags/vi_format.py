from django import template

register = template.Library()

_VI_WEEKDAYS = {
    0: "Thứ 2",
    1: "Thứ 3",
    2: "Thứ 4",
    3: "Thứ 5",
    4: "Thứ 6",
    5: "Thứ 7",
    6: "Chủ nhật",
}


@register.filter
def weekday_vi(value):
    try:
        dow = value.weekday()
        return _VI_WEEKDAYS.get(dow, "")
    except Exception:
        return ""


@register.filter
def vnd(amount):
    try:
        n = float(amount)
        s = f"{n:,.0f}".replace(",", ".")
        return f"{s} VND"
    except Exception:
        return ""


@register.filter
def add_thousand_separator(amount):
    """Add thousand separator to numbers (Vietnamese format with dots)"""
    try:
        n = float(amount)
        return f"{n:,.0f}".replace(",", ".")
    except Exception:
        return "0"


@register.filter
def mul(value, arg):
    """Multiply two values"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


