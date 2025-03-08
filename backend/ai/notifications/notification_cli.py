#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Notification CLI

Command-line interface for managing notifications in the ArbitrageX trading bot.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Ensure notifications directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notifications.notification_manager import (
    NotificationManager, 
    NotificationCategory, 
    NotificationPriority,
    NotificationChannel
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="ArbitrageX Notification Management CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Send notification
    send_parser = subparsers.add_parser("send", help="Send a notification")
    send_parser.add_argument("--title", required=True, help="Notification title")
    send_parser.add_argument("--message", required=True, help="Notification message")
    send_parser.add_argument("--category", default="INFO", choices=[c.name for c in NotificationCategory], 
                          help="Notification category")
    send_parser.add_argument("--priority", default="MEDIUM", choices=[p.name for p in NotificationPriority], 
                          help="Notification priority")
    send_parser.add_argument("--channels", nargs="+", choices=[c.name for c in NotificationChannel], 
                          help="Specific channels to send to")
    
    # Send notification from template
    template_parser = subparsers.add_parser("send-template", help="Send a notification using a template")
    template_parser.add_argument("--template", required=True, help="Template name")
    template_parser.add_argument("--data", required=True, help="JSON data for template variables")
    
    # Configure notification channels
    config_parser = subparsers.add_parser("config", help="Configure notification settings")
    config_parser.add_argument("--action", required=True, choices=["show", "update"], help="Action to perform")
    config_parser.add_argument("--data", help="JSON data for configuration update")
    
    # Enable/disable notification channels
    channel_parser = subparsers.add_parser("channel", help="Manage notification channels")
    channel_parser.add_argument("--action", required=True, choices=["enable", "disable", "list"], 
                             help="Action to perform")
    channel_parser.add_argument("--channel", choices=[c.name for c in NotificationChannel], 
                             help="Channel to manage")
    channel_parser.add_argument("--config", help="JSON configuration for the channel")
    
    # Get notification history
    history_parser = subparsers.add_parser("history", help="View notification history")
    history_parser.add_argument("--limit", type=int, default=10, help="Maximum number of notifications to show")
    history_parser.add_argument("--category", choices=[c.name for c in NotificationCategory], 
                             help="Filter by category")
    history_parser.add_argument("--min-priority", choices=[p.name for p in NotificationPriority], 
                             help="Filter by minimum priority")
    history_parser.add_argument("--since", help="Show notifications since (format: YYYY-MM-DD or Xh for X hours)")
    history_parser.add_argument("--format", choices=["text", "json"], default="text", 
                             help="Output format")
    
    # Setup wizard
    setup_parser = subparsers.add_parser("setup", help="Run setup wizard for notifications")
    setup_parser.add_argument("--channel", required=True, choices=[c.name for c in NotificationChannel], 
                           help="Channel to set up")
    
    # Test notifications
    test_parser = subparsers.add_parser("test", help="Send test notifications")
    test_parser.add_argument("--channel", choices=[c.name for c in NotificationChannel], 
                          help="Channel to test")
    
    return parser.parse_args()


def send_notification(args, notification_manager):
    """Send a notification."""
    channels = [NotificationChannel[c] for c in args.channels] if args.channels else None
    
    notification_id = notification_manager.notify(
        title=args.title,
        message=args.message,
        category=args.category,
        priority=args.priority,
        channels=channels
    )
    
    print(f"Notification sent successfully (ID: {notification_id})")


def send_from_template(args, notification_manager):
    """Send a notification using a template."""
    try:
        template_data = json.loads(args.data)
    except json.JSONDecodeError:
        print("Error: Invalid JSON data for template variables")
        return
    
    notification_id = notification_manager.notify_from_template(
        template_name=args.template,
        **template_data
    )
    
    if notification_id:
        print(f"Notification sent successfully from template (ID: {notification_id})")
    else:
        print(f"Error: Template '{args.template}' not found")


def configure_notifications(args, notification_manager):
    """Configure notification settings."""
    if args.action == "show":
        print(json.dumps(notification_manager.config, indent=2))
    elif args.action == "update":
        try:
            new_config = json.loads(args.data)
        except json.JSONDecodeError:
            print("Error: Invalid JSON data for configuration")
            return
        
        success = notification_manager.update_config(new_config)
        if success:
            print("Notification configuration updated successfully")
        else:
            print("Error updating notification configuration")


def manage_channels(args, notification_manager):
    """Manage notification channels."""
    if args.action == "list":
        # List all available channels and their status
        print("Available notification channels:")
        print("-" * 50)
        for channel in NotificationChannel:
            config = notification_manager.config.get("channel_configs", {}).get(channel.name, {})
            status = "Enabled" if config.get("enabled", False) else "Disabled"
            
            if channel in notification_manager.channels:
                status += " (Active)"
            
            print(f"{channel.name}: {status}")
        print("-" * 50)
    elif args.action in ["enable", "disable"]:
        # Enable or disable a channel
        if not args.channel:
            print("Error: --channel parameter is required for enable/disable actions")
            return
        
        if args.action == "enable":
            # Parse channel config if provided
            config = None
            if args.config:
                try:
                    config = json.loads(args.config)
                except json.JSONDecodeError:
                    print("Error: Invalid JSON data for channel configuration")
                    return
            
            success = notification_manager.enable_channel(args.channel, config)
            if success:
                print(f"Notification channel {args.channel} enabled successfully")
            else:
                print(f"Error enabling notification channel {args.channel}")
        else:  # disable
            success = notification_manager.disable_channel(args.channel)
            if success:
                print(f"Notification channel {args.channel} disabled successfully")
            else:
                print(f"Error disabling notification channel {args.channel}")


def view_history(args, notification_manager):
    """View notification history."""
    # Parse "since" parameter
    since = None
    if args.since:
        if args.since.endswith('h'):
            # Parse as "Xh" format (X hours ago)
            try:
                hours = int(args.since[:-1])
                since = datetime.now() - timedelta(hours=hours)
            except ValueError:
                print(f"Error: Invalid format for --since: {args.since}")
                return
        else:
            # Parse as YYYY-MM-DD format
            try:
                since = datetime.fromisoformat(args.since)
            except ValueError:
                print(f"Error: Invalid format for --since: {args.since}")
                return
    
    # Get notifications
    notifications = notification_manager.get_notification_history(
        limit=args.limit,
        category=args.category,
        min_priority=args.min_priority,
        since=since
    )
    
    if args.format == "json":
        # Output as JSON
        output = [notification.to_dict() for notification in notifications]
        print(json.dumps(output, indent=2))
    else:
        # Output as text
        if not notifications:
            print("No notifications found matching the criteria")
            return
        
        print(f"Notification History (showing {len(notifications)} of {len(notification_manager.notification_history)} notifications):")
        print("-" * 80)
        
        for notification in notifications:
            timestamp = notification.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{notification.priority.name}] {notification.title}")
            print(f"Category: {notification.category.name}")
            print(f"Message: {notification.message}")
            print("-" * 80)


