import React, { useMemo, useState } from 'react';
import { Trade } from '../services/websocket';
import { formatEther, formatUnits } from 'ethers';

interface TradeHistoryTableProps {
  trades: Trade[];
  isLoading: boolean;
}

interface FilterState {
  status: string;
  tokenPair: string;
  minProfit: string;
  dateRange: {
    start: string;
    end: string;
  };
}

export const TradeHistoryTable: React.FC<TradeHistoryTableProps> = ({
  trades,
  isLoading
}) => {
  const [sortField, setSortField] = useState<keyof Trade>('timestamp');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filters, setFilters] = useState<FilterState>({
    status: 'all',
    tokenPair: 'all',
    minProfit: '',
    dateRange: {
      start: '',
      end: ''
    }
  });
  const [isFilterVisible, setIsFilterVisible] = useState(false);

  // Get unique token pairs from trades
  const uniqueTokenPairs = useMemo(() => {
    const pairs = new Set(trades.map(trade => `${trade.tokenIn}/${trade.tokenOut}`));
    return ['all', ...Array.from(pairs)];
  }, [trades]);

  const filteredTrades = useMemo(() => {
    return trades.filter(trade => {
      // Status filter
      if (filters.status !== 'all' && trade.status !== filters.status) {
        return false;
      }

      // Token pair filter
      if (filters.tokenPair !== 'all' && 
          `${trade.tokenIn}/${trade.tokenOut}` !== filters.tokenPair) {
        return false;
      }

      // Minimum profit filter
      if (filters.minProfit && 
          parseFloat(formatUnits(trade.profit)) < parseFloat(filters.minProfit)) {
        return false;
      }

      // Date range filter
      const tradeDate = new Date(trade.timestamp);
      if (filters.dateRange.start && 
          tradeDate < new Date(filters.dateRange.start)) {
        return false;
      }
      if (filters.dateRange.end && 
          tradeDate > new Date(filters.dateRange.end)) {
        return false;
      }

      return true;
    });
  }, [trades, filters]);

  const sortedTrades = useMemo(() => {
    return [...filteredTrades].sort((a, b) => {
      if (sortField === 'timestamp') {
        return sortDirection === 'desc'
          ? new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
          : new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      }
      if (sortField === 'profit') {
        return sortDirection === 'desc'
          ? parseFloat(formatUnits(b.profit)) - parseFloat(formatUnits(a.profit))
          : parseFloat(formatUnits(a.profit)) - parseFloat(formatUnits(b.profit));
      }
      return sortDirection === 'desc'
        ? String(b[sortField]).localeCompare(String(a[sortField]))
        : String(a[sortField]).localeCompare(String(b[sortField]));
    });
  }, [filteredTrades, sortField, sortDirection]);

  const handleSort = (field: keyof Trade) => {
    setSortDirection(current => 
      sortField === field ? (current === 'asc' ? 'desc' : 'asc') : 'desc'
    );
    setSortField(field);
  };

  const formatAmount = (amount: string, decimals: number = 18) => {
    try {
      return formatUnits(amount, decimals);
    } catch {
      return amount;
    }
  };

  const getStatusColor = (status: Trade['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-yellow-500';
    }
  };

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-full mb-4"></div>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 bg-gray-100 rounded w-full mb-2"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <button
          onClick={() => setIsFilterVisible(!isFilterVisible)}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          <svg className="-ml-0.5 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clipRule="evenodd" />
          </svg>
          Filters
        </button>
        <div className="text-sm text-gray-500">
          {filteredTrades.length} trades found
        </div>
      </div>

      {isFilterVisible && (
        <div className="bg-gray-50 p-4 rounded-lg grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="all">All</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="pending">Pending</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Token Pair</label>
            <select
              value={filters.tokenPair}
              onChange={(e) => setFilters(prev => ({ ...prev, tokenPair: e.target.value }))}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              {uniqueTokenPairs.map(pair => (
                <option key={pair} value={pair}>{pair}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Min Profit</label>
            <input
              type="number"
              value={filters.minProfit}
              onChange={(e) => setFilters(prev => ({ ...prev, minProfit: e.target.value }))}
              placeholder="0.0"
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            />
          </div>

          <div className="space-y-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Start Date</label>
              <input
                type="date"
                value={filters.dateRange.start}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange, start: e.target.value }
                }))}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">End Date</label>
              <input
                type="date"
                value={filters.dateRange.end}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange, end: e.target.value }
                }))}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              />
            </div>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full bg-white rounded-lg overflow-hidden">
          <thead className="bg-gray-50">
            <tr>
              <th
                onClick={() => handleSort('timestamp')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Time
                {sortField === 'timestamp' && (
                  <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pair
              </th>
              <th
                onClick={() => handleSort('amountIn')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Amount
                {sortField === 'amountIn' && (
                  <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th
                onClick={() => handleSort('profit')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Profit
                {sortField === 'profit' && (
                  <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Gas
              </th>
              <th
                onClick={() => handleSort('status')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                Status
                {sortField === 'status' && (
                  <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {sortedTrades.map((trade) => (
              <tr key={trade.txHash} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(trade.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {`${trade.tokenIn}/${trade.tokenOut}`}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatAmount(trade.amountIn)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={trade.profit.startsWith('-') ? 'text-red-500' : 'text-green-500'}>
                    {formatAmount(trade.profit)}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {`${trade.gasUsed.toLocaleString()} @ ${formatUnits(trade.gasPrice, 9)} gwei`}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`${getStatusColor(trade.status)} capitalize`}>
                    {trade.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredTrades.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No trades found
          </div>
        )}
      </div>
    </div>
  );
}; 