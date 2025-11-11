from django.db import models

class Specialties(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'specialties'

    def __str__(self): return self.name

class Doctors(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField("accounts.Users", models.CASCADE)
    specialty = models.ForeignKey(Specialties, models.PROTECT)
    license_number = models.CharField(unique=True, max_length=100)
    years_experience = models.IntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    room_number = models.CharField(max_length=50, blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    # Rank: 'THS' (Thạc sĩ), 'TS' (Tiến sĩ), 'PGS' (Phó Giáo sư), 'GS' (Giáo sư)
    rank = models.CharField(max_length=10, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'doctors'

    def __str__(self): return f"BS. {self.user.full_name} ({self.specialty.name})"


# Managed tables for extensible doctor/user profile settings
class UserExtras(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField("accounts.Users", models.CASCADE, related_name="extras")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    address_short = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "user_extras"


class DoctorSettings(models.Model):
    id = models.BigAutoField(primary_key=True)
    doctor = models.OneToOneField("doctors.Doctors", models.CASCADE, related_name="settings")
    degree_title = models.CharField(max_length=50, blank=True, null=True)
    default_work_days = models.CharField(max_length=64, blank=True, null=True)  # e.g. Mon,Tue,Wed
    default_start_time = models.TimeField(blank=True, null=True)
    default_end_time = models.TimeField(blank=True, null=True)
    default_slot_minutes = models.IntegerField(blank=True, null=True)
    notify_web = models.BooleanField(default=True)
    notify_today_shift = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "doctor_settings"