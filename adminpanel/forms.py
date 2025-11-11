from django import forms
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.forms import DateInput, TextInput, PasswordInput, CheckboxInput, Select
from .models import Specialty, DoctorRankFee, Drug, UserLite
from accounts.models import Users
from patients.models import PatientProfiles

class SpecialtyForm(forms.ModelForm):
    class Meta:
        model = Specialty
        fields = ["name", "description"]

class RankFeeForm(forms.ModelForm):
    class Meta:
        model = DoctorRankFee
        fields = ["rank", "default_fee"]

class DrugForm(forms.ModelForm):
    class Meta:
        model = Drug
        fields = ["code", "name", "unit", "unit_price", "quantity", "is_active"]
        widgets = {
            "unit_price": forms.NumberInput(attrs={"step": "100", "min": "0"}),
            "quantity": forms.NumberInput(attrs={"min": "0"}),
        }

    def clean_quantity(self):
        q = self.cleaned_data.get("quantity") or 0
        if q < 0:
            raise forms.ValidationError("Số lượng không được âm.")
        return q

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserLite
        fields = ["role", "is_active"]

class CreateUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mật khẩu")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Nhập lại mật khẩu")

    class Meta:
        model = UserLite
        fields = ["full_name", "email", "phone", "role", "is_active", "password", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if UserLite.objects.filter(email=email).exists():
            raise forms.ValidationError("Email đã tồn tại.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password2"):
            self.add_error("password2", "Mật khẩu nhập lại không khớp.")
        return cleaned

    def save(self, commit=True):
        # Ghi ra users.password_hash = make_password(...)
        user = super().save(commit=False)
        user.password_hash = make_password(self.cleaned_data["password"])
        now = timezone.now()
        user.created_at = now
        user.updated_at = now
        if commit:
            user.save(using=self._meta.model.objects.db)  # dùng DB mặc định
        return user

class UpdateUserForm(forms.ModelForm):
    new_password = forms.CharField(
        label="Mật khẩu mới (tuỳ chọn)", widget=forms.PasswordInput, required=False
    )
    confirm_password = forms.CharField(
        label="Nhập lại mật khẩu", widget=forms.PasswordInput, required=False
    )

    class Meta:
        model = UserLite
        fields = ["full_name", "email", "phone", "role", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # chuẩn hoá email hiển thị
        if self.instance and self.instance.email:
            self.initial["email"] = self.instance.email.lower()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = UserLite.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Email đã tồn tại.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password")
        p2 = cleaned.get("confirm_password")
        if p1 or p2:
            if p1 != p2:
                self.add_error("confirm_password", "Mật khẩu nhập lại không khớp.")
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        p = self.cleaned_data.get("new_password")
        if p:
            obj.password_hash = make_password(p)
        if commit:
            obj.save(using=self._meta.model.objects.db)
        return obj


# ==================== PATIENT FORMS (server-rendered) ====================
class PatientCreateForm(forms.Form):
    full_name = forms.CharField(label="Họ và tên", max_length=255,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Nhập họ và tên"}))
    email = forms.EmailField(label="Email",
        widget=TextInput(attrs={"class": "form-control", "placeholder": "name@example.com"}))
    password = forms.CharField(label="Mật khẩu",
        widget=PasswordInput(attrs={"class": "form-control", "placeholder": "Mật khẩu đăng nhập"}), required=False)
    phone = forms.CharField(label="Số điện thoại", max_length=20, required=False,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "VD: 0912345678"}))
    cccd = forms.CharField(label="CCCD", max_length=20,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Nhập CCCD"}))
    date_of_birth = forms.DateField(label="Ngày sinh", required=False,
        widget=DateInput(attrs={"class": "form-control", "type": "date"}))
    gender = forms.ChoiceField(label="Giới tính",
        choices=[("", "--"), ("MALE", "Nam"), ("FEMALE", "Nữ"), ("OTHER", "Khác")], required=False,
        widget=Select(attrs={"class": "form-select"}))
    address = forms.CharField(label="Địa chỉ", max_length=255, required=False,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Nhập địa chỉ liên hệ"}))
    is_active = forms.BooleanField(label="Tài khoản đang hoạt động", required=False, initial=True,
        widget=CheckboxInput(attrs={"class": "form-check-input"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Users.objects.filter(email=email).exists():
            raise forms.ValidationError("Email đã tồn tại.")
        return email

    def clean_cccd(self):
        cccd = self.cleaned_data["cccd"].strip()
        if not cccd:
            raise forms.ValidationError("CCCD là bắt buộc.")
        if PatientProfiles.objects.filter(cccd=cccd).exists():
            raise forms.ValidationError("CCCD đã tồn tại.")
        return cccd

    def save(self):
        data = self.cleaned_data
        user = Users.objects.create(
            email=data["email"],
            full_name=data["full_name"],
            phone=data.get("phone") or None,
            role="PATIENT",
            is_active=1 if data.get("is_active") else 0,
            password_hash=make_password(data.get("password") or "12345678"),
        )
        PatientProfiles.objects.create(
            user=user,
            cccd=data["cccd"],
            date_of_birth=data.get("date_of_birth") or None,
            gender=data.get("gender") or None,
            address=data.get("address") or None,
        )
        return user


class PatientUpdateForm(forms.Form):
    full_name = forms.CharField(label="Họ và tên", max_length=255,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Nhập họ và tên"}))
    phone = forms.CharField(label="Số điện thoại", max_length=20, required=False,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "VD: 0912345678"}))
    password = forms.CharField(label="Mật khẩu (để trống nếu không đổi)", required=False,
        widget=PasswordInput(attrs={"class": "form-control", "placeholder": "Để trống nếu không đổi"}))
    cccd = forms.CharField(label="CCCD", max_length=20,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Nhập CCCD"}))
    date_of_birth = forms.DateField(label="Ngày sinh", required=False,
        widget=DateInput(attrs={"class": "form-control", "type": "date"}))
    gender = forms.ChoiceField(label="Giới tính",
        choices=[("MALE", "Nam"), ("FEMALE", "Nữ"), ("OTHER", "Khác")], required=False,
        widget=Select(attrs={"class": "form-select"}))
    address = forms.CharField(label="Địa chỉ", max_length=255, required=False,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Nhập địa chỉ liên hệ"}))
    is_active = forms.BooleanField(label="Tài khoản đang hoạt động", required=False,
        widget=CheckboxInput(attrs={"class": "form-check-input"}))

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop("user_instance", None)
        self.profile_instance = kwargs.pop("profile_instance", None)
        super().__init__(*args, **kwargs)
        if self.user_instance:
            self.fields["is_active"].initial = bool(self.user_instance.is_active)

    def clean_cccd(self):
        cccd = self.cleaned_data["cccd"].strip()
        qs = PatientProfiles.objects.filter(cccd=cccd)
        if self.profile_instance:
            qs = qs.exclude(pk=self.profile_instance.pk)
        if qs.exists():
            raise forms.ValidationError("CCCD đã tồn tại.")
        return cccd

    def save(self):
        data = self.cleaned_data
        u = self.user_instance
        p = self.profile_instance
        u.full_name = data["full_name"]
        u.phone = data.get("phone") or None
        u.is_active = 1 if data.get("is_active") else 0
        if data.get("password"):
            u.password_hash = make_password(data["password"])
        u.save()

        p.cccd = data["cccd"]
        p.date_of_birth = data.get("date_of_birth") or None
        p.gender = data.get("gender") or None
        p.address = data.get("address") or None
        p.save()
        return u
