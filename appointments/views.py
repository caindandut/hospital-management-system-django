from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import IntegrityError
from django.utils import timezone
from datetime import datetime, date, time
from .models import Schedules, Appointments
from doctors.models import Doctors
from accounts.models import Users
from core.choices import ScheduleStatus, Role
from clinic.decorators import role_required, patient_required, doctor_or_staff_required


# -----------------------------------------------------------------------------
# Helpers to resolve role and external user for the current request
# -----------------------------------------------------------------------------
def _get_external_user(request):
    try:
        email = getattr(request.user, 'email', None)
        if not email:
            return None
        return Users.objects.filter(email=email).first()
    except Exception:
        return None


def _get_user_role(request):
    ext = _get_external_user(request)
    return getattr(ext, 'role', None)


def _local_day_range(d: date):
    """Return timezone-aware UTC datetimes for start/end of local day."""
    try:
        from zoneinfo import ZoneInfo
        local_tz = ZoneInfo('Asia/Ho_Chi_Minh')
        utc_tz = ZoneInfo('UTC')
        start = datetime.combine(d, time.min, tzinfo=local_tz).astimezone(utc_tz)
        end = datetime.combine(d, time.max, tzinfo=local_tz).astimezone(utc_tz)
        return start, end
    except Exception:
        # Fallback: assume server timezone is correct
        start = timezone.make_aware(datetime.combine(d, time.min))
        end = timezone.make_aware(datetime.combine(d, time.max))
        return start, end


@doctor_or_staff_required
def schedule_index(request):
    """Hiển thị form tạo khung lịch và danh sách lịch làm việc"""
    user = request.user
    
    # Lấy danh sách bác sĩ cho dropdown (chỉ hiển thị nếu user là STAFF)
    doctors = []
    if _get_user_role(request) == Role.STAFF:
        doctors = Doctors.objects.select_related('user').all()
    
    # Lấy danh sách lịch làm việc
    schedules = Schedules.objects.select_related('doctor__user').all()
    
    # Nếu user là DOCTOR, chỉ hiển thị lịch của chính mình
    if _get_user_role(request) == Role.DOCTOR:
        try:
            ext_user = _get_external_user(request)
            doctor = Doctors.objects.get(user=ext_user)
            schedules = schedules.filter(doctor=doctor)
        except Doctors.DoesNotExist:
            schedules = Schedules.objects.none()
    
    # Xử lý filter
    filter_date = request.GET.get('filter_date')
    filter_doctor = request.GET.get('filter_doctor')
    
    if filter_date:
        schedules = schedules.filter(work_date=filter_date)
    if filter_doctor and _get_user_role(request) == Role.STAFF:
        schedules = schedules.filter(doctor_id=filter_doctor)
    
    context = {
        'doctors': doctors,
        'schedules': schedules,
        'user_role': getattr(user, 'role', None),
        'filter_date': filter_date,
        'filter_doctor': filter_doctor,
    }
    
    return render(request, 'appointments/schedule_index.html', context)


@doctor_or_staff_required
def today_visits(request):
    """Danh sách bệnh nhân khám hôm nay cho bác sĩ hoặc nhân viên"""
    today = timezone.localdate()
    start_dt, end_dt = _local_day_range(today)

    # Lọc theo bác sĩ nếu là DOCTOR
    doctor_filter = {}
    ext_user = _get_external_user(request)
    if ext_user and _get_user_role(request) == Role.DOCTOR:
        try:
            doc = Doctors.objects.filter(user=ext_user).first()
            if doc:
                doctor_filter = {"doctor": doc}
        except Exception:
            doctor_filter = {}

    appts = (Appointments.objects
             .select_related("patient__user", "doctor__user", "schedule")
             .filter(appointment_at__range=(start_dt, end_dt), **doctor_filter)
             .order_by("appointment_at"))

    context = {
        "appointments": appts,
        "today": today,
    }
    return render(request, 'appointments/today_visits.html', context)


@doctor_or_staff_required
def appointment_detail(request, appointment_id: int):
    appt = get_object_or_404(
        Appointments.objects.select_related(
            "patient__user", "doctor__user", "schedule"
        ),
        id=appointment_id,
    )

    # Quyền xem: bác sĩ chỉ xem được lịch của mình
    ext_user = _get_external_user(request)
    if _get_user_role(request) == Role.DOCTOR and appt.doctor.user != ext_user:
        messages.error(request, 'Bạn không có quyền truy cập chức năng này.')
        return redirect('appointments:appt_doctor_today')

    return render(request, 'appointments/appointment_detail.html', {"appointment": appt})

