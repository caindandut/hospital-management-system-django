from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.urls import reverse
from django.db.models import Count, Sum, Q, F, DateTimeField, DecimalField
from django.utils.timezone import localdate, now, timedelta, make_aware
from datetime import datetime, time as dt_time
from django.db.models.functions import Cast
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from clinic.decorators import role_required
from core.choices import Role
from appointments.models import Appointments, Schedules, AppointmentLogs
from billing.models import Invoices, Payments, InvoicePrintLogs, InvoiceItems
from django.views.decorators.http import require_POST
from django.db.models.functions import Coalesce, TruncDate
from django.db.models import Value as V, DecimalField
from doctors.models import Doctors, DoctorSettings, UserExtras
from accounts.models import Users
from patients.models import PatientProfiles
from accounts.models import Users as AccountsUsers
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.hashers import make_password
from staff.models import StaffProfiles
from chatbot.models import ChatbotSessions, ChatbotMessages
from .models import Specialty, DoctorRankFee, Drug, UserLite
from .forms import SpecialtyForm, RankFeeForm, DrugForm, UserRoleForm, CreateUserForm, UpdateUserForm
@login_required
@role_required([Role.ADMIN])
def admin_doctors_list(request):
    q = (request.GET.get("q", "") or "").strip()
    sp = request.GET.get("specialty", "")
    st = request.GET.get("status", "")
    qs = Doctors.objects.select_related("user", "specialty").all()
    if q:
        qs = qs.filter(Q(user__full_name__icontains=q) | Q(user__email__icontains=q) | Q(license_number__icontains=q))
    if sp:
        qs = qs.filter(specialty_id=sp)
    if st == "active":
        qs = qs.filter(user__is_active=1)
    elif st == "inactive":
        qs = qs.filter(user__is_active=0)
    specialties = Specialty.objects.order_by("name")
    rank_fees = DoctorRankFee.objects.all()
    
    # Create fee mapping for JavaScript and template
    fee_mapping = {}
    rank_fee_dict = {}
    for rank_fee in rank_fees:
        fee_mapping[rank_fee.rank] = int(rank_fee.default_fee)
        rank_fee_dict[rank_fee.rank] = rank_fee.default_fee
    
    return render(request, "adminpanel/doctors_list.html", {
        "doctors": qs.order_by("user__full_name"),
        "specialties": specialties,
        "rank_fees": rank_fees,
        "fee_mapping": fee_mapping,
        "rank_fee_dict": rank_fee_dict,
        "q": q, "sp": sp, "st": st,
    })


@login_required
@role_required([Role.ADMIN])
@transaction.atomic
def admin_doctors_create(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "msg": "Invalid method"}, status=405)

    try:
        full_name = (request.POST.get("full_name", "") or "").strip()
        email = (request.POST.get("email", "") or "").strip().lower()
        phone = (request.POST.get("phone", "") or "").strip()
        specialty_id = request.POST.get("specialty_id")
        rank = request.POST.get("rank", "")
        license_number = (request.POST.get("license_number", "") or "").strip()
        years_experience = int(request.POST.get("years_experience") or 0)
        room_number = (request.POST.get("room_number", "") or "").strip()
        fee_raw = (request.POST.get("consultation_fee") or "0").replace(".", "").replace(",", "")
        try:
            consultation_fee = float(fee_raw or 0)
        except Exception:
            consultation_fee = 0
        password = request.POST.get("password", "").strip()
        password2 = request.POST.get("password2", "").strip()

        if not full_name or not email or not specialty_id or not password:
            return JsonResponse({"ok": False, "msg": "Vui lòng nhập đầy đủ thông tin bắt buộc."}, status=400)
        
        if password != password2:
            return JsonResponse({"ok": False, "msg": "Mật khẩu xác nhận không khớp."}, status=400)
        
        if len(password) < 6:
            return JsonResponse({"ok": False, "msg": "Mật khẩu phải có ít nhất 6 ký tự."}, status=400)
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"ok": False, "msg": "Email không hợp lệ."}, status=400)
        if Users.objects.filter(email=email).exists():
            return JsonResponse({"ok": False, "msg": "Email đã tồn tại."}, status=400)
        if license_number and Doctors.objects.filter(license_number=license_number).exists():
            return JsonResponse({"ok": False, "msg": "Số giấy phép đã tồn tại."}, status=400)

        now = timezone.now()
        user = Users.objects.create(
            email=email,
            full_name=full_name,
            phone=phone or None,
            role="DOCTOR",
            is_active=1,  # Always active by default
            password_hash=make_password(password),
            created_at=now,
            updated_at=now,
        )
        Doctors.objects.create(
            user=user,
            specialty_id=specialty_id,
            license_number=license_number or None,
            years_experience=years_experience,
            room_number=room_number or None,
            consultation_fee=consultation_fee,
            rank=rank or None,
        )
        messages.success(request, f"Đã tạo bác sĩ {full_name} thành công.")
        return JsonResponse({"ok": True})
    except Exception as e:
        print(f"Error creating doctor: {e}")
        return JsonResponse({"ok": False, "msg": f"Có lỗi xảy ra: {str(e)}"}, status=500)


@login_required
@role_required([Role.ADMIN])
def admin_doctor_toggle_active(request, doctor_id):
    d = get_object_or_404(Doctors.objects.select_related("user"), pk=doctor_id)
    d.user.is_active = 0 if d.user.is_active else 1
    d.user.save(update_fields=["is_active"])
    messages.success(request, f"Đã {'mở' if d.user.is_active else 'khóa'} tài khoản bác sĩ {d.user.full_name}.")
    return redirect("adminpanel:admin_doctors_list")


