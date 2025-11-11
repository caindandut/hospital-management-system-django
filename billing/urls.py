"""
URLs for billing app
"""
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Legacy route: redirect to staff board
    
    
    # Invoice management
    path('invoice/create-from-appt/<int:appointment_id>/', views.invoice_create_from_appt, name='invoice_create_from_appt'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:invoice_id>/pay-cash/', views.invoice_pay_cash, name='invoice_pay_cash'),
    path('invoice/<int:invoice_id>/print/', views.invoice_print, name='invoice_print'),
    path('invoice/list/', views.invoice_list, name='invoice_list'),
]
