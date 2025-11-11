from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from clinic.decorators import doctor_or_staff_required, staff_required, doctor_required
from accounts.models import Users
from accounts.forms import ChangePasswordForm
from accounts.passwords import check_password, hash_password
from .models import Doctors, UserExtras, DoctorSettings
from .forms import (
    DoctorBasicForm,
    UserExtrasForm,
    DoctorProfessionalForm,
    DoctorSettingsForm,
)
from .pricing import normalize_rank, get_consultation_fee
from appointments.models import Appointments
from patients.models import PatientProfiles
from emr.models import MedicalRecords, Prescriptions
from decimal import Decimal


def _get_ext_user(request):
    email = getattr(request.user, "email", None)
    if not email:
        return None
    return Users.objects.filter(email=email).first()


@login_required
def profile(request):
    ext_user = _get_ext_user(request)
    if not ext_user:
        messages.error(request, "Không tìm thấy tài khoản ngoài.")
        return redirect("theme:home")

    doctor = Doctors.objects.select_related("user", "specialty").filter(user=ext_user).first()
    extras, _ = UserExtras.objects.get_or_create(user=ext_user)
    settings, _ = DoctorSettings.objects.get_or_create(doctor=doctor) if doctor else (None, None)
    is_doctor_role = getattr(ext_user, 'role', '') == 'DOCTOR'

    if request.method == "POST":
        which = request.POST.get("which")
        if which == "basic":
            form_basic = DoctorBasicForm(request.POST, instance=ext_user)
            form_basic.fields["email"].initial = ext_user.email
            form_extras = UserExtrasForm(request.POST, request.FILES, instance=extras)

            basic_ok = form_basic.is_valid()
            extras_ok = form_extras.is_valid()

            if basic_ok:
                form_basic.save()
            else:
                messages.error(request, "Vui lòng kiểm tra lại thông tin cơ bản.")

            if extras_ok:
                form_extras.save()
            else:
                # Fallback: if only avatar file is provided, save it directly
                if request.FILES.get("avatar"):
                    try:
                        extras.avatar = request.FILES["avatar"]
                        extras.save(update_fields=["avatar"])
                        extras_ok = True
                    except Exception:
                        pass
                if not extras_ok:
                    messages.error(request, "Vui lòng kiểm tra lại ảnh đại diện/địa chỉ liên hệ.")

            if basic_ok or extras_ok:
                messages.success(request, "Đã lưu thông tin cơ bản")
                return redirect("doctors:profile")
        elif which == "professional" and doctor:
            form_prof = DoctorProfessionalForm(request.POST, instance=doctor)
            # Allow updating degree_title (from settings form) when saving professional tab
            form_settings_inline = DoctorSettingsForm(request.POST, instance=settings) if settings else None
            if form_prof.is_valid() and (form_settings_inline is None or form_settings_inline.is_valid()):
                doc = form_prof.save(commit=False)
                # Normalize rank when saving
                raw_rank = request.POST.get("rank") or request.POST.get("degree")
                if raw_rank:
                    doc.rank = normalize_rank(raw_rank)
                doc.save()
                if form_settings_inline:
                    # Only save degree_title; avoid changing other settings inadvertently
                    settings.degree_title = form_settings_inline.cleaned_data.get("degree_title")
                    settings.save(update_fields=["degree_title"])
                messages.success(request, "Đã lưu thông tin hành nghề")
                return redirect("doctors:profile")
        elif which == "create_doctor" and not doctor and is_doctor_role:
            # Tạo mới bản ghi Doctors liên kết với external user
            form_prof = DoctorProfessionalForm(request.POST)
            if form_prof.is_valid():
                new_doc = form_prof.save(commit=False)
                new_doc.user = ext_user
                # Normalize rank when creating
                raw_rank = request.POST.get("rank") or request.POST.get("degree")
                if raw_rank:
                    new_doc.rank = normalize_rank(raw_rank)
                new_doc.save()
                messages.success(request, "Đã tạo hồ sơ bác sĩ.")
                return redirect("doctors:profile")
        elif which == "room_quick" and doctor:
            # Quick update for room_number from sidebar
            room_val = request.POST.get("room_number", "").strip()
            doctor.room_number = room_val or None
            doctor.save(update_fields=["room_number"])
            messages.success(request, "Đã lưu thông tin nhanh")
            return redirect("doctors:profile")
    
    form_basic = DoctorBasicForm(instance=ext_user)
    form_basic.fields["email"].initial = ext_user.email
    form_extras = UserExtrasForm(instance=extras)
    form_prof = DoctorProfessionalForm(instance=doctor) if doctor else DoctorProfessionalForm()

    return render(request, "doctors/profile.html", {
        "form_basic": form_basic,
        "form_extras": form_extras,
        "form_prof": form_prof,
        "has_doctor": bool(doctor),
        "is_doctor_role": is_doctor_role,
        # Extra context for header/sidebar rendering
        "user": ext_user,  # Add user context
        "doctor": doctor,
        "doctor_profile": doctor,  # alias to keep template compatibility
        "specialty_name": getattr(doctor.specialty, "name", None) if doctor else None,
        "room_number": getattr(doctor, "room_number", None) if doctor else None,
    })