def run_setup_wizard(args, notification_manager):
    """Run setup wizard for a notification channel."""
    channel_name = args.channel
    
    print(f"Setup wizard for {channel_name} notification channel")
    print("-" * 50)
    
    # Get existing config or create empty one
    channel_configs = notification_manager.config.get("channel_configs", {})
    channel_config = channel_configs.get(channel_name, {})
    
    # Different setup for each channel type
    if channel_name == "EMAIL":
        channel_config["enabled"] = True
        channel_config["smtp_server"] = input("SMTP Server [smtp.gmail.com]: ") or "smtp.gmail.com"
        channel_config["smtp_port"] = int(input("SMTP Port [587]: ") or "587")
        channel_config["username"] = input("Email Username: ")
        channel_config["password"] = input("Email Password: ")
        channel_config["sender"] = input(f"Sender Name [{channel_config['username']}]: ") or channel_config['username']
        
        recipients = input("Recipients (comma-separated): ")
        channel_config["recipients"] = [r.strip() for r in recipients.split(",")]
        
        use_tls = input("Use TLS? (y/n) [y]: ").lower() != "n"
        channel_config["use_tls"] = use_tls
    
    elif channel_name == "TELEGRAM":
        channel_config["enabled"] = True
        channel_config["bot_token"] = input("Telegram Bot Token: ")
        
        chat_ids = input("Chat IDs (comma-separated): ")
        channel_config["chat_ids"] = [c.strip() for c in chat_ids.split(",")]
        
        parse_mode = input("Parse Mode (HTML/Markdown) [HTML]: ") or "HTML"
        channel_config["parse_mode"] = parse_mode
    
    elif channel_name == "SLACK":
        channel_config["enabled"] = True
        channel_config["webhook_url"] = input("Slack Webhook URL: ")
        channel_config["channel"] = input("Slack Channel [#arbitragex]: ") or "#arbitragex"
        channel_config["username"] = input("Bot Username [ArbitrageX Bot]: ") or "ArbitrageX Bot"
        channel_config["icon_emoji"] = input("Icon Emoji [:robot_face:]: ") or ":robot_face:"
    
    elif channel_name == "WEBHOOK":
        channel_config["enabled"] = True
        channel_config["url"] = input("Webhook URL: ")
        channel_config["method"] = input("HTTP Method (POST/PUT) [POST]: ") or "POST"
        
        content_type = input("Content-Type [application/json]: ") or "application/json"
        channel_config["headers"] = {"Content-Type": content_type}
        
        channel_config["timeout_seconds"] = int(input("Timeout in seconds [5]: ") or "5")
    
    elif channel_name == "CONSOLE":
        channel_config["enabled"] = True
        
        show_timestamp = input("Show timestamp? (y/n) [y]: ").lower() != "n"
        channel_config["show_timestamp"] = show_timestamp
        
        color_enabled = input("Enable colors? (y/n) [y]: ").lower() != "n"
        channel_config["color_enabled"] = color_enabled
    
    # Update config
    channel_configs[channel_name] = channel_config
    notification_manager.config["channel_configs"] = channel_configs
    
    # Save to file
    success = notification_manager.update_config(notification_manager.config)
    if success:
        print(f"{channel_name} notification channel configured successfully")
    else:
        print(f"Error configuring {channel_name} notification channel")


