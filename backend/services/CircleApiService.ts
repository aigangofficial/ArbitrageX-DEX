import axios, { AxiosInstance } from 'axios';
import { createHash } from 'crypto';
import dotenv from 'dotenv';

dotenv.config();

interface CircleWallet {
  walletId: string;
  address: string;
  description?: string;
  balances?: Array<{
    amount: string;
    currency: string;
  }>;
}

interface CircleApiResponse<T> {
  data: T;
}

export class CircleApiService {
  private readonly apiClient: AxiosInstance;
  private readonly circleUuid: string = '1da3ea8d-1b7b-49a2-9915-2f861b2feef2';

  constructor() {
    const apiKey = process.env.CIRCLE_API_KEY;

    if (!apiKey) {
      throw new Error('Missing CIRCLE_API_KEY environment variable');
    }

    this.apiClient = axios.create({
      baseURL: 'https://api.circle.com/v1/w3s/',
      headers: {
        'accept': 'application/json',
        'authorization': `Bearer ${apiKey}`,
        'content-type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.apiClient.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('Circle API Error:', {
          status: error.response?.status,
          data: error.response?.data,
          endpoint: error.config?.url,
        });
        throw error;
      }
    );
  }

  private generateIdempotencyKey(operation: string): string {
    const data = `${this.circleUuid}-${operation}-${Date.now()}`;
    return createHash('sha256').update(data).digest('hex');
  }

  async getWallets(): Promise<CircleWallet[]> {
    try {
      const response = await this.apiClient.get<CircleApiResponse<{ wallets: CircleWallet[] }>>('wallets');
      return response.data.data.wallets;
    } catch (error) {
      console.error('Failed to fetch wallets:', error);
      throw error;
    }
  }

  async createWallet(description: string): Promise<CircleWallet> {
    try {
      const response = await this.apiClient.post<CircleApiResponse<CircleWallet>>('wallets', {
        idempotencyKey: this.circleUuid,
        description,
        accountType: 'BlockchainWallet',
        blockchain: 'MATIC'
      });
      return response.data.data;
    } catch (error) {
      console.error('Failed to create wallet:', error);
      throw error;
    }
  }

  async getWalletBalance(walletId: string): Promise<Array<{ amount: string; currency: string }>> {
    try {
      const response = await this.apiClient.get<CircleApiResponse<{ balances: Array<{ amount: string; currency: string }> }>>(
        `wallets/${walletId}/balances`
      );
      return response.data.data.balances;
    } catch (error) {
      console.error(`Failed to fetch balance for wallet ${walletId}:`, error);
      throw error;
    }
  }

  async setupWebhook(url: string): Promise<void> {
    try {
      await this.apiClient.post('notifications/subscriptions', {
        endpoint: url,
        subscriptionDetails: {
          walletEvents: true,
        },
      });
    } catch (error) {
      console.error('Failed to setup webhook:', error);
      throw error;
    }
  }
}

// Example usage:
async function testCircleApiConnection() {
  try {
    const circleApi = new CircleApiService();

    // Test getting wallets
    console.log('Fetching wallets...');
    const wallets = await circleApi.getWallets();
    console.log('Existing wallets:', wallets);

    if (wallets.length === 0) {
      // Create a new wallet if none exist
      console.log('Creating new wallet...');
      const newWallet = await circleApi.createWallet('ArbitrageX Trading Wallet');
      console.log('New wallet created:', newWallet);

      // Get balance of new wallet
      console.log('Fetching wallet balance...');
      const balance = await circleApi.getWalletBalance(newWallet.walletId);
      console.log('Wallet balance:', balance);
    }
  } catch (error) {
    console.error('Circle API test failed:', error);
    process.exit(1);
  }
}

// Only run the test if this file is being executed directly
if (require.main === module) {
  testCircleApiConnection();
}
