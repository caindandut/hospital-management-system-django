/**
 * Unified Message System for DUT Hospital
 * Handles all success and error messages consistently
 */

// Message configuration
const MESSAGE_CONFIG = {
    success: {
        color: '#28a745', // Green
        icon: '✓',
        duration: 5000, // 5 seconds
        autoHide: true
    },
    error: {
        color: '#dc3545', // Red
        icon: '!',
        duration: 8000, // 8 seconds
        autoHide: true
    }
};

// Initialize message system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeMessageSystem();
});

/**
 * Initialize the message system
 */
function initializeMessageSystem() {
    // Create message container if it doesn't exist
    createMessageContainer();
    
    // Process any existing Django messages
    processDjangoMessages();
}

/**
 * Create the message container
 */
function createMessageContainer() {
    let container = document.getElementById('message-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'message-container';
        container.className = 'message-container';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Process Django messages from the server
 */
function processDjangoMessages() {
    const processedMessages = new Set();
    
    // Check for Django messages in the page
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(function(alert) {
        const messageText = extractMessageText(alert);
        const messageType = determineMessageType(alert);
        
        // Skip duplicate messages
        const messageKey = messageType + ':' + messageText;
        if (processedMessages.has(messageKey)) {
            alert.remove();
            return;
        }
        processedMessages.add(messageKey);
        
        // Show the message using our unified system
        showMessage(messageText, messageType);
        
        // Remove the original alert
        alert.remove();
    });
    
    // Also check for Django messages in JSON script tag
    const messageScript = document.getElementById('django-messages');
    if (messageScript) {
        try {
            const messages = JSON.parse(messageScript.textContent);
            messages.forEach(function(msg) {
                const messageKey = msg.type + ':' + msg.text;
                if (!processedMessages.has(messageKey)) {
                    processedMessages.add(messageKey);
                    showMessage(msg.text, msg.type);
                }
            });
        } catch (e) {
            console.log('Could not parse Django messages from script tag');
        }
    }
}

/**
 * Extract clean message text from alert element
 */
function extractMessageText(alert) {
    let text = alert.textContent.trim();
    
    // Remove close button text
    const closeButton = alert.querySelector('.btn-close');
    if (closeButton) {
        text = text.replace(closeButton.textContent, '').trim();
    }
    
    // Remove icon text
    const icon = alert.querySelector('i');
    if (icon) {
        text = text.replace(icon.textContent, '').trim();
    }
    
    return text;
}

/**
 * Determine message type from CSS classes
 */
function determineMessageType(alert) {
    if (alert.classList.contains('alert-success')) {
        return 'success';
    } else if (alert.classList.contains('alert-danger') || alert.classList.contains('alert-error')) {
        return 'error';
    } else if (alert.classList.contains('alert-warning')) {
        return 'warning';
    } else if (alert.classList.contains('alert-info')) {
        return 'info';
    }
    return 'info';
}

/**
 * Show inline message in auth form
 * @param {string} text - The message text
 * @param {string} type - The message type (success, error, warning, info)
 */
function showInlineMessage(text, type = 'info') {
    const messageId = 'inline-message-' + Date.now();
    const config = MESSAGE_CONFIG[type] || MESSAGE_CONFIG.error;
    
    // Remove any existing inline messages
    const existingMessages = document.querySelectorAll('.inline-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Find the auth form
    const authForm = document.querySelector('.auth-form');
    if (!authForm) return;
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.id = messageId;
    messageElement.className = 'inline-message inline-message-' + type;
    messageElement.style.cssText = `
        background: ${config.color};
        color: white;
        padding: 8px 12px;
        margin: 0 0 0.75rem 0;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 500;
        font-size: 13px;
        position: relative;
        overflow: hidden;
        animation: slideInFromTop 0.3s ease-out;
        border-left: 3px solid rgba(255, 255, 255, 0.4);
    `;
    
    // Add icon
    const iconElement = document.createElement('span');
    iconElement.className = 'inline-message-icon';
    iconElement.textContent = config.icon;
    iconElement.style.cssText = `
        background: rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
        flex-shrink: 0;
        margin-right: 6px;
    `;
    
    // Add text
    const textElement = document.createElement('span');
    textElement.className = 'inline-message-text';
    textElement.textContent = text;
    textElement.style.cssText = `
        flex: 1;
        line-height: 1.4;
    `;
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.className = 'inline-message-close';
    closeButton.innerHTML = '×';
    closeButton.style.cssText = `
        background: none;
        border: none;
        color: white;
        font-size: 16px;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.8;
        transition: opacity 0.2s;
        margin-left: auto;
        font-weight: bold;
    `;
    
    // Assemble message
    messageElement.appendChild(iconElement);
    messageElement.appendChild(textElement);
    messageElement.appendChild(closeButton);
    
    // Insert at the beginning of the form
    authForm.insertBefore(messageElement, authForm.firstChild);
    
    // Close button functionality
    closeButton.addEventListener('click', function() {
        hideInlineMessage(messageId);
    });
    
    // Auto-hide functionality
    if (config.autoHide) {
        setTimeout(function() {
            hideInlineMessage(messageId);
        }, config.duration);
    }
    
    return messageId;
}

/**
 * Hide inline message
 * @param {string} messageId - The message ID to hide
 */
function hideInlineMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.style.animation = 'slideOutToTop 0.3s ease-in forwards';
        setTimeout(function() {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 300);
    }
}

/**
 * Show a message
 * @param {string} text - The message text
 * @param {string} type - The message type (success, error, warning, info)
 */
function showMessage(text, type = 'info') {
    // Check if we're on an auth page and show inline message
    if (document.body.classList.contains('auth-body')) {
        return showInlineMessage(text, type);
    }
    
    const container = createMessageContainer();
    const messageId = 'message-' + Date.now();
    const config = MESSAGE_CONFIG[type] || MESSAGE_CONFIG.error;
    
    // Create message element
    const messageElement = document.createElement('div');
    messageElement.id = messageId;
    messageElement.className = 'message message-' + type;
    messageElement.style.cssText = `
        background: ${config.color};
        color: white;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 500;
        font-size: 13px;
        position: relative;
        overflow: hidden;
        animation: slideInFromRight 0.3s ease-out;
        max-width: 100%;
        margin-left: 0;
        margin-right: 0;
        border-left: 3px solid rgba(255, 255, 255, 0.4);
    `;
    
    // Add icon
    const iconElement = document.createElement('span');
    iconElement.className = 'message-icon';
    iconElement.textContent = config.icon;
    iconElement.style.cssText = `
        background: rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
        flex-shrink: 0;
        margin-right: 6px;
    `;
    
    // Add text
    const textElement = document.createElement('span');
    textElement.className = 'message-text';
    textElement.textContent = text;
    textElement.style.cssText = `
        flex: 1;
        line-height: 1.4;
        max-width: 320px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    `;
    
    // Add close button
    const closeButton = document.createElement('button');
    closeButton.className = 'message-close';
    closeButton.innerHTML = '×';
    closeButton.style.cssText = `
        background: none;
        border: none;
        color: white;
        font-size: 16px;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.8;
        transition: opacity 0.2s;
        margin-left: auto;
        font-weight: bold;
    `;
    
    // Add progress bar
    const progressBar = document.createElement('div');
    progressBar.className = 'message-progress';
    progressBar.style.cssText = `
        position: absolute;
        bottom: 0;
        left: 0;
        height: 3px;
        background: rgba(255, 255, 255, 0.3);
        width: 100%;
        transition: width ${config.duration}ms linear;
    `;
    
    // Assemble message
    messageElement.appendChild(iconElement);
    messageElement.appendChild(textElement);
    messageElement.appendChild(closeButton);
    messageElement.appendChild(progressBar);
    
    // Add to container
    container.appendChild(messageElement);
    
    // Add hover effects
    messageElement.addEventListener('mouseenter', function() {
        closeButton.style.opacity = '1';
    });
    
    messageElement.addEventListener('mouseleave', function() {
        closeButton.style.opacity = '0.8';
    });
    
    // Close button functionality
    closeButton.addEventListener('click', function() {
        hideMessage(messageId);
    });
    
    // Auto-hide functionality
    if (config.autoHide) {
        // Start progress bar animation
        setTimeout(() => {
            progressBar.style.width = '0%';
        }, 10);
        
        // Auto-hide with pause on hover
        let remaining = config.duration;
        let start = Date.now();
        let timer = setTimeout(function autoHide() {
            hideMessage(messageId);
        }, remaining);
        
        messageElement.addEventListener('mouseenter', function() {
            clearTimeout(timer);
            remaining -= Date.now() - start;
        });
        
        messageElement.addEventListener('mouseleave', function() {
            start = Date.now();
            timer = setTimeout(function() {
                hideMessage(messageId);
            }, remaining);
        });
    }
    
    return messageId;
}

/**
 * Hide a message
 * @param {string} messageId - The message ID to hide
 */
function hideMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.style.animation = 'slideOutToRight 0.3s ease-in forwards';
        setTimeout(function() {
            if (message.parentNode) {
                message.parentNode.removeChild(message);
            }
        }, 300);
    }
}

