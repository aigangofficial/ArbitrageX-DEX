# ArbitrageX Testing Guide

## Mainnet Fork Testing

### Environment Setup

1. Configure Mainnet Fork
```bash
# Set up environment variables
cp config/.env.example config/.env.fork
# Edit .env.fork with your Mainnet RPC URL
```

2. Install Dependencies
```bash
npm install
```

3. Start Local Fork
```bash
npm run start:fork
```

### Test Suites

1. Contract Tests
```bash
# Run all contract tests
npm test:contracts

# Run specific test
npm test:contracts -- -g "should execute flash loan"
```

2. Integration Tests
```bash
# Run all integration tests
npm test:integration

# Run specific integration test
npm test:integration -- -g "arbitrage execution"
```

3. End-to-End Tests
```bash
# Run all E2E tests
npm test:e2e
```

### Baseline Metrics

1. Gas Usage
- Average Gas per Trade: ~250,000
- Flash Loan Gas: ~150,000
- DEX Swap Gas: ~100,000

2. Profit Margins
- Minimum Profit: 0.1%
- Average Profit: 0.3-0.5%
- High Profit: >1%

3. Execution Latency
- Price Update: <100ms
- Trade Execution: <5s
- Block Confirmation: ~12s

### Test Coverage

1. Smart Contracts
- FlashLoanService: 100%
- ArbitrageExecutor: 100%
- Price Feed Integration: 95%

2. Backend Services
- API Endpoints: 90%
- WebSocket Service: 85%
- Price Monitoring: 90%

3. Frontend Components
- Price Display: 80%
- Trade Execution: 85%
- Network Status: 90%

### Common Test Scenarios

1. Flash Loan Tests
```typescript
it('should execute and repay flash loan', async () => {
  // Test implementation
});
```

2. Arbitrage Tests
```typescript
it('should execute profitable arbitrage', async () => {
  // Test implementation
});
```

3. Gas Price Tests
```typescript
it('should handle high gas prices', async () => {
  // Test implementation
});
```

### Monitoring Tests

1. Metrics Collection
```typescript
it('should track gas usage', async () => {
  // Test implementation
});
```

2. Alert Triggers
```typescript
it('should trigger alerts on high failure rate', async () => {
  // Test implementation
});
```

### Test Environment Variables

```env
# Required for tests
MAINNET_RPC_URL=your_mainnet_rpc_url
FORK_BLOCK_NUMBER=19261000
FORK_ENABLED=true

# Optional for extended tests
ETHERSCAN_API_KEY=your_api_key
ALCHEMY_API_KEY=your_api_key
```

### Running Tests in CI

```yaml
# .github/workflows/test.yml
name: Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
      - run: npm install
      - run: npm test
```

### Test Reports

Test results are stored in:
- `/test-results/contracts.xml`
- `/test-results/integration.xml`
- `/test-results/e2e.xml`

### Troubleshooting Tests

1. Fork Reset
```typescript
before(async () => {
  await network.provider.request({
    method: "hardhat_reset",
    params: [{
      forking: {
        jsonRpcUrl: process.env.MAINNET_RPC_URL,
        blockNumber: FORK_CONFIG.blockNumber
      }
    }]
  });
});
```

2. Snapshot Management
```typescript
beforeEach(async () => {
  await network.provider.send("evm_snapshot", []);
});

afterEach(async () => {
  await network.provider.send("evm_revert", ["latest"]);
});
```

### Best Practices

1. Always reset fork before test suite
2. Use snapshots for efficient test isolation
3. Use mainnet forking for all external interactions
4. Use real contract addresses from mainnet
5. Test with realistic gas prices
6. Verify flash loan repayment
7. Check profit calculations
8. Monitor execution time
9. Validate error handling
10. Document test scenarios