@doctor_or_staff_required
def schedule_create(request):
    """Xử lý tạo khung lịch mới"""
    if request.method != 'POST':
        return redirect('appointments:schedule_index')
    
    user = request.user
    
    try:
        # Lấy dữ liệu từ form
        work_date = request.POST.get('work_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        slot_duration = request.POST.get('slot_duration')
        doctor_id = request.POST.get('doctor_id')
        
        # Validate dữ liệu
        if not all([work_date, start_time, end_time, slot_duration]):
            messages.error(request, 'Vui lòng điền đầy đủ thông tin.')
            return redirect('appointments:schedule_index')
        
        # Parse datetime
        work_date = datetime.strptime(work_date, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = datetime.strptime(end_time, '%H:%M').time()
        slot_duration = int(slot_duration)
        
        # Validate thời gian
        if start_time >= end_time:
            messages.error(request, 'Giờ bắt đầu phải nhỏ hơn giờ kết thúc.')
            return redirect('appointments:schedule_index')
        
        # Xác định doctor_id
        if _get_user_role(request) == Role.DOCTOR:
            # Nếu user là DOCTOR, chỉ tạo lịch cho chính mình
            try:
                ext_user = _get_external_user(request)
                doctor = Doctors.objects.get(user=ext_user)
                doctor_id = doctor.id
            except Doctors.DoesNotExist:
                messages.error(request, 'Không tìm thấy thông tin bác sĩ.')
                return redirect('appointments:schedule_index')
        elif _get_user_role(request) == Role.STAFF:
            # Nếu user là STAFF, sử dụng doctor_id từ form
            if not doctor_id:
                messages.error(request, 'Vui lòng chọn bác sĩ.')
                return redirect('appointments:schedule_index')
            doctor_id = int(doctor_id)
        else:
            messages.error(request, 'Bạn không có quyền tạo lịch làm việc.')
            return redirect('appointments:schedule_index')
        
        # Tạo schedule mới
        schedule = Schedules.objects.create(
            doctor_id=doctor_id,
            work_date=work_date,
            start_time=start_time,
            end_time=end_time,
            slot_duration_minutes=slot_duration,
            status=ScheduleStatus.OPEN,
            created_at=timezone.now()
        )
        
        messages.success(request, f'Đã tạo khung lịch thành công cho ngày {work_date.strftime("%d/%m/%Y")}.')
        
    except ValueError as e:
        messages.error(request, 'Dữ liệu không hợp lệ.')
    except IntegrityError:
        messages.error(request, 'Khung lịch này đã tồn tại cho bác sĩ được chọn.')
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
    
    return redirect('appointments:schedule_index')


@doctor_or_staff_required
def schedule_open(request, schedule_id):
    """Cập nhật trạng thái schedule thành OPEN"""
    if request.method != 'POST':
        return redirect('appointments:schedule_index')
    
    user = request.user
    
    try:
        schedule = get_object_or_404(Schedules, id=schedule_id)
        
        # Kiểm tra quyền: DOCTOR chỉ có thể sửa lịch của mình, STAFF có thể sửa tất cả
        if _get_user_role(request) == Role.DOCTOR:
            try:
                ext_user = _get_external_user(request)
                doctor = Doctors.objects.get(user=ext_user)
                if schedule.doctor != doctor:
                    messages.error(request, 'Bạn chỉ có thể sửa lịch của chính mình.')
                    return redirect('appointments:schedule_index')
            except Doctors.DoesNotExist:
                messages.error(request, 'Không tìm thấy thông tin bác sĩ.')
                return redirect('appointments:schedule_index')
        
        schedule.status = ScheduleStatus.OPEN
        schedule.save()
        
        messages.success(request, 'Đã mở khung lịch thành công.')
        
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
    
    return redirect('appointments:schedule_index')


@doctor_or_staff_required
def schedule_close(request, schedule_id):
    """Cập nhật trạng thái schedule thành CLOSED"""
    if request.method != 'POST':
        return redirect('appointments:schedule_index')
    
    user = request.user
    
    try:
        schedule = get_object_or_404(Schedules, id=schedule_id)
        
        # Kiểm tra quyền: DOCTOR chỉ có thể sửa lịch của mình, STAFF có thể sửa tất cả
        if _get_user_role(request) == Role.DOCTOR:
            try:
                ext_user = _get_external_user(request)
                doctor = Doctors.objects.get(user=ext_user)
                if schedule.doctor != doctor:
                    messages.error(request, 'Bạn chỉ có thể sửa lịch của chính mình.')
                    return redirect('appointments:schedule_index')
            except Doctors.DoesNotExist:
                messages.error(request, 'Không tìm thấy thông tin bác sĩ.')
                return redirect('appointments:schedule_index')
        
        schedule.status = ScheduleStatus.CLOSED
        schedule.save()
        
        messages.success(request, 'Đã đóng khung lịch thành công.')
        
    except Exception as e:
        messages.error(request, f'Có lỗi xảy ra: {str(e)}')
    
    return redirect('appointments:schedule_index')


# =============================================================================
# PATIENT BOOKING VIEWS
# =============================================================================

from django.views.decorators.cache import never_cache

@never_cache
@patient_required
def new_step1(request):
    """Bước 1: Chọn chuyên khoa & bác sĩ"""
    from django.core.paginator import Paginator
    from doctors.models import Specialties
    
    # Lấy danh sách chuyên khoa
    specialties = Specialties.objects.all()
    
    # Xử lý POST - chọn bác sĩ
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        if doctor_id:
            return redirect(f'/appointments/new/slots/?doctor_id={doctor_id}')
        else:
            messages.error(request, 'Vui lòng chọn bác sĩ.')
    
    # Xử lý GET - hiển thị form và danh sách bác sĩ
    selected_specialty_id = request.GET.get('specialty_id')
    
    # Lấy danh sách bác sĩ và annotate giá theo rank từ database
    from django.db import models
    from django.db.models import Case, When, IntegerField, Value, CharField, F, Subquery, OuterRef
    from adminpanel.models import DoctorRankFee
    
    # Subquery để lấy giá từ DoctorRankFee
    rank_fee_subquery = Subquery(
        DoctorRankFee.objects.filter(rank=OuterRef('settings__degree_title'))
        .values('default_fee')[:1]
    )
    
    degree_title = F('settings__degree_title')
    fee_order = Case(
        When(settings__degree_title__isnull=False, then=rank_fee_subquery),
        default=Value(200000),
        output_field=IntegerField(),
    )
    degree_label = Case(
        When(settings__degree_title="ThS", then=Value("ThS")),
        When(settings__degree_title="TS",  then=Value("TS")),
        When(settings__degree_title="PGS", then=Value("PGS")),
        When(settings__degree_title="GS",  then=Value("GS")),
        default=Value("BS"),
        output_field=CharField(),
    )

    doctors_query = (
        Doctors.objects.select_related('user', 'specialty', 'settings')
        .annotate(effective_fee=fee_order, degree_label=degree_label)
        .order_by('effective_fee', 'user__full_name')
    )
    
    if selected_specialty_id:
        doctors_query = doctors_query.filter(specialty_id=selected_specialty_id)
    
    # Phân trang
    paginator = Paginator(doctors_query, 6)
    page_number = request.GET.get('page')
    doctors = paginator.get_page(page_number)
    
    context = {
        'title': 'Đặt lịch hẹn - Bước 1',
        'step': 1,
        'specialties': specialties,
        'doctors': doctors,
        'selected_specialty_id': selected_specialty_id,
    }
    
    # Debug info
    print(f"DEBUG: Specialties count: {specialties.count()}")
    print(f"DEBUG: Doctors count: {doctors.paginator.count}")
    print(f"DEBUG: Selected specialty: {selected_specialty_id}")
    
    return render(request, 'appointments/new_step1.html', context)


# Legacy function - moved to services.py
# Kept for compatibility with step3 view that still references it
def build_available_slots_legacy(doctor_id, date):
    """Legacy function - use services.build_available_slots instead"""
    from .services import build_available_slots
    slots = build_available_slots(doctor_id, date)
    
    # Convert to old format for step3 compatibility
    legacy_slots = []
    schedule = None
    
    try:
        schedule = Schedules.objects.filter(
            doctor_id=doctor_id,
            work_date=date,
            status='OPEN'
        ).first()
    except:
        pass
    
    for slot in slots:
        from datetime import datetime
        slot_time = datetime.strptime(slot['start'], '%H:%M').time()
        slot_datetime = datetime.combine(date, slot_time)
        
        legacy_slots.append({
            'time': slot_time,
            'datetime': slot_datetime,
            'available': slot['available'],
            'formatted_time': slot['start']
        })
    
    return legacy_slots, schedule


@never_cache
@patient_required
def new_step2(request):
    """Bước 2: Chọn ngày & slot trống"""
    from datetime import datetime, date, timedelta
    from .services import build_available_slots
    
    # Lấy doctor_id từ query string hoặc POST
    doctor_id = request.GET.get('doctor_id')
    if not doctor_id and request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        
    if not doctor_id:
        messages.error(request, 'Vui lòng chọn bác sĩ trước.')
        return redirect('appointments:new_step1')
    
    try:
        doctor_id = int(doctor_id)
        doctor = Doctors.objects.select_related('user', 'specialty', 'user__extras').get(id=doctor_id)
    except (Doctors.DoesNotExist, ValueError):
        messages.error(request, 'Không tìm thấy bác sĩ.')
        return redirect('appointments:new_step1')
    
    # Date restrictions: today to today+5
    tz_now = timezone.localtime(timezone.now())
    today = tz_now.date()
    max_date = today + timedelta(days=5)
    
    # Xử lý POST - chọn slot
    if request.method == 'POST':
        selected_date = request.POST.get('date')
        appointment_time = request.POST.get('appointment_time')
        
        if not selected_date or not appointment_time:
            messages.error(request, 'Vui lòng chọn ngày và giờ khám.')
        else:
            try:
                parsed_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
                
                # Validate date range
                if parsed_date < today or parsed_date > max_date:
                    messages.error(request, f'Chỉ có thể đặt lịch từ hôm nay đến {max_date.strftime("%d/%m/%Y")}.')
                    return redirect(f'{request.path}?doctor_id={doctor_id}&date={selected_date}')
                
                # Re-validate slot availability
                slots = build_available_slots(doctor_id, parsed_date)
                slot_valid = any(s["start"] == appointment_time and s["available"] for s in slots)
                
                if not slot_valid:
                    messages.error(request, 'Khung giờ không còn khả dụng, vui lòng chọn lại.')
                    return redirect(f'{request.path}?doctor_id={doctor_id}&date={selected_date}')
                
                # OK → redirect to step 3
                return redirect(f'/appointments/new/confirm/?doctor_id={doctor_id}&date={selected_date}&time={appointment_time}')
            except ValueError:
                messages.error(request, 'Ngày không hợp lệ.')
    
    # Xử lý GET - hiển thị form và slots
    selected_date = request.GET.get('date')
    
    # Parse and validate selected date
    if selected_date:
        try:
            parsed_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            # Enforce date range
            if parsed_date < today:
                parsed_date = today
            elif parsed_date > max_date:
                parsed_date = max_date
        except ValueError:
            parsed_date = today
    else:
        parsed_date = today
    
    # Get available slots
    slots = build_available_slots(doctor_id, parsed_date)
    
    context = {
        'title': 'Đặt lịch hẹn - Bước 2',
        'step': 2,
        'doctor': doctor,
        'doctor_id': doctor_id,
        'date': parsed_date,
        'min_date': today,
        'max_date': max_date,
        'slots': slots,
        'room_number': getattr(doctor, 'room_number', None),
    }
    return render(request, 'appointments/new_step2.html', context)


@never_cache
@patient_required
def new_step3(request):
    """Bước 3: Xác nhận & tạo lịch hẹn"""
    from datetime import datetime, date, time, timedelta
    from .models import Appointments, AppointmentLogs
    from patients.models import PatientProfiles
    from core.choices import ApptStatus, Source
    from .services import build_available_slots
    
    # Lấy tham số từ query string
    doctor_id = request.GET.get('doctor_id')
    appointment_date = request.GET.get('date')
    appointment_time = request.GET.get('time')
    
    # Validate tham số
    if not all([doctor_id, appointment_date, appointment_time]):
        messages.error(request, 'Thiếu thông tin đặt lịch. Vui lòng chọn lại.')
        return redirect('appointments:new_step1')
    
    try:
        doctor_id = int(doctor_id)
        doctor = Doctors.objects.select_related('user', 'specialty').get(id=doctor_id)
        parsed_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        parsed_time = datetime.strptime(appointment_time, '%H:%M').time()
    except (Doctors.DoesNotExist, ValueError):
        messages.error(request, 'Thông tin không hợp lệ.')
        return redirect('appointments:new_step1')
    
    # Validate date range (today to today+5)
    tz_now = timezone.localtime(timezone.now())
    today = tz_now.date()
    max_date = today + timedelta(days=5)
    
    if parsed_date < today or parsed_date > max_date:
        messages.error(request, f'Chỉ có thể đặt lịch từ hôm nay đến {max_date.strftime("%d/%m/%Y")}.')
        return redirect('appointments:new_step1')
    
    # If today: check time hasn't passed
    if parsed_date == today and timezone.localtime(timezone.now()).time() >= parsed_time:
        messages.error(request, 'Không thể đặt lịch cho thời gian đã qua.')
        return redirect(f'/appointments/new/slots/?doctor_id={doctor_id}&date={appointment_date}')
    
    # Re-validate slot availability
    slots = build_available_slots(doctor_id, parsed_date)
    slot_valid = any(s["start"] == appointment_time and s["available"] for s in slots)
    
    if not slot_valid:
        messages.error(request, 'Khung giờ không còn khả dụng, vui lòng chọn lại.')
        return redirect(f'/appointments/new/slots/?doctor_id={doctor_id}&date={appointment_date}')
    
    # Update variables for consistency
    appointment_date = parsed_date
    appointment_time = parsed_time
    
    # Kiểm tra user có PatientProfile chưa
    if not request.user.is_authenticated:
        messages.error(request, 'Vui lòng đăng nhập để đặt lịch hẹn.')
        return redirect('theme:login')
    
    try:
        # Tìm Users instance từ Django User (request.user)
        from accounts.models import Users
        
        # Tìm Users instance bằng email (cách chính)
        users_instance = Users.objects.get(email=request.user.email)
        
        # Tìm PatientProfiles
        patient_profile = PatientProfiles.objects.get(user=users_instance)
        
    except (PatientProfiles.DoesNotExist, Users.DoesNotExist, ValueError) as e:
        print(f"DEBUG: Error finding patient profile: {e}")
        messages.error(request, 'Vui lòng cập nhật thông tin bệnh nhân trước khi đặt lịch.')
        return redirect('theme:profile')
    
    # Xử lý POST - tạo appointment
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, 'Vui lòng nhập lý do khám.')
        else:
            # Re-check slot availability
            slots, schedule = build_available_slots_legacy(doctor_id, appointment_date)
            selected_slot_available = any(
                slot['formatted_time'] == appointment_time.strftime('%H:%M') and slot['available']
                for slot in slots
            )
            
            if not selected_slot_available:
                messages.error(request, 'Slot đã đầy, vui lòng chọn lại.')
                return redirect(f'/appointments/new/slots/?doctor_id={doctor_id}&date={appointment_date.strftime("%Y-%m-%d")}')
            
            # Tìm schedule chứa khoảng thời gian
            try:
                schedule = Schedules.objects.get(
                    doctor_id=doctor_id,
                    work_date=appointment_date,
                    start_time__lte=appointment_time,
                    end_time__gt=appointment_time,
                    status='OPEN'
                )
            except Schedules.DoesNotExist:
                messages.error(request, 'Không tìm thấy lịch làm việc phù hợp.')
                return redirect(f'/appointments/new/slots/?doctor_id={doctor_id}&date={appointment_date.strftime("%Y-%m-%d")}')
            
            # Tạo appointment (chống race-condition)
            appointment_datetime = datetime.combine(appointment_date, appointment_time)
            try:
                appointment = Appointments.objects.create(
                    patient=patient_profile,
                    doctor=doctor,
                    schedule=schedule,
                    appointment_at=appointment_datetime,
                    status=ApptStatus.PENDING,
                    reason=reason,
                    source=Source.PORTAL,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
            except IntegrityError:
                messages.error(request, 'Slot vừa được đặt bởi người khác. Vui lòng chọn giờ khác.')
                return redirect(f'/appointments/new/slots/?doctor_id={doctor_id}&date={appointment_date.strftime("%Y-%m-%d")}')

            # Ghi log
            try:
                AppointmentLogs.objects.create(
                    appointment=appointment,
                    action='CREATE',
                    actor_user=users_instance,  # Sử dụng Users instance thay vì request.user
                    note=f'Đặt lịch hẹn qua portal - {reason}',
                    created_at=timezone.now()
                )
            except Exception:
                pass
            
            messages.success(request, 'Đặt lịch thành công!')
            return redirect('appointments:my_appointments')
    
    # GET - hiển thị form xác nhận
    # Tìm schedule để lấy thông tin slot duration
    try:
        schedule = Schedules.objects.get(
            doctor_id=doctor_id,
            work_date=appointment_date,
            start_time__lte=appointment_time,
            end_time__gt=appointment_time,
            status='OPEN'
        )
        slot_duration = schedule.slot_duration_minutes
    except Schedules.DoesNotExist:
        messages.error(request, 'Không tìm thấy lịch làm việc phù hợp.')
        return redirect(f'/appointments/new/slots/?doctor_id={doctor_id}&date={appointment_date.strftime("%Y-%m-%d")}')
    
    # Compute effective fee based on degree_title
    from django.db.models import Case, When, IntegerField, Value
    fee_case = Case(
        When(settings__degree_title="ThS", then=Value(200000)),
        When(settings__degree_title="TS",  then=Value(500000)),
        When(settings__degree_title="PGS", then=Value(900000)),
        When(settings__degree_title="GS",  then=Value(1200000)),
        default=Value(200000),
        output_field=IntegerField(),
    )
    try:
        doc_with_fee = Doctors.objects.select_related('settings').annotate(effective_fee=fee_case).get(id=doctor_id)
        effective_fee = doc_with_fee.effective_fee
    except Exception:
        effective_fee = None

    context = {
        'title': 'Đặt lịch hẹn - Bước 3',
        'step': 3,
        'doctor': doctor,
        'appointment_date': appointment_date,
        'appointment_time': appointment_time,
        'slot_duration': slot_duration,
        'doctor_id': doctor_id,
        'room_number': getattr(doctor, 'room_number', None),
        'effective_fee': effective_fee,
        # Thêm thông tin bệnh nhân để hiển thị ở bước xác nhận
        'patient_user': users_instance,
        'patient_profile': patient_profile,
    }
    return render(request, 'appointments/new_step3.html', context)


@patient_required
def my_appointments(request):
    """Danh sách lịch hẹn của bệnh nhân"""
    from django.core.paginator import Paginator
    from django.conf import settings
    from .models import Appointments
    
    if not request.user.is_authenticated:
        messages.error(request, 'Vui lòng đăng nhập để xem lịch hẹn.')
        return redirect('theme:login')
    
    try:
        # Tìm Users instance từ Django User
        from accounts.models import Users
        users_instance = Users.objects.get(email=request.user.email)
        
        # Tìm PatientProfiles
        from patients.models import PatientProfiles
        patient_profile = PatientProfiles.objects.get(user=users_instance)
        
        # Lấy danh sách appointments
        from django.db.models import Case, When, IntegerField, Value
        fee_case = Case(
            When(doctor__settings__degree_title="ThS", then=Value(200000)),
            When(doctor__settings__degree_title="TS",  then=Value(500000)),
            When(doctor__settings__degree_title="PGS", then=Value(900000)),
            When(doctor__settings__degree_title="GS",  then=Value(1200000)),
            default=Value(200000),
            output_field=IntegerField(),
        )

        appointments = Appointments.objects.filter(
            patient=patient_profile
        ).select_related(
            'doctor__user', 'doctor__specialty', 'schedule'
        ).annotate(
            effective_fee=fee_case
        ).order_by('-appointment_at')
        
        # Pagination
        paginator = Paginator(appointments, 10)  # 10 appointments per page
        page_number = request.GET.get('page')
        appointments_page = paginator.get_page(page_number)
        
        # Settings cho thời gian hủy hẹn (phút)
        cancel_before_minutes = getattr(settings, 'APPOINTMENT_CANCEL_BEFORE_MINUTES', 120)
        
        context = {
            'title': 'Lịch hẹn của tôi',
            'appointments': appointments_page,
            'cancel_before_minutes': cancel_before_minutes,
        }
        
    except (Users.DoesNotExist, PatientProfiles.DoesNotExist) as e:
        print(f"DEBUG: Error finding patient profile: {e}")
        messages.error(request, 'Vui lòng cập nhật thông tin bệnh nhân.')
        return redirect('theme:profile')
    
    return render(request, 'appointments/my.html', context)


@patient_required
def cancel_appointment(request, pk):
    """Hủy lịch hẹn (POST only)"""
    from django.conf import settings
    from datetime import datetime, timedelta
    from .models import Appointments, AppointmentLogs
    
    if not request.user.is_authenticated:
        messages.error(request, 'Vui lòng đăng nhập.')
        return redirect('theme:login')
    
    if request.method != 'POST':
        return redirect('appointments:my_appointments')
    
    try:
        # Tìm Users instance từ Django User
        from accounts.models import Users
        users_instance = Users.objects.get(email=request.user.email)
        
        # Tìm PatientProfiles
        from patients.models import PatientProfiles
        patient_profile = PatientProfiles.objects.get(user=users_instance)
        
        # Tìm appointment
        appointment = Appointments.objects.select_related(
            'doctor__user', 'doctor__specialty'
        ).get(id=pk, patient=patient_profile)
        
        # Kiểm tra trạng thái có thể hủy
        if appointment.status not in ['PENDING', 'CONFIRMED']:
            messages.error(request, 'Không thể hủy lịch hẹn với trạng thái này.')
            return redirect('appointments:my_appointments')
        
        # Kiểm tra thời gian hủy hẹn
        cancel_before_minutes = getattr(settings, 'APPOINTMENT_CANCEL_BEFORE_MINUTES', 120)
        now = timezone.now()
        cancel_deadline = appointment.appointment_at - timedelta(minutes=cancel_before_minutes)
        
        if now > cancel_deadline:
            messages.warning(request, f'Không thể hủy lịch hẹn. Phải hủy trước {cancel_before_minutes} phút giờ hẹn.')
            return redirect('appointments:my_appointments')
        
        # Cập nhật trạng thái
        appointment.status = 'CANCELLED'
        appointment.updated_at = timezone.now()
        appointment.save()
        
        # Ghi log
        AppointmentLogs.objects.create(
            appointment=appointment,
            action='CANCEL',
            actor_user=users_instance,
            note=f'Hủy lịch hẹn bởi bệnh nhân',
            created_at=timezone.now()
        )
        
        messages.success(request, 'Đã hủy lịch hẹn thành công.')
        
    except (Users.DoesNotExist, PatientProfiles.DoesNotExist) as e:
        print(f"DEBUG: Error finding patient profile: {e}")
        messages.error(request, 'Vui lòng cập nhật thông tin bệnh nhân.')
        return redirect('theme:profile')
    except Appointments.DoesNotExist:
        messages.error(request, 'Không tìm thấy lịch hẹn hoặc bạn không có quyền hủy lịch hẹn này.')
    except Exception as e:
        print(f"DEBUG: Error canceling appointment: {e}")
        messages.error(request, 'Có lỗi xảy ra khi hủy lịch hẹn.')
    
    return redirect('appointments:my_appointments')


# =============================================================================
# DOCTOR WORKFLOW VIEWS
# =============================================================================

from clinic.decorators import doctor_owns_appointment
from .services import start_appointment, save_record, upsert_prescriptions, complete_appointment
from emr.models import Drugs

@role_required(["DOCTOR", "ADMIN"])
def doctor_today(request):
    """Danh sách ca hôm nay của bác sĩ hiện tại"""
    today = timezone.localdate()
    start_dt, end_dt = _local_day_range(today)
    
    # Get external user
    ext_user = _get_external_user(request)
    if not ext_user:
        messages.error(request, "Không tìm thấy thông tin người dùng.")
        return redirect("theme:home")
    
    # Build query for today's appointments with invoice status
    from django.db.models import OuterRef, Subquery
    from billing.models import Invoices
    
    inv_sub = Invoices.objects.filter(appointment_id=OuterRef("pk")).values("status")[:1]
    qs = (Appointments.objects
          .select_related("doctor__user", "doctor", "doctor__specialty", "schedule", "patient__user")
          .filter(doctor__user_id=ext_user.id, appointment_at__range=(start_dt, end_dt))
          .annotate(invoice_status=Subquery(inv_sub))
          .order_by("appointment_at"))
    
    # Build simple stats for today
    from django.db.models import Count, Q
    stats = qs.aggregate(
        total=Count("id"),
        confirmed=Count("id", filter=Q(status="CONFIRMED")),
        completed=Count("id", filter=Q(status="COMPLETED")),
    )
    
    return render(request, "appointments/doctor_today.html", {"appts": qs, "stats": stats})

@doctor_owns_appointment
def appt_start(request, pk):
    """Start appointment: CONFIRMED → CHECKED_IN"""
    if request.method == "POST":
        try:
            ext_user = _get_external_user(request)
            start_appointment(request.appt, ext_user)
            messages.success(request, "Đã bắt đầu khám.")
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {str(e)}")
    
    return redirect("appointments:appt_doctor_today")

@doctor_owns_appointment
def appt_record(request, pk):
    """Medical record form for appointment"""
    appt = request.appt
    
    if request.method == "POST":
        data = {
            "symptoms": request.POST.get("symptoms", ""),
            "diagnosis": request.POST.get("diagnosis", ""),
            "advice": request.POST.get("advice", ""),
            # attachments: để sau (JSON)
        }
        try:
            ext_user = _get_external_user(request)
            save_record(appt, data, ext_user)
            messages.success(request, "Đã lưu hồ sơ.")
            return redirect("appointments:appt_record", pk=pk)
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {str(e)}")
    
    # Get medical record if exists
    try:
        mr = appt.medical_record
    except:
        mr = None
    
    return render(request, "appointments/doctor_record.html", {"appt": appt, "mr": mr})

@doctor_owns_appointment
def appt_prescribe(request, pk):
    """Prescription form for appointment"""
    appt = request.appt
    
    # Get medical record
    try:
        mr = appt.medical_record
    except:
        mr = None
        messages.error(request, "Vui lòng tạo hồ sơ khám trước khi kê đơn.")
        return redirect("appointments:appt_record", pk=pk)
    
    if request.method == "POST":
        # Parse prescription data from form
        items = []
        drug_ids = request.POST.getlist("drug_id")
        quantities = request.POST.getlist("quantity")
        dosages = request.POST.getlist("dosage")
        frequencies = request.POST.getlist("frequency")
        durations = request.POST.getlist("duration_days")
        
        for i, drug_id in enumerate(drug_ids):
            if drug_id:  # Skip empty rows
                try:
                    drug = Drugs.objects.get(pk=drug_id)
                    items.append({
                        "drug": drug,
                        "quantity": float(quantities[i]) if quantities[i] else 0,
                        "dosage": dosages[i] if i < len(dosages) else "",
                        "frequency": frequencies[i] if i < len(frequencies) else "",
                        "duration_days": int(durations[i]) if i < len(durations) and durations[i] else None,
                    })
                except (Drugs.DoesNotExist, ValueError, IndexError):
                    continue
        
        try:
            ext_user = _get_external_user(request)
            upsert_prescriptions(mr, items, ext_user)
            messages.success(request, "Đã lưu đơn thuốc.")
            return redirect("appointments:appt_prescribe", pk=pk)
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {str(e)}")
    
    # Get active drugs and existing prescriptions
    drugs = Drugs.objects.filter(is_active=1).order_by("name")
    prescriptions = mr.prescriptions.all() if mr else []
    
    return render(request, "appointments/doctor_prescribe.html", {
        "appt": appt,
        "drugs": drugs,
        "prescriptions": prescriptions,
        "mr": mr
    })

@doctor_owns_appointment
def appt_complete(request, pk):
    """Complete appointment: CHECKED_IN → COMPLETED"""
    if request.method == "POST":
        try:
            ext_user = _get_external_user(request)
            inv = complete_appointment(request.appt, ext_user)
            messages.success(request, "Đã hoàn tất ca. Hóa đơn đã tạo (chưa thanh toán).")
            # Redirect to visit summary instead of doctor today page
            return redirect("doctors:visit_summary", appointment_id=pk)
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {str(e)}")
    
    return redirect("appointments:appt_doctor_today")


@role_required(["DOCTOR", "ADMIN"])
def pending_appointments(request):
    """Danh sách lịch hẹn chờ xác nhận của bác sĩ"""
    from django.db.models import Count, Q
    
    # Get external user
    ext_user = _get_external_user(request)
    if not ext_user:
        messages.error(request, "Không tìm thấy thông tin người dùng.")
        return redirect("theme:home")
    
    # Get pending, confirmed and cancelled appointments for this doctor
    appointments = (Appointments.objects
                   .select_related("doctor__user", "doctor", "doctor__specialty", "schedule", "patient__user")
                   .filter(doctor__user_id=ext_user.id)
                   .filter(status__in=['PENDING', 'CONFIRMED', 'CANCELLED'])
                   .order_by('appointment_at'))
    
    # Build stats
    stats = appointments.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status="PENDING")),
        confirmed=Count("id", filter=Q(status="CONFIRMED")),
        cancelled=Count("id", filter=Q(status="CANCELLED")),
    )
    
    context = {
        'appointments': appointments,
        'stats': stats,
    }
    
    return render(request, "appointments/pending_appointments.html", context)
