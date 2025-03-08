"""
ArbitrageX Notification System

This package provides real-time notification capabilities for the ArbitrageX trading bot.
It supports multiple notification channels, including email, Telegram, Slack, webhooks, and console.
"""

from .notification_manager import (
    NotificationManager,
    NotificationCategory,
    NotificationPriority,
    NotificationChannel,
    Notification
)

# Version
__version__ = "1.0.0"

# Create a singleton instance for easy access
# (will be initialized when first accessed)
_notification_manager = None

def get_notification_manager():
    """
    Get the singleton notification manager instance.
    
    Returns:
        NotificationManager: The notification manager instance
    """
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager

def notify(title, message, category, priority="MEDIUM", data=None, channels=None):
    """
    Send a notification.
    
    Args:
        title (str): Notification title
        message (str): Notification message
        category (str or NotificationCategory): Notification category
        priority (str or NotificationPriority, optional): Notification priority. Defaults to "MEDIUM".
        data (dict, optional): Additional data for the notification. Defaults to None.
        channels (list, optional): Specific channels to send to. Defaults to None.
        
    Returns:
        str: Notification ID
    """
    manager = get_notification_manager()
    return manager.notify(title, message, category, priority, data, channels)

def notify_from_template(template_name, **kwargs):
    """
    Send a notification using a template.
    
    Args:
        template_name (str): Name of the template to use
        **kwargs: Values for template placeholders
        
    Returns:
        str: Notification ID or None if template not found
    """
    manager = get_notification_manager()
    return manager.notify_from_template(template_name, **kwargs)

def shutdown():
    """Shutdown the notification manager."""
    global _notification_manager
    if _notification_manager is not None:
        _notification_manager.shutdown()
        _notification_manager = None 