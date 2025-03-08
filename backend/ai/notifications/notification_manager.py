#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Notification Manager

This module provides a notification system for the ArbitrageX trading bot,
allowing real-time alerts for important events through various channels
such as email, Telegram, and Slack.
"""

import os
import json
import time
import logging
import threading
from queue import Queue
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum, auto
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/ai/logs/notifications.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("notifications")

class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

class NotificationCategory(Enum):
    """Categories for grouping notifications."""
    TRADE = auto()
    SECURITY = auto()
    SYSTEM = auto()
    ERROR = auto()
    PERFORMANCE = auto()
    INFO = auto()

class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = auto()
    TELEGRAM = auto()
    SLACK = auto()
    WEBHOOK = auto()
    CONSOLE = auto()

class Notification:
    """
    Represents a notification with its content and metadata.
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        category: NotificationCategory,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[NotificationChannel]] = None
    ):
        """
        Initialize a notification.
        
        Args:
            title: Brief title/subject of the notification
            message: Detailed message content
            category: Category of the notification
            priority: Priority level of the notification
            data: Additional structured data related to the notification
            channels: Specific channels to send this notification to (if None, use default channels)
        """
        self.title = title
        self.message = message
        self.category = category
        self.priority = priority
        self.data = data or {}
        self.channels = channels
        self.timestamp = datetime.now()
        self.id = f"{int(time.time())}-{hash(title) % 10000}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "category": self.category.name,
            "priority": self.priority.name,
            "data": self.data,
            "channels": [c.name for c in self.channels] if self.channels else None,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create notification from dictionary."""
        notification = cls(
            title=data["title"],
            message=data["message"],
            category=NotificationCategory[data["category"]],
            priority=NotificationPriority[data["priority"]],
            data=data.get("data", {}),
            channels=[NotificationChannel[c] for c in data["channels"]] if data.get("channels") else None
        )
        notification.id = data.get("id")
        notification.timestamp = datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
        return notification
    
    def __str__(self) -> str:
        """String representation of the notification."""
        return f"[{self.priority.name}] {self.title}: {self.message} ({self.category.name})"


class NotificationManager:
    """
    Manages notifications and sends them through configured channels.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the notification manager.
        
        Args:
            config_path: Path to the notification configuration file
        """
        self.config_path = config_path or "backend/ai/config/notifications.json"
        self.config = self._load_config()
        
        self.channels = {}
        self._initialize_channels()
        
        self.notification_history = []
        self.max_history_size = self.config.get("max_history_size", 1000)
        
        # Set up notification queue and worker thread
        self.notification_queue = Queue()
        self._queue_processor_running = True
        self._queue_processor_thread = threading.Thread(target=self._process_notification_queue)
        self._queue_processor_thread.daemon = True
        self._queue_processor_thread.start()
        
        logger.info("Notification manager initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load notification configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Create default config
                config = self._create_default_config()
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                return config
        except Exception as e:
            logger.error(f"Error loading notification config: {str(e)}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default notification configuration."""
        return {
            "enabled": True,
            "max_history_size": 1000,
            "default_channels": ["CONSOLE"],
            "channel_configs": {
                "EMAIL": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "your-email@gmail.com",
                    "password": "",  # Store securely, not in config
                    "sender": "ArbitrageX Bot <your-email@gmail.com>",
                    "recipients": ["your-email@gmail.com"],
                    "use_tls": True
                },
                "TELEGRAM": {
                    "enabled": False,
                    "bot_token": "",  # Store securely, not in config
                    "chat_ids": [],
                    "parse_mode": "HTML"
                },
                "SLACK": {
                    "enabled": False,
                    "webhook_url": "",  # Store securely, not in config
                    "channel": "#arbitragex",
                    "username": "ArbitrageX Bot",
                    "icon_emoji": ":robot_face:"
                },
                "WEBHOOK": {
                    "enabled": False,
                    "url": "https://your-webhook-url.com",
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "timeout_seconds": 5
                },
                "CONSOLE": {
                    "enabled": True,
                    "show_timestamp": True,
                    "color_enabled": True
                }
            },
            "category_routing": {
                "TRADE": ["CONSOLE", "TELEGRAM"],
                "SECURITY": ["CONSOLE", "EMAIL", "TELEGRAM"],
                "SYSTEM": ["CONSOLE"],
                "ERROR": ["CONSOLE", "EMAIL", "TELEGRAM"],
                "PERFORMANCE": ["CONSOLE"],
                "INFO": ["CONSOLE"]
            },
            "priority_thresholds": {
                "EMAIL": "MEDIUM",
                "TELEGRAM": "MEDIUM",
                "SLACK": "MEDIUM",
                "WEBHOOK": "LOW",
                "CONSOLE": "LOW"
            },
            "rate_limiting": {
                "enabled": True,
                "max_per_minute": 10,
                "max_per_hour": 50,
                "max_per_day": 200
            },
            "notification_templates": {
                "TRADE_SUCCESS": {
                    "title": "Trade Successful",
                    "message": "Trade #{trade_id} completed successfully. Profit: {profit} {currency}",
                    "category": "TRADE",
                    "priority": "MEDIUM"
                },
                "TRADE_FAILURE": {
                    "title": "Trade Failed",
                    "message": "Trade #{trade_id} failed: {reason}",
                    "category": "TRADE",
                    "priority": "HIGH"
                },
                "SECURITY_ALERT": {
                    "title": "Security Alert",
                    "message": "Security concern detected: {message}",
                    "category": "SECURITY",
                    "priority": "CRITICAL"
                },
                "ERROR": {
                    "title": "System Error",
                    "message": "An error occurred: {message}",
                    "category": "ERROR",
                    "priority": "HIGH"
                }
            }
        }
    
    def _initialize_channels(self) -> None:
        """Initialize all enabled notification channels."""
        channel_configs = self.config.get("channel_configs", {})
        
        # Email channel
        if channel_configs.get("EMAIL", {}).get("enabled", False):
            self.channels[NotificationChannel.EMAIL] = EmailChannel(channel_configs["EMAIL"])
        
        # Telegram channel
        if channel_configs.get("TELEGRAM", {}).get("enabled", False):
            self.channels[NotificationChannel.TELEGRAM] = TelegramChannel(channel_configs["TELEGRAM"])
        
        # Slack channel
        if channel_configs.get("SLACK", {}).get("enabled", False):
            self.channels[NotificationChannel.SLACK] = SlackChannel(channel_configs["SLACK"])
        
        # Webhook channel
        if channel_configs.get("WEBHOOK", {}).get("enabled", False):
            self.channels[NotificationChannel.WEBHOOK] = WebhookChannel(channel_configs["WEBHOOK"])
        
        # Console channel (always enabled)
        self.channels[NotificationChannel.CONSOLE] = ConsoleChannel(channel_configs.get("CONSOLE", {}))
    
    def _get_channels_for_notification(self, notification: Notification) -> List[NotificationChannel]:
        """
        Determine which channels should receive the notification.
        
        Args:
            notification: The notification to route
            
        Returns:
            List of channels to send the notification to
        """
        # If channels are explicitly specified in the notification, use those
        if notification.channels:
            return [c for c in notification.channels if c in self.channels]
        
        # Otherwise, use category routing from config
        category_routing = self.config.get("category_routing", {})
        channel_names = category_routing.get(notification.category.name, self.config.get("default_channels", ["CONSOLE"]))
        
        # Filter by priority thresholds
        priority_thresholds = self.config.get("priority_thresholds", {})
        allowed_channels = []
        
        for channel_name in channel_names:
            try:
                channel = NotificationChannel[channel_name]
                if channel not in self.channels:
                    continue
                
                threshold = NotificationPriority[priority_thresholds.get(channel_name, "LOW")]
                if self._compare_priorities(notification.priority, threshold) >= 0:
                    allowed_channels.append(channel)
            except (KeyError, ValueError):
                logger.warning(f"Invalid channel name: {channel_name}")
        
        return allowed_channels
    
    def _compare_priorities(self, p1: NotificationPriority, p2: NotificationPriority) -> int:
        """
        Compare two priorities.
        
        Args:
            p1: First priority
            p2: Second priority
            
        Returns:
            1 if p1 > p2, 0 if p1 == p2, -1 if p1 < p2
        """
        priority_order = {
            NotificationPriority.LOW: 0,
            NotificationPriority.MEDIUM: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.CRITICAL: 3
        }
        
        v1 = priority_order[p1]
        v2 = priority_order[p2]
        
        if v1 > v2:
            return 1
        elif v1 == v2:
            return 0
        else:
            return -1
    
    def _process_notification_queue(self) -> None:
        """Process notifications from the queue (runs in a separate thread)."""
        while self._queue_processor_running:
            try:
                notification = self.notification_queue.get(timeout=1)
                
                # Determine which channels to send to
                channels = self._get_channels_for_notification(notification)
                
                # Send to each channel
                for channel_type in channels:
                    if channel_type in self.channels:
                        try:
                            self.channels[channel_type].send(notification)
                        except Exception as e:
                            logger.error(f"Error sending notification to {channel_type.name}: {str(e)}")
                
                # Add to history
                self._add_to_history(notification)
                
                # Mark as done
                self.notification_queue.task_done()
            except Exception as e:
                if not isinstance(e, TimeoutError):
                    logger.error(f"Error processing notification queue: {str(e)}")
    
    def _add_to_history(self, notification: Notification) -> None:
        """
        Add a notification to the history.
        
        Args:
            notification: The notification to add
        """
        self.notification_history.append(notification)
        
        # Trim history if needed
        if len(self.notification_history) > self.max_history_size:
            self.notification_history = self.notification_history[-self.max_history_size:]
    
    def notify(
        self,
        title: str,
        message: str,
        category: Union[NotificationCategory, str],
        priority: Union[NotificationPriority, str] = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[Union[NotificationChannel, str]]] = None
    ) -> str:
        """
        Create and queue a notification.
        
        Args:
            title: Brief title/subject of the notification
            message: Detailed message content
            category: Category of the notification
            priority: Priority level of the notification
            data: Additional structured data related to the notification
            channels: Specific channels to send this notification to
            
        Returns:
            ID of the created notification
        """
        if not self.config.get("enabled", True):
            logger.info(f"Notifications disabled, ignoring: {title}")
            return "disabled"
        
        # Convert string enums to actual enum values
        if isinstance(category, str):
            try:
                category = NotificationCategory[category]
            except KeyError:
                logger.warning(f"Invalid category: {category}, using INFO")
                category = NotificationCategory.INFO
        
        if isinstance(priority, str):
            try:
                priority = NotificationPriority[priority]
            except KeyError:
                logger.warning(f"Invalid priority: {priority}, using MEDIUM")
                priority = NotificationPriority.MEDIUM
        
        if channels:
            processed_channels = []
            for channel in channels:
                if isinstance(channel, str):
                    try:
                        channel = NotificationChannel[channel]
                        processed_channels.append(channel)
                    except KeyError:
                        logger.warning(f"Invalid channel: {channel}")
                else:
                    processed_channels.append(channel)
            channels = processed_channels
        
        # Create notification
        notification = Notification(
            title=title,
            message=message,
            category=category,
            priority=priority,
            data=data,
            channels=channels
        )
        
        # Add to queue for processing
        self.notification_queue.put(notification)
        
        logger.debug(f"Notification queued: {notification}")
        return notification.id
    
    def notify_from_template(
        self,
        template_name: str,
        **kwargs
    ) -> Optional[str]:
        """
        Create and queue a notification using a template.
        
        Args:
            template_name: Name of the template to use
            **kwargs: Values to fill in template placeholders
            
        Returns:
            ID of the created notification or None if template not found
        """
        templates = self.config.get("notification_templates", {})
        if template_name not in templates:
            logger.warning(f"Template not found: {template_name}")
            return None
        
        template = templates[template_name]
        
        # Format message and title with provided values
        title = template["title"]
        message = template["message"]
        
        try:
            title = title.format(**kwargs)
            message = message.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing value for template placeholder: {e}")
        
        # Get category and priority from template
        category = template.get("category", "INFO")
        priority = template.get("priority", "MEDIUM")
        
        return self.notify(
            title=title,
            message=message,
            category=category,
            priority=priority,
            data=kwargs
        )
    
    def get_notification_history(
        self,
        limit: Optional[int] = None,
        category: Optional[Union[NotificationCategory, str]] = None,
        min_priority: Optional[Union[NotificationPriority, str]] = None,
        since: Optional[datetime] = None
    ) -> List[Notification]:
        """
        Get notification history with optional filtering.
        
        Args:
            limit: Maximum number of notifications to return
            category: Filter by category
            min_priority: Minimum priority to include
            since: Only include notifications after this time
            
        Returns:
            List of notifications matching the criteria
        """
        # Convert string enums to actual enum values if needed
        if isinstance(category, str):
            try:
                category = NotificationCategory[category]
            except KeyError:
                logger.warning(f"Invalid category: {category}")
                category = None
        
        if isinstance(min_priority, str):
            try:
                min_priority = NotificationPriority[min_priority]
            except KeyError:
                logger.warning(f"Invalid priority: {min_priority}")
                min_priority = None
        
        # Filter by criteria
        filtered = self.notification_history
        
        if category:
            filtered = [n for n in filtered if n.category == category]
        
        if min_priority:
            filtered = [n for n in filtered if self._compare_priorities(n.priority, min_priority) >= 0]
        
        if since:
            filtered = [n for n in filtered if n.timestamp >= since]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda n: n.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def shutdown(self) -> None:
        """Shut down the notification manager."""
        self._queue_processor_running = False
        
        # Wait for queue processor to finish
        if self._queue_processor_thread.is_alive():
            self._queue_processor_thread.join(timeout=5)
        
        logger.info("Notification manager shut down")
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update notification configuration.
        
        Args:
            new_config: New configuration values
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Merge with existing config
            self.config.update(new_config)
            
            # Re-initialize channels
            self.channels = {}
            self._initialize_channels()
            
            # Save updated config
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info("Notification configuration updated")
            return True
        except Exception as e:
            logger.error(f"Error updating notification config: {str(e)}")
            return False
    
    def enable_channel(self, channel: Union[NotificationChannel, str], config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Enable a notification channel.
        
        Args:
            channel: The channel to enable
            config: Configuration for the channel
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert string to enum if needed
            if isinstance(channel, str):
                try:
                    channel = NotificationChannel[channel]
                except KeyError:
                    logger.error(f"Invalid channel name: {channel}")
                    return False
            
            # Update config
            channel_name = channel.name
            channel_configs = self.config.get("channel_configs", {})
            
            if channel_name not in channel_configs:
                channel_configs[channel_name] = {}
            
            channel_configs[channel_name]["enabled"] = True
            
            if config:
                channel_configs[channel_name].update(config)
            
            self.config["channel_configs"] = channel_configs
            
            # Save config
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Re-initialize channels
            self.channels = {}
            self._initialize_channels()
            
            logger.info(f"Notification channel enabled: {channel_name}")
            return True
        except Exception as e:
            logger.error(f"Error enabling notification channel: {str(e)}")
            return False
    
    def disable_channel(self, channel: Union[NotificationChannel, str]) -> bool:
        """
        Disable a notification channel.
        
        Args:
            channel: The channel to disable
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert string to enum if needed
            if isinstance(channel, str):
                try:
                    channel = NotificationChannel[channel]
                except KeyError:
                    logger.error(f"Invalid channel name: {channel}")
                    return False
            
            # Update config
            channel_name = channel.name
            channel_configs = self.config.get("channel_configs", {})
            
            if channel_name in channel_configs:
                channel_configs[channel_name]["enabled"] = False
            
            self.config["channel_configs"] = channel_configs
            
            # Save config
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            # Remove from active channels
            if channel in self.channels:
                del self.channels[channel]
            
            logger.info(f"Notification channel disabled: {channel_name}")
            return True
        except Exception as e:
            logger.error(f"Error disabling notification channel: {str(e)}")
            return False


class NotificationChannelBase:
    """Base class for notification channels."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the notification channel.
        
        Args:
            config: Channel configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
    
    def send(self, notification: Notification) -> bool:
        """
        Send a notification through this channel.
        
        Args:
            notification: The notification to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning(f"{self.__class__.__name__} is disabled, not sending notification: {notification.title}")
            return False
        
        return self._send_notification(notification)
    
    def _send_notification(self, notification: Notification) -> bool:
        """
        Send a notification through this channel (to be implemented by subclasses).
        
        Args:
            notification: The notification to send
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement _send_notification")
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update channel configuration.
        
        Args:
            config: New configuration values
        """
        self.config.update(config)
        self.enabled = self.config.get("enabled", True)


class EmailChannel(NotificationChannelBase):
    """Email notification channel."""
    
    def _send_notification(self, notification: Notification) -> bool:
        """Send notification via email."""
        try:
            smtp_server = self.config.get("smtp_server")
            smtp_port = self.config.get("smtp_port", 587)
            username = self.config.get("username")
            password = self.config.get("password")
            sender = self.config.get("sender")
            recipients = self.config.get("recipients", [])
            use_tls = self.config.get("use_tls", True)
            
            if not smtp_server or not username or not password or not sender or not recipients:
                logger.error("Incomplete email configuration")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = f"[{notification.priority.name}] {notification.title}"
            
            # Create HTML body
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .notification {{ padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                    .priority-LOW {{ background-color: #f0f0f0; }}
                    .priority-MEDIUM {{ background-color: #f0f8ff; }}
                    .priority-HIGH {{ background-color: #fff0f0; }}
                    .priority-CRITICAL {{ background-color: #ffe0e0; color: #c00; }}
                    .title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                    .message {{ margin-bottom: 10px; }}
                    .metadata {{ color: #666; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="notification priority-{notification.priority.name}">
                    <div class="title">{notification.title}</div>
                    <div class="message">{notification.message}</div>
                    <div class="metadata">
                        Category: {notification.category.name}<br>
                        Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML body
            msg.attach(MIMEText(html, "html"))
            
            # Connect to SMTP server
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()
            
            if use_tls:
                server.starttls()
                server.ehlo()
            
            server.login(username, password)
            
            # Send email
            server.sendmail(sender, recipients, msg.as_string())
            server.quit()
            
            logger.info(f"Email notification sent: {notification.title}")
            return True
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False


class TelegramChannel(NotificationChannelBase):
    """Telegram notification channel."""
    
    def _send_notification(self, notification: Notification) -> bool:
        """Send notification via Telegram."""
        try:
            bot_token = self.config.get("bot_token")
            chat_ids = self.config.get("chat_ids", [])
            parse_mode = self.config.get("parse_mode", "HTML")
            
            if not bot_token or not chat_ids:
                logger.error("Incomplete Telegram configuration")
                return False
            
            # Create message
            priority_emoji = {
                NotificationPriority.LOW: "ℹ️",
                NotificationPriority.MEDIUM: "⚠️",
                NotificationPriority.HIGH: "🚨",
                NotificationPriority.CRITICAL: "‼️"
            }
            
            emoji = priority_emoji.get(notification.priority, "ℹ️")
            
            if parse_mode == "HTML":
                message = f"{emoji} <b>{notification.title}</b>\n\n{notification.message}\n\n<i>Category: {notification.category.name}</i>"
            else:
                message = f"{emoji} *{notification.title}*\n\n{notification.message}\n\n_Category: {notification.category.name}_"
            
            # Send to each chat
            success = True
            for chat_id in chat_ids:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": parse_mode
                }
                
                response = requests.post(url, json=data, timeout=10)
                
                if not response.ok:
                    logger.error(f"Telegram API error: {response.text}")
                    success = False
            
            logger.info(f"Telegram notification sent: {notification.title}")
            return success
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {str(e)}")
            return False


class SlackChannel(NotificationChannelBase):
    """Slack notification channel."""
    
    def _send_notification(self, notification: Notification) -> bool:
        """Send notification via Slack."""
        try:
            webhook_url = self.config.get("webhook_url")
            channel = self.config.get("channel")
            username = self.config.get("username", "ArbitrageX Bot")
            icon_emoji = self.config.get("icon_emoji", ":robot_face:")
            
            if not webhook_url:
                logger.error("Incomplete Slack configuration")
                return False
            
            # Create message
            color = {
                NotificationPriority.LOW: "#CCCCCC",
                NotificationPriority.MEDIUM: "#3A87AD",
                NotificationPriority.HIGH: "#FF9900",
                NotificationPriority.CRITICAL: "#CC0000"
            }.get(notification.priority, "#CCCCCC")
            
            attachment = {
                "fallback": f"{notification.title}: {notification.message}",
                "color": color,
                "pretext": f"[{notification.priority.name}] New notification",
                "title": notification.title,
                "text": notification.message,
                "fields": [
                    {
                        "title": "Category",
                        "value": notification.category.name,
                        "short": True
                    },
                    {
                        "title": "Time",
                        "value": notification.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "short": True
                    }
                ],
                "footer": "ArbitrageX Trading Bot",
                "ts": int(notification.timestamp.timestamp())
            }
            
            data = {
                "username": username,
                "icon_emoji": icon_emoji,
                "attachments": [attachment]
            }
            
            if channel:
                data["channel"] = channel
            
            # Send to Slack
            response = requests.post(webhook_url, json=data, timeout=10)
            
            if not response.ok:
                logger.error(f"Slack API error: {response.text}")
                return False
            
            logger.info(f"Slack notification sent: {notification.title}")
            return True
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False


class WebhookChannel(NotificationChannelBase):
    """Generic webhook notification channel."""
    
    def _send_notification(self, notification: Notification) -> bool:
        """Send notification via webhook."""
        try:
            url = self.config.get("url")
            method = self.config.get("method", "POST")
            headers = self.config.get("headers", {"Content-Type": "application/json"})
            timeout = self.config.get("timeout_seconds", 5)
            
            if not url:
                logger.error("Incomplete webhook configuration")
                return False
            
            # Create payload
            payload = notification.to_dict()
            
            # Send request
            if method.upper() == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, json=payload, headers=headers, timeout=timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return False
            
            if not response.ok:
                logger.error(f"Webhook error: {response.status_code} - {response.text}")
                return False
            
            logger.info(f"Webhook notification sent: {notification.title}")
            return True
        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")
            return False


class ConsoleChannel(NotificationChannelBase):
    """Console notification channel."""
    
    def _send_notification(self, notification: Notification) -> bool:
        """Print notification to console."""
        try:
            show_timestamp = self.config.get("show_timestamp", True)
            color_enabled = self.config.get("color_enabled", True)
            
            # ANSI color codes
            colors = {
                "reset": "\033[0m",
                "bold": "\033[1m",
                "red": "\033[31m",
                "green": "\033[32m",
                "yellow": "\033[33m",
                "blue": "\033[34m",
                "magenta": "\033[35m",
                "cyan": "\033[36m",
                "white": "\033[37m"
            }
            
            priority_colors = {
                NotificationPriority.LOW: colors["blue"] if color_enabled else "",
                NotificationPriority.MEDIUM: colors["green"] if color_enabled else "",
                NotificationPriority.HIGH: colors["yellow"] if color_enabled else "",
                NotificationPriority.CRITICAL: colors["red"] if color_enabled else ""
            }
            
            reset = colors["reset"] if color_enabled else ""
            bold = colors["bold"] if color_enabled else ""
            
            # Format message
            timestamp_str = f"[{notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] " if show_timestamp else ""
            priority_color = priority_colors.get(notification.priority, "")
            
            print(f"{timestamp_str}{priority_color}{bold}[{notification.priority.name}] {notification.title}{reset}: {notification.message}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending console notification: {str(e)}")
            return False


def main():
    """Test the notification manager functionality."""
    print("Initializing notification manager...")
    notification_manager = NotificationManager()
    
    # Enable channels for testing
    notification_manager.enable_channel(NotificationChannel.CONSOLE, {
        "show_timestamp": True,
        "color_enabled": True
    })
    
    # Send test notifications
    print("\nSending test notifications...")
    
    # Test different priorities
    notification_manager.notify(
        title="Low Priority Test",
        message="This is a low priority test notification",
        category=NotificationCategory.INFO,
        priority=NotificationPriority.LOW
    )
    
    notification_manager.notify(
        title="Medium Priority Test",
        message="This is a medium priority test notification",
        category=NotificationCategory.TRADE,
        priority=NotificationPriority.MEDIUM
    )
    
    notification_manager.notify(
        title="High Priority Test",
        message="This is a high priority test notification",
        category=NotificationCategory.SYSTEM,
        priority=NotificationPriority.HIGH
    )
    
    notification_manager.notify(
        title="Critical Priority Test",
        message="This is a critical priority test notification",
        category=NotificationCategory.SECURITY,
        priority=NotificationPriority.CRITICAL
    )
    
    # Test template
    notification_manager.notify_from_template(
        template_name="TRADE_SUCCESS",
        trade_id=12345,
        profit=0.25,
        currency="ETH"
    )
    
    # Get history
    print("\nNotification history:")
    history = notification_manager.get_notification_history(limit=5)
    for notification in history:
        print(f"- {notification}")
    
    # Shutdown
    print("\nShutting down notification manager...")
    notification_manager.shutdown()
    print("Notification manager test completed")


if __name__ == "__main__":
    main() 