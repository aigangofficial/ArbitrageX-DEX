# ArbitrageX Project Documentation

## Project Overview

ArbitrageX is an AI-powered trading platform that identifies and executes arbitrage opportunities across various decentralized exchanges (DEXs). The system consists of a backend service built with Node.js, TypeScript, and Express, and a frontend built with Next.js and React.

## System Architecture

### Backend Components

1. **API Server**: Express-based REST API server
2. **WebSocket Server**: Real-time communication for system status and trade updates
3. **Bot Service**: Automated trading bot that executes arbitrage opportunities
4. **AI Service**: Machine learning models for predicting profitable trades
5. **Web3 Service**: Blockchain interaction using ethers.js
6. **Database Services**: MongoDB for persistent storage and Redis for caching

### Frontend Components

1. **Dashboard**: Main UI for monitoring system status and trades
2. **AI Dashboard**: Specialized view for AI insights and predictions
3. **Trade Panel**: Interface for viewing and managing trades
4. **System Health Monitor**: Real-time status of all system components

## Key Files and Directories

### Backend

- `backend/api/server.ts`: Main Express server setup
- `backend/api/routes/`: API route definitions
- `backend/api/services/`: Core service implementations
  - `Web3Service.ts`: Blockchain connectivity and contract interactions
  - `AIService.ts`: AI prediction and analysis
  - `MonitoringService.ts`: System health monitoring
- `backend/api/websocket/`: WebSocket server implementation
  - `WebSocketService.ts`: Manages real-time connections and broadcasts
- `backend/api/models/`: Database models
- `backend/api/controllers/`: Request handlers

### Frontend

- `frontend/pages/`: Next.js page components
  - `index.tsx`: Main dashboard
  - `new-dashboard.tsx`: Enhanced dashboard with WebSocket integration
  - `ai-dashboard.tsx`: AI insights and predictions
- `frontend/components/`: Reusable UI components
  - `AIComponents.tsx`: AI-related UI components
  - `SystemHealthMonitor.tsx`: Health status display
- `frontend/hooks/`: Custom React hooks
  - `useWebSocket.ts`: WebSocket connection management

### Configuration

- `.env`: Environment variables for API keys, URLs, and configuration
- `backend/.env`: Backend-specific environment variables

## Key Features

### Blockchain Integration

The system connects to Ethereum and other blockchains using Infura. The Web3Service manages these connections with a robust retry mechanism and fallback options.

```typescript
// Web3Service connection example
async connectWithBackoff(attempt = 1) {
  try {
    // Connect to Infura or other provider
    this.provider = new ethers.providers.JsonRpcProvider(process.env.MAINNET_RPC_URL);
    this.signer = new ethers.Wallet(process.env.PRIVATE_KEY, this.provider);
    this.connected = true;
    this.logger.info('Connected to blockchain provider');
    return true;
  } catch (error) {
    // Retry with exponential backoff
    // ...
  }
}
```

### WebSocket Real-time Updates

The system uses WebSockets to provide real-time updates on system health, trade status, and AI insights.

```typescript
// WebSocket connection URL
const wsUrl = 'ws://localhost:3002/ws';

// Client-side connection example
const socket = new WebSocket(wsUrl);
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle different message types
  if (data.type === 'systemHealth') {
    // Update system health UI
  } else if (data.type === 'bot_status') {
    // Update bot status UI
  }
};
```

### AI Integration

The system uses machine learning models to predict profitable arbitrage opportunities and optimize trade execution.

```typescript
// AI prediction example
async predictArbitrageOpportunity(tokenPair, exchangeData) {
  // Process data and make prediction
  const prediction = await this.model.predict(processedData);
  return {
    probability: prediction.probability,
    estimatedProfit: prediction.profit,
    confidence: prediction.confidence,
    recommendedAction: prediction.action
  };
}
```

## Running the System

### Starting the Backend

```bash
# Start all services
./scripts/start_arbitragex.sh

# Stop all services
./scripts/kill_all_arbitragex.sh
```

### Starting the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Start development server
npm run dev
```

### Accessing the UI

- Main Dashboard: http://localhost:3001
- New Dashboard: http://localhost:3001/new-dashboard
- AI Dashboard: http://localhost:3001/ai-dashboard

## System Health Monitoring

The system includes comprehensive health monitoring for all components:

1. **Blockchain Connection**: Checks connectivity to Ethereum via Infura
2. **Database Connection**: Verifies MongoDB connection status
3. **Cache Connection**: Confirms Redis is operational
4. **Web3 Service**: Validates contract interactions are working

Health status is available via:
- REST API: `GET http://localhost:3002/health`
- WebSocket: Messages with type `systemHealth`

