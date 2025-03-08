# ArbitrageX Project Documentation

## Overview

ArbitrageX is a sophisticated arbitrage trading bot designed to identify and execute profitable trading opportunities across multiple decentralized exchanges (DEXes) on Ethereum and other EVM-compatible blockchains. The system consists of several components including a backend API, WebSocket service, blockchain connection, and trading bot.

## Project Structure

The project is organized into the following main directories:

- `backend/`: Contains the API server, WebSocket service, and database models
- `frontend/`: Contains the user interface for monitoring and controlling the bot
- `bot/`: Contains the arbitrage bot implementation and trading strategies
- `contracts/`: Contains smart contracts for interacting with the blockchain
- `scripts/`: Contains utility scripts for starting, stopping, and managing the project

## Setup and Installation

### Prerequisites

- Node.js v18+
- MongoDB
- Redis
- Ethereum node (local or remote)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   npm install --legacy-peer-deps
   ```
3. Configure environment variables in `.env` file

## Starting the Project

The project includes several scripts to start different components:

### `scripts/start_full_project.sh`

This is the main script to start all components of the project, including:
- Local blockchain node
- Backend API server
- WebSocket service
- Frontend server
- Trading bot

Usage:
```
./scripts/start_full_project.sh
```

### `scripts/start_arbitragex.sh`

Starts only the ArbitrageX backend services without the blockchain node.

Usage:
```
./scripts/start_arbitragex.sh
```

### `scripts/kill_all_arbitragex.sh`

Stops all running ArbitrageX processes.

Usage:
```
./scripts/kill_all_arbitragex.sh
```

### `scripts/start-mainnet-fork.sh`

Starts a local fork of the Ethereum mainnet for testing purposes.

Usage:
```
./scripts/start-mainnet-fork.sh
```

### `scripts/monitor_services.sh`

Monitors the status of all running services.

Usage:
```
./scripts/monitor_services.sh
```

## WebSocket Service

The WebSocket service provides real-time updates on system health and bot status. It's accessible at `ws://localhost:3002/ws`.

### Testing WebSocket Connection

A test script is provided to verify the WebSocket connection:

```
node websocket-test.js
```

This script connects to the WebSocket server and displays messages received, including:
- System health status (blockchain, MongoDB, Redis, Web3 connections)
- Bot status (active status, trades, profit, etc.)

## Bot Operation

The trading bot scans for arbitrage opportunities across different DEXes and executes trades when profitable opportunities are found.

### Bot Status

The bot status is available through the WebSocket service and includes:
- Active status
- Last heartbeat time
- Total trades
- Successful trades
- Failed trades
- Total profit
- Average gas used
- Network information

### Starting the Bot

The bot can be started using the API:

```
curl -X POST http://localhost:3001/api/v1/bot/start
```

### Stopping the Bot

The bot can be stopped using the API:

```
curl -X POST http://localhost:3001/api/v1/bot/stop
```

## API Endpoints

### Bot Control

- `POST /api/v1/bot/start`: Start the trading bot
- `POST /api/v1/bot/stop`: Stop the trading bot
- `GET /api/v1/bot/status`: Get the current bot status

### Health Checks

- `GET /api/v1/health`: Check the health of all services
- `GET /api/v1/blockchain/health`: Check the blockchain connection

### Trading

- `GET /api/v1/trades`: Get a list of all trades
- `GET /api/v1/trades/stats`: Get trading statistics

### AI Predictions

- `GET /api/v1/ai/predictions`: Get AI predictions for arbitrage opportunities
- `GET /api/v1/ai/stats`: Get AI performance statistics
- `GET /api/v1/ai/learning`: Get AI learning statistics

## Troubleshooting

### Common Issues

1. **WebSocket Connection Refused**
   - Ensure the backend server is running
   - Check if the WebSocket port (3002) is available

2. **Blockchain Connection Error**
   - Verify that the local blockchain node is running
   - Check the RPC URL in the environment variables

3. **Missing Dependencies**
   - Run `npm install --legacy-peer-deps` to install dependencies with compatibility mode

### Logs

Logs are available in the following locations:
- Backend logs: `backend/logs/`
- Bot logs: `bot/logs/`

## Development

### Building the Project

```
npm run build
```

### Running Tests

```
npm test
```

### Deployment

The project can be deployed using the deployment script:

```
./scripts/deploy.sh
```

## Environment Variables

Key environment variables:

- `NETWORK_RPC`: URL of the Ethereum node (default: `http://127.0.0.1:8545`)
- `NETWORK_NAME`: Name of the network (default: `mainnet`)
- `CHAIN_ID`: Chain ID of the network (default: `1`)
- `MONGODB_URI`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- `PORT`: Backend API port (default: `3001`)
- `WS_PORT`: WebSocket port (default: `3002`)

## Security Considerations

- Private keys should be stored securely and never committed to the repository
- Use environment variables for sensitive information
- Implement rate limiting for API endpoints
- Regularly update dependencies to patch security vulnerabilities

## Performance Optimization

The bot includes several optimization strategies:
- Gas price optimization
- Trade size optimization
- Slippage tolerance adjustment
- Multi-path routing for better execution prices

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 