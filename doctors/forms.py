from django import forms
from accounts.models import Users
from .models import Doctors, UserExtras, DoctorSettings, Specialties


class DoctorBasicForm(forms.ModelForm):
    email = forms.EmailField(disabled=True, required=False, label="Email")

    class Meta:
        model = Users
        fields = ["full_name", "phone"]
        labels = {"full_name": "Họ và tên", "phone": "Số điện thoại"}


class UserExtrasForm(forms.ModelForm):
    class Meta:
        model = UserExtras
        fields = ["avatar", "address_short"]
        labels = {"avatar": "Ảnh đại diện", "address_short": "Địa chỉ liên hệ"}


class DoctorProfessionalForm(forms.ModelForm):
    class Meta:
        model = Doctors
        fields = ["specialty", "license_number", "years_experience", "bio", "room_number"]
        labels = {
            "specialty": "Chuyên khoa",
            "license_number": "Giấy phép hành nghề",
            "years_experience": "Năm kinh nghiệm",
            "bio": "Mô tả chuyên môn",
            "room_number": "Phòng làm việc",
        }


class DoctorSettingsForm(forms.ModelForm):
    class Meta:
        model = DoctorSettings
        fields = [
            "degree_title",
            "default_work_days",
            "default_start_time",
            "default_end_time",
            "default_slot_minutes",
            "notify_web",
            "notify_today_shift",
        ]
        labels = {
            "degree_title": "Học vị/Chức danh",
            "default_work_days": "Ngày làm việc (VD: Mon,Tue,Wed)",
            "default_start_time": "Giờ bắt đầu",
            "default_end_time": "Giờ kết thúc",
            "default_slot_minutes": "Thời lượng slot (phút)",
            "notify_web": "Nhận thông báo qua web",
            "notify_today_shift": "Thông báo ca trực hôm nay",
        }


