from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("debug/", views.debug_dashboard, name="debug_dashboard"),
    path("appointments/", views.appointments, name="appointments"),
    path("appointments/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("doctors/", views.admin_doctors_list, name="admin_doctors_list"),
    path("doctors/create/", views.admin_doctors_create, name="admin_doctors_create"),
    path("doctors/<int:doctor_id>/toggle/", views.admin_doctor_toggle_active, name="admin_doctor_toggle_active"),
    path("doctors/<int:doctor_id>/update/", views.admin_doctor_update, name="admin_doctor_update"),
path("patients/", views.patients_list, name="admin_patients_list"),
path("patients/create/", views.patient_create, name="admin_patient_create"),
path("patients/<int:pk>/edit/", views.patient_edit, name="admin_patient_edit"),
path("patients/<int:pk>/update/", views.admin_patient_update, name="admin_patient_update"),
path("patients/<int:pk>/delete/", views.admin_patient_delete, name="admin_patient_delete"),
path("staff/", views.admin_staff_list, name="admin_staff_list"),
path("staff/<int:pk>/update/", views.admin_staff_update, name="admin_staff_update"),
    path("invoices/", views.invoices, name="invoices"),
    path('billing/invoices/', views.invoice_list, name='admin_invoice_list'),
    path('billing/invoice/<int:pk>/', views.invoice_detail, name='admin_invoice_detail'),
    path('invoices/<int:pk>/print/', views.invoice_print, name='admin_invoice_print'),
    path('billing/invoice/<int:pk>/cash/', views.invoice_cash, name='admin_invoice_cash'),
    path("settings/", views.settings_view, name="settings"),

    # specialties
    path("settings/specialty/create/", views.specialty_create, name="specialty_create"),
    path("settings/specialty/<int:pk>/update/", views.specialty_update, name="specialty_update"),
    path("settings/specialty/<int:pk>/delete/", views.specialty_delete, name="specialty_delete"),

    # rank fees
    path("settings/rankfee/create/", views.rankfee_create, name="rankfee_create"),
    path("settings/rankfee/<int:pk>/update/", views.rankfee_update, name="rankfee_update"),
    path("settings/rankfee/<int:pk>/delete/", views.rankfee_delete, name="rankfee_delete"),

    # drugs
    path("settings/drug/create/", views.drug_create, name="drug_create"),
    path("settings/drug/<int:pk>/update/", views.drug_update, name="drug_update"),
    path("settings/drug/<int:pk>/delete/", views.drug_delete, name="drug_delete"),

    # users
    path("settings/user/create/", views.user_create, name="user_create"),
    path("settings/user/<int:pk>/update/", views.user_update, name="user_update"),
    path("settings/user/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("settings/user/<int:pk>/delete/", views.user_delete, name="user_delete"),
]
