import { useState, useEffect, useCallback } from 'react';
import { useToast } from '../context/ToastContext';

type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'error';

interface UseWebSocketReturn {
  connectionStatus: ConnectionStatus;
  lastMessage: any;
  sendMessage: (message: any) => void;
  reconnect: () => void;
}

export const useWebSocket = (url: string = 'ws://localhost:3000/api/ws/arbitrage'): UseWebSocketReturn => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<any>(null);
  const { showToast } = useToast();

  const connect = useCallback(() => {
    try {
      setConnectionStatus('connecting');
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setConnectionStatus('connected');
        showToast({
          type: 'success',
          title: 'Connection Established',
          message: 'Successfully connected to ArbitrageX service'
        });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          
          // Handle different message types
          if (data.type === 'opportunity') {
            showToast({
              type: 'info',
              title: 'New Opportunity',
              message: `${data.tokenPair} arbitrage opportunity detected`
            });
          } else if (data.type === 'execution') {
            showToast({
              type: data.success ? 'success' : 'error',
              title: data.success ? 'Trade Executed' : 'Execution Failed',
              message: data.message
            });
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        showToast({
          type: 'error',
          title: 'Connection Error',
          message: 'Failed to connect to ArbitrageX service'
        });
      };

      ws.onclose = () => {
        setConnectionStatus('disconnected');
        showToast({
          type: 'warning',
          title: 'Connection Closed',
          message: 'Connection to ArbitrageX service was closed'
        });
        
        // Attempt to reconnect after a delay
        setTimeout(() => {
          if (connectionStatus !== 'connected') {
            connect();
          }
        }, 5000);
      };

      setSocket(ws);

      return () => {
        ws.close();
      };
    } catch (error) {
      console.error('Failed to establish WebSocket connection:', error);
      setConnectionStatus('error');
      showToast({
        type: 'error',
        title: 'Connection Error',
        message: 'Failed to connect to ArbitrageX service'
      });
    }
  }, [url, connectionStatus, showToast]);

  const reconnect = useCallback(() => {
    if (socket) {
      socket.close();
    }
    connect();
  }, [socket, connect]);

  const sendMessage = useCallback(
    (message: any) => {
      if (socket && connectionStatus === 'connected') {
        socket.send(JSON.stringify(message));
      } else {
        showToast({
          type: 'error',
          title: 'Connection Error',
          message: 'Cannot send message: not connected to ArbitrageX service'
        });
      }
    },
    [socket, connectionStatus, showToast]
  );

  useEffect(() => {
    connect();
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [connect, socket]);

  return {
    connectionStatus,
    lastMessage,
    sendMessage,
    reconnect
  };
}; 