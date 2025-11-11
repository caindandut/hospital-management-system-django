from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.shortcuts import get_object_or_404
from clinic.decorators import staff_or_admin_required, admin_required
from billing.models import Invoices, InvoiceItems, Payments, InvoicePrintLogs
from accounts.models import Users
from .models import StaffProfiles


def _resolve_target_user(request, allow_admin_override: bool):
    email = getattr(request.user, 'email', None)
    if not email:
        return None
    me = Users.objects.filter(email=email).first()
    if not me:
        return None
    if allow_admin_override:
        user_id = request.GET.get("user_id") or request.POST.get("user_id")
        if user_id:
            target = Users.objects.filter(id=user_id).first()
            if target:
                return target
    return me


def _get_or_create_profile(user: Users) -> StaffProfiles:
    prof = StaffProfiles.objects.filter(user=user).first()
    if prof:
        return prof
    # For unmanaged table, create via raw create if table exists
    prof = StaffProfiles(
        user=user,
        full_name=user.full_name or user.email,
        status="ACTIVE",
        shift="ROTATE",
        created_at=timezone.now(),
        updated_at=timezone.now(),
    )
    # Save will work if the table exists as per provided SQL
    prof.save(force_insert=True)
    return prof


@staff_or_admin_required
@require_http_methods(["GET", "POST"])
def staff_profile_self(request):
    target_user = _resolve_target_user(request, allow_admin_override=True)
    if not target_user:
        messages.error(request, "Không tìm thấy người dùng.")
        return redirect("theme:home")

    # If admin hits self endpoint with user_id, accept; otherwise me
    profile = _get_or_create_profile(target_user)

    if request.method == "POST":
        # Server validations
        full_name = (request.POST.get("full_name") or "").strip()
        email_readonly = (request.POST.get("email") or "").strip()
        gender = request.POST.get("gender") or None
        dob = request.POST.get("date_of_birth") or None
        cccd = request.POST.get("cccd") or None
        phone = request.POST.get("phone") or None
        address = request.POST.get("address") or None
        employee_code = request.POST.get("employee_code") or None
        position = request.POST.get("position") or None
        shift = request.POST.get("shift") or None
        start_date = request.POST.get("start_date") or None
        status = request.POST.get("status") or None

        if not full_name:
            messages.error(request, "Họ tên là bắt buộc.")
            return redirect(request.path + (f"?user_id={target_user.id}" if request.GET.get("user_id") else ""))

        import re
        if cccd:
            if not re.fullmatch(r"^[0-9]{9,12}$", cccd):
                messages.error(request, "CCCD không hợp lệ (9-12 số).")
                return redirect(request.path + (f"?user_id={target_user.id}" if request.GET.get("user_id") else ""))
        if phone:
            if not re.fullmatch(r"^[0-9]{10}$", phone):
                messages.error(request, "SĐT không hợp lệ (10 số).")
                return redirect(request.path + (f"?user_id={target_user.id}" if request.GET.get("user_id") else ""))

        from datetime import datetime
        def parse_date(val):
            try:
                return datetime.strptime(val, "%Y-%m-%d").date() if val else None
            except Exception:
                return None

        profile.full_name = full_name
        profile.gender = gender
        profile.date_of_birth = parse_date(dob)
        profile.cccd = cccd or None
        profile.phone = phone or None
        profile.address = address or None
        profile.employee_code = employee_code or None
        profile.position = position or None
        profile.shift = shift or None
        profile.start_date = parse_date(start_date)
        profile.status = status or None
        profile.updated_at = timezone.now()
        profile.save()

        messages.success(request, "Cập nhật thành công.")
        return redirect(request.path + (f"?user_id={target_user.id}" if request.GET.get("user_id") else ""))

    context = {
        "profile": profile,
        "target_user": target_user,
    }
    return render(request, "staff/profile_form.html", context)


@admin_required
@require_http_methods(["GET", "POST"])
def staff_profile_manage(request):
    target_user = _resolve_target_user(request, allow_admin_override=True)
    if not target_user:
        messages.error(request, "Thiếu user_id hợp lệ.")
        return redirect("theme:home")

    profile = _get_or_create_profile(target_user)

    if request.method == "POST":
        # Reuse same processing as self
        return staff_profile_self(request)

    context = {
        "profile": profile,
        "target_user": target_user,
        "is_manage": True,
    }
    return render(request, "staff/profile_form.html", context)


# Note: staff dashboard removed per request

# ===================== CASHIER VIEWS =====================

@staff_or_admin_required
def cashier_invoices(request):
    qs = (Invoices.objects
          .select_related("appointment__patient__user",
                          "appointment__doctor__user",
                          "appointment__doctor")
          .filter(status="UNPAID")
          .order_by("-created_at"))
    return render(request, "staff/cashier_list.html", {"invoices": qs})