@login_required
@role_required([Role.ADMIN])
@transaction.atomic
def admin_doctor_update(request, doctor_id):
    d = get_object_or_404(Doctors.objects.select_related("user"), pk=doctor_id)
    if request.method != "POST":
        return JsonResponse({"ok": False, "msg": "Invalid method"}, status=405)

    # Fields allowed to update
    d.user.full_name = (request.POST.get("full_name", d.user.full_name) or d.user.full_name)
    d.user.phone = request.POST.get("phone") or None
    d.rank = request.POST.get("rank") or None
    d.room_number = request.POST.get("room_number") or None
    d.license_number = request.POST.get("license_number") or d.license_number
    d.years_experience = int(request.POST.get("years_experience") or d.years_experience or 0)
    fee_raw = (request.POST.get("consultation_fee") or "").replace(".", "").replace(",", "")
    try:
        d.consultation_fee = float(fee_raw) if fee_raw else d.consultation_fee
    except Exception:
        pass
    sp = request.POST.get("specialty_id")
    if sp:
        d.specialty_id = sp
    d.user.save(update_fields=["full_name", "phone"])
    d.save()
    messages.success(request, "Đã cập nhật bác sĩ.")
    return JsonResponse({"ok": True})


def date_to_datetime_range(date_obj):
    """Convert a date to timezone-aware datetime range (start and end of day)"""
    from zoneinfo import ZoneInfo
    from django.utils import timezone
    
    # Get local timezone
    local_tz = ZoneInfo('Asia/Ho_Chi_Minh')
    utc_tz = ZoneInfo('UTC')
    
    # Create start and end of day in local timezone
    start_of_day = datetime.combine(date_obj, dt_time.min, tzinfo=local_tz)
    end_of_day = datetime.combine(date_obj, dt_time.max, tzinfo=local_tz)
    
    # Convert to UTC (what Django uses internally)
    return start_of_day.astimezone(utc_tz), end_of_day.astimezone(utc_tz)


@login_required
@role_required([Role.ADMIN])
def debug_dashboard(request):
    """Debug view to show dashboard data without charts"""
    # Just call the regular dashboard but with debug template
    context = _get_dashboard_context(request)
    return render(request, "adminpanel/debug_dashboard.html", context)


