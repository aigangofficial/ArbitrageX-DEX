import { useState, useEffect, useCallback } from 'react';
import { WebSocketService, Trade, BotStatus } from '../services/websocket';
import { APIService } from '../services/api';
import { useToast } from '../context/ToastContext';

interface UseArbitrageXOptions {
  wsUrl?: string;
  apiUrl?: string;
}

type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

interface UseArbitrageXReturn {
  connectionStatus: ConnectionStatus;
  lastMessage: any;
  sendMessage: (message: any) => void;
export function useArbitrageX(options: UseArbitrageXOptions = {}) {
  const [ws] = useState(() => new WebSocketService(options.wsUrl));
  const [api] = useState(() => new APIService(options.apiUrl));
  
  const [isConnected, setIsConnected] = useState(false);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');

  // Initialize WebSocket connection and event listeners
  useEffect(() => {
    const handleConnect = () => {
      setIsConnected(true);
      setConnectionState('connected');
      setError(null);
    };

    const handleDisconnect = () => {
      setIsConnected(false);
      setConnectionState('disconnected');
    };

    const handleError = (err: Error) => {
      setError(err);
      setConnectionState('error');
    };

    const handleReconnecting = (data: { attempt: number; maxAttempts: number }) => {
      setConnectionState('connecting');
      setReconnectAttempts(data.attempt);
    };

    const handleTrade = (trade: Trade) => {
      setTrades(current => [trade, ...current]);
    };
    
    const handleStatus = (status: BotStatus) => {
      setBotStatus(status);
    };

    // Subscribe to WebSocket events
    ws.on('connected', handleConnect);
    ws.on('disconnected', handleDisconnect);
    ws.on('error', handleError);
    ws.on('reconnecting', handleReconnecting);
    ws.on('trade', handleTrade);
    ws.on('status', handleStatus);

    // Subscribe to channels
    ws.subscribe('trade_update');
    ws.subscribe('bot_status');

    // Load initial data
    loadInitialData();

    return () => {
      ws.removeListener('connected', handleConnect);
      ws.removeListener('disconnected', handleDisconnect);
      ws.removeListener('error', handleError);
      ws.removeListener('reconnecting', handleReconnecting);
      ws.removeListener('trade', handleTrade);
      ws.removeListener('status', handleStatus);
      ws.disconnect();
    };
  }, [ws]);

  // Load initial data from API
  const loadInitialData = useCallback(async () => {
    try {
      const [tradesData, statusData] = await Promise.all([
        api.getTrades(100),
        api.getBotStatus()
      ]);
      setTrades(tradesData);
      setBotStatus(statusData);
    } catch (err) {
      setError(err as Error);
    }
  }, [api]);

  // Execute arbitrage trade
  const executeArbitrage = useCallback(async (params: {
    tokenIn: string;
    tokenOut: string;
    amount: string;
    router: string;
  }) => {
    try {
      const result = await api.executeArbitrage(params);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to execute trade'));
      throw err;
    }
  }, [api]);

  // Get trade statistics
  const getTradeStats = useCallback(async () => {
    try {
      return await api.getTradeStats();
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch trade stats'));
      throw err;
    }
  }, [api]);

  // Get health metrics
  const getHealthMetrics = useCallback(async () => {
    try {
      return await api.getHealthMetrics();
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch health metrics'));
      throw err;
    }
  }, [api]);

  // Admin functions
  const generateBypassToken = useCallback(async (params: {
    subject: string;
    scope?: string[];
  }) => {
    try {
      return await api.generateBypassToken(params);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to generate bypass token'));
      throw err;
    }
  }, [api]);

  const revokeBypassToken = useCallback(async (token: string) => {
    try {
      return await api.revokeBypassToken(token);
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, [api]);

  return {
    isConnected,
    trades,
    botStatus,
    error,
    executeArbitrage,
    getTradeStats,
    getHealthMetrics,
    generateBypassToken,
    revokeBypassToken,
    reconnectAttempts,
    connectionState
  };
} 