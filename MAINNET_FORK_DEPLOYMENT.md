# ArbitrageX Mainnet Fork Deployment Guide

## Overview

ArbitrageX is designed to run on a **mainnet fork** environment, not on testnets like Sepolia. This approach allows us to:

1. Test against real liquidity conditions and DEX states
2. Simulate arbitrage opportunities with actual market data
3. Interact with production contracts without spending real ETH
4. Develop and test strategies in a realistic environment

## ⚠️ Important Warning

**DO NOT deploy this project to Sepolia, Goerli, or any other testnet!**

Testnets do not have:

- The same liquidity pools as mainnet
- The same token prices or price movements
- Many of the contracts we need to interact with (or they have different addresses)
- Realistic arbitrage opportunities

## Deployment Instructions

### Prerequisites

1. Make sure you have a `.env` file with the following variables:

   ```
   MAINNET_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
   FORK_BLOCK_NUMBER=19261000
   ```

2. Install dependencies:
   ```bash
   npm install
   cd backend && npm install
   cd ../frontend && npm install
   ```

### Option 1: One-Command Deployment (Recommended)

We've created a single command to start a mainnet fork and deploy all contracts:

```bash
npm run start:mainnet-fork
```

This will:

1. Start a Hardhat node with mainnet forking
2. Deploy all contracts to the fork
3. Configure the contracts for arbitrage
4. Save contract addresses for the backend

### Option 2: Manual Deployment

If you prefer to run the steps manually:

1. Start a Hardhat node with mainnet forking:

   ```bash
   npx hardhat node --fork $MAINNET_RPC_URL --fork-block-number 19261000
   ```

2. In a new terminal, deploy the contracts:
   ```bash
   npm run deploy
   # or
   npx hardhat run scripts/deploy.ts --network localhost
   ```

## Running the Bot

After deployment, you can start the backend services:

```bash
cd backend
docker-compose up -d
cd api && npm run start:prod
cd ../execution && npm run bot:start
```

And the frontend dashboard:

```bash
cd frontend
npm run build
serve -s build -l 3001
```

## Testing

To run tests against the mainnet fork:

```bash
npm run test:contracts
```

## Troubleshooting

### Common Issues

1. **RPC Rate Limiting**: If you encounter rate limiting from your RPC provider, consider:

   - Using a paid API plan
   - Reducing the frequency of requests
   - Caching blockchain data where possible

2. **Contract Deployment Failures**: Ensure you're using the correct contract addresses for:

   - Uniswap V2 Router
   - SushiSwap Router
   - Aave V3 Pool
   - WETH and USDC tokens

3. **Insufficient Balance**: The default Hardhat accounts have plenty of ETH on the fork, but you might need to acquire specific tokens:
   - Use `scripts/get-tokens.ts` to acquire test tokens on the fork
   - Impersonate whale accounts for large token amounts

## Advanced Configuration

For advanced users who need to customize the fork environment:

1. **Custom Fork Block**:

   ```
   FORK_BLOCK_NUMBER=YOUR_BLOCK_NUMBER npm run start:mainnet-fork
   ```

2. **Custom RPC URL**:

   ```
   MAINNET_RPC_URL=YOUR_RPC_URL npm run start:mainnet-fork
   ```

3. **Running with Specific AI Modules**:
   ```bash
   cd backend/ai
   python strategy_optimizer.py --testnet
   ```

## Support

If you encounter any issues with the mainnet fork deployment, please open an issue on GitHub or contact the development team.
