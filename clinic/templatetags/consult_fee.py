from django import template
from doctors.pricing import get_consultation_fee

register = template.Library()


@register.filter
def consultation_fee_vnd(doctor):
    try:
        fee = get_consultation_fee(doctor)
        return f"{fee:,.0f}".replace(",", ".") + " VND"
    except Exception:
        return "0 VND"


