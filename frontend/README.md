# ArbitrageX Frontend Dashboard

This is the frontend dashboard for the ArbitrageX project, an AI-driven arbitrage trading bot that leverages flash loans for high-speed, risk-free arbitrage across multiple blockchain networks.

## Features

- **Real-Time Metrics**: Monitor key performance indicators like total trades, success rate, and profit.
- **AI Insights Panel**: View AI-predicted arbitrage opportunities with confidence scores and estimated profits.
- **Trade History**: Track all executed trades with detailed information.
- **Network Selector**: Switch between different blockchain networks (Ethereum, Arbitrum, Polygon, BSC).
- **AI Strategy Insights**: Apply AI-recommended trading strategies based on market conditions.
- **Manual Trade Execution**: Execute trades manually with custom parameters.
- **Bot Status Monitoring**: Monitor the health and status of the trading bot.

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/arbitragex-new.git
   cd arbitragex-new/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Create a `.env.local` file with the following variables:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:3000/api
   NEXT_PUBLIC_WS_URL=ws://localhost:3000/api/ws/arbitrage
   ```

### Running the Development Server

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the dashboard.

### Building for Production

```bash
npm run build
# or
yarn build
```

Then start the production server:

```bash
npm run start
# or
yarn start
```

## Project Structure

- `components/`: UI components used throughout the application
  - `AIInsightsPanel.tsx`: Displays AI-predicted arbitrage opportunities
  - `AIStrategyInsights.tsx`: Shows AI-recommended trading strategies
  - `ArbitrageExecutionForm.tsx`: Form for manual trade execution
  - `BotStatusPanel.tsx`: Displays bot health and status
  - `DashboardLayout.tsx`: Main layout for the dashboard
  - `NetworkSelector.tsx`: Component for switching between networks
  - `RealTimeMetrics.tsx`: Displays key performance metrics
  - `ToastNotification.tsx`: Toast notification component
  - `TradeHistoryTable.tsx`: Table for viewing trade history
- `context/`: React context providers
  - `ToastContext.tsx`: Context for managing toast notifications
- `hooks/`: Custom React hooks
  - `useArbitrageX.ts`: Hook for managing ArbitrageX data
  - `useWebSocket.ts`: Hook for WebSocket connection
- `pages/`: Next.js pages
  - `dashboard.tsx`: Main dashboard page
  - `index.tsx`: Landing page
- `services/`: API and WebSocket services
  - `api/`: API service for REST endpoints
  - `websocket.ts`: WebSocket service for real-time updates

## Technologies Used

- **Next.js**: React framework for server-rendered applications
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **WebSockets**: Real-time communication with the backend
- **Context API**: State management

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
