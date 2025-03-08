#!/usr/bin/env node

const fs = require('fs');

// Read the JSON files
const trades = JSON.parse(fs.readFileSync('trades.json', 'utf8'));
const tradeStats = JSON.parse(fs.readFileSync('trade_stats.json', 'utf8'));
const marketData = JSON.parse(fs.readFileSync('market_data.json', 'utf8'));

// Get prices in USD from market data
const prices = {
  // Extract prices from market data
  'ETH': parseFloat(marketData.data.prices['ETH/USDC']),
  'BTC': parseFloat(marketData.data.prices['BTC/USDC']),
  'WETH': parseFloat(marketData.data.prices['ETH/USDC']), // WETH has same price as ETH
  // Add more coins as needed
};

// Token address to symbol mapping
const tokenAddressToSymbol = {
  '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2': 'WETH', // WETH
  '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': 'USDC',
  // Add more token mappings as needed
};

// Format currency
function formatCurrency(amount, decimals = 2) {
  if (isNaN(amount)) return 'N/A';
  return parseFloat(amount).toFixed(decimals);
}

// Convert any coin to USD
function coinToUsd(amount, symbol) {
  if (isNaN(amount)) return 0;
  
  // If the symbol is USDC or other stablecoins, return the amount directly
  if (symbol === 'USDC' || symbol === 'USDT' || symbol === 'DAI') {
    return parseFloat(amount);
  }
  
  // Otherwise, convert using the price data
  const price = prices[symbol] || prices['ETH']; // Default to ETH price if not found
  return parseFloat(amount) * price;
}

// Format coin amount with USD equivalent
function formatCoinWithUsd(amount, symbol) {
  if (isNaN(amount)) return 'N/A';
  const usdAmount = coinToUsd(amount, symbol);
  return `${formatCurrency(amount)} ${symbol} ($${formatCurrency(usdAmount)})`;
}

// Calculate gas cost in USD
function calculateGasCostUsd(gasUsed, gasPrice) {
  if (isNaN(gasUsed) || isNaN(gasPrice)) return 0;
  // Gas cost in ETH = (gasUsed * gasPrice) / 10^18
  const gasCostEth = (gasUsed * parseFloat(gasPrice)) / 1e18;
  return coinToUsd(gasCostEth, 'ETH');
}

// Get token symbol from address
function getTokenSymbol(address) {
  return tokenAddressToSymbol[address] || 'Unknown';
}

// Generate summary
let summary = `# ArbitrageX Trade Results Summary\n\n`;

// Available endpoints
summary += `## Available Trade Endpoints\n\n`;
summary += `- GET /api/v1/trades - List recent trades\n`;
summary += `- GET /api/v1/trades/stats - Get trade statistics and bot status\n`;
summary += `- GET /api/v1/trades/:txHash - Get details of a specific trade\n`;
summary += `- POST /api/v1/trades/execute - Execute a new trade\n\n`;

// Current trade statistics
summary += `## Current Trade Statistics\n\n`;
if (tradeStats && tradeStats.success) {
  const stats = tradeStats.stats;
  summary += `- Total Trades: ${stats.totalTrades}\n`;
  summary += `- Successful Trades: ${stats.successfulTrades}\n`;
  summary += `- Failed Trades: ${stats.failedTrades}\n`;
  summary += `- Total Profit: ${formatCoinWithUsd(stats.totalProfit, 'ETH')}\n`;
  
  // Calculate average gas cost in USD
  const avgGasUsed = parseFloat(stats.averageGasUsed) || 0;
  // Use average gas price from trades if available, otherwise use a default
  let avgGasPrice = 15e9; // Default: 15 Gwei
  
  if (trades && trades.success && trades.trades && trades.trades.length > 0) {
    // Calculate average gas price from trades
    const totalGasPrice = trades.trades.reduce((sum, trade) => sum + parseFloat(trade.gasPrice || 0), 0);
    if (totalGasPrice > 0) {
      avgGasPrice = totalGasPrice / trades.trades.length;
    }
  }
  
  const avgGasCostEth = (avgGasUsed * avgGasPrice) / 1e18;
  const avgGasCostUsd = coinToUsd(avgGasCostEth, 'ETH');
  
  summary += `- Average Gas Used: ${formatCurrency(avgGasUsed)} (≈${formatCurrency(avgGasCostEth, 6)} ETH / $${formatCurrency(avgGasCostUsd)})\n\n`;
} else {
  summary += `- No trade statistics available\n\n`;
}

// Recent trades
summary += `## Recent Trades\n\n`;
if (trades && trades.success && trades.trades && trades.trades.length > 0) {
  trades.trades.forEach((trade, index) => {
    const date = new Date(trade.timestamp).toLocaleString();
    
    // Get token symbols
    const tokenInSymbol = getTokenSymbol(trade.tokenIn);
    const tokenOutSymbol = getTokenSymbol(trade.tokenOut);
    
    // Calculate USD values
    const amountInEth = parseFloat(trade.amountIn) / 1e18;
    const amountInUsd = coinToUsd(amountInEth, tokenInSymbol);
    const amountOutUsd = coinToUsd(trade.amountOut, tokenOutSymbol);
    const profitUsd = coinToUsd(trade.profit, 'ETH');
    
    summary += `### Trade ${index + 1}\n`;
    summary += `- Timestamp: ${date}\n`;
    summary += `- Token In: ${formatCurrency(amountInEth)} ${tokenInSymbol} ($${formatCurrency(amountInUsd)})\n`;
    summary += `- Token Out: ${formatCurrency(trade.amountOut)} ${tokenOutSymbol} ($${formatCurrency(amountOutUsd)})\n`;
    summary += `- Profit: ${formatCoinWithUsd(trade.profit, 'ETH')}\n`;
    summary += `- Status: ${trade.status}\n`;
    summary += `- Router: ${trade.router}\n`;
    
    // Calculate gas cost in USD
    const gasCostEth = (trade.gasUsed * parseFloat(trade.gasPrice)) / 1e18;
    const gasCostUsd = coinToUsd(gasCostEth, 'ETH');
    
    summary += `- Gas Used: ${trade.gasUsed} (≈${formatCurrency(gasCostEth, 6)} ETH / $${formatCurrency(gasCostUsd)})\n\n`;
  });
} else {
  summary += `- No recent trades available\n\n`;
}

// Current market prices
summary += `## Current Market Prices\n\n`;
Object.entries(prices).forEach(([symbol, price]) => {
  if (symbol !== 'WETH') { // Skip WETH as it's the same as ETH
    summary += `- ${symbol}/USD: $${formatCurrency(price)}\n`;
  }
});
summary += '\n';

// How to access trade results
summary += `## How to Access Trade Results\n\n`;
summary += `### Via API\n`;
summary += `- Fetch recent trades: \`curl http://localhost:3002/api/v1/trades\`\n`;
summary += `- Get trade statistics: \`curl http://localhost:3002/api/v1/trades/stats\`\n`;
summary += `- Get market prices: \`curl http://localhost:3002/api/v1/market/data\`\n\n`;

summary += `### Via Frontend\n`;
summary += `- Navigate to http://localhost:3001/dashboard\n`;
summary += `- Check the "Recent Trades" section\n\n`;

// Monitor script details
summary += `## Monitor Script\n\n`;
summary += `- The monitor script checks for new trades every minute\n`;
summary += `- Results are logged to \`logs/monitor.log\`\n`;

// Write to file
fs.writeFileSync('trade_results_summary.md', summary);
console.log('Trade summary with USD values for all coins generated: trade_results_summary.md'); 