def _get_dashboard_context(request):
    """Helper function to get dashboard context - shared by dashboard and debug views"""
    try:
        # 1) Days range (7 or 30)
        try:
            days = int(request.GET.get("range", "7"))
        except Exception:
            days = 7
        if days not in (7, 30):
            days = 7

        today = localdate()
        date_from = today - timedelta(days=days - 1)
        
        # Get timezone-aware datetime ranges
        today_start, today_end = date_to_datetime_range(today)
        date_from_start, _ = date_to_datetime_range(date_from)

        # 2) KPI
        from decimal import Decimal
        
        appt_today = Appointments.objects.filter(appointment_at__range=(today_start, today_end)).count()
        revenue_today = (
            Invoices.objects.filter(created_at__range=(today_start, today_end), status="PAID")
            .aggregate(total=Coalesce(Sum("amount_due"), V(0, output_field=DecimalField())))
            .get("total")
            or Decimal(0)
        )
        unpaid = Invoices.objects.filter(status="UNPAID").count()
        active_doctors = Doctors.objects.filter(user__is_active=1).count()

        # 3) Appointments by day - group by local date (not UTC!)
        from zoneinfo import ZoneInfo
        local_tz = ZoneInfo('Asia/Ho_Chi_Minh')
        
        appointments_in_range = Appointments.objects.filter(
            appointment_at__range=(date_from_start, today_end)
        )
        
        appt_map = {}
        for appt in appointments_in_range:
            # Convert to local timezone, then extract date
            local_dt = appt.appointment_at.astimezone(local_tz)
            local_date = local_dt.date()
            appt_map[local_date] = appt_map.get(local_date, 0) + 1

        # 4) Revenue by day - group by local date (not UTC!)
        invoices_in_range = Invoices.objects.filter(
            created_at__range=(date_from_start, today_end), 
            status="PAID"
        )
        
        rev_map = {}
        for inv in invoices_in_range:
            # Convert to local timezone, then extract date
            local_dt = inv.created_at.astimezone(local_tz)
            local_date = local_dt.date()
            rev_map[local_date] = rev_map.get(local_date, 0.0) + float(inv.amount_due or 0)

        # 5) Build continuous labels and series (fill zero for missing days)
        chart_labels = []
        chart_appt = []
        chart_revenue = []
        for i in range(days):
            d = date_from + timedelta(days=i)
            chart_labels.append(d.strftime("%d/%m"))
            chart_appt.append(appt_map.get(d, 0))
            chart_revenue.append(rev_map.get(d, 0.0))

        # 6) Doctors by specialty
        by_spec = (
            Doctors.objects.select_related("specialty")
            .values("specialty__name")
            .annotate(total=Count("id"))
            .order_by("specialty__name")
        )
        chart_doc_spec_labels = [x["specialty__name"] or "Khác" for x in by_spec]
        chart_doc_spec_data = [x["total"] for x in by_spec]

        # 7) Revenue by item type per day (stacked) - group by local date
        from collections import defaultdict
        
        item_invoices = InvoiceItems.objects.filter(
            invoice__created_at__range=(date_from_start, today_end)
        ).select_related('invoice')
        
        by_day_type = defaultdict(lambda: defaultdict(float))
        all_types = set()
        for item in item_invoices:
            # Convert invoice created_at to local timezone, then extract date
            local_dt = item.invoice.created_at.astimezone(local_tz)
            local_date = local_dt.date()
            t = item.item_type or "OTHER"
            v = float(item.quantity or 0) * float(item.unit_price or 0)
            by_day_type[local_date][t] += v
            all_types.add(t)
        all_types = sorted(all_types)

        chart_rev_type_labels = chart_labels[:]
        chart_rev_type_datasets = []
        for t in all_types:
            data = []
            for i in range(days):
                d = date_from + timedelta(days=i)
                data.append(by_day_type[d].get(t, 0))
            chart_rev_type_datasets.append({"label": t, "data": data})

        # 5) Appointment status distribution today
        states = [
            ("PENDING", "Chờ xác nhận"),
            ("CONFIRMED", "Đã xác nhận"),
            ("IN_PROGRESS", "Đang khám"),
            ("COMPLETED", "Hoàn tất"),
            ("CANCELLED", "Đã hủy"),
            ("NO_SHOW", "Không đến"),
        ]
        today_appt = Appointments.objects.filter(appointment_at__range=(today_start, today_end))
        chart_appt_status_labels = [vn for code, vn in states]
        chart_appt_status_data = [today_appt.filter(status=code).count() for code, vn in states]

        # Helper function to convert time to minutes
        def _minutes(t):
            return t.hour * 60 + t.minute

        # --- DOCTOR PERFORMANCE TODAY ---
        schedules = (
            Schedules.objects
            .select_related("doctor", "doctor__user")
            .filter(work_date=today, status__in=["OPEN", "CLOSED"])
        )

        # Calculate total slots per doctor
        slots_by_doctor = {}
        for s in schedules:
            st = _minutes(s.start_time)
            en = _minutes(s.end_time)
            dur = int(s.slot_duration_minutes or 0) or 30
            # Fix: Ensure we don't get negative slots and handle edge cases
            if en > st and dur > 0:
                total_slots = (en - st) // dur
            else:
                total_slots = 0
            
            doctor_name = s.doctor.user.full_name if getattr(s.doctor, "user", None) else f"BS #{s.doctor_id}"
            
            did = s.doctor_id
            if did not in slots_by_doctor:
                slots_by_doctor[did] = {
                    "name": doctor_name,
                    "open_slots": 0,
                }
            slots_by_doctor[did]["open_slots"] += total_slots


        # Count booked appointments (valid status only)
        valid_status = ["PENDING", "CONFIRMED", "IN_PROGRESS", "COMPLETED"]
        appt_today_by_doctor = (
            Appointments.objects
            .filter(appointment_at__range=(today_start, today_end), status__in=valid_status)
            .values("doctor_id")
            .annotate(cnt=Count("id"))
        )
        booked_map = {x["doctor_id"]: x["cnt"] for x in appt_today_by_doctor}

        doctor_perf_rows = []
        for did, info in slots_by_doctor.items():
            open_slots = info["open_slots"]
            booked = booked_map.get(did, 0)
            fill = 0 if open_slots <= 0 else round(booked * 100.0 / open_slots, 1)
            doctor_perf_rows.append({
                "doctor_id": did,
                "doctor_name": info["name"],
                "open_slots": open_slots,
                "booked": booked,
                "utilization": fill,
            })

        # Sort by utilization (high to low)
        doctor_perf_rows.sort(key=lambda r: r["utilization"], reverse=True)

        # --- TOP 5 DOCTORS BY APPOINTMENTS (7/30 DAYS) ---
        appt_range = (
            Appointments.objects
            .filter(appointment_at__range=(date_from_start, today_end), status__in=valid_status)
            .values("doctor_id", "doctor__user__full_name")
            .annotate(total=Count("id"))
            .order_by("-total")[:5]
        )
        top5_labels = [x["doctor__user__full_name"] or f"BS #{x['doctor_id']}" for x in appt_range]
        top5_data = [x["total"] for x in appt_range]

        context = {
            "appt_today": appt_today,
            "revenue_today": revenue_today,
            "unpaid": unpaid,
            "active_doctors": active_doctors,

            "day_range": days,
            "date_from": date_from,
            "today": today,

            "chart_labels": chart_labels,
            "chart_appt": chart_appt,
            "chart_revenue": chart_revenue,

            "chart_doc_spec_labels": chart_doc_spec_labels,
            "chart_doc_spec_data": chart_doc_spec_data,

            "chart_rev_type_labels": chart_rev_type_labels,
            "chart_rev_type_datasets": chart_rev_type_datasets,

            "chart_appt_status_labels": chart_appt_status_labels,
            "chart_appt_status_data": chart_appt_status_data,

            "doctor_perf_rows": doctor_perf_rows,
            "top5_doctor_labels": top5_labels,
            "top5_doctor_data": top5_data,
        }

        return context

    except Exception as e:
        # Log the exception for debugging
        import traceback
        print(f"!!! DASHBOARD ERROR !!!")
        print(f"Exception: {e}")
        print(f"Traceback:")
        traceback.print_exc()
        print(f"!!! END ERROR !!!")
        
        context = {
            "appt_today": 0,
            "revenue_today": 0,
            "unpaid": 0,
            "active_doctors": 0,
            "day_range": 7,
            "date_from": localdate(),
            "today": localdate(),
            "chart_labels": [],
            "chart_appt": [],
            "chart_revenue": [],
            "chart_doc_spec_labels": [],
            "chart_doc_spec_data": [],
            "chart_rev_type_labels": [],
            "chart_rev_type_datasets": [],
            "chart_appt_status_labels": [],
            "chart_appt_status_data": [],
            "doctor_perf_rows": [],
            "top5_doctor_labels": [],
            "top5_doctor_data": [],
        }
        return context


@login_required
@role_required([Role.ADMIN])
def dashboard(request):
    """Dashboard view with charts for 7/30 days"""
    context = _get_dashboard_context(request)
    return render(request, "adminpanel/dashboard.html", context)


