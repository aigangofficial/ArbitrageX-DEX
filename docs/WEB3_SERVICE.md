# ArbitrageX Web3 Service

This document provides an overview of the ArbitrageX Web3 Service, which is responsible for connecting the backend API to the blockchain and facilitating interactions with smart contracts.

## 🚀 Overview

The Web3 Service is a critical component of the ArbitrageX system that:

1. Establishes and maintains a connection to the blockchain (Ethereum mainnet or a fork)
2. Loads and initializes smart contract instances
3. Provides an interface for executing arbitrage operations
4. Manages execution modes (test/production)
5. Exposes blockchain health information

## 📋 Key Components

### Web3Service Class

The `Web3Service` class (`backend/api/services/Web3Service.ts`) is the core of the Web3 integration, providing:

- Connection to Ethereum nodes
- Contract instance initialization
- Methods for executing arbitrage operations
- Methods for setting execution modes
- Health check functionality

### Blockchain Router

The `blockchainRouter` (`backend/api/routes/blockchainRouter.ts`) exposes the Web3 Service functionality through REST API endpoints:

- `GET /api/v1/blockchain/health` - Check blockchain connection status
- `POST /api/v1/blockchain/execute-arbitrage` - Execute an arbitrage operation
- `POST /api/v1/blockchain/set-execution-mode` - Set the execution mode (test/production)

## 🔄 Integration Flow

The Web3 Service integrates with the ArbitrageX system as follows:

1. The backend API initializes the Web3Service during startup
2. The Web3Service connects to the blockchain provider (mainnet or fork)
3. Contract addresses are loaded from configuration files
4. Contract instances are initialized with the loaded addresses
5. The blockchainRouter exposes the Web3Service functionality through REST endpoints
6. The frontend or other services can interact with the blockchain through these endpoints

## 🧪 Testing the Web3 Service

### Web3 Service Integration Test

The `test_web3_service.js` script (`scripts/test_web3_service.js`) provides a comprehensive test of the Web3 Service:

```bash
# Run the Web3 service integration test
node scripts/test_web3_service.js
```

This test:

1. Starts a Hardhat node in fork mode
2. Deploys contracts to the fork
3. Starts the backend API with Web3 integration
4. Tests the blockchain health endpoint
5. Tests the execution mode endpoint

### Using the Process Management Script

The process management script provides a convenient way to test the Web3 Service:

```bash
# Run the Web3 service integration test
./scripts/manage_processes.sh test-web3

# Run a full integration test including the Web3 service
./scripts/manage_processes.sh integration-test
```

### Manual Testing

You can also test the Web3 Service manually:

1. Start the Hardhat node:
   ```bash
   npx hardhat node --hostname 127.0.0.1 --port 8546 --fork https://mainnet.infura.io/v3/YOUR_INFURA_KEY
   ```

2. Deploy contracts:
   ```bash
   npx hardhat run scripts/deploy.ts --network localhost
   ```

3. Start the API server:
   ```bash
   cd backend/api
   PORT=3002 npm start
   ```

4. Test the blockchain health endpoint:
   ```bash
   curl http://127.0.0.1:3002/api/v1/blockchain/health
   ```

5. Test setting the execution mode:
   ```bash
   curl -X POST http://127.0.0.1:3002/api/v1/blockchain/set-execution-mode \
     -H "Content-Type: application/json" \
     -d '{"mode": "test"}'
   ```

## 📊 Expected Responses

### Blockchain Health Endpoint

```json
{
  "status": "connected",
  "provider": {
    "url": "http://127.0.0.1:8546",
    "network": "hardhat",
    "chainId": 31337
  },
  "contracts": {
    "securityAdmin": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "arbitrageExecutor": "0xb6057e08a11da09a998985874FE2119e98dB3D5D",
    "flashLoanService": "0xad203b3144f8c09a20532957174fc0366291643c",
    "uniswapRouter": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "sushiswapRouter": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    "aavePool": "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9",
    "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
  }
}
```

### Set Execution Mode Endpoint

```json
{
  "status": "success",
  "message": "Execution mode set to \"test\"",
  "mode": "test"
}
```

## 🔧 Configuration

The Web3 Service can be configured through environment variables:

- `ETHEREUM_RPC_URL` - The URL of the Ethereum node to connect to (default: `http://127.0.0.1:8546`)
- `NETWORK_RPC` - Alternative RPC URL for the network
- `NETWORK_NAME` - Name of the network (e.g., `mainnet`, `sepolia`)
- `CHAIN_ID` - Chain ID of the network

Contract addresses are loaded from `backend/config/contractAddresses.json`, which is generated during contract deployment.

## 🚨 Troubleshooting

### Common Issues

1. **Connection Issues**
   - Ensure the Hardhat node is running on the correct port
   - Check that the RPC URL is correct
   - Verify network connectivity

2. **Contract Interaction Failures**
   - Ensure contracts are deployed correctly
   - Verify contract addresses in the configuration file
   - Check that the signer has sufficient funds

3. **API Server Issues**
   - Ensure the API server is running on the correct port
   - Check for TypeScript compilation errors
   - Verify that the Web3Service is initialized correctly

### Debugging

For detailed debugging, check the logs:

```bash
# Check API server logs
cd backend/api
DEBUG=arbitragex:* npm start

# Check Hardhat node logs
npx hardhat node --hostname 127.0.0.1 --port 8546 --fork https://mainnet.infura.io/v3/YOUR_INFURA_KEY --verbose
```

## 🔄 Execution Modes

The Web3 Service supports two execution modes:

1. **Test Mode (0)** - For testing arbitrage strategies without real execution
2. **Production Mode (1)** - For executing real arbitrage operations

To set the execution mode:

```bash
curl -X POST http://127.0.0.1:3002/api/v1/blockchain/set-execution-mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "test"}'
```

## 🔗 Integration with AI Components

The Web3 Service integrates with the AI components of ArbitrageX:

1. The AI strategy optimizer identifies profitable arbitrage opportunities
2. The execution service uses the Web3 Service to execute these opportunities
3. The Web3 Service interacts with the blockchain to perform the arbitrage

This integration allows for:
- Real-time arbitrage execution
- AI-driven decision making
- Blockchain-based transaction execution
- Profit optimization through smart contract interactions

## 🚀 Next Steps

Future enhancements to the Web3 Service include:

1. **Multi-chain Support** - Extend the service to support multiple blockchains
2. **Gas Optimization** - Implement advanced gas estimation and optimization
3. **Transaction Bundling** - Support for bundling multiple transactions
4. **MEV Protection** - Enhanced protection against MEV attacks
5. **Performance Monitoring** - Real-time monitoring of blockchain interactions 