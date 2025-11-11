from django.db import models


class StaffProfiles(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("accounts.Users", models.CASCADE, unique=True)
    employee_code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    cccd = models.CharField(max_length=20, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    shift = models.CharField(max_length=20, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "staff_profiles"


