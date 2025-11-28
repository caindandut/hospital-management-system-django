from django.contrib import admin, messages

from .models import StaffProfiles
from billing.models import Payments


@admin.register(StaffProfiles)
class StaffProfilesAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "employee_code", "phone", "position", "status")
    search_fields = ("full_name", "employee_code", "phone", "user__email")

    def _has_payments(self, staff: StaffProfiles) -> bool:
        """
        Kiểm tra nhân viên đã từng thu tiền/thanh toán cho bệnh nhân nào chưa.
        Dựa theo bảng payments.received_by_user (liên kết với accounts.Users).
        """
        user = staff.user
        if not user:
            return False
        return Payments.objects.filter(received_by_user=user).exists()

    def delete_model(self, request, obj):
        """
        Chỉ cho phép xóa nhân viên nếu chưa thực hiện thanh toán (không có bản ghi Payments).
        """
        if self._has_payments(obj):
            messages.error(
                request,
                "Không thể xóa nhân viên này vì đã từng thực hiện thanh toán cho bệnh nhân.",
            )
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Xử lý xóa hàng loạt nhân viên: chỉ xóa các nhân viên chưa từng thanh toán.
        """
        blocked = []
        deletable_ids = []

        for staff in queryset:
            if self._has_payments(staff):
                blocked.append(str(staff))
            else:
                deletable_ids.append(staff.pk)

        if blocked:
            messages.error(
                request,
                "Không thể xóa các nhân viên đã từng thực hiện thanh toán: "
                + ", ".join(blocked),
            )

        if deletable_ids:
            super().delete_queryset(request, queryset.filter(pk__in=deletable_ids))


