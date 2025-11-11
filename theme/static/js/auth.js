function togglePassword(fieldId) {
    var passwordInput = document.getElementById(fieldId);
    var passwordIcon = document.getElementById(fieldId + '-icon');

    if (!passwordInput || !passwordIcon) {
        return;
    }

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        passwordIcon.className = 'bi bi-eye-slash';
    } else {
        passwordInput.type = 'password';
        passwordIcon.className = 'bi bi-eye';
    }
}
