from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Doctor Schedule Management URLs
    path('doctor/schedule/', views.schedule_index, name='schedule_index'),
    path('doctor/schedule/create/', views.schedule_create, name='schedule_create'),
    path('doctor/schedule/<int:schedule_id>/open/', views.schedule_open, name='schedule_open'),
    path('doctor/schedule/<int:schedule_id>/close/', views.schedule_close, name='schedule_close'),
    path('doctor/appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    
    # Doctor Workflow URLs
    path("doctor/today/", views.doctor_today, name="appt_doctor_today"),
    path("doctor/pending/", views.pending_appointments, name="pending_appointments"),
    path("<int:pk>/start/", views.appt_start, name="appt_start"),
    path("<int:pk>/record/", views.appt_record, name="appt_record"),
    path("<int:pk>/prescribe/", views.appt_prescribe, name="appt_prescribe"),
    path("<int:pk>/complete/", views.appt_complete, name="appt_complete"),
    
    # Patient Booking URLs
    path('new/', views.new_step1, name='new_step1'),
    path('new/slots/', views.new_step2, name='new_step2'),
    path('new/confirm/', views.new_step3, name='new_step3'),
    path('my/', views.my_appointments, name='my_appointments'),
    path('<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),
]
