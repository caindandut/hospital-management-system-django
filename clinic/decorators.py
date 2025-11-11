"""
Decorators for role-based access control
"""
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from core.choices import Role


def _resolve_user_role(request):
    """Return user role string by looking up ExternalUser by email."""
    try:
        if not request.user.is_authenticated:
            return None
        email = getattr(request.user, "email", None)
        if not email:
            return None
        from accounts.models import Users as ExternalUser
        ext = ExternalUser.objects.filter(email=email).first()
        return getattr(ext, "role", None)
    except Exception:
        return None


def role_required(allowed_roles):
    """
    Decorator to check if user has required role(s)
    
    Args:
        allowed_roles (list): List of allowed roles
        
    Usage:
        @role_required([Role.DOCTOR, Role.STAFF])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.error(request, "Bạn cần đăng nhập để truy cập chức năng này.")
                return redirect('theme:login')
            
            # Check if user has required role
            user_role = _resolve_user_role(request)
            if user_role not in allowed_roles:
                messages.error(request, "Bạn không có quyền truy cập chức năng này.")
                return redirect('theme:home')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Convenience decorators for specific roles
def patient_required(view_func):
    """Decorator for patient-only views"""
    return role_required([Role.PATIENT])(view_func)


def doctor_required(view_func):
    """Decorator for doctor-only views"""
    return role_required([Role.DOCTOR])(view_func)


def staff_required(view_func):
    """Decorator for staff-only views"""
    return role_required([Role.STAFF])(view_func)


def admin_required(view_func):
    """Decorator for admin-only views"""
    return role_required([Role.ADMIN])(view_func)


def doctor_or_staff_required(view_func):
    """Decorator for doctor and staff views"""
    return role_required([Role.DOCTOR, Role.STAFF])(view_func)


def staff_or_admin_required(view_func):
    """Decorator for staff and admin views"""
    return role_required([Role.STAFF, Role.ADMIN])(view_func)


def authenticated_required(view_func):
    """
    Decorator to check if user is authenticated (any role)
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Bạn cần đăng nhập để truy cập chức năng này.")
            return redirect('theme:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def doctor_owns_appointment(view):
    """Chỉ cho phép bác sĩ là chủ sở hữu lịch hẹn."""
    def _wrap(request, pk, *args, **kwargs):
        from appointments.models import Appointments
        try:
            appt = Appointments.objects.select_related("doctor__user").get(pk=pk)
        except Appointments.DoesNotExist:
            messages.error(request, "Không tìm thấy lịch hẹn.")
            return redirect("appointments:appt_doctor_today")
        
        user_role = _resolve_user_role(request)
        if user_role not in ("DOCTOR", "ADMIN"):
            messages.error(request, "Bạn không có quyền truy cập chức năng này.")
            return redirect("theme:home")
        
        if user_role == "DOCTOR":
            try:
                email = getattr(request.user, "email", None)
                if email:
                    from accounts.models import Users as ExternalUser
                    ext = ExternalUser.objects.filter(email=email).first()
                    if ext and appt.doctor.user_id != ext.id:
                        messages.error(request, "Bạn không có quyền với lịch hẹn này.")
                        return redirect("appointments:appt_doctor_today")
            except Exception:
                messages.error(request, "Lỗi xác thực người dùng.")
                return redirect("appointments:appt_doctor_today")
        
        request.appt = appt
        return view(request, pk, *args, **kwargs)
    return _wrap
