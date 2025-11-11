/**
 * Main JavaScript Entry Point
 * Initializes all modules and handles global application setup
 */

// Application configuration
const App = {
    config: {
        debug: false,
        apiBaseUrl: '/api/',
        alertAutoHideDelay: 5000,
        animationDuration: 500
    },

    // Initialize the application
    init: function() {
        this.log('Initializing DUT Hospital Application...');
        
        // Initialize modules
        this.initModules();
        
        // Setup global event listeners
        this.setupGlobalEventListeners();
        
        this.log('Application initialized successfully');
    },

    // Initialize all modules
    initModules: function() {
        // Global alerts are initialized automatically via global-alerts.js
        // Auth forms are initialized automatically via auth-forms.js
        // Profile forms are initialized automatically via profile-forms.js
        // Common utilities are available via common-utils.js
        
        this.log('All modules initialized');
    },

    // Setup global event listeners
    setupGlobalEventListeners: function() {
        // Handle form submissions globally
        document.addEventListener('submit', function(e) {
            const form = e.target;
            if (form.classList.contains('needs-validation')) {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            }
        });

        // Handle escape key for modals and alerts
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                // Close any open modals
                const openModals = document.querySelectorAll('.modal.show');
                openModals.forEach(modal => {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                });

                // Close any alerts
                const alerts = document.querySelectorAll('.alert.show');
                alerts.forEach(alert => {
                    if (window.hideAlert) {
                        window.hideAlert(alert);
                    }
                });
            }
        });

        // Handle window resize
        window.addEventListener('resize', Utils.debounce(function() {
            // Handle responsive adjustments
            App.handleResize();
        }, 250));

        this.log('Global event listeners setup complete');
    },

    // Handle window resize
    handleResize: function() {
        // Adjust alert positioning on mobile
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (window.innerWidth < 768) {
                alert.style.maxWidth = '90%';
            } else {
                alert.style.maxWidth = '';
            }
        });
    },

    // Utility logging function
    log: function(message) {
        if (this.config.debug) {
            console.log('[DUT Hospital]', message);
        }
    },

    // Show application info
    showInfo: function() {
        console.log('DUT Hospital Application v1.0.0');
        console.log('Built with Django and Bootstrap');
        console.log('Available modules:', {
            'Global Alerts': typeof showCustomAlert !== 'undefined',
            'Auth Forms': typeof togglePassword !== 'undefined',
            'Profile Forms': typeof initProfileForm !== 'undefined',
            'Common Utils': typeof Utils !== 'undefined'
        });
    }
};

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// Make App available globally for debugging
window.App = App;

// Show info in console for debugging
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    App.config.debug = true;
    App.showInfo();
}
