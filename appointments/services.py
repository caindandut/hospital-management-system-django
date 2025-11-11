from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db import transaction
from .models import Schedules, Appointments, AppointmentLogs
from .constants import LOG_ACTION
from emr.models import MedicalRecords, Prescriptions
from django.core.exceptions import ValidationError
from django.db.models import F
from adminpanel.models import Drug
from billing.models import Invoices, InvoiceItems
from decimal import Decimal
from django.db.models import Sum, F
from doctors.pricing import get_consultation_fee

# Statuses that don't count as occupied slots
EXCLUDE_STATUSES = ("CANCELLED", "NO_SHOW")

def log(appt, action, actor, note=None):
    """Helper function to create appointment logs"""
    AppointmentLogs.objects.create(
        appointment=appt, 
        action=action, 
        actor_user=actor, 
        note=note, 
        created_at=timezone.now()
    )

@transaction.atomic
def start_appointment(appt, actor):
    """Start an appointment: CONFIRMED → IN_PROGRESS"""
    if appt.status != "CONFIRMED":
        raise ValueError(f"Cannot start appointment with status {appt.status}")
    
    appt.status = "IN_PROGRESS"
    appt.save(update_fields=["status"])
    log(appt, LOG_ACTION["STARTED"], actor)

@transaction.atomic
def save_record(appt, data, actor):
    """Save or update medical record for appointment"""
    mr, created = MedicalRecords.objects.get_or_create(
        appointment=appt, 
        defaults={
            "symptoms": data.get("symptoms", ""),
            "diagnosis": data.get("diagnosis", ""),
            "advice": data.get("advice", ""),
            "attachments": data.get("attachments"),
            "created_at": timezone.now(),
        }
    )
    if not created:
        mr.symptoms = data.get("symptoms", "")
        mr.diagnosis = data.get("diagnosis", "")
        mr.advice = data.get("advice", "")
        mr.attachments = data.get("attachments")
        mr.save()
    
    log(appt, LOG_ACTION["UPDATED_RECORD"], actor)
    return mr

@transaction.atomic
def upsert_prescriptions(mr, items, actor):
    """Update prescriptions for medical record"""
    # items: list dict {drug, quantity, dosage, frequency, duration_days}
    Prescriptions.objects.filter(medical_record=mr).delete()
    
    to_create = []
    for item in items:
        drug = item["drug"]
        quantity = item["quantity"]
        to_create.append(Prescriptions(
            medical_record=mr,
            drug=drug,
            drug_name_snapshot=drug.name,
            unit_snapshot=drug.unit,
            unit_price_snapshot=drug.unit_price,
            dosage=item.get("dosage"),
            frequency=item.get("frequency"),
            duration_days=item.get("duration_days"),
            quantity=quantity,
        ))
    
    if to_create:
        Prescriptions.objects.bulk_create(to_create)
    
    log(mr.appointment, LOG_ACTION["UPDATED_PRESCRIPTION"], actor)

