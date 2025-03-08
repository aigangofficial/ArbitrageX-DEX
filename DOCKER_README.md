# Docker Setup for ArbitrageX Trading Bot

This document explains how to deploy and run the ArbitrageX trading bot using Docker containers.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/arbitragex.git
   cd arbitragex
   ```

2. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit the .env file with your settings
   ```

3. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

4. View logs:
   ```bash
   docker-compose logs -f arbitragex
   ```

## Environment Variables

Set these variables in your `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `ETHEREUM_NODE_URL` | Ethereum mainnet RPC URL | `https://mainnet.infura.io/v3/your-infura-key` |
| `ARBITRUM_NODE_URL` | Arbitrum RPC URL | `https://arb1.arbitrum.io/rpc` |
| `OPTIMISM_NODE_URL` | Optimism RPC URL | `https://mainnet.optimism.io` |
| `POLYGON_NODE_URL` | Polygon RPC URL | `https://polygon-rpc.com` |
| `BASE_NODE_URL` | Base RPC URL | `https://mainnet.base.org` |
| `ETHEREUM_PRIVATE_KEY` | Private key for transactions | Empty (required for production) |
| `FLASHBOTS_AUTH_KEY` | Flashbots authentication key | Empty (optional) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for notifications | Empty (optional) |
| `SLACK_WEBHOOK_URL` | Slack webhook URL for notifications | Empty (optional) |
| `SIMULATION_MODE` | Run in simulation mode | `true` |
| `API_AUTH_ENABLED` | Enable authentication for API | `false` |
| `API_AUTH_TOKEN` | Authentication token for API | Empty |

## Container Services

### ArbitrageX Bot
- **Container Name**: `arbitragex-bot`
- **Description**: Main trading bot that runs the strategies
- **Volumes**:
  - `./backend/ai/logs`: Log files
  - `./backend/ai/metrics`: Performance metrics
  - `./backend/ai/config`: Configuration files

### API Service
- **Container Name**: `arbitragex-api`
- **Description**: REST API for interacting with the trading bot
- **Port**: 8000
- **Endpoints**:
  - `GET /api/v1/status`: Get trading bot status
  - `GET /api/v1/metrics`: Get performance metrics
  - `POST /api/v1/start`: Start the trading bot
  - `POST /api/v1/stop`: Stop the trading bot

### Dashboard
- **Container Name**: `arbitragex-dashboard`
- **Description**: Web UI for monitoring and controlling the trading bot
- **Port**: 3000
- **Features**:
  - Real-time performance monitoring
  - Strategy configuration
  - Trade history visualization
  - Log viewer

## Running Commands

### Start a Simulation
```bash
docker-compose exec arbitragex ./arbitragex.sh start --trades=100
```

### Run a Backtest
```bash
docker-compose exec arbitragex ./arbitragex.sh backtest --strategy=ml_enhanced --days=30
```

### View Logs
```bash
docker-compose exec arbitragex ./arbitragex.sh logs --follow
```

### Compare Strategies
```bash
docker-compose exec arbitragex ./arbitragex.sh backtest --compare-all
```

## Production Deployment

For production deployment with real funds:

1. Update your `.env` file with real API keys and private keys
2. Modify `docker-compose.yml` to use production settings:
   ```yaml
   command: start --no-simulation
   ```
3. Consider setting up monitoring and alerts
4. Ensure proper security measures are in place

⚠️ **WARNING**: Running in production mode connects to real networks and uses real funds. Only use after thorough testing!

## Updating the Bot

To update to the latest version:

```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## Troubleshooting

### Container Won't Start
- Check logs: `docker-compose logs arbitragex`
- Verify environment variables in `.env` file
- Ensure volumes have proper permissions

### Connection Issues
- Verify RPC URLs in `.env` file
- Check network connectivity
- Ensure firewall allows required connections

### Performance Issues
- Check container resource usage: `docker stats`
- Consider increasing container resources in `docker-compose.yml`
- Optimize strategy configurations 