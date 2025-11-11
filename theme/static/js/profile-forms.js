/**
 * Profile Forms JavaScript
 * Handles form interactions and validation for profile pages
 */

// Profile form functionality
function initProfileForm() {
    const editBtn = document.getElementById('editBtn');
    const saveBtn = document.getElementById('saveBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const form = document.getElementById('profileForm');
    const inputs = form.querySelectorAll('input, select, textarea');

    if (!editBtn || !saveBtn || !cancelBtn) return;

    // Edit button click
    editBtn.addEventListener('click', function() {
        inputs.forEach(input => {
            input.disabled = false;
            input.classList.add('form-control');
        });
        
        editBtn.style.display = 'none';
        saveBtn.style.display = 'inline-block';
        cancelBtn.style.display = 'inline-block';
    });

    // Cancel button click
    cancelBtn.addEventListener('click', function() {
        inputs.forEach(input => {
            input.disabled = true;
            input.classList.remove('form-control');
        });
        
        editBtn.style.display = 'inline-block';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';
        
        // Reset form to original values
        form.reset();
    });

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        
        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (typeof showSuccessToast === 'function') {
                    showSuccessToast(data.message || 'Cập nhật thông tin thành công!');
                } else {
                    showSuccessAlert(data.message || 'Cập nhật thông tin thành công!');
                }
                
                // Disable inputs after successful save
                inputs.forEach(input => {
                    input.disabled = true;
                    input.classList.remove('form-control');
                });
                
                editBtn.style.display = 'inline-block';
                saveBtn.style.display = 'none';
                cancelBtn.style.display = 'none';
            } else {
                if (typeof showErrorToast === 'function') {
                    showErrorToast(data.message || 'Có lỗi xảy ra khi cập nhật thông tin!');
                } else {
                    showErrorAlert(data.message || 'Có lỗi xảy ra khi cập nhật thông tin!');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (typeof showErrorToast === 'function') {
                showErrorToast('Có lỗi xảy ra khi cập nhật thông tin!');
            } else {
                showErrorAlert('Có lỗi xảy ra khi cập nhật thông tin!');
            }
        });
    });
}

// Initialize profile form when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('profileForm')) {
        initProfileForm();
    }
});
