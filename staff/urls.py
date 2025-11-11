from django.urls import path
from . import views


app_name = "staff"


urlpatterns = [
    path("profile/", views.staff_profile_self, name="profile_self"),
    path("profile/manage/", views.staff_profile_manage, name="profile_manage"),

    # Cashier
    path("cashier/", views.cashier_invoices, name="staff_cashier"),
    path("cashier/invoice/<int:pk>/", views.cashier_invoice_detail, name="staff_invoice_detail"),
    path("cashier/invoice/<int:pk>/print/", views.invoice_print, name="staff_invoice_print"),
    path("cashier/invoice/<int:pk>/pay/", views.invoice_pay_cash, name="staff_invoice_pay"),
]


