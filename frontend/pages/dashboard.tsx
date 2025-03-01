import React, { useState, useCallback, useEffect } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { BotStatusPanel } from '../components/BotStatusPanel';
import { TradeHistoryTable } from '../components/TradeHistoryTable';
import { ArbitrageExecutionForm } from '../components/ArbitrageExecutionForm';
import { AIInsightsPanel, AIOpportunity } from '../components/AIInsightsPanel';
import { RealTimeMetrics } from '../components/RealTimeMetrics';
import { NetworkSelector, Network, ExecutionMode } from '../components/NetworkSelector';
import { AIStrategyInsights, AIStrategy } from '../components/AIStrategyInsights';
import ExecutionModeSelector from '../components/ExecutionModeSelector';
import { useToast } from '../context/ToastContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { Trade, BotStatus } from '../services/websocket';
import { APIService } from '../services/api';

// Define interface for metrics
interface Metrics {
  totalTrades: number;
  successRate: number;
  totalProfit: string;
  avgExecutionTime: number;
  activeOpportunities: number;
  gasUsed: string;
}

// Extended Trade interface to include network
interface ExtendedTrade extends Trade {
  network?: string;
}

// Mock networks data
const NETWORKS: Network[] = [
  {
    id: 'ethereum',
    name: 'Ethereum',
    icon: '/images/ethereum.svg',
    color: '#627EEA',
    isActive: true
  },
  {
    id: 'arbitrum',
    name: 'Arbitrum',
    icon: '/images/arbitrum.svg',
    color: '#28A0F0',
    isActive: true
  },
  {
    id: 'polygon',
    name: 'Polygon',
    icon: '/images/polygon.svg',
    color: '#8247E5',
    isActive: true
  },
  {
    id: 'bsc',
    name: 'BSC',
    icon: '/images/bsc.svg',
    color: '#F3BA2F',
    isActive: false
  }
];

// Mock AI strategies data
const MOCK_STRATEGIES: AIStrategy[] = [
  {
    id: 'strategy-1',
    name: 'Flash Loan Arbitrage: ETH-USDC',
    description: 'Leverages flash loans to execute high-volume arbitrage between Uniswap V3 and SushiSwap for ETH-USDC pair during high volatility periods.',
    confidence: 0.87,
    expectedReturn: '+0.5-2% per trade',
    timeFrame: '1-5 minutes',
    tokenPairs: ['ETH-USDC', 'WETH-USDC'],
    networks: ['Ethereum', 'Arbitrum'],
    riskLevel: 'Medium'
  },
  {
    id: 'strategy-2',
    name: 'Multi-Hop Optimization',
    description: 'Uses AI-optimized routing through multiple DEXes to capture price inefficiencies across 3+ trading pairs, focusing on stablecoin triangular arbitrage.',
    confidence: 0.72,
    expectedReturn: '+0.3-1.2% per trade',
    timeFrame: '2-10 minutes',
    tokenPairs: ['USDC-USDT', 'USDT-DAI', 'DAI-USDC'],
    networks: ['Ethereum', 'Polygon'],
    riskLevel: 'Low'
  },
  {
    id: 'strategy-3',
    name: 'Cross-Chain Opportunity Hunter',
    description: 'Identifies and exploits price differences for the same assets across different blockchain networks, accounting for bridge fees and execution times.',
    confidence: 0.65,
    expectedReturn: '+1.5-4% per trade',
    timeFrame: '5-15 minutes',
    tokenPairs: ['ETH-USDC', 'WBTC-ETH', 'MATIC-USDC'],
    networks: ['Ethereum', 'Arbitrum', 'Polygon', 'BSC'],
    riskLevel: 'High'
  }
];

// Mock opportunities data
const MOCK_OPPORTUNITIES: AIOpportunity[] = [
  {
    id: 'opp-1',
    tokenPair: 'WETH-USDC',
    confidence: 0.86,
    estimatedProfit: '$38.02',
    executionTime: 122,
    gasCost: '$5.23',
    netProfit: '$32.79',
    timestamp: new Date(),
    network: 'Ethereum',
    isRecommended: true
  },
  {
    id: 'opp-2',
    tokenPair: 'WBTC-USDT',
    confidence: 0.79,
    estimatedProfit: '$42.15',
    executionTime: 145,
    gasCost: '$3.15',
    netProfit: '$39.00',
    timestamp: new Date(),
    network: 'Arbitrum',
    isRecommended: true
  },
  {
    id: 'opp-3',
    tokenPair: 'MATIC-USDC',
    confidence: 0.92,
    estimatedProfit: '$21.87',
    executionTime: 98,
    gasCost: '$1.25',
    netProfit: '$20.62',
    timestamp: new Date(),
    network: 'Polygon',
    isRecommended: true
  }
];

