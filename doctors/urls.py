from django.urls import path
from . import views

app_name = "doctors"

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("profile/password/", views.change_password, name="doctor_change_password"),
    path("visit-summary/<int:appointment_id>/", views.doctor_visit_summary, name="visit_summary"),
    path("visit-summary/<int:appointment_id>/print/", views.doctor_visit_summary_print, name="visit_summary_print"),
    path("visit-summary/<int:appointment_id>/pdf/", views.doctor_visit_summary_pdf, name="visit_summary_pdf"),
    path("print-prescription/<int:appointment_id>/", views.doctor_print_prescription, name="print_prescription"),
    path("confirm-appointment/<int:pk>/", views.doctor_confirm_appointment, name="confirm_appointment"),
]


