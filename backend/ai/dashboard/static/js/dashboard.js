/**
 * ArbitrageX Dashboard Common JavaScript
 * 
 * This file contains common functionality used across the dashboard.
 */

// Global variables
let refreshInterval = 30000; // Default refresh interval in ms
let lastNotificationId = null;

/**
 * Initialize dashboard common functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Check for new notifications periodically
    setInterval(checkForNewNotifications, 30000);
    
    // Add event listener for theme toggle if it exists
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Toggle between light and dark theme
 */
function toggleTheme() {
    const body = document.body;
    const isDarkMode = body.classList.contains('dark-mode');
    
    if (isDarkMode) {
        body.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
    }
    
    // Update theme in settings if possible
    updateThemeSetting(!isDarkMode);
}

/**
 * Update theme setting via API
 * @param {boolean} isDarkMode - Whether dark mode is enabled
 */
function updateThemeSetting(isDarkMode) {
    fetch('/api/settings/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            appearance: {
                theme: isDarkMode ? 'dark' : 'light'
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Theme setting updated:', data);
    })
    .catch(error => {
        console.error('Error updating theme setting:', error);
    });
}

/**
 * Check for new notifications
 */
function checkForNewNotifications() {
    fetch('/api/notifications?limit=1')
        .then(response => response.json())
        .then(data => {
            if (data.notifications && data.notifications.length > 0) {
                const latestNotification = data.notifications[0];
                
                // If we have a new notification
                if (lastNotificationId !== null && lastNotificationId !== latestNotification.id) {
                    // Update badge
                    updateNotificationBadge();
                    
                    // Show browser notification if enabled
                    showBrowserNotification(latestNotification);
                }
                
                // Update last notification ID
                lastNotificationId = latestNotification.id;
            }
        })
        .catch(error => {
            console.error('Error checking for notifications:', error);
        });
}

/**
 * Update notification badge in the navbar
 */
function updateNotificationBadge() {
    fetch('/api/notifications?since=24h')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notification-badge');
            if (!badge) return;
            
            if (data.notifications && data.notifications.length > 0) {
                badge.textContent = data.notifications.length;
                badge.classList.remove('d-none');
            } else {
                badge.classList.add('d-none');
            }
        })
        .catch(error => {
            console.error('Error updating notification badge:', error);
        });
}

/**
 * Show browser notification
 * @param {Object} notification - Notification object
 */
function showBrowserNotification(notification) {
    // Check if browser notifications are supported and enabled
    if (!("Notification" in window)) {
        console.log("Browser does not support notifications");
        return;
    }
    
    // Check if permission is already granted
    if (Notification.permission === "granted") {
        createNotification(notification);
    }
    // Otherwise, request permission
    else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(function (permission) {
            if (permission === "granted") {
                createNotification(notification);
            }
        });
    }
}

/**
 * Create and show a browser notification
 * @param {Object} notification - Notification object
 */
function createNotification(notification) {
    const title = notification.title;
    const options = {
        body: notification.message,
        icon: '/static/img/logo.png',
        tag: notification.id
    };
    
    const browserNotification = new Notification(title, options);
    
    browserNotification.onclick = function() {
        window.focus();
        window.location.href = '/notifications';
        this.close();
    };
    
    // Auto close after 5 seconds
    setTimeout(browserNotification.close.bind(browserNotification), 5000);
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 * @param {boolean} includeTime - Whether to include time
 * @returns {string} Formatted date string
 */
function formatDate(dateString, includeTime = true) {
    const date = new Date(dateString);
    
    if (includeTime) {
        return date.toLocaleString();
    } else {
        return date.toLocaleDateString();
    }
}

/**
 * Format currency value
 * @param {number} value - Value to format
 * @param {string} currency - Currency code
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted currency string
 */
function formatCurrency(value, currency = 'ETH', decimals = 4) {
    return value.toFixed(decimals) + ' ' + currency;
}

/**
 * Show an alert message
 * @param {string} message - Alert message
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {number} duration - Duration in milliseconds
 */
function showAlert(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 300);
        }, duration);
    }
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Whether copy was successful
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        return navigator.clipboard.writeText(text)
            .then(() => true)
            .catch(() => false);
    } else {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        
        try {
            const successful = document.execCommand('copy');
            document.body.removeChild(textarea);
            return Promise.resolve(successful);
        } catch (err) {
            document.body.removeChild(textarea);
            return Promise.resolve(false);
        }
    }
}

/**
 * Format strategy name for display
 * @param {string} strategy - Strategy code
 * @returns {string} Formatted strategy name
 */
function formatStrategy(strategy) {
    switch (strategy) {
        case 'l2':
            return 'Layer 2';
        case 'flash':
            return 'Flash Loan';
        case 'ml_enhanced':
            return 'ML Enhanced';
        case 'combined':
            return 'Combined';
        case 'mev_protected':
            return 'MEV Protected';
        default:
            return strategy;
    }
}

/**
 * Format file size
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size string
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} Truncated text
 */
function truncateText(text, maxLength = 50) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
}

/**
 * Check system status
 */
function checkStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updateSystemStatus(data);
        })
        .catch(error => {
            console.error('Error checking status:', error);
        });
}

/**
 * Update system status display
 * @param {Object} data - Status data
 */
function updateSystemStatus(data) {
    const statusIndicator = document.getElementById('bot-status-indicator');
    const statusText = document.getElementById('bot-status-text');
    const startBtn = document.getElementById('start-bot-btn');
    const stopBtn = document.getElementById('stop-bot-btn');
    
    if (!statusIndicator || !statusText) return;
    
    if (data.status === 'running') {
        statusIndicator.className = 'status-dot status-active';
        statusText.textContent = 'Bot is running';
        if (startBtn) startBtn.style.display = 'none';
        if (stopBtn) stopBtn.style.display = 'inline-block';
    } else if (data.status === 'stopped') {
        statusIndicator.className = 'status-dot status-inactive';
        statusText.textContent = 'Bot is stopped';
        if (startBtn) startBtn.style.display = 'inline-block';
        if (stopBtn) stopBtn.style.display = 'none';
    } else {
        statusIndicator.className = 'status-dot status-unknown';
        statusText.textContent = 'Status unknown';
        if (startBtn) startBtn.style.display = 'inline-block';
        if (stopBtn) stopBtn.style.display = 'none';
    }
    
    // Update refresh time
    const refreshTime = document.getElementById('refresh-time');
    if (refreshTime) {
        refreshTime.textContent = 'Last update: ' + new Date().toLocaleTimeString();
    }
} 