@login_required
@role_required([Role.ADMIN])
def appointments(request):
    """Admin appointments list with filters, KPI, and pagination"""
    from django.core.paginator import Paginator
    from django.utils import timezone
    from datetime import datetime
    
    # Parse date helper
    def _parse_date(s):
        try:
            return datetime.strptime(s, "%d/%m/%Y").date()
        except Exception:
            return None
    
    # Get filter parameters
    q = request.GET.get("q", "").strip()
    date_from = _parse_date(request.GET.get("date_from", ""))
    date_to = _parse_date(request.GET.get("date_to", ""))
    doctor_id = request.GET.get("doctor_id") or None
    specialty_id = request.GET.get("specialty_id") or None
    status = request.GET.get("status") or None
    source = request.GET.get("source") or None
    order = request.GET.get("order", "desc")
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 10))

    # Base queryset
    qs = (Appointments.objects
          .select_related("doctor", "doctor__user", "doctor__specialty",
                          "patient", "patient__user"))

    # Apply filters
    if date_from and date_to:
        qs = qs.filter(appointment_at__date__range=(date_from, date_to))
    elif date_from:
        qs = qs.filter(appointment_at__date__gte=date_from)
    elif date_to:
        qs = qs.filter(appointment_at__date__lte=date_to)

    if doctor_id:
        qs = qs.filter(doctor_id=doctor_id)
    if specialty_id:
        qs = qs.filter(doctor__specialty_id=specialty_id)
    if status:
        qs = qs.filter(status=status)
    if source:
        qs = qs.filter(source=source)
    if q:
        qs = qs.filter(
            Q(patient__user__full_name__icontains=q) |
            Q(patient__user__phone__icontains=q) |
            Q(doctor__user__full_name__icontains=q)
        )

    # Sort by appointment time
    if order == "asc":
        qs = qs.order_by("appointment_at")
    else:
        qs = qs.order_by("-appointment_at")

    # KPI based on current filters
    now = timezone.now()
    kpi = {
        "upcoming": qs.filter(appointment_at__gte=now,
                              status__in=["PENDING", "CONFIRMED"]).count(),
        "in_progress": qs.filter(status="IN_PROGRESS").count(),
        "completed": qs.filter(status="COMPLETED").count(),
        "cancelled": qs.filter(status="CANCELLED").count(),
    }

    # Pagination
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)
    start_index = (page_obj.number - 1) * paginator.per_page

    # Data for filter dropdowns
    doctors = Doctors.objects.select_related("user").all()
    specialties = Doctors.objects.select_related("specialty").values_list(
        "specialty_id", "specialty__name"
    ).distinct()

    context = {
        "appointments_page": page_obj,
        "start_index": start_index,
        "filters": {
            "q": q,
            "date_from": request.GET.get("date_from", ""),
            "date_to": request.GET.get("date_to", ""),
            "doctor_id": doctor_id or "",
            "specialty_id": specialty_id or "",
            "status": status or "",
            "source": source or "",
            "order": order,
            "page_size": page_size,
        },
        "kpi": kpi,
        "doctors": doctors,
        "specialties": specialties,
    }
    return render(request, "adminpanel/appointments.html", context)


@login_required
@role_required([Role.ADMIN])
def appointment_detail(request, pk):
    """Admin appointment detail view"""
    appointment = get_object_or_404(
        Appointments.objects.select_related(
            "patient", "patient__user", "doctor", "doctor__user", "doctor__specialty"
        ),
        pk=pk
    )
    return render(request, "adminpanel/appointment_detail.html", {"appointment": appointment})


@login_required
@role_required([Role.ADMIN])
def doctors(request):
    qs = (Doctors.objects
          .select_related("user","specialty")
          .order_by("user__full_name"))
    q = request.GET.get("q")
    if q:
        qs = qs.filter(Q(user__full_name__icontains=q) | Q(license_number__icontains=q))
    return render(request, "adminpanel/doctors.html", {"items": qs[:200]})


from django.contrib.auth.decorators import user_passes_test

def _is_admin(user):
    if not getattr(user, "is_authenticated", False):
        return False
    # Allow Django staff/superuser
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    # Map to external accounts.Users by email
    try:
        if getattr(user, "email", None):
            ext = AccountsUsers.objects.filter(email=user.email).first()
            if ext and getattr(ext, "role", None) == "ADMIN" and bool(getattr(ext, "is_active", 1)):
                return True
    except Exception:
        pass
    return False

@user_passes_test(_is_admin)
def patients_list(request):
    from django.core.paginator import Paginator
    q = (request.GET.get("q", "") or "").strip()
    qs = PatientProfiles.objects.select_related("user").all().order_by("user__full_name")
    if q:
        qs = qs.filter(Q(user__full_name__icontains=q) | Q(user__email__icontains=q) | Q(cccd__icontains=q) | Q(user__phone__icontains=q))
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page") or 1)
    # KPI (nếu chưa có dữ liệu thì 0)
    kpi = {"upcoming": 0, "in_progress": 0, "completed": 0, "cancelled": 0}
    from .forms import PatientCreateForm, PatientUpdateForm
    # detail/edit modal control
    open_detail_modal = False
    open_edit_modal = False
    detail_user = None
    detail_profile = None
    edit_form = None
    edit_id = None
    if request.GET.get("detail"):
        try:
            u = AccountsUsers.objects.get(pk=int(request.GET.get("detail")), role="PATIENT")
            p = PatientProfiles.objects.get(user=u)
            detail_user = u
            detail_profile = p
            open_detail_modal = True
        except Exception:
            pass
    if request.GET.get("edit"):
        try:
            u = AccountsUsers.objects.get(pk=int(request.GET.get("edit")), role="PATIENT")
            p = PatientProfiles.objects.get(user=u)
            initial = {
                "full_name": u.full_name,
                "phone": u.phone,
                "is_active": bool(u.is_active),
                "cccd": p.cccd,
                "date_of_birth": p.date_of_birth,
                "gender": p.gender,
                "address": p.address,
            }
            edit_form = PatientUpdateForm(initial=initial, user_instance=u, profile_instance=p)
            open_edit_modal = True
            edit_id = u.id
        except Exception:
            pass
    context = {
        "patients": page_obj,
        "paginator": paginator,
        "page_obj": page_obj,
        "q": q,
        "create_form": PatientCreateForm(),
        "edit_form": edit_form,
        "edit_id": edit_id,
        "detail_user": detail_user,
        "detail_profile": detail_profile,
        "open_detail_modal": open_detail_modal,
        "open_edit_modal": open_edit_modal,
        "kpi": kpi,
    }
    return render(request, "adminpanel/patients_list.html", context)


