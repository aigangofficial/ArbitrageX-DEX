import React, { useState, useCallback, useEffect } from 'react';
import { DashboardLayout } from '../components/DashboardLayout';
import { BotStatusPanel } from '../components/BotStatusPanel';
import { TradeHistoryTable } from '../components/TradeHistoryTable';
import { ArbitrageExecutionForm } from '../components/ArbitrageExecutionForm';
import { AIInsightsPanel, AIOpportunity } from '../components/AIInsightsPanel';
import { RealTimeMetrics } from '../components/RealTimeMetrics';
import { NetworkSelector, Network } from '../components/NetworkSelector';
import { AIStrategyInsights, AIStrategy } from '../components/AIStrategyInsights';
import { useToast } from '../context/ToastContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { Trade, BotStatus } from '../services/websocket';

// Define interface for metrics
interface Metrics {
  totalTrades: number;
  successRate: number;
  totalProfit: string;
  avgExecutionTime: number;
  activeOpportunities: number;
  gasUsed: string;
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
    gasCost: '$9.00',
    netProfit: '$29.02',
    timestamp: new Date(),
    network: 'Ethereum',
    isRecommended: true
  },
  {
    id: 'opp-2',
    tokenPair: 'WETH-DAI',
    confidence: 0.42,
    estimatedProfit: '$5.18',
    executionTime: 128,
    gasCost: '$8.28',
    netProfit: '-$3.10',
    timestamp: new Date(Date.now() - 120000),
    network: 'Arbitrum',
    isRecommended: false
  }
];

// Mock metrics data
const MOCK_METRICS: Metrics = {
  totalTrades: 128,
  successRate: 86,
  totalProfit: '$2,841.75',
  avgExecutionTime: 118,
  activeOpportunities: 3,
  gasUsed: '0.58 ETH'
};

// Mock trades data
const MOCK_TRADES: Trade[] = Array.from({ length: 20 }).map((_, i) => ({
  tokenIn: i % 2 === 0 ? '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2' : '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
  tokenOut: i % 2 === 0 ? '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48' : '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
  amountIn: (Math.random() * 10 + 1).toString(),
  amountOut: (Math.random() * 20000 + 1000).toString(),
  profit: i % 3 === 0 ? `-${(Math.random() * 10).toFixed(2)}` : (Math.random() * 100).toFixed(2),
  gasUsed: Math.floor(Math.random() * 200000 + 50000),
  gasPrice: (Math.random() * 100 + 20).toString(),
  txHash: `0x${Math.random().toString(16).substring(2, 42)}`,
  blockNumber: 17000000 + i,
  timestamp: new Date(Date.now() - i * 1000 * 60 * 10),
  router: i % 2 === 0 ? '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D' : '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
  status: i % 5 === 0 ? 'failed' : 'completed'
}));

// Mock bot status data
const MOCK_BOT_STATUS: BotStatus = {
  isActive: true,
  lastHeartbeat: new Date(),
  totalTrades: 128,
  successfulTrades: 110,
  failedTrades: 18,
  totalProfit: '$2,841.75',
  averageGasUsed: 150000,
  memoryUsage: {
    heapUsed: 512 * 1024 * 1024,
    heapTotal: 1024 * 1024 * 1024,
    external: 50 * 1024 * 1024
  },
  cpuUsage: 23,
  pendingTransactions: 2,
  network: 'ethereum',
  version: '1.2.3',
  uptime: 302400, // 3.5 days in seconds
  isHealthy: true
};

