# ArbitrageX WebSocket Service Guide

## Overview

The WebSocket service in ArbitrageX provides real-time updates on system health, bot status, and trading activities. This document explains how to use the WebSocket service, the message types it broadcasts, and how to implement custom clients.

## Connection Details

- **WebSocket URL**: `ws://localhost:3002/ws`
- **Protocol**: WebSocket (RFC 6455)
- **Authentication**: None (for internal use only)

## Message Types

The WebSocket service broadcasts several types of messages:

### 1. System Health (`systemHealth`)

Provides the health status of all system components.

**Example Message:**
```json
{
  "type": "systemHealth",
  "data": {
    "blockchain": true,
    "mongodb": true,
    "redis": true,
    "web3": true
  }
}
```

**Fields:**
- `blockchain`: Boolean indicating if the blockchain connection is healthy
- `mongodb`: Boolean indicating if the MongoDB connection is healthy
- `redis`: Boolean indicating if the Redis connection is healthy
- `web3`: Boolean indicating if the Web3 connection is healthy

### 2. Bot Status (`bot_status`)

Provides the current status of the trading bot.

**Example Message:**
```json
{
  "type": "bot_status",
  "data": {
    "isActive": true,
    "lastHeartbeat": "2025-03-07T02:17:40.000Z",
    "totalTrades": 7,
    "successfulTrades": 7,
    "failedTrades": 0,
    "totalProfit": "0.35",
    "averageGasUsed": 23076.57,
    "memoryUsage": {
      "heapUsed": 67584000,
      "heapTotal": 93487104,
      "external": 1825648
    },
    "cpuUsage": 2.5,
    "pendingTransactions": 0,
    "network": "mainnet",
    "connected": true
  }
}
```

**Fields:**
- `isActive`: Boolean indicating if the bot is active
- `lastHeartbeat`: Timestamp of the last heartbeat from the bot
- `totalTrades`: Total number of trades attempted
- `successfulTrades`: Number of successful trades
- `failedTrades`: Number of failed trades
- `totalProfit`: Total profit in ETH
- `averageGasUsed`: Average gas used per transaction
- `memoryUsage`: Object containing memory usage statistics
- `cpuUsage`: CPU usage percentage
- `pendingTransactions`: Number of pending transactions
- `network`: Current blockchain network
- `connected`: Boolean indicating if the bot is connected

### 3. Trade Update (`trade_update`)

Sent when a new trade is executed.

**Example Message:**
```json
{
  "type": "trade_update",
  "data": {
    "tradeId": "trade_1234567890",
    "tokenA": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "tokenB": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "amountIn": "1.0",
    "amountOut": "1.05",
    "profit": "0.05",
    "gasUsed": 150000,
    "timestamp": "2025-03-07T02:30:45.000Z",
    "status": "success",
    "txHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
  }
}
```

**Fields:**
- `tradeId`: Unique identifier for the trade
- `tokenA`: Address of the first token in the pair
- `tokenB`: Address of the second token in the pair
- `amountIn`: Amount of tokenA used in the trade
- `amountOut`: Amount of tokenB received from the trade
- `profit`: Profit from the trade in ETH
- `gasUsed`: Gas used for the transaction
- `timestamp`: Timestamp when the trade was executed
- `status`: Status of the trade (success, failed)
- `txHash`: Transaction hash on the blockchain

### 4. Arbitrage Opportunity (`arbitrage_opportunity`)

Sent when a new arbitrage opportunity is detected.

**Example Message:**
```json
{
  "type": "arbitrage_opportunity",
  "data": {
    "opportunityId": "opp_1234567890",
    "tokenA": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "tokenB": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "exchange1": "UNISWAP",
    "exchange2": "SUSHISWAP",
    "price1": "1.02",
    "price2": "1.05",
    "priceDifference": "2.94",
    "estimatedProfit": "0.03",
    "timestamp": "2025-03-07T02:29:45.000Z"
  }
}
```

**Fields:**
- `opportunityId`: Unique identifier for the opportunity
- `tokenA`: Address of the first token in the pair
- `tokenB`: Address of the second token in the pair
- `exchange1`: Name of the first exchange
- `exchange2`: Name of the second exchange
- `price1`: Price on the first exchange
- `price2`: Price on the second exchange
- `priceDifference`: Percentage difference between prices
- `estimatedProfit`: Estimated profit in ETH
- `timestamp`: Timestamp when the opportunity was detected

### 5. Error Notification (`error`)

Sent when an error occurs in the system.

**Example Message:**
```json
{
  "type": "error",
  "data": {
    "message": "Failed to execute trade",
    "code": "TRADE_EXECUTION_FAILED",
    "timestamp": "2025-03-07T02:35:12.000Z",
    "details": {
      "tradeId": "trade_1234567890",
      "reason": "Insufficient funds"
    }
  }
}
```

**Fields:**
- `message`: Error message
- `code`: Error code
- `timestamp`: Timestamp when the error occurred
- `details`: Additional details about the error

## Using the WebSocket Service

### JavaScript/Node.js Client

Here's a simple Node.js client to connect to the WebSocket service:

