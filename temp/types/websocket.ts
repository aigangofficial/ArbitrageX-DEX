import { WebSocket } from 'ws';

export interface CustomWebSocket extends WebSocket {
  isAlive: boolean;
  subscriptions: Set<string>;
}

export type WebSocketMessageType =
  | 'CONNECTED'
  | 'SUBSCRIBED'
  | 'UNSUBSCRIBED'
  | 'ERROR'
  | 'TRADE_UPDATE'
  | 'PRICE_UPDATE'
  | 'ARBITRAGE_OPPORTUNITY';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data?: any;
  message?: string;
  timestamp: string;
}

export interface SubscriptionMessage {
  type: 'SUBSCRIBE' | 'UNSUBSCRIBE';
  channels: string[];
}

export type WebSocketChannel = 'trades' | 'prices' | 'opportunities' | 'system' | 'errors';
