from django.contrib import admin, messages

from .models import PatientProfiles
from appointments.models import Appointments


@admin.register(PatientProfiles)
class PatientProfilesAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "cccd", "date_of_birth")
    search_fields = ("user__full_name", "user__email", "cccd")

    def delete_model(self, request, obj):
        """
        Chỉ cho phép xóa bệnh nhân nếu chưa có bất kỳ lịch hẹn nào.
        Nếu đã có lịch hẹn sẽ hiển thị thông báo (toast) và KHÔNG xóa.
        """
        if Appointments.objects.filter(patient=obj).exists():
            messages.error(
                request,
                "Không thể xóa bệnh nhân này vì đã có phát sinh đặt lịch / khám bệnh.",
            )
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """
        Xử lý xóa hàng loạt: chỉ xóa các bệnh nhân chưa có lịch hẹn.
        Các bệnh nhân có lịch sẽ bị giữ lại và hiện thông báo.
        """
        blocked = []
        deletable_ids = []

        for patient in queryset:
            if Appointments.objects.filter(patient=patient).exists():
                blocked.append(str(patient))
            else:
                deletable_ids.append(patient.pk)

        if blocked:
            messages.error(
                request,
                "Không thể xóa các bệnh nhân đã có lịch hẹn / khám: "
                + ", ".join(blocked),
            )

        if deletable_ids:
            super().delete_queryset(request, queryset.filter(pk__in=deletable_ids))
