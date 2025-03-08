# ArbitrageX Backend API with Web3 Integration

This module provides the backend API for the ArbitrageX system, including Web3 integration for interacting with smart contracts on the blockchain.

## Features

- **Web3 Integration**: Connect to Ethereum, Arbitrum, and Polygon networks
- **Smart Contract Interaction**: Execute arbitrage trades and manage execution modes
- **RESTful API**: Endpoints for blockchain health, arbitrage execution, and system status
- **WebSocket Support**: Real-time updates for trade execution and system status

## Setup

### Prerequisites

- Node.js 16+
- npm or yarn
- Access to Ethereum RPC endpoints (Infura, Alchemy, or local node)

### Installation

```bash
# Install dependencies
npm install

# Create .env file from template
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

### Environment Variables

```
# Server Configuration
PORT=3000
NODE_ENV=development

# Blockchain Configuration
ETHEREUM_RPC_URL=http://localhost:8545
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/your-api-key
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/your-api-key

# Security
JWT_SECRET=your-jwt-secret
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX=100

# Feature Flags
FORK_MODE=false
```

## Running the API

### Development Mode

```bash
# Start in development mode
npm run start:dev
```

### Production Mode

```bash
# Build the project
npm run build

# Start in production mode
npm run start:prod
```

### With Hardhat Fork

```bash
# Start with Hardhat fork integration
FORK_MODE=true ETHEREUM_RPC_URL=http://localhost:8545 npm run start:dev
```

## API Endpoints

### Blockchain Endpoints

#### GET /api/v1/blockchain/health

Check the health of the blockchain connection.

**Response:**

```json
{
  "status": "connected",
  "provider": {
    "url": "http://localhost:8545",
    "network": "mainnet",
    "blockNumber": 12345678
  },
  "contracts": {
    "arbitrageExecutor": "0x1234567890123456789012345678901234567890",
    "flashLoanService": "0x0987654321098765432109876543210987654321"
  }
}
```

#### POST /api/v1/blockchain/execute-arbitrage

Execute an arbitrage trade.

**Request:**

```json
{
  "sourceToken": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
  "targetToken": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "amount": "1.0",
  "sourceDex": "uniswap_v3",
  "targetDex": "sushiswap"
}
```

**Response:**

```json
{
  "status": "success",
  "txHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
}
```

#### POST /api/v1/blockchain/set-execution-mode

Set the execution mode for the arbitrage system.

**Request:**

```json
{
  "mode": "test"
}
```

**Response:**

```json
{
  "status": "success",
  "mode": "test"
}
```

### Other Endpoints

#### GET /api/v1/health

Check the health of the API server.

**Response:**

```json
{
  "status": "ok",
  "uptime": 3600,
  "timestamp": 1625097600000
}
```

## Testing

### Unit Tests

```bash
# Run unit tests
npm test
```

### Integration Tests

```bash
# Run integration tests
npm run test:integration
```

### Web3 Integration Test

```bash
# Run Web3 integration test
node scripts/test_web3_service.js
```

## Architecture

The Web3 integration is built with the following components:

1. **Web3Service**: Core service for blockchain interaction

   - Connects to Ethereum, Arbitrum, and Polygon networks
   - Manages contract instances and addresses
   - Provides methods for executing arbitrage and managing execution modes

2. **Blockchain Router**: API endpoints for blockchain interaction

   - Health check endpoint
   - Arbitrage execution endpoint
   - Execution mode management endpoint

3. **Express Middleware**: Makes Web3Service available to routes
   - Initializes Web3Service on application startup
   - Injects Web3Service into request objects

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
