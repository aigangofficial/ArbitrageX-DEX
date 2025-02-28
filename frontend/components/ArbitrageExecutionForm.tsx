import React, { useState } from 'react';
import { parseEther } from 'ethers';

interface ArbitrageExecutionFormProps {
  onExecute: (params: {
    tokenIn: string;
    tokenOut: string;
    amount: string;
    router: string;
  }) => Promise<void>;
  isLoading: boolean;
}

const SUPPORTED_TOKENS = [
  { symbol: 'WETH', address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2' },
  { symbol: 'USDC', address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48' },
  { symbol: 'DAI', address: '0x6B175474E89094C44Da98b954EedeAC495271d0F' },
  { symbol: 'USDT', address: '0xdAC17F958D2ee523a2206206994597C13D831ec7' }
];

const SUPPORTED_ROUTERS = [
  { name: 'Uniswap V2', address: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D' },
  { name: 'SushiSwap', address: '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F' }
];

export const ArbitrageExecutionForm: React.FC<ArbitrageExecutionFormProps> = ({
  onExecute,
  isLoading
}) => {
  const [tokenIn, setTokenIn] = useState(SUPPORTED_TOKENS[0].address);
  const [tokenOut, setTokenOut] = useState(SUPPORTED_TOKENS[1].address);
  const [amount, setAmount] = useState('');
  const [router, setRouter] = useState(SUPPORTED_ROUTERS[0].address);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      // Validate inputs
      if (!amount || parseFloat(amount) <= 0) {
        throw new Error('Please enter a valid amount');
      }

      if (tokenIn === tokenOut) {
        throw new Error('Input and output tokens must be different');
      }

      // Convert amount to Wei
      const amountInWei = parseEther(amount).toString();

      await onExecute({
        tokenIn,
        tokenOut,
        amount: amountInWei,
        router
      });

      // Reset form
      setAmount('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Execute Arbitrage Trade</h3>
        <p className="mt-1 text-sm text-gray-500">
          Manually trigger an arbitrage trade between supported tokens.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <label htmlFor="tokenIn" className="block text-sm font-medium text-gray-700">
            Input Token
          </label>
          <select
            id="tokenIn"
            value={tokenIn}
            onChange={(e) => setTokenIn(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            disabled={isLoading}
          >
            {SUPPORTED_TOKENS.map((token) => (
              <option key={token.address} value={token.address}>
                {token.symbol}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="tokenOut" className="block text-sm font-medium text-gray-700">
            Output Token
          </label>
          <select
            id="tokenOut"
            value={tokenOut}
            onChange={(e) => setTokenOut(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            disabled={isLoading}
          >
            {SUPPORTED_TOKENS.map((token) => (
              <option key={token.address} value={token.address}>
                {token.symbol}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
            Amount
          </label>
          <div className="mt-1">
            <input
              type="number"
              id="amount"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.0"
              step="0.000001"
              min="0"
              className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
              disabled={isLoading}
            />
          </div>
        </div>

        <div>
          <label htmlFor="router" className="block text-sm font-medium text-gray-700">
            DEX Router
          </label>
          <select
            id="router"
            value={router}
            onChange={(e) => setRouter(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            disabled={isLoading}
          >
            {SUPPORTED_ROUTERS.map((r) => (
              <option key={r.address} value={r.address}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isLoading}
          className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
            isLoading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Executing...
            </>
          ) : (
            'Execute Trade'
          )}
        </button>
      </div>
    </form>
  );
}; 