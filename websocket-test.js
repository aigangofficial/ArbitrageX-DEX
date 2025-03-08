/**
 * WebSocket Test Client for ArbitrageX
 * 
 * This script connects to the ArbitrageX WebSocket server and logs messages
 * received, with special focus on system health status.
 * 
 * Usage: node websocket-test.js
 */

const WebSocket = require('ws');

// WebSocket server URL
const wsUrl = 'ws://localhost:3002/ws';

console.log(`Connecting to WebSocket server at ${wsUrl}...`);

// Create WebSocket connection
const socket = new WebSocket(wsUrl);

// Connection opened
socket.on('open', () => {
  console.log('Connected to WebSocket server successfully!');
});

// Listen for messages
socket.on('message', (data) => {
  try {
    const message = JSON.parse(data);
    
    // Log all message types
    console.log(`Received message type: ${message.type}`);
    
    // Special handling for system health messages
    if (message.type === 'systemHealth') {
      console.log('SYSTEM HEALTH STATUS:');
      console.log(`- Blockchain: ${message.data.blockchain ? 'Connected ✅' : 'Disconnected ❌'}`);
      console.log(`- MongoDB: ${message.data.mongodb ? 'Connected ✅' : 'Disconnected ❌'}`);
      console.log(`- Redis: ${message.data.redis ? 'Connected ✅' : 'Disconnected ❌'}`);
      console.log(`- Web3: ${message.data.web3 ? 'Connected ✅' : 'Disconnected ❌'}`);
      console.log('-----------------------------------');
    }
    
    // Special handling for bot status messages
    if (message.type === 'bot_status') {
      console.log('BOT STATUS UPDATE:');
      console.log(`- Active: ${message.data.isActive ? 'Yes ✅' : 'No ❌'}`);
      console.log(`- Last Heartbeat: ${new Date(message.data.lastHeartbeat).toLocaleString()}`);
      console.log(`- Total Trades: ${message.data.totalTrades}`);
      console.log(`- Successful Trades: ${message.data.successfulTrades}`);
      console.log(`- Failed Trades: ${message.data.failedTrades}`);
      console.log(`- Total Profit: ${message.data.totalProfit} ETH`);
      console.log(`- Average Gas Used: ${message.data.averageGasUsed}`);
      console.log(`- Network: ${message.data.network}`);
      console.log('-----------------------------------');
    }
  } catch (error) {
    console.error('Error parsing message:', error);
    console.log('Raw message:', data.toString());
  }
});

// Handle errors
socket.on('error', (error) => {
  console.error('WebSocket error:', error);
});

// Connection closed
socket.on('close', () => {
  console.log('Disconnected from WebSocket server');
});

// Keep the connection alive
process.on('SIGINT', () => {
  console.log('Closing WebSocket connection...');
  socket.close();
  process.exit(0);
});

console.log('Waiting for messages... (Press Ctrl+C to exit)'); 