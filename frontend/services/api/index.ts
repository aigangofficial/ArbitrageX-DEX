import axios, { AxiosInstance } from 'axios';
import { Trade, BotStatus } from '../websocket';

export class APIService {
  private api: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:3000/api/v1') {
    this.api = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      response => response,
      error => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Trade endpoints
  public async getTrades(limit: number = 10): Promise<Trade[]> {
    const response = await this.api.get(`/trades?limit=${limit}`);
    return response.data.trades;
  }

  public async getTrade(txHash: string): Promise<Trade> {
    const response = await this.api.get(`/trades/${txHash}`);
    return response.data.trade;
  }

  public async executeArbitrage(params: {
    tokenIn: string;
    tokenOut: string;
    amount: string;
    router: string;
  }): Promise<{ tradeId: string }> {
    const response = await this.api.post('/trades/execute', params);
    return response.data;
  }

  public async getTradeStats(): Promise<{
    totalTrades: number;
    successfulTrades: number;
    failedTrades: number;
    totalProfit: string;
    avgGasUsed: number;
  }> {
    const response = await this.api.get('/trades/stats');
    return response.data.stats;
  }

  // Bot status endpoints
  public async getBotStatus(): Promise<BotStatus> {
    const response = await this.api.get('/status');
    return response.data.status;
  }

  public async getHealthMetrics(): Promise<{
    status: string;
    checks: {
      uptime: { status: string; value: number };
      memory: { status: string; value: number; threshold: number };
      lastHeartbeat: { status: string; value: Date; threshold: string };
      pendingTransactions: { status: string; value: number };
    };
    timestamp: string;
  }> {
    const response = await this.api.get('/status/health');
    return response.data;
  }

  // Admin endpoints
  public async generateBypassToken(params: {
    subject: string;
    scope?: string[];
  }): Promise<{ token: string }> {
    const response = await this.api.post('/admin/bypass-token', params);
    return response.data;
  }

  public async revokeBypassToken(token: string): Promise<{ success: boolean }> {
    const response = await this.api.delete('/admin/bypass-token', {
      data: { token }
    });
    return response.data;
  }

  public async getTokenStats(token: string): Promise<{
    usageCount: number;
    uniqueIPs: number;
    lastUsed: Date;
    isRevoked: boolean;
  }> {
    const response = await this.api.get('/admin/bypass-token/stats', {
      headers: { 'x-bypass-token': token }
    });
    return response.data.stats;
  }

  // Error handling helper
  private handleError(error: any): never {
    if (error.response) {
      throw new Error(error.response.data.error || 'API request failed');
    }
    throw error;
  }
} 