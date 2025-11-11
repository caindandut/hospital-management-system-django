from django import forms


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(label="Mật khẩu hiện tại", widget=forms.PasswordInput)
    new_password1    = forms.CharField(label="Mật khẩu mới", widget=forms.PasswordInput)
    new_password2    = forms.CharField(label="Nhập lại mật khẩu mới", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1") or ""
        p2 = cleaned.get("new_password2") or ""
        if p1 != p2:
            raise forms.ValidationError("Mật khẩu nhập lại không khớp.")
        if len(p1) < 8 or p1.isdigit() or p1.isalpha():
            raise forms.ValidationError("Mật khẩu mới phải ≥ 8 ký tự và gồm cả chữ & số.")
        return cleaned


