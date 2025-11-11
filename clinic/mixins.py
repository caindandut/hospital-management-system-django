"""
Mixins for role-based access control in Class-Based Views
"""
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from core.choices import Role


class RoleRequiredMixin:
    """
    Mixin to check if user has required role(s) for Class-Based Views
    
    Usage:
        class MyView(RoleRequiredMixin, View):
            allowed_roles = [Role.DOCTOR, Role.STAFF]
    """
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, "Bạn cần đăng nhập để truy cập chức năng này.")
            return redirect('theme:login')
        
        # Check if user has required role
        user_role = None
        try:
            email = getattr(request.user, 'email', None)
            if email:
                from accounts.models import Users as ExternalUser
                ext = ExternalUser.objects.filter(email=email).first()
                user_role = getattr(ext, 'role', None)
        except Exception:
            user_role = None
        if user_role not in self.allowed_roles:
            messages.error(request, "Bạn không có quyền truy cập chức năng này.")
            return redirect('theme:home')
        
        return super().dispatch(request, *args, **kwargs)


# Convenience mixins for specific roles
class PatientRequiredMixin(RoleRequiredMixin):
    """Mixin for patient-only views"""
    allowed_roles = [Role.PATIENT]


class DoctorRequiredMixin(RoleRequiredMixin):
    """Mixin for doctor-only views"""
    allowed_roles = [Role.DOCTOR]


class StaffRequiredMixin(RoleRequiredMixin):
    """Mixin for staff-only views"""
    allowed_roles = [Role.STAFF]


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin for admin-only views"""
    allowed_roles = [Role.ADMIN]


class DoctorOrStaffRequiredMixin(RoleRequiredMixin):
    """Mixin for doctor and staff views"""
    allowed_roles = [Role.DOCTOR, Role.STAFF]


class StaffOrAdminRequiredMixin(RoleRequiredMixin):
    """Mixin for staff and admin views"""
    allowed_roles = [Role.STAFF, Role.ADMIN]


class AuthenticatedRequiredMixin:
    """
    Mixin to check if user is authenticated (any role)
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Bạn cần đăng nhập để truy cập chức năng này.")
            return redirect('theme:login')
        return super().dispatch(request, *args, **kwargs)