@staff_or_admin_required
def cashier_invoice_detail(request, pk):
    inv = get_object_or_404(
        Invoices.objects.select_related("appointment__patient__user",
                                        "appointment__doctor__user",
                                        "appointment__doctor"),
        pk=pk
    )
    # annotate thành tiền cho từng dòng
    items = (InvoiceItems.objects
             .filter(invoice=inv)
             .annotate(
                 line_total_calc=ExpressionWrapper(
                     F("quantity") * F("unit_price"),
                     output_field=DecimalField(max_digits=12, decimal_places=2)
                 )
             )
             .order_by("id"))

    # tổng tiền
    total = (InvoiceItems.objects
             .filter(invoice=inv)
             .aggregate(
                 total=Sum(
                     ExpressionWrapper(
                         F("quantity") * F("unit_price"),
                         output_field=DecimalField(max_digits=12, decimal_places=2)
                     )
                 )
             )["total"] or 0)

    return render(request, "staff/cashier_detail.html",
                  {"inv": inv, "items": items, "total": total})


@staff_or_admin_required
def invoice_print(request, pk):
    inv = get_object_or_404(
        Invoices.objects.select_related(
            "appointment",
            "appointment__patient__user",
            "appointment__doctor__user",
            "appointment__doctor__specialty",
            "printed_by_user",
        ),
        pk=pk
    )
    items = (InvoiceItems.objects
             .filter(invoice=inv)
             .annotate(
                 line_total_calc=ExpressionWrapper(
                     F("quantity") * F("unit_price"),
                     output_field=DecimalField(max_digits=12, decimal_places=2)
                 )
             )
             .order_by("id"))

    total = (InvoiceItems.objects
             .filter(invoice=inv)
             .aggregate(
                 total=Sum(
                     ExpressionWrapper(
                         F("quantity") * F("unit_price"),
                         output_field=DecimalField(max_digits=12, decimal_places=2)
                     )
                 )
             )["total"] or 0)

    # Get the correct Users instance
    ext_user = _resolve_target_user(request, allow_admin_override=False)
    if not ext_user:
        messages.error(request, "Không tìm thấy thông tin người dùng.")
        return redirect("staff:staff_cashier")

    InvoicePrintLogs.objects.create(
        invoice=inv,
        printed_by_user=ext_user,
        printed_at=timezone.now(),
        copy_tag=("ORIGINAL" if inv.printed_at is None else "COPY"),
        note=None,
    )
    if inv.printed_at is None:
        inv.printed_at = timezone.now()
        inv.printed_by_user = ext_user
        inv.save(update_fields=["printed_at", "printed_by_user"])
    # Convert to shared template format
    lines = items
    
    clinic = {
        "name": "PHÒNG KHÁM ĐẠI HỌC BÁCH KHOA ĐÀ NẴNG",
        "address": "54 Nguyễn Lương Bằng, Liên Chiểu, Đà NẴng",
        "phone": "(0236) 3731 111",
    }

    return render(request, "billing/invoice_print.html", {
        "invoice": inv,
        "lines": lines,
        "clinic": clinic,
    })


@staff_or_admin_required
@transaction.atomic
def invoice_pay_cash(request, pk):
    inv = get_object_or_404(Invoices, pk=pk)
    if request.method == "POST":
        if inv.status != "UNPAID":
            messages.error(request, "Hóa đơn đã thanh toán hoặc không ở trạng thái chờ thu.")
            return redirect("staff:staff_invoice_detail", pk=pk)

        # Get the correct Users instance
        ext_user = _resolve_target_user(request, allow_admin_override=False)
        if not ext_user:
            messages.error(request, "Không tìm thấy thông tin người dùng.")
            return redirect("staff:staff_cashier")

        from django.db.models import F, ExpressionWrapper, DecimalField
        total = InvoiceItems.objects.filter(invoice=inv).aggregate(
            t=Sum(ExpressionWrapper(F("quantity") * F("unit_price"),
                                    output_field=DecimalField(max_digits=12, decimal_places=2)))
        )["t"] or 0

        Payments.objects.create(
            invoice=inv,
            amount=total,
            method="CASH",
            paid_at=timezone.now(),
            received_by_user=ext_user,
            note=None,
        )
        inv.status = "PAID"
        inv.amount_due = 0
        inv.subtotal = total
        inv.save(update_fields=["status", "amount_due", "subtotal"])
        messages.success(request, "Đã nhận tiền mặt. Hóa đơn chuyển sang ĐÃ THANH TOÁN.")
        return redirect("staff:staff_cashier")
    return redirect("staff:staff_invoice_detail", pk=pk)