const Dashboard: React.FC = () => {
  const { showToast } = useToast();
  const apiService = new APIService();
  
  // State for network selection
  const [selectedNetwork, setSelectedNetwork] = useState('ethereum');
  
  // State for execution mode
  const [executionMode, setExecutionMode] = useState<ExecutionMode>(ExecutionMode.FORK);
  const [isLoadingMode, setIsLoadingMode] = useState(false);
  
  // State for trades and metrics
  const [trades, setTrades] = useState<ExtendedTrade[]>([]);
  const [isLoadingTrades, setIsLoadingTrades] = useState(false);
  const [metrics, setMetrics] = useState<Metrics>({
    totalTrades: 0,
    successRate: 0,
    totalProfit: '$0.00',
    avgExecutionTime: 0,
    activeOpportunities: 0,
    gasUsed: '0 ETH'
  });
  
  // State for bot status
  const [botStatus, setBotStatus] = useState({
    isActive: true,
    status: 'idle',
    lastUpdated: new Date().toISOString(),
    activeStrategies: 0,
    pendingTransactions: 0,
    connectedNodes: 0,
    cpuUsage: 0,
    memoryUsage: { heapUsed: 0, heapTotal: 0, external: 0 },
    uptime: 0,
    network: 'Ethereum',
    successfulTrades: 0,
    totalTrades: 0,
    totalProfit: '0'
  });
  
  // State for AI opportunities and strategies
  const [opportunities, setOpportunities] = useState<AIOpportunity[]>(MOCK_OPPORTUNITIES);
  const [strategies, setStrategies] = useState<AIStrategy[]>(MOCK_STRATEGIES);
  const [isLoadingStrategies, setIsLoadingStrategies] = useState(false);
  const [isLoadingOpportunities, setIsLoadingOpportunities] = useState(false);
  const [isLoadingMetrics, setIsLoadingMetrics] = useState(false);
  const [isLoadingBotStatus, setIsLoadingBotStatus] = useState(false);
  
  // State for arbitrage execution
  const [isExecutingTrade, setIsExecutingTrade] = useState(false);

  // WebSocket connection for real-time updates
  const { lastMessage, connectionStatus } = useWebSocket('ws://localhost:3001');

  // Load execution mode on component mount
  useEffect(() => {
    const fetchExecutionMode = async () => {
      try {
        const modeData = await apiService.getExecutionMode();
        setExecutionMode(modeData.mode as ExecutionMode);
      } catch (error) {
        console.error('Failed to fetch execution mode:', error);
        showToast({
          type: 'error',
          title: 'Error',
          message: 'Failed to fetch execution mode'
        });
      }
    };
    
    fetchExecutionMode();
  }, []);

  // Handle network change
  const handleNetworkChange = useCallback((networkId: string) => {
    setSelectedNetwork(networkId);
    
    // Refresh data for the new network
    fetchTradesForNetwork(networkId);
    
    showToast({
      type: 'info',
      title: 'Network Changed',
      message: `Switched to ${NETWORKS.find(n => n.id === networkId)?.name || networkId} network`
    });
  }, []);

  // Handle execution mode change
  const handleExecutionModeChange = useCallback(async (mode: ExecutionMode) => {
    try {
      setIsLoadingMode(true);
      
      // Call API to update execution mode
      await apiService.setExecutionMode(mode);
      
      setExecutionMode(mode);
      
      showToast({
        type: mode === ExecutionMode.MAINNET ? 'warning' : 'success',
        title: 'Execution Mode Changed',
        message: `Switched to ${mode === ExecutionMode.MAINNET ? 'Mainnet' : 'Fork'} execution mode`
      });
    } catch (error) {
      console.error('Failed to change execution mode:', error);
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to change execution mode'
      });
    } finally {
      setIsLoadingMode(false);
    }
  }, []);

  // Fetch trades for the selected network
  const fetchTradesForNetwork = useCallback(async (networkId: string) => {
    try {
      setIsLoadingTrades(true);
      const tradesData = await apiService.getTrades(10) as ExtendedTrade[];
      
      // Filter trades by network if needed
      const filteredTrades = tradesData.filter(trade => 
        trade.network?.toLowerCase() === networkId.toLowerCase()
      );
      
      setTrades(filteredTrades);
    } catch (error) {
      console.error('Failed to fetch trades:', error);
    } finally {
      setIsLoadingTrades(false);
    }
  }, []);

  // Handle trade execution
  const handleExecuteTrade = useCallback(async (params: {
    tokenIn: string;
    tokenOut: string;
    amount: string;
    router: string;
  }) => {
    try {
      setIsExecutingTrade(true);
      
      // Show warning if in mainnet mode
      if (executionMode === ExecutionMode.MAINNET) {
        showToast({
          type: 'warning',
          title: 'Live Execution',
          message: 'Executing trade on MAINNET with real assets'
        });
      }
      
      const result = await apiService.executeArbitrage(params);
      
      showToast({
        type: 'success',
        title: 'Trade Executed',
        message: `Trade executed successfully with ID: ${result.tradeId}`
      });
      
      // Refresh trades after execution
      fetchTradesForNetwork(selectedNetwork);
    } catch (error) {
      console.error('Trade execution failed:', error);
      showToast({
        type: 'error',
        title: 'Execution Failed',
        message: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      setIsExecutingTrade(false);
    }
  }, [selectedNetwork, executionMode]);

  // Handle strategy application
  const handleApplyStrategy = useCallback((strategy: AIStrategy) => {
    showToast({
      type: 'info',
      title: 'Strategy Applied',
      message: `Applied strategy: ${strategy.name}`
    });
  }, []);

  // Handle opportunity simulation
  const handleSimulateOpportunity = useCallback((opportunity: AIOpportunity) => {
    showToast({
      type: 'info',
      title: 'Simulating Opportunity',
      message: `Simulating ${opportunity.tokenPair} opportunity`
    });
  }, []);

  // Handle opportunity execution
  const handleExecuteOpportunity = useCallback((opportunity: AIOpportunity) => {
    showToast({
      type: 'info',
      title: 'Executing Opportunity',
      message: `Executing ${opportunity.tokenPair} opportunity`
    });
  }, []);

  // Process WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data);
        
        if (data.type === 'trade') {
          // Update trades if a new trade is received
          setTrades(prevTrades => [data.trade, ...prevTrades.slice(0, 9)]);
        } else if (data.type === 'botStatus') {
          // Update bot status
          setBotStatus(data.status);
        } else if (data.type === 'metrics') {
          // Update metrics
          setMetrics(data.metrics);
        } else if (data.type === 'opportunity') {
          // Update opportunities
          setOpportunities(prevOpps => [data.opportunity, ...prevOpps.slice(0, 2)]);
        } else if (data.type === 'executionModeChanged') {
          // Update execution mode if changed from another client
          setExecutionMode(data.mode);
          
          showToast({
            type: data.mode === ExecutionMode.MAINNET ? 'warning' : 'success',
            title: 'Execution Mode Changed',
            message: `Execution mode changed to ${data.mode === ExecutionMode.MAINNET ? 'Mainnet' : 'Fork'}`
          });
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
      }
    }
  }, [lastMessage]);

  return (
    <DashboardLayout title="ArbitrageX Dashboard">
      <div className="dashboard-grid">
        {/* Top row */}
        <div className="top-row">
          <BotStatusPanel status={botStatus} isLoading={isLoadingBotStatus} />
          <RealTimeMetrics metrics={metrics} isLoading={isLoadingMetrics} />
          <NetworkSelector
            networks={NETWORKS}
            selectedNetwork={selectedNetwork}
            onNetworkChange={handleNetworkChange}
            executionMode={executionMode}
            onExecutionModeChange={handleExecutionModeChange}
          />
          <ExecutionModeSelector />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Execute Arbitrage Trade</h2>
            <ArbitrageExecutionForm
              onExecute={handleExecuteTrade}
              isLoading={isExecutingTrade}
            />
            {executionMode === ExecutionMode.MAINNET && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600 flex items-center">
                  <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9z" clipRule="evenodd" />
                  </svg>
                  Warning: You are in MAINNET execution mode. Trades will use real assets.
                </p>
              </div>
            )}
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">AI-Detected Opportunities</h2>
            <AIInsightsPanel 
              opportunities={opportunities} 
              isLoading={isLoadingOpportunities}
              onSimulateTrade={handleSimulateOpportunity}
              onExecuteTrade={handleExecuteOpportunity}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">AI Strategy Insights</h2>
            <AIStrategyInsights
              strategies={strategies}
              isLoading={isLoadingStrategies}
              onApplyStrategy={handleApplyStrategy}
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Trade History</h2>
          <TradeHistoryTable trades={trades} isLoading={isLoadingTrades} />
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard; 