@user_passes_test(_is_admin)
def patient_create(request):
    from .forms import PatientCreateForm
    if request.method != "POST":
        return redirect("adminpanel:admin_patients_list")
    form = PatientCreateForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Đã tạo bệnh nhân.")
        return redirect("adminpanel:admin_patients_list")
    # lỗi: render lại list và bật modal
    from django.core.paginator import Paginator
    qs = PatientProfiles.objects.select_related("user").all().order_by("user__full_name")
    page_obj = Paginator(qs, 10).get_page(1)
    context = {"patients": page_obj, "create_form": form, "open_create_modal": True, "q": request.GET.get("q", ""), "kpi": {"upcoming":0,"in_progress":0,"completed":0,"cancelled":0}}
    return render(request, "adminpanel/patients_list.html", context)


@user_passes_test(_is_admin)
def patient_edit(request, pk):
    from .forms import PatientUpdateForm
    # pk here is Users.id (we passed edit_id = user.id)
    u = get_object_or_404(AccountsUsers, pk=pk, role="PATIENT")
    try:
        p = PatientProfiles.objects.select_related("user").get(user=u)
    except PatientProfiles.DoesNotExist:
        messages.error(request, "Bệnh nhân chưa có hồ sơ PatientProfiles. Vui lòng tạo mới bằng nút Thêm.")
        return redirect("adminpanel:admin_patients_list")
    if request.method == "POST":
        form = PatientUpdateForm(request.POST, user_instance=p.user, profile_instance=p)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật bệnh nhân.")
            return redirect("adminpanel:admin_patients_list")
        # render lại với lỗi và mở modal edit
        from django.core.paginator import Paginator
        qs = PatientProfiles.objects.select_related("user").all().order_by("user__full_name")
        page_obj = Paginator(qs, 10).get_page(request.GET.get("page") or 1)
        context = {"patients": page_obj, "page_obj": page_obj, "edit_form": form, "edit_id": pk, "open_edit_modal": True, "create_form": None, "kpi": {"upcoming":0,"in_progress":0,"completed":0,"cancelled":0}}
        return render(request, "adminpanel/patients_list.html", context)
    else:
        # GET: nạp form và mở modal edit
        form = PatientUpdateForm(initial={
            "full_name": p.user.full_name,
            "phone": p.user.phone,
            "cccd": p.cccd,
            "date_of_birth": p.date_of_birth,
            "gender": p.gender,
            "address": p.address,
            "is_active": bool(p.user.is_active),
        }, user_instance=p.user, profile_instance=p)
        from django.core.paginator import Paginator
        qs = PatientProfiles.objects.select_related("user").all().order_by("user__full_name")
        page_obj = Paginator(qs, 10).get_page(request.GET.get("page") or 1)
        context = {"patients": page_obj, "page_obj": page_obj, "edit_form": form, "edit_id": pk, "open_edit_modal": True, "create_form": None, "kpi": {"upcoming":0,"in_progress":0,"completed":0,"cancelled":0}}
        return render(request, "adminpanel/patients_list.html", context)


@user_passes_test(_is_admin)
@transaction.atomic
def patient_delete(request, pk):
    if request.method != "POST":
        return redirect("adminpanel:admin_patients_list")
    
    try:
        p = get_object_or_404(PatientProfiles.objects.select_related("user"), pk=pk)
        user = p.user
        
        # Xóa cascade: xóa tất cả dữ liệu liên quan trước khi xóa patient
        # 1. Xóa appointments của bệnh nhân này
        Appointments.objects.filter(patient=p).delete()
        
        # 2. Xóa appointment logs liên quan
        AppointmentLogs.objects.filter(appointment__patient=p).delete()
        
        # 3. Xóa invoices của bệnh nhân này (nếu có)
        Invoices.objects.filter(appointment__patient=p).delete()
        
        # 4. Xóa chatbot sessions của bệnh nhân
        ChatbotSessions.objects.filter(user=user).delete()
        
        # 5. Xóa UserExtras nếu có
        UserExtras.objects.filter(user=user).delete()
        
        # 6. Cuối cùng xóa patient profile và user
        p.delete()  # Sẽ tự động xóa user do CASCADE
        
        messages.success(request, "Đã xóa bệnh nhân và tất cả dữ liệu liên quan.")
        
    except Exception as e:
        print(f"Error deleting patient: {e}")
        messages.error(request, f"Không thể xóa bệnh nhân: {str(e)}")
    
    return redirect("adminpanel:admin_patients_list")


# ===================== PATIENT ADMIN APIs =====================
@login_required
@role_required([Role.ADMIN])
def admin_patients_list(request):
    q = (request.GET.get("q", "") or "").strip()
    qs = PatientProfiles.objects.select_related("user").all().order_by("user__full_name")
    if q:
        qs = qs.filter(Q(user__full_name__icontains=q) | Q(user__email__icontains=q) | Q(cccd__icontains=q))
    return render(request, "adminpanel/patients_list.html", {"patients": qs, "q": q})


@login_required
@role_required([Role.ADMIN])
def admin_staff_list(request):
    q = (request.GET.get("q", "") or "").strip()
    qs = StaffProfiles.objects.select_related("user").all().order_by("user__full_name")
    if q:
        qs = qs.filter(Q(user__full_name__icontains=q) | Q(user__email__icontains=q) | 
                       Q(employee_code__icontains=q) | Q(cccd__icontains=q))
    return render(request, "adminpanel/staff_list.html", {"staff": qs, "q": q})


