from django.contrib import admin, messages

from .models import Doctors
from appointments.models import Appointments


@admin.register(Doctors)
class DoctorsAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "specialty", "license_number")
    search_fields = ("user__full_name", "user__email", "license_number", "specialty__name")

    def delete_model(self, request, obj):
        """
        Chỉ cho phép xóa bác sĩ nếu bác sĩ đó chưa khám / chưa có lịch hẹn nào.
        Nếu đã có lịch hẹn (ở bất kỳ trạng thái nào) thì hiển thị thông báo và không xóa.
        """
        if Appointments.objects.filter(doctor=obj).exists():
            messages.error(
                request,
                "Không thể xóa bác sĩ này vì đã có/đã từng có bệnh nhân đặt khám hoặc đã khám.",
            )
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Xử lý xóa hàng loạt bác sĩ: chỉ xóa các bác sĩ chưa có lịch hẹn.
        """
        blocked = []
        deletable_ids = []

        for doctor in queryset:
            if Appointments.objects.filter(doctor=doctor).exists():
                blocked.append(str(doctor))
            else:
                deletable_ids.append(doctor.pk)

        if blocked:
            messages.error(
                request,
                "Không thể xóa các bác sĩ đã có/đã từng có lịch khám với bệnh nhân: "
                + ", ".join(blocked),
            )

        if deletable_ids:
            super().delete_queryset(request, queryset.filter(pk__in=deletable_ids))
