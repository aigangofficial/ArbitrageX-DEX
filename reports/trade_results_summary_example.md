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
- Total Profit: 0.35 ETH ($799.05)
- Average Gas Used: 23076.57 (≈0.000346 ETH / $0.79)

## Recent Trades

### Trade 1
- Timestamp: 3/6/2024, 2:15:30 AM
- Token In: 10.00 WETH ($22830.00)
- Token Out: 22900.50 USDC ($22900.50)
- Profit: 0.03 ETH ($68.49)
- Status: Completed
- Router: UniswapV2
- Gas Used: 21500 (≈0.000323 ETH / $0.74)

### Trade 2
- Timestamp: 3/6/2024, 1:45:12 AM
- Token In: 15000.00 USDC ($15000.00)
- Token Out: 6.60 WETH ($15069.90)
- Profit: 0.03 ETH ($68.49)
- Status: Completed
- Router: SushiSwap
- Gas Used: 23400 (≈0.000351 ETH / $0.80)

### Trade 3
- Timestamp: 3/6/2024, 1:20:45 AM
- Token In: 5.00 WETH ($11415.00)
- Token Out: 0.75 BTC ($11490.00)
- Profit: 0.03 ETH ($68.49)
- Status: Completed
- Router: UniswapV3
- Gas Used: 25300 (≈0.000380 ETH / $0.87)

### Trade 4
- Timestamp: 3/6/2024, 12:55:18 AM
- Token In: 0.50 BTC ($7660.00)
- Token Out: 7700.00 USDC ($7700.00)
- Profit: 0.02 ETH ($45.66)
- Status: Completed
- Router: SushiSwap
- Gas Used: 22100 (≈0.000332 ETH / $0.76)

### Trade 5
- Timestamp: 3/6/2024, 12:30:05 AM
- Token In: 12000.00 USDC ($12000.00)
- Token Out: 5.30 WETH ($12099.90)
- Profit: 0.04 ETH ($91.32)
- Status: Completed
- Router: UniswapV2
- Gas Used: 21800 (≈0.000327 ETH / $0.75)

### Trade 6
- Timestamp: 3/5/2024, 11:45:30 PM
- Token In: 8.00 WETH ($18264.00)
- Token Out: 1.20 BTC ($18384.00)
- Profit: 0.05 ETH ($114.15)
- Status: Completed
- Router: UniswapV3
- Gas Used: 24500 (≈0.000368 ETH / $0.84)

### Trade 7
- Timestamp: 3/5/2024, 11:15:22 PM
- Token In: 1.00 BTC ($15320.00)
- Token Out: 6.75 WETH ($15411.75)
- Profit: 0.15 ETH ($342.45)
- Status: Completed
- Router: SushiSwap
- Gas Used: 22900 (≈0.000344 ETH / $0.78)

## Current Market Prices

- ETH/USD: $2283.00
- BTC/USD: $15320.00
- USDC/USD: $1.00

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