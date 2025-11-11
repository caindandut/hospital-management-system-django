from django.db import models

class MedicalRecords(models.Model):
    id = models.BigAutoField(primary_key=True)
    appointment = models.OneToOneField("appointments.Appointments", models.CASCADE, related_name="medical_record")
    symptoms = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    advice = models.TextField(blank=True, null=True)
    attachments = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'medical_records'

class Drugs(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'drugs'

    def __str__(self): return self.name

class Prescriptions(models.Model):
    id = models.BigAutoField(primary_key=True)
    medical_record = models.ForeignKey(MedicalRecords, models.CASCADE, related_name="prescriptions")
    drug = models.ForeignKey(Drugs, models.DO_NOTHING)
    drug_name_snapshot = models.CharField(max_length=255)
    unit_snapshot = models.CharField(max_length=50)
    unit_price_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    dosage = models.CharField(max_length=100, blank=True, null=True)
    frequency = models.CharField(max_length=100, blank=True, null=True)
    duration_days = models.IntegerField(blank=True, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prescriptions'