@transaction.atomic
def complete_appointment(appt, actor):
    """Complete appointment: IN_PROGRESS → COMPLETED and create invoice"""
    if appt.status != "IN_PROGRESS":
        raise ValueError(f"Cannot complete appointment with status {appt.status}")
    
    # 1) Update appointment status first to satisfy DB triggers
    appt.status = "COMPLETED"
    appt.save(update_fields=["status"])

    # 2) Get doctor's rank-based fee (normalized & safe)
    fee = get_consultation_fee(appt.doctor)
    
    # 3) Create or get invoice
    inv, created = Invoices.objects.get_or_create(
        appointment=appt,
        defaults={
            "subtotal": 0,
            "discount": 0,
            "amount_due": 0,
            "status": "UNPAID",
            "created_by_user": actor, 
            "created_at": timezone.now()
        }
    )
    
    # 4) Clear existing items (in case doctor changes prescription)
    InvoiceItems.objects.filter(invoice=inv).delete()
    
    items = []
    
    # 5) Consultation fee line
    items.append(InvoiceItems(
        invoice=inv, 
        item_type="CONSULTATION", 
        ref_id=appt.doctor_id,
        description="Phí khám bệnh", 
        unit=None,
        quantity=1, 
        unit_price=fee
    ))
    
    # 6) Drug lines
    try:
        mr = appt.medical_record
        # Before creating lines, ensure stock availability and prepare consumption list
        to_consume = []
        for prescription in mr.prescriptions.all():
            # Check stock if model has quantity field
            try:
                d = Drug.objects.get(pk=prescription.drug_id)
                qty_needed = int(prescription.quantity)
                if hasattr(d, 'quantity'):
                    if d.quantity < qty_needed:
                        raise ValidationError(f"Thuốc '{d.name}' không đủ hàng. Còn {d.quantity}, cần {qty_needed}.")
                    to_consume.append((d.pk, qty_needed))
            except Drug.DoesNotExist:
                pass
            items.append(InvoiceItems(
                invoice=inv, 
                item_type="DRUG", 
                ref_id=prescription.id,
                description=prescription.drug_name_snapshot, 
                unit=prescription.unit_snapshot,
                quantity=prescription.quantity, 
                unit_price=prescription.unit_price_snapshot
            ))
        # Consume stock atomically
        for pk, qty in to_consume:
            Drug.objects.filter(pk=pk).update(quantity=F('quantity') - qty)
    except MedicalRecords.DoesNotExist:
        pass  # No medical record yet
    
    # 7) Create invoice items
    InvoiceItems.objects.bulk_create(items)
    
    # 8) Update invoice totals using SUM(quantity * unit_price)
    from django.db.models import ExpressionWrapper, DecimalField
    total = InvoiceItems.objects.filter(invoice=inv).aggregate(
        total=Sum(ExpressionWrapper(F("quantity") * F("unit_price"),
                                    output_field=DecimalField(max_digits=12, decimal_places=2)))
    )["total"] or 0
    inv.subtotal = total
    inv.amount_due = total
    inv.save(update_fields=["subtotal", "amount_due"])
    
    # 9) Log completion
    log(appt, LOG_ACTION["COMPLETED"], actor)
    return inv

def build_available_slots(doctor_id, work_date):
    """
    Return list[dict] of slots for a doctor on a specific date.
    Each element: {"start": "HH:MM", "end": "HH:MM", "available": bool}
    - Split time based on slot_duration_minutes from each schedule
    - Exclude slots with existing appointments (status NOT IN EXCLUDE_STATUSES)
    - If today: disable slots where 'end' <= now
    - Sort by start time ascending; merge if multiple schedules
    """
    tz_now = timezone.localtime(timezone.now())
    today = tz_now.date()

    # Get OPEN schedules for the date
    schedules = Schedules.objects.filter(
        doctor_id=doctor_id, 
        work_date=work_date, 
        status="OPEN"
    )

    # Get taken appointment times
    taken_times = set(
        Appointments.objects
        .filter(
            doctor_id=doctor_id,
            appointment_at__date=work_date,
        )
        .exclude(status__in=EXCLUDE_STATUSES)
        .values_list("appointment_at__time", flat=True)
    )

    slots = []
    for schedule in schedules:
        step_minutes = schedule.slot_duration_minutes
        current = datetime.combine(work_date, schedule.start_time)
        end_time = datetime.combine(work_date, schedule.end_time)

        while current + timedelta(minutes=step_minutes) <= end_time:
            start_time = current.time()
            slot_end_time = (current + timedelta(minutes=step_minutes)).time()

            start_str = start_time.strftime("%H:%M")
            end_str = slot_end_time.strftime("%H:%M")

            available = True

            # Check if slot is already taken
            if start_time in taken_times:
                available = False

            # If today: disable slots that have already ended
            if work_date == today and timezone.localtime(timezone.now()).time() >= slot_end_time:
                available = False

            slots.append({
                "start": start_str, 
                "end": end_str, 
                "available": available
            })
            current += timedelta(minutes=step_minutes)

    # Sort and remove duplicates by start time
    seen_starts = set()
    unique_slots = []
    for slot in sorted(slots, key=lambda x: x["start"]):
        if slot["start"] not in seen_starts:
            unique_slots.append(slot)
            seen_starts.add(slot["start"])
    
    return unique_slots
