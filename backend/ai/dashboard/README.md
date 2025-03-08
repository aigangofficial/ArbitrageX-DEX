# ArbitrageX Web Dashboard

The ArbitrageX Web Dashboard provides a user-friendly interface for monitoring and controlling the ArbitrageX trading bot. It offers real-time metrics, trade history, strategy management, and system configuration through an intuitive web interface.

## Features

- **Real-time Monitoring**: View bot status, trade history, and performance metrics in real-time
- **Interactive Charts**: Visualize profit history and strategy distribution
- **Trade Management**: View detailed trade information and performance
- **Strategy Configuration**: Configure and manage trading strategies
- **Backtesting Interface**: Run and analyze backtests directly from the dashboard
- **Notification Center**: View and manage system notifications
- **Security Controls**: Manage security settings and access controls
- **System Logs**: Access and search system logs
- **User Management**: Create and manage dashboard users
- **API Access**: Generate and manage API keys for external integrations
- **Theme Support**: Choose between light and dark themes

## Installation

The dashboard is included as part of the ArbitrageX trading bot. No additional installation is required.

## Usage

### Starting the Dashboard

To start the dashboard, use the ArbitrageX unified command:

```bash
./arbitragex.sh dashboard start
```

Additional options:
- `--host=HOST`: Specify the host to bind to (default: 127.0.0.1)
- `--port=PORT`: Specify the port to run on (default: 5000)
- `--debug`: Run in debug mode
- `--browser`: Open the dashboard in a browser automatically

### Stopping the Dashboard

To stop the dashboard:

```bash
./arbitragex.sh dashboard stop
```

### Checking Dashboard Status

To check if the dashboard is running:

```bash
./arbitragex.sh dashboard status
```

### User Management

To create a new dashboard user:

```bash
./arbitragex.sh dashboard create-user --username=admin2 --password=secure_password --email=admin2@example.com
```

### API Key Management

To generate a new API key for external integrations:

```bash
./arbitragex.sh dashboard generate-key
```

### Configuration

To configure dashboard settings:

```bash
./arbitragex.sh dashboard configure --port=8080 --theme=dark
```

Available configuration options:
- `--host`: Host to bind to
- `--port`: Port to run on
- `--debug`: Debug mode (true/false)
- `--theme`: Dashboard theme (light/dark)
- `--session-lifetime`: Session lifetime in seconds

### Resetting to Defaults

To reset the dashboard to default settings:

```bash
./arbitragex.sh dashboard reset --confirm
```

## Dashboard Structure

The dashboard is organized into several sections:

1. **Home**: Overview of bot status, key metrics, and recent activity
2. **Trades**: Detailed trade history and performance metrics
3. **Strategies**: Strategy configuration and performance comparison
4. **Backtesting**: Interface for running and analyzing backtests
5. **Notifications**: View and manage system notifications
6. **Security**: Security settings and access controls
7. **Logs**: System logs and error messages
8. **Settings**: Dashboard configuration and user preferences
9. **Profile**: User profile management

## API Endpoints

The dashboard provides several API endpoints for integration with external systems:

- `/api/status`: Get system status
- `/api/trades`: Get trade history
- `/api/metrics`: Get system metrics
- `/api/notifications`: Get notification history
- `/api/start`: Start the trading bot
- `/api/stop`: Stop the trading bot

API authentication is required for all endpoints. Use the `X-API-Key` header with a valid API key.

## Security

The dashboard implements several security measures:

- **Authentication**: Username/password authentication for all users
- **Session Management**: Secure session handling with configurable lifetime
- **API Authentication**: API key authentication for external integrations
- **CSRF Protection**: Protection against cross-site request forgery
- **Input Validation**: Validation of all user inputs
- **Secure Defaults**: Secure default settings

## Troubleshooting

### Dashboard Won't Start

1. Check if another instance is already running:
   ```bash
   ./arbitragex.sh dashboard status
   ```

2. Check for port conflicts:
   ```bash
   lsof -i :5000
   ```

3. Check the dashboard logs:
   ```bash
   tail -n 100 backend/ai/logs/dashboard.log
   ```

### Can't Log In

1. Reset your password by creating a new user:
   ```bash
   ./arbitragex.sh dashboard create-user --username=your_username --password=new_password
   ```

2. If that doesn't work, reset the dashboard:
   ```bash
   ./arbitragex.sh dashboard reset --confirm
   ```
   Then create a new user.

### Dashboard is Slow

1. Check system resources:
   ```bash
   top
   ```

2. Consider running the dashboard on a different port or host:
   ```bash
   ./arbitragex.sh dashboard configure --port=8080
   ```

## Development

The dashboard is built with:

- **Flask**: Web framework
- **Socket.IO**: Real-time communication
- **Bootstrap**: UI framework
- **ApexCharts**: Interactive charts
- **jQuery**: DOM manipulation

To modify the dashboard:

1. Edit templates in `backend/ai/dashboard/templates/`
2. Edit static files in `backend/ai/dashboard/static/`
3. Edit Python code in `backend/ai/dashboard/app.py`

## License

The ArbitrageX Web Dashboard is proprietary software. All rights reserved. 