def test_notifications(args, notification_manager):
    """Send test notifications."""
    channel = args.channel
    channels = [NotificationChannel[channel]] if channel else None
    
    print("Sending test notifications...")
    
    # Send test notifications with different priorities
    priorities = [
        ("Low Priority Test", "This is a low priority test notification", NotificationPriority.LOW),
        ("Medium Priority Test", "This is a medium priority test notification", NotificationPriority.MEDIUM),
        ("High Priority Test", "This is a high priority test notification", NotificationPriority.HIGH),
        ("Critical Priority Test", "This is a critical priority test notification", NotificationPriority.CRITICAL)
    ]
    
    for title, message, priority in priorities:
        notification_id = notification_manager.notify(
            title=title,
            message=message,
            category=NotificationCategory.INFO,
            priority=priority,
            channels=channels
        )
        print(f"Sent {priority.name} notification (ID: {notification_id})")
    
    print("Test notifications completed")


def main():
    """Main function."""
    args = parse_args()
    
    # Initialize notification manager
    notification_manager = NotificationManager()
    
    try:
        # Execute command
        if args.command == "send":
            send_notification(args, notification_manager)
        elif args.command == "send-template":
            send_from_template(args, notification_manager)
        elif args.command == "config":
            configure_notifications(args, notification_manager)
        elif args.command == "channel":
            manage_channels(args, notification_manager)
        elif args.command == "history":
            view_history(args, notification_manager)
        elif args.command == "setup":
            run_setup_wizard(args, notification_manager)
        elif args.command == "test":
            test_notifications(args, notification_manager)
        else:
            print("Error: No command specified")
            print("Run 'notification_cli.py --help' for usage information")
    finally:
        # Ensure we shut down the notification manager properly
        notification_manager.shutdown()


if __name__ == "__main__":
    main() 