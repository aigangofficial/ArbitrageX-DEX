# ArbitrageX Notification System

The ArbitrageX Notification System provides real-time alerts for important events in the trading bot. It supports multiple notification channels and flexible configuration options.

## Features

- Multiple notification channels:
  - **Email**: Receive notifications via email
  - **Telegram**: Get instant alerts on your Telegram account
  - **Slack**: Receive notifications in your Slack workspace
  - **Webhook**: Send notifications to any HTTP endpoint
  - **Console**: Display notifications in the terminal

- Priority levels for filtering notifications:
  - **Low**: Informational messages
  - **Medium**: Important updates
  - **High**: Warnings that need attention
  - **Critical**: Urgent issues requiring immediate action

- Categorization of notifications:
  - **Trade**: Events related to trading activity
  - **Security**: Security-related alerts
  - **System**: System status and operations
  - **Error**: Error reports
  - **Performance**: Performance metrics
  - **Info**: General information

- Additional capabilities:
  - Customizable notification templates
  - Notification history tracking
  - Rate limiting to prevent notification flooding
  - Channel-specific configuration
  - Easy integration with other system components

## Command-Line Interface

The notification system can be controlled through the ArbitrageX unified command system:

```bash
./arbitragex.sh notify [command] [options]
```

### Available Commands

#### Sending Notifications

```bash
# Send a simple notification
./arbitragex.sh notify send --title="Test Notification" --message="This is a test notification" --category=INFO --priority=MEDIUM

# Send using a template
./arbitragex.sh notify send-template --template=TRADE_SUCCESS --data='{"trade_id": 12345, "profit": 0.25, "currency": "ETH"}'
```

#### Managing Channels

```bash
# List all available channels and their status
./arbitragex.sh notify channel --action=list

# Enable a channel
./arbitragex.sh notify channel --action=enable --channel=TELEGRAM --config='{"bot_token": "YOUR_BOT_TOKEN", "chat_ids": ["YOUR_CHAT_ID"]}'

# Disable a channel
./arbitragex.sh notify channel --action=disable --channel=EMAIL
```

#### Setting Up Channels

```bash
# Run setup wizard for a channel
./arbitragex.sh notify setup --channel=TELEGRAM

# Test notifications
./arbitragex.sh notify test --channel=SLACK
```

#### View Notification History

```bash
# View recent notifications
./arbitragex.sh notify history --limit=10

# Filter by category and priority
./arbitragex.sh notify history --category=TRADE --min-priority=HIGH

# View notifications from the last few hours
./arbitragex.sh notify history --since=24h
```

#### Configuration Management

```bash
# Show current configuration
./arbitragex.sh notify config --action=show

# Update configuration
./arbitragex.sh notify config --action=update --data='{"rate_limiting": {"max_per_minute": 5}}'
```

## Programmatic Usage

You can also use the notification system programmatically in your Python code:

```python
from backend.ai.notifications import notify, notify_from_template

# Send a simple notification
notify(
    title="Trade Executed",
    message="Trade #12345 executed successfully with 0.1 ETH profit",
    category="TRADE",
    priority="HIGH"
)

# Send using a template
notify_from_template(
    template_name="TRADE_SUCCESS",
    trade_id=12345,
    profit=0.1,
    currency="ETH"
)
```

## Configuration

The notification system's configuration is stored in `backend/ai/config/notifications.json`. You can edit this file directly or use the configuration commands.

### Default Configuration

The default configuration includes:

- Console notifications enabled by default
- Email, Telegram, Slack, and Webhook channels disabled (require setup)
- Category routing rules for determining which notifications go to which channels
- Priority thresholds for filtering notifications by importance
- Rate limiting to prevent notification flooding
- Notification templates for common events

## Setting Up Channels

### Email

To set up email notifications:

1. Run the setup wizard:
   ```bash
   ./arbitragex.sh notify setup --channel=EMAIL
   ```
2. Provide SMTP server details, credentials, and recipient addresses.
3. For Gmail, you might need to enable "Less secure app access" or use App Passwords.

### Telegram

To set up Telegram notifications:

1. Create a bot with BotFather on Telegram and get the API token.
2. Start a conversation with your bot and get your chat ID.
3. Run the setup wizard:
   ```bash
   ./arbitragex.sh notify setup --channel=TELEGRAM
   ```
4. Enter your bot token and chat ID when prompted.

### Slack

To set up Slack notifications:

1. Create an incoming webhook in your Slack workspace.
2. Run the setup wizard:
   ```bash
   ./arbitragex.sh notify setup --channel=SLACK
   ```
3. Enter your webhook URL and channel details when prompted.

## Integration with ArbitrageX

The notification system is integrated with various components of ArbitrageX:

- **Trading Strategies**: Send notifications about trade execution, profits, and opportunities
- **Security Module**: Alert on security concerns, suspicious transactions, and unauthorized access attempts
- **System Monitor**: Notify about system status, resource usage, and performance metrics
- **Error Handler**: Report errors and exceptional conditions

## Extending the System

To add a new notification channel:

1. Create a new channel class that inherits from `NotificationChannelBase`
2. Implement the `_send_notification` method
3. Register the channel in the `NotificationChannel` enum and `NotificationManager` class

## Troubleshooting

- **Notifications not sending**: Check the notification logs at `backend/ai/logs/notifications.log`
- **Channel configuration issues**: Verify your credentials and connection details
- **Rate limiting**: If you're being rate-limited, adjust the rate limiting settings in the configuration

For more information, run:
```bash
./arbitragex.sh notify --help
``` 