@login_required
@role_required([Role.ADMIN])
@transaction.atomic
def admin_staff_update(request, pk):
    if request.method != "POST":
        messages.error(request, "Phương thức không hợp lệ.")
        return redirect("adminpanel:admin_staff_list")
    
    staff = get_object_or_404(StaffProfiles.objects.select_related("user"), pk=pk)
    
    try:
        # Update user fields
        staff.user.full_name = request.POST.get("full_name", staff.user.full_name)
        staff.user.phone = request.POST.get("phone") or None
        staff.user.email = request.POST.get("email", staff.user.email)
        staff.user.is_active = 1 if request.POST.get("is_active") == "1" else 0
        
        # Update staff profile fields
        staff.employee_code = request.POST.get("employee_code") or None
        staff.full_name = request.POST.get("full_name", staff.full_name)
        staff.gender = request.POST.get("gender") or None
        staff.date_of_birth = request.POST.get("date_of_birth") or None
        staff.cccd = request.POST.get("cccd") or None
        staff.phone = request.POST.get("phone") or None
        staff.address = request.POST.get("address") or None
        staff.position = request.POST.get("position") or None
        staff.shift = request.POST.get("shift") or None
        staff.start_date = request.POST.get("start_date") or None
        staff.status = request.POST.get("status") or None
        staff.updated_at = timezone.now()
        
        # Update password if provided
        password = request.POST.get("password")
        if password:
            staff.user.password_hash = make_password(password)
            staff.user.save(update_fields=["full_name", "phone", "email", "is_active", "password_hash"])
        else:
            staff.user.save(update_fields=["full_name", "phone", "email", "is_active"])
        
        staff.save()
        
        messages.success(request, f"Đã cập nhật thông tin nhân viên {staff.user.full_name} thành công!")
        
    except Exception as e:
        messages.error(request, f"Có lỗi xảy ra khi cập nhật: {str(e)}")
    
    return redirect("adminpanel:admin_staff_list")


@login_required
@role_required([Role.ADMIN])
def admin_patient_detail(request, pk):
    p = get_object_or_404(PatientProfiles.objects.select_related("user"), pk=pk)
    data = {
        "id": p.id,
        "full_name": p.user.full_name,
        "email": p.user.email,
        "phone": p.user.phone or "",
        "is_active": bool(p.user.is_active),
        "cccd": p.cccd,
        "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else "",
        "gender": p.gender or "",
        "address": p.address or "",
    }
    return JsonResponse({"ok": True, "data": data})


@login_required
@role_required([Role.ADMIN])
@transaction.atomic
def admin_patient_create(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Invalid method"}, status=405)
    full_name = (request.POST.get("full_name", "") or "").strip()
    email = (request.POST.get("email", "") or "").strip().lower()
    password = request.POST.get("password") or ""
    phone = (request.POST.get("phone", "") or "").strip()
    cccd = (request.POST.get("cccd", "") or "").strip()
    date_of_birth = request.POST.get("date_of_birth") or None
    gender = request.POST.get("gender") or None
    address = request.POST.get("address") or None
    is_active = 1 if (request.POST.get("is_active") == "on") else 0

    if not full_name or not email or not cccd:
        return JsonResponse({"ok": False, "message": "Vui lòng nhập Họ tên, Email và CCCD."}, status=400)
    if AccountsUsers.objects.filter(email=email).exists():
        return JsonResponse({"ok": False, "message": "Email đã tồn tại."}, status=400)
    if PatientProfiles.objects.filter(cccd=cccd).exists():
        return JsonResponse({"ok": False, "message": "CCCD đã tồn tại."}, status=400)

    user = AccountsUsers.objects.create(
        email=email,
        full_name=full_name,
        phone=phone or None,
        role="PATIENT",
        is_active=is_active,
        password_hash=make_password(password or get_random_string(10)),
    )
    PatientProfiles.objects.create(
        user=user,
        cccd=cccd,
        date_of_birth=date_of_birth or None,
        gender=gender or None,
        address=address or None,
    )
    return JsonResponse({"ok": True, "message": "Đã tạo bệnh nhân."})


@login_required
@role_required([Role.ADMIN])
@transaction.atomic
def admin_patient_update(request, pk):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Invalid method"}, status=405)
    p = get_object_or_404(PatientProfiles.objects.select_related("user"), pk=pk)
    full_name = (request.POST.get("full_name", p.user.full_name) or p.user.full_name)
    phone = request.POST.get("phone") or None
    cccd = (request.POST.get("cccd") or p.cccd)
    date_of_birth = request.POST.get("date_of_birth") or None
    gender = request.POST.get("gender") or None
    address = request.POST.get("address") or None
    is_active = 1 if (request.POST.get("is_active") == "on") else 0
    password = request.POST.get("password") or None

    # unique checks
    if PatientProfiles.objects.exclude(pk=pk).filter(cccd=cccd).exists():
        return JsonResponse({"ok": False, "message": "CCCD đã tồn tại."}, status=400)

    p.user.full_name = full_name
    p.user.phone = phone
    p.user.is_active = is_active
    if password:
        p.user.password_hash = make_password(password)
    p.user.save(update_fields=["full_name", "phone", "is_active", "password_hash"] if password else ["full_name", "phone", "is_active"])

    p.cccd = cccd
    p.date_of_birth = date_of_birth or None
    p.gender = gender or None
    p.address = address or None
    p.save()
    return JsonResponse({"ok": True, "message": "Đã cập nhật bệnh nhân."})


@login_required
@role_required([Role.ADMIN])
@transaction.atomic
def admin_patient_delete(request, pk):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Invalid method"}, status=405)
    
    try:
        p = get_object_or_404(PatientProfiles.objects.select_related("user"), pk=pk)
        user = p.user
        
        # Xóa cascade: xóa tất cả dữ liệu liên quan trước khi xóa patient
        # 1. Xóa appointments của bệnh nhân này
        Appointments.objects.filter(patient=p).delete()
        
        # 2. Xóa appointment logs liên quan
        AppointmentLogs.objects.filter(appointment__patient=p).delete()
        
        # 3. Xóa invoices của bệnh nhân này (nếu có)
        Invoices.objects.filter(appointment__patient=p).delete()
        
        # 4. Xóa chatbot sessions của bệnh nhân
        ChatbotSessions.objects.filter(user=user).delete()
        
        # 5. Xóa UserExtras nếu có
        UserExtras.objects.filter(user=user).delete()
        
        # 6. Cuối cùng xóa patient profile và user
        p.delete()  # Sẽ tự động xóa user do CASCADE
        # user.delete()  # Không cần vì CASCADE đã xóa
        
        return JsonResponse({"ok": True, "message": "Đã xóa bệnh nhân và tất cả dữ liệu liên quan."})
        
    except Exception as e:
        print(f"Error deleting patient: {e}")
        return JsonResponse({"ok": False, "message": f"Không thể xóa bệnh nhân: {str(e)}"}, status=500)


@login_required
@role_required([Role.ADMIN])
def invoices(request):
    qs = (Invoices.objects
          .select_related("appointment__patient__user","appointment__doctor__user")
          .order_by("-created_at"))
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status.upper())
    return render(request, "adminpanel/invoices.html", {"items": qs[:200]})