/**
 * Show success message
 * @param {string} text - The success message
 */
function showSuccessMessage(text) {
    return showMessage(text, 'success');
}

/**
 * Show error message
 * @param {string} text - The error message
 */
function showErrorMessage(text) {
    return showMessage(text, 'error');
}

/**
 * Show warning message
 * @param {string} text - The warning message
 */
function showWarningMessage(text) {
    return showMessage(text, 'warning');
}

/**
 * Show info message
 * @param {string} text - The info message
 */
function showInfoMessage(text) {
    return showMessage(text, 'info');
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInFromTop {
        0% {
            transform: translateY(-100%);
            opacity: 0;
        }
        100% {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes slideInFromRight {
        0% {
            transform: translateX(100%);
            opacity: 0;
        }
        100% {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutToTop {
        0% {
            transform: translateY(0);
            opacity: 1;
        }
        100% {
            transform: translateY(-100%);
            opacity: 0;
        }
    }
    
    @keyframes slideOutToRight {
        0% {
            transform: translateX(0);
            opacity: 1;
        }
        100% {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .message-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        width: auto;
        max-width: 420px;
        padding: 0;
        pointer-events: none;
    }
    
    /* Special positioning for auth pages */
    body.auth-body .message-container {
        top: 20px;
        right: 20px;
        left: auto;
        max-width: 350px;
    }
    
    /* Mobile responsive for auth pages */
    @media (max-width: 768px) {
        body.auth-body .message-container {
            top: 10px;
            right: 10px;
            left: 10px;
            max-width: none;
        }
    }
    
    .message-container .message {
        pointer-events: auto;
    }
    
    .message-close:hover {
        opacity: 1 !important;
    }
`;
document.head.appendChild(style);

// Export functions for global use
window.showMessage = showMessage;
window.showSuccessMessage = showSuccessMessage;
window.showErrorMessage = showErrorMessage;
window.showWarningMessage = showWarningMessage;
window.showInfoMessage = showInfoMessage;
window.hideMessage = hideMessage;
window.showInlineMessage = showInlineMessage;
window.hideInlineMessage = hideInlineMessage;
