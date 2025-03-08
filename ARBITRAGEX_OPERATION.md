# ArbitrageX Operation Guide

This guide explains how to operate the ArbitrageX system, including starting and stopping services, monitoring, and troubleshooting.

## System Components

ArbitrageX consists of the following components:

1. **Arbitrage Bot** - The core trading engine that identifies and executes arbitrage opportunities
2. **API Server** - Provides REST API endpoints for the frontend and external integrations
3. **Frontend Dashboard** - Web interface for monitoring and controlling the system
4. **Service Monitor** - Monitors the health of all system components

## Quick Start

### Starting the System

To start all ArbitrageX services at once, run:

```bash
./start_arbitragex.sh
```

This script will:
- Start the Arbitrage Bot
- Start the API Server
- Start the Frontend Dashboard
- Start the Service Monitor
- Create log files in the `logs` directory

### Stopping the System

To stop all ArbitrageX services, run:

```bash
./stop_arbitragex.sh
```

This script will terminate all running ArbitrageX processes.

## Manual Operation

If you prefer to start services individually:

### Starting the Bot

```bash
cd backend/execution
npm run bot:start
```

### Starting the API Server

```bash
cd backend/api
npm run start:dev
```

### Starting the Frontend

```bash
cd frontend
npm run dev
```

### Monitoring Services

```bash
./monitor_services.sh
```

## Accessing the System

- **Frontend Dashboard**: http://localhost:3001
- **API Endpoints**: http://localhost:3000

## Log Files

Log files are stored in the following locations:

- Bot logs: `logs/bot.log`
- API logs: `logs/api.log`
- Frontend logs: `logs/frontend.log`
- Monitor logs: `logs/monitor.log`

## Troubleshooting

### Common Issues

1. **Port conflicts**: If ports 3000 or 3001 are already in use, the start script will attempt to kill the processes using those ports.

2. **Missing dependencies**: Ensure all dependencies are installed by running:
   ```bash
   cd backend/execution && npm install
   cd backend/api && npm install
   cd frontend && npm install
   ```

3. **Database connection issues**: Verify MongoDB is running if the bot fails to start.

4. **RPC provider issues**: Check the `.env` file to ensure the RPC provider URLs are correct.

### Checking Service Status

To check the status of all services:

```bash
./monitor_services.sh
```

This will show the status of each service, check for log files, and monitor for recent trade activity.

## Advanced Configuration

### Environment Variables

The system uses environment variables for configuration. Key variables include:

- `ETHEREUM_RPC_URL`: Ethereum RPC provider URL
- `NETWORK_NAME`: Network name (mainnet, sepolia, etc.)
- `CHAIN_ID`: Chain ID of the network

These can be configured in the `.env` file in the project root.

### Bot Parameters

Bot parameters can be adjusted in `backend/bot/bot_settings.json`.

## Security Considerations

- The bot handles private keys and funds. Ensure your environment is secure.
- Use a dedicated machine for running the bot in production.
- Regularly backup your configuration and database.
- Monitor system logs for any suspicious activity.

## Performance Optimization

For optimal performance:

- Use a reliable and fast RPC provider
- Run the bot on a machine with sufficient CPU and memory
- Consider using a dedicated database server for high-volume trading
- Adjust gas price strategies in the bot settings for better execution 