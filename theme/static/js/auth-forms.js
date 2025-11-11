/**
 * Authentication Forms JavaScript
 * Handles form validation and interactions for login, register, and change password pages
 */

// Login form validation
function initLoginForm() {
    const loginForm = document.querySelector('.auth-form');
    if (!loginForm) return;

    loginForm.addEventListener('submit', function(e) {
        const loginField = document.getElementById('login_field').value.trim();
        const password = document.getElementById('password').value;
        
        if (!loginField) {
            e.preventDefault();
            showErrorMessage('Vui lòng nhập email hoặc số điện thoại!');
            return false;
        }
        
        if (!password) {
            e.preventDefault();
            showErrorMessage('Vui lòng nhập mật khẩu!');
            return false;
        }
    });
}

// Register form validation
function initRegisterForm() {
    const registerForm = document.querySelector('.auth-form');
    if (!registerForm) return;

    registerForm.addEventListener('submit', function(e) {
        const firstName = document.getElementById('first_name').value.trim();
        const lastName = document.getElementById('last_name').value.trim();
        const email = document.getElementById('email').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const password1 = document.getElementById('password1').value;
        const password2 = document.getElementById('password2').value;
        const terms = document.getElementById('terms').checked;
        
        if (!firstName) {
            e.preventDefault();
            showErrorMessage('Vui lòng nhập họ!');
            return false;
        }
        
        if (!lastName) {
            e.preventDefault();
            showErrorMessage('Vui lòng nhập tên!');
            return false;
        }
        
        if (!email) {
            e.preventDefault();
            showErrorMessage('Vui lòng nhập email!');
            return false;
        }
        
        if (!phone) {
            e.preventDefault();
            showErrorMessage('Vui lòng nhập số điện thoại!');
            return false;
        }
        
        if (!password1) {
            e.preventDefault();
            showErrorMessage('Vui lòng nhập mật khẩu!');
            return false;
        }
        
        if (password1.length < 8) {
            e.preventDefault();
            showErrorMessage('Mật khẩu phải có ít nhất 8 ký tự!');
            return false;
        }
        
        if (password1 !== password2) {
            e.preventDefault();
            showErrorMessage('Mật khẩu xác nhận không khớp!');
            return false;
        }
        
        if (!terms) {
            e.preventDefault();
            showErrorMessage('Vui lòng đồng ý với điều khoản sử dụng!');
            return false;
        }
    });
}

// Change password form validation
function initChangePasswordForm() {
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (!changePasswordForm) return;

    changePasswordForm.addEventListener('submit', function(e) {
        const newPassword = document.getElementById('new_password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        
        if (newPassword !== confirmPassword) {
            e.preventDefault();
            showErrorMessage('Mật khẩu xác nhận không khớp!');
            return false;
        }
        
        if (newPassword.length < 8) {
            e.preventDefault();
            showErrorMessage('Mật khẩu mới phải có ít nhất 8 ký tự!');
            return false;
        }
    });
}

// Password toggle functionality
function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    const icon = document.getElementById(fieldId + '_icon');
    
    if (field.type === 'password') {
        field.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        field.type = 'password';
        icon.className = 'bi bi-eye';
    }
}

// Initialize forms based on page
document.addEventListener('DOMContentLoaded', function() {
    // Check which page we're on and initialize appropriate form
    if (document.querySelector('#login_field')) {
        initLoginForm();
    } else if (document.querySelector('#first_name')) {
        initRegisterForm();
    } else if (document.querySelector('#changePasswordForm')) {
        initChangePasswordForm();
    }
});

// Export functions for global use
window.togglePassword = togglePassword;
