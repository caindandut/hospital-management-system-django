/**
 * Common Utilities JavaScript
 * Shared utility functions used across the application
 */

// Utility functions for common operations
const Utils = {
    /**
     * Format phone number
     * @param {string} phone - Phone number to format
     * @returns {string} - Formatted phone number
     */
    formatPhone: function(phone) {
        if (!phone) return '';
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.length === 10) {
            return cleaned.replace(/(\d{4})(\d{3})(\d{3})/, '$1 $2 $3');
        }
        return phone;
    },

    /**
     * Validate email format
     * @param {string} email - Email to validate
     * @returns {boolean} - True if valid email
     */
    validateEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Validate phone number format
     * @param {string} phone - Phone number to validate
     * @returns {boolean} - True if valid phone
     */
    validatePhone: function(phone) {
        const phoneRegex = /^[\+]?[0-9\s\-\(\)]+$/;
        return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
    },

    /**
     * Debounce function to limit function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} - Debounced function
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Show loading state
     * @param {HTMLElement} element - Element to show loading state
     */
    showLoading: function(element) {
        if (element) {
            element.disabled = true;
            const originalText = element.textContent;
            element.setAttribute('data-original-text', originalText);
            element.innerHTML = '<i class="bi bi-hourglass-split"></i> Đang xử lý...';
        }
    },

    /**
     * Hide loading state
     * @param {HTMLElement} element - Element to hide loading state
     */
    hideLoading: function(element) {
        if (element) {
            element.disabled = false;
            const originalText = element.getAttribute('data-original-text');
            if (originalText) {
                element.textContent = originalText;
                element.removeAttribute('data-original-text');
            }
        }
    },

    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     * @returns {Promise<boolean>} - True if successful
     */
    copyToClipboard: async function(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                document.body.removeChild(textArea);
                return true;
            } catch (err) {
                document.body.removeChild(textArea);
                return false;
            }
        }
    },

    /**
     * Format date to Vietnamese format
     * @param {Date|string} date - Date to format
     * @returns {string} - Formatted date
     */
    formatDate: function(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('vi-VN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    },

    /**
     * Format currency to Vietnamese format
     * @param {number} amount - Amount to format
     * @returns {string} - Formatted currency
     */
    formatCurrency: function(amount) {
        if (amount === null || amount === undefined) return '0 ₫';
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(amount);
    }
};

// Export Utils for global use
window.Utils = Utils;
