# JavaScript Architecture - DUT Hospital

## Cấu trúc file JavaScript

### Core Files
- **`main.js`** - Entry point chính, khởi tạo ứng dụng và quản lý global events
- **`global-alerts.js`** - Hệ thống thông báo toàn cục với hiệu ứng animation
- **`common-utils.js`** - Các utility functions dùng chung

### Feature-specific Files
- **`auth-forms.js`** - Xử lý form đăng nhập, đăng ký, đổi mật khẩu
- **`profile-forms.js`** - Xử lý form profile và các tương tác liên quan
- **`auth.js`** - Các chức năng authentication cơ bản (existing)

## Thứ tự load JavaScript

```html
<!-- Bootstrap JS -->
<script src="{% static 'js/bootstrap.bundle.min.js' %}"></script>
<script src="{% static 'js/auth.js' %}"></script>
<script src="{% static 'js/global-alerts.js' %}"></script>
<script src="{% static 'js/common-utils.js' %}"></script>
<script src="{% static 'js/auth-forms.js' %}"></script>
<script src="{% static 'js/profile-forms.js' %}"></script>
<script src="{% static 'js/main.js' %}"></script>
```

## Cách sử dụng

### Global Functions
```javascript
// Thông báo
showSuccessAlert('Thành công!');
showErrorAlert('Có lỗi!');
showCustomAlert('Thông báo', 'info', '.container', 'afterbegin');

// Utilities
Utils.formatPhone('0123456789');
Utils.validateEmail('test@example.com');
Utils.copyToClipboard('Text to copy');
```

### Module-specific Functions
```javascript
// Auth forms
togglePassword('password_field');

// Profile forms
// Tự động khởi tạo khi có form profile
```

## Debugging

Trên localhost, debug mode sẽ tự động bật:
```javascript
App.showInfo(); // Hiển thị thông tin ứng dụng
App.config.debug = true; // Bật debug logging
```

## Thêm module mới

1. Tạo file JavaScript mới trong thư mục `js/`
2. Thêm vào template theo thứ tự dependency
3. Khởi tạo trong `main.js` nếu cần
4. Export functions global nếu cần sử dụng từ bên ngoài

## Best Practices

- Sử dụng `Utils.debounce()` cho các event handlers có thể gọi nhiều lần
- Sử dụng `showCustomAlert()` thay vì `alert()` native
- Validate form data trước khi submit
- Sử dụng `Utils.showLoading()` và `Utils.hideLoading()` cho buttons
- Export functions cần thiết ra global scope
