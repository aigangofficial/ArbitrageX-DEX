import React from 'react';
import Head from 'next/head';
import { useWebSocket } from '../hooks/useWebSocket';

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  title = 'ArbitrageX Dashboard'
}) => {
  const { connectionStatus } = useWebSocket();

  const renderConnectionStatus = () => {
    let statusColor = 'bg-gray-400';
    let statusText = 'Disconnected';

    switch (connectionStatus) {
      case 'connected':
        statusColor = 'bg-green-500';
        statusText = 'Connected';
        break;
      case 'connecting':
        statusColor = 'bg-yellow-500';
        statusText = 'Connecting...';
        break;
      case 'error':
        statusColor = 'bg-red-500';
        statusText = 'Connection Error';
        break;
      default:
        statusColor = 'bg-gray-400';
        statusText = 'Disconnected';
    }

    return (
      <div className="flex items-center">
        <div className={`w-3 h-3 rounded-full ${statusColor} mr-2`}></div>
        <span className="text-sm text-gray-600">{statusText}</span>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>{title}</title>
        <meta name="description" content="ArbitrageX - Automated DeFi Arbitrage Platform" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {renderConnectionStatus()}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>
    </div>
  );
}; 