from django.db import models
from core.choices import ScheduleStatus, ApptStatus, Source

class Schedules(models.Model):
    id = models.BigAutoField(primary_key=True)
    doctor = models.ForeignKey("doctors.Doctors", models.CASCADE, related_name="schedules")
    work_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.IntegerField()
    status = models.CharField(max_length=6, choices=ScheduleStatus.choices)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'schedules'
        unique_together = (('doctor','work_date','start_time','end_time'),)

class Appointments(models.Model):
    id = models.BigAutoField(primary_key=True)
    patient = models.ForeignKey("patients.PatientProfiles", models.CASCADE, related_name="appointments")
    doctor  = models.ForeignKey("doctors.Doctors", models.PROTECT, related_name="appointments")
    schedule = models.ForeignKey(Schedules, models.PROTECT, related_name="appointments")
    appointment_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=ApptStatus.choices)
    reason = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=7, choices=Source.choices)
    chatbot_session = models.ForeignKey("chatbot.ChatbotSessions", models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'appointments'
        unique_together = (('doctor','appointment_at'),)

class AppointmentLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    appointment = models.ForeignKey(Appointments, models.CASCADE, related_name="logs")
    action = models.CharField(max_length=32)  # CREATE/CONFIRMED/IN_PROGRESS/COMPLETED/CANCELLED/NO_SHOW/UPDATED_*
    actor_user = models.ForeignKey("accounts.Users", models.DO_NOTHING, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'appointment_logs'