## Recent Improvements

### Blockchain Connection Fixes

The blockchain connection was enhanced to ensure reliable connectivity to Ethereum via Infura:

1. **Environment Variable Configuration**: 
   - The system now properly uses the `MAINNET_RPC_URL` from the root `.env` file
   - Example: `MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY`

2. **Connection Reliability**:
   - Implemented exponential backoff for connection retries
   - Added proper error handling to prevent application crashes
   - Improved logging to help diagnose connection issues

3. **Health Monitoring**:
   - Enhanced the health endpoint to accurately report blockchain connection status
   - Added direct checks in the WebSocketService to monitor blockchain connectivity

### WebSocket Service Enhancement

The WebSocketService was updated to directly check system health instead of making HTTP requests:

```typescript
// Direct health checks in WebSocketService
private async broadcastSystemHealth() {
  try {
    const mongoDbConnected = mongoose.connection.readyState === 1;
    
    let redisConnected = false;
    try {
      redisConnected = await RedisService.getInstance().isConnected();
    } catch (error) {
      this.logger.error('Error checking Redis connection');
    }
    
    let web3Connected = false;
    try {
      web3Connected = Web3Service.getInstance().isConnected();
    } catch (error) {
      this.logger.error('Error checking Web3 connection');
    }
    
    const systemHealth = {
      type: 'systemHealth',
      data: {
        blockchain: web3Connected,
        mongodb: mongoDbConnected,
        redis: redisConnected,
        web3: web3Connected
      }
    };
    
    this.broadcast(systemHealth);
  } catch (error) {
    this.logger.error('Error broadcasting system health');
  }
}
```

### Error Handling Improvements

Error handling was enhanced to prevent circular JSON errors when logging:

```typescript
try {
  // Operation that might fail
} catch (error) {
  // Safe error logging
  if (error instanceof Error) {
    logger.error(`Error message: ${error.message}`);
  } else {
    logger.error(`Unknown error: ${String(error)}`);
  }
}
```

## Testing WebSocket Connectivity

Two test tools are provided to verify WebSocket functionality:

### Browser-based Test

Open `websocket-test.html` in a web browser to:
- Visually monitor system health status
- See real-time updates from the WebSocket server
- Test connection and disconnection

### Command-line Test

Run `node websocket-test.js` to:
- Connect to the WebSocket server from the command line
- Monitor system health messages
- View bot status updates

Example output:
```
Connecting to WebSocket server at ws://localhost:3002/ws...
Connected to WebSocket server successfully!
Received message type: systemHealth
SYSTEM HEALTH STATUS:
- Blockchain: Connected ✅
- MongoDB: Connected ✅
- Redis: Connected ✅
- Web3: Connected ✅
-----------------------------------
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failures**
   - Ensure the WebSocket server is running on port 3002
   - Check for WebSocket errors in the browser console
   - Verify the correct WebSocket URL is being used: `ws://localhost:3002/ws`

2. **Blockchain Connection Issues**
   - Verify Infura API key is valid in the `.env` file
   - Check network connectivity to Infura endpoints
   - Review logs for Web3Service connection errors

3. **System Health Reporting Incorrect Status**
   - Check individual service logs in the `logs/` directory
   - Verify all required services are running
   - Restart the backend using `./scripts/kill_all_arbitragex.sh && ./scripts/start_arbitragex.sh`

### Logs

Log files are stored in the `logs/` directory:
- `api.log`: API server logs
- `bot.log`: Trading bot logs
- `error.log`: Consolidated error logs
- `combined.log`: All system logs

## Development Guidelines

### Adding New Features

1. Create new service classes in `backend/api/services/`
2. Add new API routes in `backend/api/routes/`
3. Implement frontend components in `frontend/components/`
4. Add new pages in `frontend/pages/`

### Testing

1. Unit tests are in `__tests__` directories
2. WebSocket testing can be done with `websocket-test.js`
3. API endpoints can be tested with Postman or curl

## Conclusion

ArbitrageX is a complex system with multiple integrated components. The key to understanding the system is to follow the data flow from the blockchain through the Web3Service, to the AI processing, and finally to the frontend display via REST APIs and WebSockets.

For any questions or issues, please refer to the specific component documentation or check the logs for detailed error information. 