```javascript
const WebSocket = require('ws');

// WebSocket server URL
const wsUrl = 'ws://localhost:3002/ws';

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
    console.log(`Received message type: ${message.type}`);
    console.log('Data:', message.data);
    
    // Handle different message types
    switch (message.type) {
      case 'systemHealth':
        handleSystemHealth(message.data);
        break;
      case 'bot_status':
        handleBotStatus(message.data);
        break;
      case 'trade_update':
        handleTradeUpdate(message.data);
        break;
      case 'arbitrage_opportunity':
        handleArbitrageOpportunity(message.data);
        break;
      case 'error':
        handleError(message.data);
        break;
      default:
        console.log('Unknown message type:', message.type);
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

// Example handler functions
function handleSystemHealth(data) {
  console.log('System Health:');
  console.log(`- Blockchain: ${data.blockchain ? 'Connected ✅' : 'Disconnected ❌'}`);
  console.log(`- MongoDB: ${data.mongodb ? 'Connected ✅' : 'Disconnected ❌'}`);
  console.log(`- Redis: ${data.redis ? 'Connected ✅' : 'Disconnected ❌'}`);
  console.log(`- Web3: ${data.web3 ? 'Connected ✅' : 'Disconnected ❌'}`);
}

function handleBotStatus(data) {
  console.log('Bot Status:');
  console.log(`- Active: ${data.isActive ? 'Yes ✅' : 'No ❌'}`);
  console.log(`- Last Heartbeat: ${new Date(data.lastHeartbeat).toLocaleString()}`);
  console.log(`- Total Trades: ${data.totalTrades}`);
  console.log(`- Successful Trades: ${data.successfulTrades}`);
  console.log(`- Failed Trades: ${data.failedTrades}`);
  console.log(`- Total Profit: ${data.totalProfit} ETH`);
}

function handleTradeUpdate(data) {
  console.log('Trade Update:');
  console.log(`- Trade ID: ${data.tradeId}`);
  console.log(`- Tokens: ${data.tokenA} -> ${data.tokenB}`);
  console.log(`- Profit: ${data.profit} ETH`);
  console.log(`- Status: ${data.status}`);
  console.log(`- TX Hash: ${data.txHash}`);
}

function handleArbitrageOpportunity(data) {
  console.log('Arbitrage Opportunity:');
  console.log(`- Opportunity ID: ${data.opportunityId}`);
  console.log(`- Tokens: ${data.tokenA} -> ${data.tokenB}`);
  console.log(`- Exchanges: ${data.exchange1} -> ${data.exchange2}`);
  console.log(`- Price Difference: ${data.priceDifference}%`);
  console.log(`- Estimated Profit: ${data.estimatedProfit} ETH`);
}

function handleError(data) {
  console.error('Error Notification:');
  console.error(`- Message: ${data.message}`);
  console.error(`- Code: ${data.code}`);
  console.error(`- Time: ${new Date(data.timestamp).toLocaleString()}`);
  if (data.details) {
    console.error('- Details:', data.details);
  }
}
```

### Browser Client

Here's a simple browser client to connect to the WebSocket service:

```html
<!DOCTYPE html>
<html>
<head>
  <title>ArbitrageX WebSocket Client</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 20px;
    }
    #messages {
      border: 1px solid #ccc;
      padding: 10px;
      height: 400px;
      overflow-y: auto;
      margin-bottom: 10px;
    }
    .message {
      margin-bottom: 10px;
      padding: 5px;
      border-bottom: 1px solid #eee;
    }
    .systemHealth { background-color: #e6f7ff; }
    .bot_status { background-color: #f6ffed; }
    .trade_update { background-color: #fff7e6; }
    .arbitrage_opportunity { background-color: #f9f0ff; }
    .error { background-color: #fff1f0; }
  </style>
</head>
<body>
  <h1>ArbitrageX WebSocket Client</h1>
  <div id="connection-status">Disconnected</div>
  <div id="messages"></div>
  <button id="connect">Connect</button>
  <button id="disconnect" disabled>Disconnect</button>

  <script>
    const messagesDiv = document.getElementById('messages');
    const connectBtn = document.getElementById('connect');
    const disconnectBtn = document.getElementById('disconnect');
    const connectionStatus = document.getElementById('connection-status');
    
    let socket = null;
    
    connectBtn.addEventListener('click', () => {
      // WebSocket server URL
      const wsUrl = 'ws://localhost:3002/ws';
      
      // Create WebSocket connection
      socket = new WebSocket(wsUrl);
      
      // Connection opened
      socket.addEventListener('open', () => {
        connectionStatus.textContent = 'Connected';
        connectionStatus.style.color = 'green';
        connectBtn.disabled = true;
        disconnectBtn.disabled = false;
        addMessage('system', 'Connected to WebSocket server successfully!');
      });
      
      // Listen for messages
      socket.addEventListener('message', (event) => {
        try {
          const message = JSON.parse(event.data);
          addMessage(message.type, message);
        } catch (error) {
          addMessage('error', `Error parsing message: ${error.message}`);
          console.error('Raw message:', event.data);
        }
      });
      
      // Handle errors
      socket.addEventListener('error', (error) => {
        connectionStatus.textContent = 'Error';
        connectionStatus.style.color = 'red';
        addMessage('error', `WebSocket error: ${error}`);
      });
      
      // Connection closed
      socket.addEventListener('close', () => {
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.style.color = 'red';
        connectBtn.disabled = false;
        disconnectBtn.disabled = true;
        addMessage('system', 'Disconnected from WebSocket server');
      });
    });
    
    disconnectBtn.addEventListener('click', () => {
      if (socket) {
        socket.close();
      }
    });
    
    function addMessage(type, data) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `message ${type}`;
      
      const timestamp = new Date().toLocaleTimeString();
      
      if (typeof data === 'string') {
        messageDiv.innerHTML = `<strong>[${timestamp}]</strong>: ${data}`;
      } else {
        messageDiv.innerHTML = `
          <strong>[${timestamp}] ${data.type}</strong>
          <pre>${JSON.stringify(data, null, 2)}</pre>
        `;
      }
      
      messagesDiv.appendChild(messageDiv);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
  </script>
</body>
</html>
```

