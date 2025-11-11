from django.db import models
from core.choices import Role

class Users(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.CharField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=7, choices=Role.choices)
    is_active = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'users'

    def __str__(self): 
        return f"{self.full_name} <{self.email}>"
    
    def get_full_name(self):
        """Return full_name for compatibility with Django User model"""
        return self.full_name or self.email
    
    @property
    def username(self):
        """Provide username property for compatibility with Django templates"""
        return self.email


class PatientProfile(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE, db_column='user_id')
    cccd = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=6, choices=[('MALE','MALE'),('FEMALE','FEMALE'),('OTHER','OTHER')], blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    insurance_number = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    blood_type = models.CharField(max_length=8, choices=[('A','A'),('B','B'),('AB','AB'),('O','O'),('UNKNOWN','UNKNOWN')], default='UNKNOWN')
    allergies = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False  # mapped to existing MySQL table
        db_table = 'patient_profiles'

    def __str__(self):
        return f"PatientProfile(user_id={self.user_id})"