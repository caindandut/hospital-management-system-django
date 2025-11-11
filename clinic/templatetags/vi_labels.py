from django import template

register = template.Library()

APPT_LABEL_VI = {
    "PENDING": "Chờ xác nhận",
    "CONFIRMED": "Đã xác nhận", 
    "IN_PROGRESS": "Đang khám",
    "COMPLETED": "Đã khám",
    "CANCELLED": "Đã hủy",
    "NO_SHOW": "Vắng mặt",
}

INV_LABEL_VI = {
    "UNPAID": "Chờ thanh toán",
    "PAID": "Đã thanh toán",
}

@register.filter
def appt_vi(code):
    """Convert appointment status code to Vietnamese label"""
    return APPT_LABEL_VI.get((code or "").upper(), code)

@register.filter
def invoice_vi(code):
    """Convert invoice status code to Vietnamese label"""
    if not code:
        return "-"
    return INV_LABEL_VI.get(code.upper(), code)

@register.filter
def invoice_badge(code):
    """Get Bootstrap badge class for invoice status"""
    code = (code or "").upper()
    if code == "PAID":
        return "badge bg-success"
    if code == "UNPAID":
        return "badge bg-warning text-dark"
    return "badge bg-secondary"