## WebSocket Service Implementation

The WebSocket service is implemented in `backend/api/websocket/WebSocketService.ts`. Here's an overview of its key components:

### Server Initialization

```typescript
// Initialize WebSocket server
this.wss = new WebSocket.Server({ port: this.port });

// Set up event handlers
this.wss.on('connection', this.handleConnection.bind(this));
this.wss.on('error', this.handleServerError.bind(this));
this.wss.on('close', this.handleServerClose.bind(this));
```

### Connection Handling

```typescript
private handleConnection(ws: WebSocket, req: http.IncomingMessage): void {
  // Add client ID and connection time
  (ws as CustomWebSocket).clientId = uuidv4();
  (ws as CustomWebSocket).connectedAt = new Date();
  
  // Log connection
  logger.info(`Client connected: ${(ws as CustomWebSocket).clientId}`);
  
  // Set up client event handlers
  ws.on('message', (message: WebSocket.Data) => this.handleMessage(ws as CustomWebSocket, message));
  ws.on('close', () => this.handleClientClose(ws as CustomWebSocket));
  ws.on('error', (error: Error) => this.handleClientError(ws as CustomWebSocket, error));
  
  // Send initial status update
  this.sendInitialStatus(ws as CustomWebSocket);
}
```

### Broadcasting Messages

```typescript
public broadcast(type: string, data: any): void {
  const message = JSON.stringify({ type, data });
  
  this.wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}
```

### Status Broadcasting

```typescript
private startStatusBroadcast(): void {
  setInterval(async () => {
    try {
      // Get the latest bot status
      const status = await BotStatus.findOne().sort({ lastHeartbeat: -1 });
      
      if (status) {
        // Broadcast the bot status to all connected clients
        this.broadcast('bot_status', {
          isActive: status.isActive,
          lastHeartbeat: status.lastHeartbeat,
          totalTrades: status.totalTrades,
          successfulTrades: status.successfulTrades,
          failedTrades: status.failedTrades,
          totalProfit: status.totalProfit,
          averageGasUsed: status.averageGasUsed,
          memoryUsage: status.memoryUsage,
          cpuUsage: status.cpuUsage,
          pendingTransactions: status.pendingTransactions,
          network: status.network,
          connected: true
        });
      }
      
      // Broadcast system health status
      this.broadcastSystemHealth();
    } catch (error) {
      logger.error(`Error broadcasting status: ${error instanceof Error ? error.message : String(error)}`);
    }
  }, this.statusInterval);
}
```

## Extending the WebSocket Service

### Adding New Message Types

To add a new message type to the WebSocket service:

1. Define the message structure
2. Create a broadcast method for the new message type
3. Call the broadcast method when appropriate

Example:

```typescript
// Define message structure
interface MarketUpdateMessage {
  pair: string;
  price: string;
  volume: string;
  change24h: string;
  timestamp: Date;
}

// Create broadcast method
public broadcastMarketUpdate(update: MarketUpdateMessage): void {
  this.broadcast('market_update', update);
}

// Call the broadcast method
marketService.on('update', (data) => {
  webSocketService.broadcastMarketUpdate(data);
});
```

### Custom Client Authentication

To add authentication to the WebSocket service:

```typescript
private handleConnection(ws: WebSocket, req: http.IncomingMessage): void {
  // Extract token from query parameters
  const url = new URL(req.url || '', `http://${req.headers.host}`);
  const token = url.searchParams.get('token');
  
  // Validate token
  if (!token || !this.validateToken(token)) {
    logger.warn(`Unauthorized connection attempt from ${req.socket.remoteAddress}`);
    ws.close(1008, 'Unauthorized');
    return;
  }
  
  // Continue with authorized connection
  // ...
}

private validateToken(token: string): boolean {
  // Implement token validation logic
  return true; // Placeholder
}
```

## Conclusion

The WebSocket service is a critical component of the ArbitrageX system, providing real-time updates on system health, bot status, and trading activities. By following this guide, you can effectively use the WebSocket service to monitor and interact with the ArbitrageX system in real-time. 