@login_required
def change_password(request):
    ext_user = _get_ext_user(request)
    if not ext_user:
        messages.error(request, "Không tìm thấy tài khoản ngoài.")
        return redirect("theme:home")

    if getattr(ext_user, 'role', '') not in ('DOCTOR', 'ADMIN'):
        messages.error(request, "Bạn không có quyền.")
        return redirect("theme:home")

    if request.method == "POST":
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            if not check_password(form.cleaned_data["current_password"], ext_user.password_hash or ""):
                messages.error(request, "Mật khẩu hiện tại không đúng.")
            else:
                ext_user.password_hash = hash_password(form.cleaned_data["new_password1"])
                try:
                    from django.utils import timezone
                    ext_user.updated_at = timezone.now()
                except Exception:
                    pass
                ext_user.save(update_fields=["password_hash", "updated_at"] if hasattr(ext_user, 'updated_at') else ["password_hash"])
                messages.success(request, "Đổi mật khẩu thành công.")
                return redirect("doctors:doctor_change_password")
    else:
        form = ChangePasswordForm()

    return render(request, "doctors/change_password.html", {"form": form})

@login_required
def doctor_visit_summary(request, appointment_id):
    """Generate and display visit summary report for completed appointment"""
    # Get the appointment and related data
    appointment = get_object_or_404(
        Appointments.objects.select_related(
            'patient__user', 'doctor__user', 'doctor__specialty'
        ),
        id=appointment_id,
        status='COMPLETED'
    )
    
    # Security check: only the doctor who handled the appointment can view it
    ext_user = _get_ext_user(request)
    if not ext_user or appointment.doctor.user != ext_user:
        messages.error(request, "Bạn không có quyền xem phiếu khám này.")
        return redirect("theme:home")
    
    # Get medical record and prescriptions
    try:
        medical_record = appointment.medical_record
        prescriptions = medical_record.prescriptions.all()
    except MedicalRecords.DoesNotExist:
        medical_record = None
        prescriptions = []
    
    # Calculate consultation fee based on doctor's rank
    consultation_fee = get_consultation_fee(appointment.doctor)
    
    # Calculate total medication cost
    medication_total = sum(
        prescription.quantity * prescription.unit_price_snapshot
        for prescription in prescriptions
    )
    
    # Calculate grand total
    grand_total = consultation_fee + medication_total
    
    context = {
        'appointment': appointment,
        'patient': appointment.patient,
        'doctor': appointment.doctor,
        'medical_record': medical_record,
        'prescriptions': prescriptions,
        'consultation_fee': consultation_fee,
        'medication_total': medication_total,
        'grand_total': grand_total,
    }
    
    return render(request, 'doctors/doctor_visit_summary.html', context)


@login_required
def doctor_print_prescription(request, appointment_id):
    """Print prescription for completed appointment"""
    # Get the appointment and related data
    appointment = get_object_or_404(
        Appointments.objects.select_related(
            'patient__user', 'doctor__user', 'doctor__specialty'
        ),
        id=appointment_id,
        status='COMPLETED'
    )
    
    # Security check: only the doctor who handled the appointment can view it
    ext_user = _get_ext_user(request)
    if not ext_user or appointment.doctor.user != ext_user:
        messages.error(request, "Bạn không có quyền in toa thuốc này.")
        return redirect("theme:home")
    
    # Get medical record and prescriptions
    try:
        medical_record = appointment.medical_record
        prescriptions = medical_record.prescriptions.select_related('drug').all().order_by('id')
    except MedicalRecords.DoesNotExist:
        medical_record = None
        prescriptions = []
    
    context = {
        'appointment': appointment,
        'patient': appointment.patient,
        'doctor': appointment.doctor,
        'medical_record': medical_record,
        'prescriptions': prescriptions,
    }
    
    return render(request, 'doctors/prescription_print.html', context)


@login_required
def doctor_visit_summary_print(request, appointment_id):
    """Print-optimized version of visit summary"""
    # Get the appointment and related data
    appointment = get_object_or_404(
        Appointments.objects.select_related(
            'patient__user', 'doctor__user', 'doctor__specialty'
        ),
        id=appointment_id,
        status='COMPLETED'
    )
    
    # Security check: only the doctor who handled the appointment can view it
    ext_user = _get_ext_user(request)
    if not ext_user or appointment.doctor.user != ext_user:
        messages.error(request, "Bạn không có quyền xem phiếu khám này.")
        return redirect("theme:home")
    
    # Get medical record and prescriptions
    try:
        medical_record = appointment.medical_record
        prescriptions = medical_record.prescriptions.all()
    except MedicalRecords.DoesNotExist:
        medical_record = None
        prescriptions = []
    
    # Calculate consultation fee based on doctor's rank
    consultation_fee = get_consultation_fee(appointment.doctor)
    
    # Calculate total medication cost
    medication_total = sum(
        prescription.quantity * prescription.unit_price_snapshot
        for prescription in prescriptions
    )
    
    # Calculate grand total
    grand_total = consultation_fee + medication_total
    
    context = {
        'appointment': appointment,
        'patient': appointment.patient,
        'doctor': appointment.doctor,
        'medical_record': medical_record,
        'prescriptions': prescriptions,
        'consultation_fee': consultation_fee,
        'medication_total': medication_total,
        'grand_total': grand_total,
    }
    
    return render(request, 'doctors/doctor_visit_summary_print.html', context)


