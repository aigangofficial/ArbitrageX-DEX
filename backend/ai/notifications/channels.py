#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Notification Channels

This module provides implementations of various notification channels
used by the ArbitrageX notification system.
"""

import os
import json
import logging
import smtplib
import requests
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from .notification_manager import Notification, NotificationPriority

logger = logging.getLogger("notifications.channels")

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