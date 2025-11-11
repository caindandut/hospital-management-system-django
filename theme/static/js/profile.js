// Patient Profile JavaScript
let isEditMode = false;
let originalValues = {};

// Store original values when page loads
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('profileForm');
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        originalValues[input.name] = input.value;
    });
    
    // Disable all form inputs initially
    setFormInputsState(false);
});

function toggleEditMode() {
    isEditMode = !isEditMode;
    const editBtn = document.getElementById('editToggleBtn');
    const saveBtn = document.getElementById('saveBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    
    if (isEditMode) {
        // Switch to edit mode
        editBtn.style.display = 'none';
        saveBtn.style.display = 'inline-block';
        cancelBtn.style.display = 'inline-block';
        setFormInputsState(true);
    } else {
        // Switch to view mode
        editBtn.style.display = 'inline-block';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';
        setFormInputsState(false);
    }
}

function cancelEdit() {
    // Restore original values
    const form = document.getElementById('profileForm');
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.value = originalValues[input.name] || '';
    });
    
    // Switch back to view mode
    toggleEditMode();
}

function setFormInputsState(enabled) {
    const form = document.getElementById('profileForm');
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.disabled = !enabled;
        if (enabled) {
            input.classList.remove('form-control-disabled');
        } else {
            input.classList.add('form-control-disabled');
        }
    });
}

// Handle form submission
document.getElementById('profileForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevent default form submission
    
    if (isEditMode) {
        // Validate form before submission
        if (validateForm()) {
            // Show loading state
            showLoadingState();
            
            // Prepare form data
            const formData = new FormData(this);
            
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfToken) {
                hideLoadingState();
                showErrorMessage('Không tìm thấy CSRF token. Vui lòng tải lại trang.');
                return;
            }
            
            console.log('CSRF Token found:', csrfToken.value);
            console.log('Sending request to:', window.location.href);

            // Debug: Log form data
            console.log('Form data being sent:');
            for (let [key, value] of formData.entries()) {
                console.log(key, value);
            }

            // Send data to server
            fetch(window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken.value,
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => {
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);
                
                if (response.ok) {
                    // Check if response is JSON
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return response.json();
                    } else {
                        // If not JSON, assume success
                        return { success: true, message: 'Lưu thông tin thành công!' };
                    }
                } else {
                    // Handle different HTTP status codes
                    if (response.status === 403) {
                        throw new Error('Lỗi xác thực. Vui lòng đăng nhập lại.');
                    } else if (response.status === 500) {
                        throw new Error('Lỗi server. Vui lòng thử lại sau.');
                    } else {
                        throw new Error(`Lỗi HTTP ${response.status}: ${response.statusText}`);
                    }
                }
            })
            .then(data => {
                // Hide loading state
                hideLoadingState();
                
                if (data.success) {
                    // Show success message
                    showSuccessMessage(data.message || 'Lưu thông tin thành công!');
                    
                    // Update original values
                    const inputs = this.querySelectorAll('input, select, textarea');
                    inputs.forEach(input => {
                        originalValues[input.name] = input.value;
                    });
                    
                    // Switch back to view mode
                    toggleEditMode();
                } else {
                    // Show error message
                    showErrorMessage(data.message || 'Có lỗi xảy ra khi lưu thông tin');
                }
            })
            .catch(error => {
                // Hide loading state
                hideLoadingState();
                
                // Show detailed error message
                console.error('Detailed error:', error);
                showErrorMessage(error.message || 'Có lỗi xảy ra khi kết nối đến server');
            });
        }
    }
});

function validateForm() {
    const form = document.getElementById('profileForm');
    const requiredFields = ['full_name', 'cccd', 'date_of_birth', 'gender'];
    let isValid = true;
    
    // Clear previous validation errors
    clearValidationErrors();
    
    // Validate required fields
    requiredFields.forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field && (!field.value || field.value.trim() === '')) {
            showFieldError(field, 'Trường này là bắt buộc');
            isValid = false;
        }
    });
    
    // Validate email format
    const emailField = form.querySelector('[name="email"]');
    if (emailField && emailField.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailField.value)) {
            showFieldError(emailField, 'Email không hợp lệ');
            isValid = false;
        }
    }
    
    // Validate phone number
    const phoneField = form.querySelector('[name="phone"]');
    if (phoneField && phoneField.value) {
        const phoneRegex = /^[0-9]{10,11}$/;
        if (!phoneRegex.test(phoneField.value.replace(/\s/g, ''))) {
            showFieldError(phoneField, 'Số điện thoại không hợp lệ (10-11 số)');
            isValid = false;
        }
    }
    
    // Validate emergency phone number
    const emergencyPhoneField = form.querySelector('[name="emergency_contact_phone"]');
    if (emergencyPhoneField && emergencyPhoneField.value) {
        const phoneRegex = /^[0-9]{10,11}$/;
        if (!phoneRegex.test(emergencyPhoneField.value.replace(/\s/g, ''))) {
            showFieldError(emergencyPhoneField, 'Số điện thoại khẩn cấp không hợp lệ (10-11 số)');
            isValid = false;
        }
    }
    
    return isValid;
}

function showFieldError(field, message) {
    field.classList.add('is-invalid');
    
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

function clearValidationErrors() {
    const form = document.getElementById('profileForm');
    const invalidFields = form.querySelectorAll('.is-invalid');
    const errorMessages = form.querySelectorAll('.invalid-feedback');
    
    invalidFields.forEach(field => field.classList.remove('is-invalid'));
    errorMessages.forEach(error => error.remove());
}

function showLoadingState() {
    const saveBtn = document.getElementById('saveBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Đang lưu...';
    saveBtn.disabled = true;
    saveBtn.setAttribute('data-original-text', originalText);
}

function hideLoadingState() {
    const saveBtn = document.getElementById('saveBtn');
    const originalText = saveBtn.getAttribute('data-original-text');
    saveBtn.innerHTML = originalText;
    saveBtn.disabled = false;
}

function showSuccessMessage(message) {
    showToast(message, 'success');
}

function showErrorMessage(message) {
    showToast(message, 'error');
}

function showToast(message, type) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    
    const icon = type === 'success' ? 'bi-check-circle-fill' : 'bi-exclamation-triangle-fill';
    const color = type === 'success' ? '#198754' : '#dc3545';
    
    toast.innerHTML = `
        <div class="toast-content">
            <i class="bi ${icon}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add styles
    toast.style.borderLeftColor = color;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Hide toast after 4 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 4000);
}
