import axios, { AxiosInstance } from 'axios';
import { Trade, BotStatus } from '../websocket';
import { ExecutionMode } from '../../components/NetworkSelector';

export class APIService {
  private api: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:3000/api/v1') {
    console.log(`Initializing API service with base URL: ${baseURL}`);
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

  // Bot control endpoints
  public async startBot(params: {
    runTime?: number;
    tokens?: string;
    dexes?: string;
    gasStrategy?: string;
  }): Promise<{ success: boolean; message: string }> {
    try {
      console.log('Starting bot with params:', params);
      const response = await this.api.post('/bot-control/start', params);
      return response.data;
    } catch (error) {
      console.error('Error starting bot:', error);
      throw this.handleError(error);
    }
  }

  public async stopBot(): Promise<{ success: boolean; message: string }> {
    try {
      console.log('Stopping bot');
      const response = await this.api.post('/bot-control/stop');
      return response.data;
    } catch (error) {
      console.error('Error stopping bot:', error);
      throw this.handleError(error);
    }
  }

  public async getBotRunningStatus(): Promise<{ isRunning: boolean }> {
    try {
      console.log('Checking bot status');
      const response = await this.api.get('/bot-control/status');
      return response.data.data;
    } catch (error) {
      console.error('Error checking bot status:', error);
      throw this.handleError(error);
    }
  }

  // Trade endpoints
  public async getTrades(limit: number = 10): Promise<Trade[]> {
    try {
      const response = await this.api.get(`/trades?limit=${limit}`);
      return response.data.trades;
    } catch (error) {
      console.error('Error fetching trades:', error);
      throw this.handleError(error);
    }
  }

  public async getTrade(txHash: string): Promise<Trade> {
    try {
      const response = await this.api.get(`/trades/${txHash}`);
      return response.data.trade;
    } catch (error) {
      console.error(`Error fetching trade ${txHash}:`, error);
      throw this.handleError(error);
    }
  }

  public async executeArbitrage(params: {
    tokenIn: string;
    tokenOut: string;
    amount: string;
    router: string;
  }): Promise<{ tradeId: string }> {
    try {
      console.log('Executing arbitrage with params:', params);
      const response = await this.api.post('/trades/execute', params);
      return response.data;
    } catch (error) {
      console.error('Error executing arbitrage:', error);
      throw this.handleError(error);
    }
  }

  public async getTradeStats(): Promise<{
    totalTrades: number;
    successfulTrades: number;
    failedTrades: number;
    totalProfit: string;
    avgGasUsed: number;
  }> {
    try {
      const response = await this.api.get('/trades/stats');
      return response.data.stats;
    } catch (error) {
      console.error('Error fetching trade stats:', error);
      throw this.handleError(error);
    }
  }

  // Bot status endpoints
  public async getBotStatus(): Promise<BotStatus> {
    try {
      const response = await this.api.get('/status');
      return response.data.status;
    } catch (error) {
      console.error('Error fetching bot status:', error);
      throw this.handleError(error);
    }
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
    try {
      const response = await this.api.get('/status/health');
      return response.data;
    } catch (error) {
      console.error('Error fetching health metrics:', error);
      throw this.handleError(error);
    }
  }

  // Execution Mode endpoints
  public async getExecutionMode(): Promise<{
    mode: ExecutionMode;
    lastUpdated: string;
    updatedBy: string;
  }> {
    try {
      const response = await this.api.get('/execution-mode');
      return response.data.data;
    } catch (error) {
      console.error('Error fetching execution mode:', error);
      throw this.handleError(error);
    }
  }

  public async setExecutionMode(mode: ExecutionMode, updatedBy: string = 'user'): Promise<{
    mode: ExecutionMode;
    lastUpdated: string;
    updatedBy: string;
  }> {
    try {
      console.log(`Setting execution mode to ${mode}`);
      const response = await this.api.post('/execution-mode', { mode, updatedBy });
      return response.data.data;
    } catch (error) {
      console.error('Error setting execution mode:', error);
      throw this.handleError(error);
    }
  }

  // Admin endpoints
  public async generateBypassToken(params: {
    subject: string;
    scope?: string[];
  }): Promise<{ token: string }> {
    try {
      const response = await this.api.post('/admin/bypass-token', params);
      return response.data;
    } catch (error) {
      console.error('Error generating bypass token:', error);
      throw this.handleError(error);
    }
  }

  public async revokeBypassToken(token: string): Promise<{ success: boolean }> {
    try {
      const response = await this.api.delete('/admin/bypass-token', {
        data: { token }
      });
      return response.data;
    } catch (error) {
      console.error('Error revoking bypass token:', error);
      throw this.handleError(error);
    }
  }

  public async getTokenStats(token: string): Promise<{
    usageCount: number;
    uniqueIPs: number;
    lastUsed: Date;
    isRevoked: boolean;
  }> {
    try {
      const response = await this.api.get('/admin/bypass-token/stats', {
        headers: { 'x-bypass-token': token }
      });
      return response.data.stats;
    } catch (error) {
      console.error('Error fetching token stats:', error);
      throw this.handleError(error);
    }
  }

  // Error handling helper
  private handleError(error: any): Error {
    if (error.response) {
      return new Error(error.response.data.error || `API request failed with status ${error.response.status}`);
    }
    if (error.request) {
      return new Error('No response received from API server. Please check your connection.');
    }
    return error;
  }
} 