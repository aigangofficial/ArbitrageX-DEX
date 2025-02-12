# ArbitrageX

A decentralized arbitrage trading system leveraging flash loans for cross-DEX arbitrage opportunities.

## Project Structure

```
ArbitrageX/
│── contracts/                 # Smart Contracts (Solidity)
│   ├── FlashLoanService.sol    # Flash Loan logic
│   ├── ArbitrageExecutor.sol   # Executes arbitrage trades
│   ├── interfaces/             # External contract interfaces
│   ├── mocks/                  # Mock contracts for testing
│
│── backend/                    # Backend API & Execution Engine
│   ├── api/                    # Express API Server
│   ├── execution/              # Trade Execution Logic
│   ├── ai/                     # AI Learning Bot
│   ├── database/               # MongoDB Integration
│
│── frontend/                   # Web Dashboard
│   ├── components/             # UI Components
│   ├── pages/                  # Dashboard Pages
│   ├── services/               # API Integration
│
│── scripts/                    # Deployment Scripts
│── tests/                      # Testing Suite
```

## Prerequisites

- Node.js v18+
- Hardhat
- MongoDB
- Ethers.js v6
- TypeScript

## Environment Setup

1. Create a `config/.env` file with the following variables:

```bash
# Network Configuration
INFURA_API_KEY=your_key
SEPOLIA_PRIVATE_KEY=your_key
ETHERSCAN_API_KEY=your_key

# Contract Addresses
SEPOLIA_AAVE_POOL=0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951
SEPOLIA_UNISWAP_ROUTER=0x3bFA4769FB09eefC5a80d6E87c3B9C650f7Ae48E
SEPOLIA_SUSHISWAP_ROUTER=0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506

# Backend Configuration
MONGODB_URI=mongodb://localhost:27017/arbitragex
API_PORT=3000
WS_PORT=3001

# Optional: AI Configuration
ENABLE_AI_OPTIMIZATION=false
```

2. Install dependencies:

```bash
# Install root project dependencies
npm install

# Install contract dependencies
cd contracts && npm install

# Install backend dependencies
cd backend && npm install

# Install frontend dependencies
cd frontend && npm install
```

## Deployment

### Phase 1: Smart Contracts (Testnet)

1. Compile contracts:

```bash
npx hardhat compile
```

2. Run tests:

```bash
npx hardhat test
```

3. Deploy to Sepolia testnet:

```bash
npx hardhat run scripts/deploy-phase1.ts --network sepolia
```

4. Verify contracts:

```bash
# FlashLoanService
npx hardhat verify --network sepolia <FLASH_LOAN_ADDRESS> <AAVE_POOL>

# ArbitrageExecutor
npx hardhat verify --network sepolia <ARBITRAGE_EXECUTOR> <UNISWAP> <SUSHISWAP> <FLASH_LOAN_ADDRESS>
```

### Phase 2: Backend Services

1. Start MongoDB:

```bash
docker-compose -f backend/docker-compose.yml up -d
```

2. Start API server:

```bash
cd backend/api && npm run start:prod
```

3. Start execution engine:

```bash
cd backend/execution && npm run bot:start
```

### Phase 3: Frontend Dashboard

1. Build frontend:

```bash
cd frontend && npm run build
```

2. Start frontend server:

```bash
serve -s build -l 3001
```

## Testing

### Smart Contract Tests

```bash
# Run all tests
npm test

# Run specific test file
npx hardhat test test/FlashLoanArbitrage.test.ts

# Run with gas reporting
REPORT_GAS=true npx hardhat test
```

### Backend Tests

```bash
cd backend && npm test
```

### Frontend Tests

```bash
cd frontend && npm test
```

## Security

- All smart contracts are thoroughly tested and follow best practices
- Flash loan validation ensures profitable trades only
- Slippage protection prevents sandwich attacks
- Gas optimization for cost-effective execution
- Automated security checks in CI/CD pipeline

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
