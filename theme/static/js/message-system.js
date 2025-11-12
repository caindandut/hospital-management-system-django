/**
 * React-Style Toast System for DUT Hospital
 * Modern toast notifications with smooth animations
 */

// Toast configuration
const TOAST_CONFIG = {
    success: {
        bgColor: '#10b981',
        icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>`,
        duration: 4000,
        autoHide: true
    },
    error: {
        bgColor: '#ef4444',
        icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>`,
        duration: 5000,
        autoHide: true
    },
    warning: {
        bgColor: '#f59e0b',
        icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/></svg>`,
        duration: 5000,
        autoHide: true
    },
    info: {
        bgColor: '#3b82f6',
        icon: `<svg viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>`,
        duration: 4000,
        autoHide: true
    }
};

// Initialize toast system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeToastSystem();
});

/**
 * Initialize the toast system
 */
function initializeToastSystem() {
    createToastContainer();
    processDjangoMessages();
}

/**
 * Create the toast container
 */
function createToastContainer() {
    // Use existing message-container or create new one
    let container = document.getElementById('message-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'message-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    } else {
        container.className = 'toast-container';
    }
    return container;
}

/**
 * Process Django messages from the server
 */
function processDjangoMessages() {
    const processedMessages = new Set();
    
    // Check for Django messages in JSON script tag
    const messageScript = document.getElementById('django-messages');
    if (messageScript) {
        try {
            const messages = JSON.parse(messageScript.textContent);
            messages.forEach(function(msg) {
                const messageKey = msg.type + ':' + msg.text;
                if (!processedMessages.has(messageKey)) {
                    processedMessages.add(messageKey);
                    showToast(msg.text, msg.type);
                }
            });
        } catch (e) {
            console.error('Could not parse Django messages:', e);
        }
    }
    
    // Remove old-style alerts if any exist
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => alert.remove());
}

/**
 * Show a toast notification
 * @param {string} message - The message text
 * @param {string} type - The toast type (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    const container = createToastContainer();
    const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const config = TOAST_CONFIG[type] || TOAST_CONFIG.info;
    
    // Create toast element
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    
    // Create toast content
    toast.innerHTML = `
        <div class="toast-icon">
            ${config.icon}
        </div>
        <div class="toast-content">
            <div class="toast-message">${escapeHtml(message)}</div>
        </div>
        <button class="toast-close" aria-label="Close">
            <svg viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
            </svg>
        </button>
        <div class="toast-progress"></div>
    `;
    
    // Add to container
    container.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Setup close button
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => hideToast(toastId));
    
    // Auto-hide functionality
    if (config.autoHide) {
        const progressBar = toast.querySelector('.toast-progress');
        let remainingTime = config.duration;
        let startTime = Date.now();
        let timeoutId;
        let isPaused = false;
        
        // Start progress animation
        setTimeout(() => {
            progressBar.style.transition = `width ${config.duration}ms linear`;
            progressBar.style.width = '0%';
        }, 10);
        
        const startTimer = () => {
            timeoutId = setTimeout(() => {
                hideToast(toastId);
            }, remainingTime);
        };
        
        startTimer();
        
        // Pause on hover
        toast.addEventListener('mouseenter', () => {
            if (!isPaused) {
                clearTimeout(timeoutId);
                remainingTime -= (Date.now() - startTime);
                progressBar.style.transition = 'none';
                const currentWidth = parseFloat(getComputedStyle(progressBar).width);
                progressBar.style.width = currentWidth + 'px';
                isPaused = true;
            }
        });
        
        // Resume on leave
        toast.addEventListener('mouseleave', () => {
            if (isPaused) {
                startTime = Date.now();
                progressBar.style.transition = `width ${remainingTime}ms linear`;
                progressBar.style.width = '0%';
                startTimer();
                isPaused = false;
            }
        });
    }
    
    return toastId;
}

/**
 * Hide a toast notification
 * @param {string} toastId - The toast ID to hide
 */
function hideToast(toastId) {
    const toast = document.getElementById(toastId);
    if (toast) {
        toast.classList.remove('show');
        toast.classList.add('hide');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

/**
 * Show success toast
 * @param {string} message - The success message
 */
function showSuccessMessage(message) {
    return showToast(message, 'success');
}

/**
 * Show error toast
 * @param {string} message - The error message
 */
function showErrorMessage(message) {
    return showToast(message, 'error');
}

/**
 * Show warning toast
 * @param {string} message - The warning message
 */
function showWarningMessage(message) {
    return showToast(message, 'warning');
}

/**
 * Show info toast
 * @param {string} message - The info message
 */
function showInfoMessage(message) {
    return showToast(message, 'info');
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - The text to escape
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add CSS styles
const style = document.createElement('style');
style.textContent = `
    .toast-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 12px;
        max-width: 420px;
        pointer-events: none;
    }
    
    @media (max-width: 768px) {
        .toast-container {
            top: 10px;
            right: 10px;
            left: 10px;
            max-width: none;
        }
    }
    
    .toast {
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);
        padding: 16px;
        display: flex;
        align-items: start;
        gap: 12px;
        min-height: 64px;
        position: relative;
        overflow: hidden;
        pointer-events: auto;
        transform: translateX(calc(100% + 20px));
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .toast.show {
        transform: translateX(0);
        opacity: 1;
    }
    
    .toast.hide {
        transform: translateX(calc(100% + 20px));
        opacity: 0;
    }
    
    .toast-icon {
        width: 24px;
        height: 24px;
        flex-shrink: 0;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 4px;
    }
    
    .toast-icon svg {
        width: 100%;
        height: 100%;
    }
    
    .toast-success .toast-icon {
        background: #d1fae5;
        color: #10b981;
    }
    
    .toast-error .toast-icon {
        background: #fee2e2;
        color: #ef4444;
    }
    
    .toast-warning .toast-icon {
        background: #fef3c7;
        color: #f59e0b;
    }
    
    .toast-info .toast-icon {
        background: #dbeafe;
        color: #3b82f6;
    }
    
    .toast-content {
        flex: 1;
        min-width: 0;
        padding-top: 2px;
    }
    
    .toast-message {
        color: #1f2937;
        font-size: 14px;
        line-height: 1.5;
        font-weight: 500;
        word-wrap: break-word;
    }
    
    .toast-close {
        width: 20px;
        height: 20px;
        flex-shrink: 0;
        background: none;
        border: none;
        padding: 0;
        cursor: pointer;
        color: #9ca3af;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 4px;
        transition: all 0.2s;
    }
    
    .toast-close:hover {
        background: #f3f4f6;
        color: #4b5563;
    }
    
    .toast-close:active {
        background: #e5e7eb;
    }
    
    .toast-close svg {
        width: 16px;
        height: 16px;
    }
    
    .toast-progress {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 4px;
        width: 100%;
        background: rgba(0, 0, 0, 0.1);
        transform-origin: left;
    }
    
    .toast-success .toast-progress {
        background: #10b981;
    }
    
    .toast-error .toast-progress {
        background: #ef4444;
    }
    
    .toast-warning .toast-progress {
        background: #f59e0b;
    }
    
    .toast-info .toast-progress {
        background: #3b82f6;
    }
    
    @keyframes toast-in {
        from {
            transform: translateX(calc(100% + 20px));
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes toast-out {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(calc(100% + 20px));
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Export functions for global use
window.showToast = showToast;
window.showSuccessMessage = showSuccessMessage;
window.showErrorMessage = showErrorMessage;
window.showWarningMessage = showWarningMessage;
window.showInfoMessage = showInfoMessage;
window.hideToast = hideToast;
window.showMessage = showToast; // Alias for backward compatibility
window.showInlineMessage = showToast; // Alias for backward compatibility
