# ArbitrageX

ArbitrageX is a sophisticated arbitrage trading bot designed to identify and execute profitable trading opportunities across multiple decentralized exchanges (DEXes) on Ethereum and other EVM-compatible blockchains.

## Features

- **Multi-DEX Arbitrage**: Scan and execute trades across Uniswap, SushiSwap, and other DEXes
- **Real-time Monitoring**: WebSocket-based real-time updates on system health and bot status
- **AI-Powered Predictions**: Machine learning models to predict profitable trading opportunities
- **Gas Optimization**: Smart gas price strategies to maximize profitability
- **Comprehensive Dashboard**: Web interface for monitoring and controlling the bot
- **Detailed Analytics**: Track performance metrics and trading history

## Project Structure

The project is organized into the following main directories:

- `backend/`: Contains the API server, WebSocket service, and database models
- `frontend/`: Contains the user interface for monitoring and controlling the bot
- `bot/`: Contains the arbitrage bot implementation and trading strategies
- `contracts/`: Contains smart contracts for interacting with the blockchain
- `scripts/`: Contains utility scripts for starting, stopping, and managing the project

## Getting Started

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
4. Start the project:
   ```
   ./scripts/start_full_project.sh
   ```

## Documentation

For detailed documentation, please refer to the following guides:

- [Complete Documentation](DOCUMENTATION.md): Comprehensive guide to the ArbitrageX project
- [WebSocket Service Guide](WEBSOCKET_SERVICE.md): Details on using the WebSocket service
- [Scanning Errors Guide](SCANNING_ERRORS.md): Troubleshooting common scanning errors

## Scripts

The project includes several scripts to start different components:

- `./scripts/start_full_project.sh`: Start all components of the project
- `./scripts/start_arbitragex.sh`: Start only the ArbitrageX backend services
- `./scripts/kill_all_arbitragex.sh`: Stop all running ArbitrageX processes
- `./scripts/monitor_services.sh`: Monitor the status of all running services

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

## WebSocket Service

The WebSocket service provides real-time updates on system health and bot status. It's accessible at `ws://localhost:3002/ws`.

A test script is provided to verify the WebSocket connection:

```
node websocket-test.js
```

## Troubleshooting

For common issues and their solutions, please refer to the [Documentation](DOCUMENTATION.md#troubleshooting) section.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 