@login_required
def invoice_list(request):
    from django.core.paginator import Paginator
    qs = (
        Invoices.objects
        .select_related('appointment__patient__user', 'appointment__doctor__user')
        .annotate(
            total=Coalesce(
                Sum(
                    F('items__quantity') * F('items__unit_price'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                ),
                V(0, output_field=DecimalField(max_digits=12, decimal_places=2))
            )
        ).order_by('-created_at')
    )

    status = request.GET.get('status')
    if status in ('UNPAID', 'PAID'):
        qs = qs.filter(status=status)
    doctor_id = request.GET.get('doctor')
    if doctor_id:
        qs = qs.filter(appointment__doctor_id=doctor_id)
    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(appointment__patient__user__full_name__icontains=q) |
            Q(appointment__patient__cccd__icontains=q)
        )
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    today = localdate()
    unpaid_today = Invoices.objects.filter(status='UNPAID', created_at__date=today).count()
    paid_today = Invoices.objects.filter(status='PAID', created_at__date=today).count()
    revenue_today = Invoices.objects.filter(status='PAID', created_at__date=today).aggregate(
        s=Coalesce(
            Sum('amount_due', output_field=DecimalField(max_digits=12, decimal_places=2)),
            V(0, output_field=DecimalField(max_digits=12, decimal_places=2))
        )
    )['s']

    return render(request, 'adminpanel/billing/invoices_list.html', {
        'page_obj': page_obj,
        'unpaid_today': unpaid_today,
        'paid_today': paid_today,
        'revenue_today': revenue_today,
    })


@login_required
@require_POST
def invoice_cash(request, pk):
    inv = get_object_or_404(Invoices, pk=pk, status='UNPAID')
    inv.status = 'PAID'
    inv.save(update_fields=['status'])
    messages.success(request, f'Đã nhận tiền mặt cho hóa đơn #{inv.id:05d}.')
    return redirect('adminpanel:admin_invoice_list')


@login_required
def invoice_detail(request, pk):
    inv = get_object_or_404(
        Invoices.objects.select_related(
            'appointment__patient__user', 
            'appointment__doctor__user',
            'appointment__doctor'
        ).prefetch_related('items'),
        pk=pk
    )
    return render(request, 'adminpanel/billing/invoice_detail.html', {'inv': inv})


@login_required
def invoice_print(request, pk):
    invoice = (
        Invoices.objects
        .select_related(
            "appointment",
            "appointment__patient__user",
            "appointment__doctor__user",
            "appointment__doctor__specialty",
            "printed_by_user",
        )
        .prefetch_related("items")
        .get(pk=pk)
    )

    lines = invoice.items.all().order_by("id")

    clinic = {
        "name": "PHÒNG KHÁM ĐẠI HỌC BÁCH KHOA ĐÀ NẴNG",
        "address": "54 Nguyễn Lương Bằng, Liên Chiểu, Đà Nẵng",
        "phone": "(0236) 3731 111",
    }

    return render(
        request,
        "billing/invoice_print.html",
        {
            "invoice": invoice,
            "lines": lines,
            "clinic": clinic,
        },
    )


@login_required
@role_required([Role.ADMIN])
def settings_view(request):
    tab = request.GET.get("tab", "specialties")
    ctx = {
        "tab": tab,
        "specialties": Specialty.objects.all().order_by("name"),
        "rankfees": DoctorRankFee.objects.all().order_by("rank"),
        "drugs": Drug.objects.all().order_by("name")[:200],
        "users": UserLite.objects.all().order_by("full_name")[:200],
        "specialty_form": SpecialtyForm(),
        "rankfee_form": RankFeeForm(),
        "drug_form": DrugForm(),
    }
    return render(request, "adminpanel/settings.html", ctx)

# ---------- specialties CRUD ----------
@login_required
@role_required([Role.ADMIN])
def specialty_create(request):
    if request.method == "POST":
        form = SpecialtyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã thêm chuyên khoa.")
    return redirect("adminpanel:settings")

@login_required
@role_required([Role.ADMIN])
def specialty_update(request, pk):
    obj = get_object_or_404(Specialty, pk=pk)
    if request.method == "POST":
        form = SpecialtyForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật chuyên khoa.")
    return redirect("adminpanel:settings")