const Dashboard: React.FC = () => {
  const { showToast } = useToast();
  const { connectionStatus, sendMessage } = useWebSocket();
  const [selectedNetwork, setSelectedNetwork] = useState('ethereum');
  const [strategies, setStrategies] = useState<AIStrategy[]>(MOCK_STRATEGIES);
  const [opportunities, setOpportunities] = useState<AIOpportunity[]>(MOCK_OPPORTUNITIES);
  const [trades, setTrades] = useState<Trade[]>(MOCK_TRADES);
  const [metrics, setMetrics] = useState<Metrics>(MOCK_METRICS);
  const [botStatus, setBotStatus] = useState<BotStatus>(MOCK_BOT_STATUS);
  const [isLoading, setIsLoading] = useState(false);

  const handleNetworkChange = useCallback((networkId: string) => {
    setSelectedNetwork(networkId);
    showToast({
      type: 'info',
      title: 'Network Changed',
      message: `Switched to ${NETWORKS.find(n => n.id === networkId)?.name || networkId} network`
    });
    
    // Simulate loading new data for the selected network
    setIsLoading(true);
    setTimeout(() => {
      // Update data based on selected network
      setIsLoading(false);
    }, 1000);
  }, [showToast]);

  const handleExecuteTrade = useCallback(async (params: any) => {
    try {
      setIsLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      showToast({
        type: 'success',
        title: 'Trade Executed',
        message: `Successfully executed trade for ${params.amount} on ${selectedNetwork}`
      });
      
      // Update trades with new trade
      const newTrade: Trade = {
        tokenIn: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', // WETH
        tokenOut: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', // USDC
        amountIn: params.amount,
        amountOut: (parseFloat(params.amount) * 1800).toString(), // Mock conversion
        profit: '42.18',
        gasUsed: 150000,
        gasPrice: '50',
        txHash: `0x${Math.random().toString(16).substring(2, 42)}`,
        blockNumber: 17000000,
        timestamp: new Date(),
        router: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', // Uniswap V2
        status: 'completed'
      };
      
      setTrades(prev => [newTrade, ...prev]);
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Execution Failed',
        message: error instanceof Error ? error.message : 'Failed to execute trade'
      });
    } finally {
      setIsLoading(false);
    }
  }, [selectedNetwork, showToast]);

  const handleExecuteOpportunity = useCallback((opportunity: AIOpportunity) => {
    showToast({
      type: 'info',
      title: 'Executing Opportunity',
      message: `Executing ${opportunity.tokenPair} arbitrage on ${opportunity.network}`
    });
    
    // Simulate execution
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      
      // Add to trade history
      const [tokenIn, tokenOut] = opportunity.tokenPair.split('-');
      const newTrade: Trade = {
        tokenIn: tokenIn === 'WETH' ? '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2' : '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        tokenOut: tokenOut === 'USDC' ? '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48' : '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        amountIn: '2.5',
        amountOut: '4500',
        profit: opportunity.netProfit.replace('$', ''),
        gasUsed: 150000,
        gasPrice: '50',
        txHash: `0x${Math.random().toString(16).substring(2, 42)}`,
        blockNumber: 17000000,
        timestamp: new Date(),
        router: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        status: 'completed'
      };
      
      setTrades(prev => [newTrade, ...prev]);
      
      showToast({
        type: 'success',
        title: 'Opportunity Executed',
        message: `Successfully executed ${opportunity.tokenPair} arbitrage`
      });
    }, 3000);
  }, [showToast]);

  const handleSimulateOpportunity = useCallback((opportunity: AIOpportunity) => {
    showToast({
      type: 'info',
      title: 'Simulating Opportunity',
      message: `Simulating ${opportunity.tokenPair} arbitrage on ${opportunity.network}`
    });
    
    // Simulate execution
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      showToast({
        type: 'success',
        title: 'Simulation Complete',
        message: `Expected profit: ${opportunity.netProfit} (${opportunity.confidence * 100}% confidence)`
      });
    }, 2000);
  }, [showToast]);

  const handleApplyStrategy = useCallback((strategy: AIStrategy) => {
    showToast({
      type: 'info',
      title: 'Applying Strategy',
      message: `Applying "${strategy.name}" strategy`
    });
    
    // Simulate applying strategy
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      showToast({
        type: 'success',
        title: 'Strategy Applied',
        message: `Successfully applied "${strategy.name}" strategy`
      });
    }, 2000);
  }, [showToast]);

  // Simulate receiving new opportunities periodically
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        const newOpportunity: AIOpportunity = {
          id: `opp-${Date.now()}`,
          tokenPair: Math.random() > 0.5 ? 'WBTC-WETH' : 'WETH-USDC',
          confidence: 0.5 + Math.random() * 0.5,
          estimatedProfit: `$${(Math.random() * 50 + 5).toFixed(2)}`,
          executionTime: Math.floor(Math.random() * 50 + 100),
          gasCost: `$${(Math.random() * 5 + 5).toFixed(2)}`,
          netProfit: `$${(Math.random() * 40).toFixed(2)}`,
          timestamp: new Date(),
          network: NETWORKS[Math.floor(Math.random() * NETWORKS.length)].name,
          isRecommended: Math.random() > 0.3
        };
        
        setOpportunities(prev => [newOpportunity, ...prev].slice(0, 5));
        
        if (newOpportunity.isRecommended) {
          showToast({
            type: 'info',
            title: 'New Opportunity',
            message: `AI detected a profitable ${newOpportunity.tokenPair} arbitrage opportunity`
          });
        }
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [showToast]);

  return (
    <DashboardLayout title="ArbitrageX Dashboard">
      <div className="mb-6 flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-800">Real-Time Arbitrage Dashboard</h2>
        <NetworkSelector 
          networks={NETWORKS} 
          selectedNetwork={selectedNetwork} 
          onNetworkChange={handleNetworkChange} 
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <RealTimeMetrics metrics={metrics} isLoading={isLoading} />
        </div>
        <div>
          <BotStatusPanel status={botStatus} isLoading={isLoading} />
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <AIInsightsPanel 
            opportunities={opportunities} 
            isLoading={isLoading} 
            onSimulateTrade={handleSimulateOpportunity}
            onExecuteTrade={handleExecuteOpportunity}
          />
        </div>
        <div>
          <ArbitrageExecutionForm onExecute={handleExecuteTrade} isLoading={isLoading} />
        </div>
      </div>
      
      <div className="grid grid-cols-1 gap-6 mb-6">
        <AIStrategyInsights 
          strategies={strategies} 
          isLoading={isLoading} 
          onApplyStrategy={handleApplyStrategy} 
        />
      </div>
      
      <div className="grid grid-cols-1 gap-6">
        <TradeHistoryTable trades={trades} isLoading={isLoading} />
      </div>
    </DashboardLayout>
  );
};

export default Dashboard; 