@login_required
def doctor_visit_summary_pdf(request, appointment_id):
    """Generate PDF version of visit summary report"""
    # Lazy imports to keep optional dependencies optional
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    
    # Get the same data as the HTML view
    appointment = get_object_or_404(
        Appointments.objects.select_related(
            'patient__user', 'doctor__user', 'doctor__specialty'
        ),
        id=appointment_id,
        status='COMPLETED'
    )
    
    # Security check: only the doctor who handled the appointment can view it
    ext_user = _get_ext_user(request)
    if not ext_user or appointment.doctor.user != ext_user:
        messages.error(request, "Bạn không có quyền xem phiếu khám này.")
        return redirect("theme:home")
    
    # Get medical record and prescriptions
    try:
        medical_record = appointment.medical_record
        prescriptions = medical_record.prescriptions.all()
    except MedicalRecords.DoesNotExist:
        medical_record = None
        prescriptions = []
    
    # Calculate consultation fee based on doctor's rank
    consultation_fee = get_consultation_fee(appointment.doctor)
    
    # Calculate total medication cost
    medication_total = sum(
        prescription.quantity * prescription.unit_price_snapshot
        for prescription in prescriptions
    )
    
    # Calculate grand total
    grand_total = consultation_fee + medication_total
    
    context = {
        'appointment': appointment,
        'patient': appointment.patient,
        'doctor': appointment.doctor,
        'medical_record': medical_record,
        'prescriptions': prescriptions,
        'consultation_fee': consultation_fee,
        'medication_total': medication_total,
        'grand_total': grand_total,
        'is_pdf': True,  # Flag to modify template for PDF
    }
    
    # Render HTML string once, reuse across engines
    html_string = render_to_string('doctors/doctor_visit_summary_pdf.html', context, request=request)

    filename = f"phieu_kham_{appointment.patient.user.full_name}_{appointment.appointment_at.strftime('%d%m%Y')}.pdf"

    # 1) Try WeasyPrint first (best quality if system libs available)
    try:
        from weasyprint import HTML  # type: ignore
        pdf_bytes = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception:
        # 2) Fallback to xhtml2pdf (pure Python, works well on Windows)
        try:
            from io import BytesIO
            from xhtml2pdf import pisa  # type: ignore
            result = BytesIO()
            pisa_status = pisa.CreatePDF(src=html_string, dest=result, encoding='utf-8')
            if pisa_status.err:
                messages.error(request, "Xuất PDF thất bại.")
                return redirect("doctors:visit_summary", appointment_id=appointment_id)
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            messages.error(request, f"PDF export không khả dụng: {str(e)}")
            return redirect("doctors:visit_summary", appointment_id=appointment_id)


@login_required
@doctor_required
def doctor_confirm_appointment(request, pk):
    """Doctor confirm a pending appointment"""
    from django.utils import timezone
    from appointments.models import Appointments, AppointmentLogs
    from core.choices import ApptStatus
    
    if request.method != 'POST':
        messages.error(request, "Phương thức không được phép.")
        return redirect("theme:home")
    
    # Get current doctor
    ext_user = _get_ext_user(request)
    if not ext_user:
        messages.error(request, "Không tìm thấy tài khoản ngoài.")
        return redirect("theme:home")
    
    doctor = Doctors.objects.select_related("user", "specialty").filter(user=ext_user).first()
    if not doctor:
        messages.error(request, "Không tìm thấy thông tin bác sĩ.")
        return redirect("theme:home")
    
    # Get appointment
    try:
        appointment = Appointments.objects.get(id=pk, doctor=doctor)
    except Appointments.DoesNotExist:
        messages.error(request, "Không tìm thấy lịch hẹn.")
        return redirect("theme:home")
    
    # Check if appointment is pending
    if appointment.status != ApptStatus.PENDING:
        messages.error(request, "Chỉ có thể xác nhận lịch hẹn đang chờ xác nhận.")
        return redirect("theme:home")
    
    # Update status to CONFIRMED
    appointment.status = ApptStatus.CONFIRMED
    appointment.updated_at = timezone.now()
    appointment.save()
    
    # Log the action
    AppointmentLogs.objects.create(
        appointment=appointment,
        action='CONFIRMED',
        actor_user=ext_user,
        note='Bác sĩ xác nhận lịch hẹn',
        created_at=timezone.now()
    )
    
    messages.success(request, f"Đã xác nhận lịch hẹn của {appointment.patient.user.full_name}.")
    return redirect("theme:home")