@login_required
@role_required([Role.ADMIN])
def specialty_delete(request, pk):
    obj = get_object_or_404(Specialty, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Đã xóa chuyên khoa.")
    return redirect("adminpanel:settings")

# ---------- rank fees CRUD ----------
@login_required
@role_required([Role.ADMIN])
def rankfee_create(request):
    if request.method == "POST":
        form = RankFeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã thêm/khởi tạo phí theo học vị.")
    return redirect("adminpanel:settings")

@login_required
@role_required([Role.ADMIN])
def rankfee_update(request, pk):
    obj = get_object_or_404(DoctorRankFee, pk=pk)
    if request.method == "POST":
        form = RankFeeForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật phí theo học vị.")
    return redirect("adminpanel:settings")

@login_required
@role_required([Role.ADMIN])
def rankfee_delete(request, pk):
    obj = get_object_or_404(DoctorRankFee, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Đã xóa phí theo học vị.")
    return redirect("adminpanel:settings")

# ---------- drugs CRUD ----------
@login_required
@role_required([Role.ADMIN])
def drug_create(request):
    if request.method == "POST":
        form = DrugForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã thêm thuốc.")
    return redirect(f"{reverse('adminpanel:settings')}?tab=drugs")

@login_required
@role_required([Role.ADMIN])
def drug_update(request, pk):
    obj = get_object_or_404(Drug, pk=pk)
    if request.method == "POST":
        form = DrugForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật thuốc.")
    return redirect(f"{reverse('adminpanel:settings')}?tab=drugs")

@login_required
@role_required([Role.ADMIN])
def drug_delete(request, pk):
    obj = get_object_or_404(Drug, pk=pk)
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, "Đã xóa thuốc.")
        except IntegrityError:
            # Thuốc đang được tham chiếu bởi prescriptions → không thể xóa cứng
            # Chuyển sang vô hiệu hóa thay thế
            obj.is_active = 0
            try:
                obj.save(update_fields=["is_active"])
            except Exception:
                pass
            messages.warning(request, "Thuốc đang được sử dụng trong đơn thuốc nên không thể xóa. Hệ thống đã chuyển sang trạng thái 'Không kích hoạt'.")
    return redirect(f"{reverse('adminpanel:settings')}?tab=drugs")

# ---------- user create / update ----------
@login_required
@role_required([Role.ADMIN])
def user_create(request):
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã tạo tài khoản mới.")
        else:
            # Lưu lỗi vào messages để hiển thị trong template
            for f, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f"{f}: {e}")
    return redirect(f"{reverse('adminpanel:settings')}?tab=users")

@login_required
@role_required([Role.ADMIN])
def user_update(request, pk):
    obj = get_object_or_404(UserLite, pk=pk)
    if request.method == "POST":
        form = UserRoleForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật tài khoản.")
    return redirect(f"{reverse('adminpanel:settings')}?tab=users")

@login_required
@role_required([Role.ADMIN])
def user_edit(request, pk):
    user = get_object_or_404(UserLite, pk=pk)
    if request.method == "POST":
        form = UpdateUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật tài khoản.")
            return redirect(f"{reverse('adminpanel:settings')}?tab=users")
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f"{field}: {e}")
            return redirect(f"{reverse('adminpanel:settings')}?tab=users")
    return redirect(f"{reverse('adminpanel:settings')}?tab=users")

@login_required
@role_required([Role.ADMIN])
def user_delete(request, pk):
    user = get_object_or_404(UserLite, pk=pk)
    if request.method == "POST":
        try:
            # Xóa cascade: xóa tất cả dữ liệu liên quan trước khi xóa user
            
            # 1. Xóa DoctorSettings trước (vì nó tham chiếu đến Doctors)
            try:
                doctor = Doctors.objects.get(user_id=user.id)
                DoctorSettings.objects.filter(doctor=doctor).delete()
            except Doctors.DoesNotExist:
                pass
            except Exception as e:
                print(f"Error deleting DoctorSettings: {e}")
            
            # 2. Xóa các bản ghi liên quan khác
            PatientProfiles.objects.filter(user_id=user.id).delete()
            StaffProfiles.objects.filter(user_id=user.id).delete()
            UserExtras.objects.filter(user_id=user.id).delete()
            
            # 3. Xóa appointments và schedules liên quan đến doctor này
            try:
                doctor = Doctors.objects.get(user_id=user.id)
                Appointments.objects.filter(doctor=doctor).delete()
                Schedules.objects.filter(doctor=doctor).delete()
            except Doctors.DoesNotExist:
                pass
            except Exception as e:
                print(f"Error deleting appointments/schedules: {e}")
            
            # 4. Xóa appointment logs
            AppointmentLogs.objects.filter(actor_user_id=user.id).delete()
            
            # 5. Xóa invoices và payments được tạo bởi user này
            Invoices.objects.filter(created_by_user_id=user.id).delete()
            Invoices.objects.filter(printed_by_user_id=user.id).delete()
            Payments.objects.filter(received_by_user_id=user.id).delete()
            InvoicePrintLogs.objects.filter(printed_by_user_id=user.id).delete()
            
            # 6. Xóa chatbot sessions và messages
            ChatbotSessions.objects.filter(user_id=user.id).delete()
            # ChatbotMessages không có user_id, chỉ có sender (string)
            
            # 7. Cuối cùng xóa user (sẽ tự động xóa Doctors do CASCADE)
            user.delete()
            messages.success(request, "Đã xoá tài khoản và tất cả dữ liệu liên quan.")
            
        except Exception as e:
            messages.error(request, f"Lỗi khi xóa tài khoản: {str(e)}")
            
    return redirect(f"{reverse('adminpanel:settings')}?tab=users")


