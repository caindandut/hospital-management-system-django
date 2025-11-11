from django.db import models

class PatientProfiles(models.Model):
    id = models.BigAutoField(primary_key=True)
    # FK sang accounts.Users (không import chéo để tránh vòng lặp): dùng string "accounts.Users"
    user = models.OneToOneField("accounts.Users", models.CASCADE)
    cccd = models.CharField(unique=True, max_length=20)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=6, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    insurance_number = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    blood_type = models.CharField(max_length=7, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patient_profiles'

    def __str__(self): return f"{self.user.full_name} - CCCD {self.cccd}"
