import React from 'react';
import { BotStatus } from '../services/websocket';
import { formatEther } from 'ethers';

interface BotStatusPanelProps {
  status: BotStatus | null;
  isLoading: boolean;
  connectionStatus?: 'connected' | 'connecting' | 'disconnected' | 'error';
}

export const BotStatusPanel: React.FC<BotStatusPanelProps> = ({
  status,
  isLoading,
  connectionStatus = 'disconnected'
}) => {
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / (24 * 60 * 60));
    const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60));
    const minutes = Math.floor((seconds % (60 * 60)) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const formatMemoryUsage = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-gray-100 p-6 rounded-lg h-32"></div>
        ))}
      </div>
    );
  }

  if (connectionStatus === 'error') {
    return (
      <div className="bg-red-50 p-4 rounded-lg">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">WebSocket Connection Error</h3>
            <div className="mt-2 text-sm text-red-700">
              Unable to connect to the bot. Please check that the backend server is running and accessible.
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (connectionStatus === 'connecting') {
    return (
      <div className="bg-yellow-50 p-4 rounded-lg">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">Connecting to Bot</h3>
            <div className="mt-2 text-sm text-yellow-700">
              Establishing connection to the bot. Please wait...
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-blue-50 p-4 rounded-lg">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2h-1V9a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Bot Status Unavailable</h3>
            <div className="mt-2 text-sm text-blue-700">
              {connectionStatus === 'connected' 
                ? "Connected to the server, but no bot status data is available. The bot may not be running."
                : "Not connected to the bot. Please check your connection and ensure the backend server is running."}
            </div>
            <div className="mt-2">
              <a href="#" className="text-sm font-medium text-blue-600 hover:text-blue-500">
                Check the documentation for troubleshooting steps →
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const metrics = [
    {
      label: 'Status',
      value: status.isActive ? 'Active' : 'Inactive',
      color: status.isActive ? 'text-green-500' : 'text-red-500',
      icon: status.isActive ? (
        <svg className="h-5 w-5 text-green-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      ) : (
        <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      )
    },
    {
      label: 'Uptime',
      value: formatUptime(status.uptime),
      color: 'text-blue-500'
    },
    {
      label: 'Memory Usage',
      value: `${formatMemoryUsage(status.memoryUsage.heapUsed)} / ${formatMemoryUsage(status.memoryUsage.heapTotal)}`,
      color: 'text-purple-500'
    },
    {
      label: 'CPU Usage',
      value: `${(status.cpuUsage * 100).toFixed(1)}%`,
      color: 'text-orange-500'
    },
    {
      label: 'Network',
      value: status.network,
      color: 'text-indigo-500'
    },
    {
      label: 'Pending Tx',
      value: status.pendingTransactions.toString(),
      color: status.pendingTransactions > 5 ? 'text-yellow-500' : 'text-green-500'
    },
    {
      label: 'Success Rate',
      value: `${((status.successfulTrades / (status.totalTrades || 1)) * 100 || 0).toFixed(1)}%`,
      color: 'text-green-500'
    },
    {
      label: 'Total Profit',
      value: formatEther(status.totalProfit),
      color: 'text-green-500'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, index) => (
        <div
          key={metric.label}
          className="bg-white p-6 rounded-lg shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium text-gray-500">{metric.label}</div>
            {metric.icon && <div>{metric.icon}</div>}
          </div>
          <div className={`mt-2 text-2xl font-semibold ${metric.color}`}>
            {metric.value}
          </div>
        </div>
      ))}
    </div>
  );
}; 