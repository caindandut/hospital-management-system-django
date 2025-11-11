from django import template

register = template.Library()


@register.filter
def vnd(amount):
    try:
        return f"{float(amount):,.0f}".replace(",", ".") + " VND"
    except Exception:
        return "0 VND"

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
    """
    Return Vietnamese weekday name for a date/datetime.
    Monday=0 .. Sunday=6
    """
    try:
        dow = value.weekday()
        return _VI_WEEKDAYS.get(dow, "")
    except Exception:
        return ""


@register.filter
def vnd(amount):
    """Format number as Vietnamese Dong, e.g., 200.000 VND"""
    try:
        n = float(amount)
        s = f"{n:,.0f}".replace(",", ".")
        return f"{s} VND"
    except Exception:
        return ""


