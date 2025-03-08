# ArbitrageX Trade Results Summary

## Available Trade Endpoints

- GET /api/v1/trades - List recent trades
- GET /api/v1/trades/stats - Get trade statistics and bot status
- GET /api/v1/trades/:txHash - Get details of a specific trade
- POST /api/v1/trades/execute - Execute a new trade

## Current Trade Statistics

- Total Trades: 7
- Successful Trades: 7
- Failed Trades: 0
- Total Profit: 0.35 ETH ($875.00)
- Average Gas Used: 0.00 (≈0.000000 ETH / $0.00)

## Recent Trades

### Trade 1
- Timestamp: 3/5/2025, 3:46:10 PM
- Token In: 3.00 WETH ($7500.00)
- Token Out: 0.05 USDC ($0.05)
- Profit: 0.05 ETH ($125.00)
- Status: completed
- Router: uniswap-sushiswap
- Gas Used: 23080 (≈0.000224 ETH / $0.56)

### Trade 2
- Timestamp: 3/5/2025, 3:41:03 PM
- Token In: 2.00 WETH ($5000.00)
- Token Out: 0.05 USDC ($0.05)
- Profit: 0.05 ETH ($125.00)
- Status: completed
- Router: uniswap-sushiswap
- Gas Used: 23080 (≈0.000253 ETH / $0.63)

### Trade 3
- Timestamp: 3/5/2025, 3:36:09 PM
- Token In: 1.00 WETH ($2500.00)
- Token Out: 0.05 USDC ($0.05)
- Profit: 0.05 ETH ($125.00)
- Status: completed
- Router: uniswap-sushiswap
- Gas Used: 23068 (≈0.000285 ETH / $0.71)

### Trade 4
- Timestamp: 3/5/2025, 3:27:07 PM
- Token In: 1.00 WETH ($2500.00)
- Token Out: 0.05 USDC ($0.05)
- Profit: 0.05 ETH ($125.00)
- Status: completed
- Router: uniswap-sushiswap
- Gas Used: 23068 (≈0.000323 ETH / $0.81)

### Trade 5
- Timestamp: 3/5/2025, 3:13:00 PM
- Token In: 6.00 WETH ($15000.00)
- Token Out: 0.05 USDC ($0.05)
- Profit: 0.05 ETH ($125.00)
- Status: completed
- Router: uniswap-sushiswap
- Gas Used: 23080 (≈0.000366 ETH / $0.91)

### Trade 6
- Timestamp: 3/5/2025, 3:06:19 PM
- Token In: 5.00 WETH ($12500.00)
- Token Out: 0.05 USDC ($0.05)
- Profit: 0.05 ETH ($125.00)
- Status: completed
- Router: uniswap-sushiswap
- Gas Used: 23080 (≈0.000414 ETH / $1.04)

### Trade 7
- Timestamp: 3/5/2025, 3:01:21 PM
- Token In: 4.00 WETH ($10000.00)
- Token Out: 0.05 USDC ($0.05)
- Profit: 0.05 ETH ($125.00)
- Status: completed
- Router: uniswap-sushiswap
- Gas Used: 23080 (≈0.000470 ETH / $1.18)

## Current Market Prices

- ETH/USD: $2500.00
- BTC/USD: $50000.00

## How to Access Trade Results

### Via API
- Fetch recent trades: `curl http://localhost:3002/api/v1/trades`
- Get trade statistics: `curl http://localhost:3002/api/v1/trades/stats`
- Get market prices: `curl http://localhost:3002/api/v1/market/data`

### Via Frontend
- Navigate to http://localhost:3001/dashboard
- Check the "Recent Trades" section

## Monitor Script

- The monitor script checks for new trades every minute
- Results are logged to `logs/monitor.log`
