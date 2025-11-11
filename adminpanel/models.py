from django.db import models

class Specialty(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = "specialties"
    
    def __str__(self): 
        return self.name

class DoctorRankFee(models.Model):
    RANK_CHOICES = [
        ("BS","Bác sĩ"),
        ("ThS","Thạc sĩ"),
        ("TS","Tiến sĩ"),
        ("PGS","Phó giáo sư"),
        ("GS","Giáo sư"),
    ]
    id = models.BigAutoField(primary_key=True)
    rank = models.CharField(max_length=10, choices=RANK_CHOICES, unique=True)
    default_fee = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        managed = False
        db_table = "doctor_rank_fees"
    
    def __str__(self): 
        return f"{self.rank} - {self.default_fee}"

class Drug(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    is_active = models.IntegerField()  # 1/0
    
    class Meta:
        managed = False
        db_table = "drugs"
    
    def __str__(self): 
        return self.name

class UserLite(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=7)  # ADMIN/DOCTOR/STAFF/PATIENT
    is_active = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    class Meta:
        managed = False
        db_table = "users"
    
    def __str__(self): 
        return f"{self.full_name} ({self.role})"
