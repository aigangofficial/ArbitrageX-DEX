import React, { useState } from 'react';
import { useArbitrageX } from '../hooks/useArbitrageX';
import { TradeHistoryTable } from '../components/TradeHistoryTable';
import { BotStatusPanel } from '../components/BotStatusPanel';
import { ArbitrageExecutionForm } from '../components/ArbitrageExecutionForm';

export default function Dashboard() {
  const {
    isConnected,
    trades,
    botStatus,
    error,
    executeArbitrage,
    reconnectAttempts,
    connectionState
  } = useArbitrageX();

  const [activeTab, setActiveTab] = useState<'status' | 'execute' | 'history'>('status');

  const renderConnectionStatus = () => {
    let statusColor = 'bg-gray-500';
    let statusText = 'Unknown';

    switch (connectionState) {
      case 'connected':
        statusColor = 'bg-green-500';
        statusText = 'Connected';
        break;
      case 'connecting':
        statusColor = 'bg-yellow-500';
        statusText = `Connecting (Attempt ${reconnectAttempts})`;
        break;
      case 'disconnected':
        statusColor = 'bg-red-500';
        statusText = 'Disconnected';
        break;
      case 'error':
        statusColor = 'bg-red-500';
        statusText = 'Error';
        break;
    }

    return (
      <div className="flex items-center space-x-2">
        <div className={`h-3 w-3 rounded-full ${statusColor}`}></div>
        <span className="text-sm font-medium">{statusText}</span>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="py-6">
        <header className="bg-white shadow-sm mb-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between py-4 space-y-4 sm:space-y-0">
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">ArbitrageX Dashboard</h1>
              {renderConnectionStatus()}
            </div>
          </div>
        </header>

        {/* Mobile Navigation */}
        <div className="sm:hidden bg-white shadow-sm mb-6">
          <div className="px-4">
            <nav className="flex -mb-px space-x-8">
              {['status', 'execute', 'history'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as any)}
                  className={`${
                    activeTab === tab
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm capitalize`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>
        </div>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Error Alert */}
          {error && (
            <div className="rounded-md bg-red-50 p-4 mb-6 animate-fade-in">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <div className="mt-2 text-sm text-red-700">{error.message}</div>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-8">
            {/* Desktop View */}
            <div className="hidden sm:block space-y-8">
              <section aria-labelledby="bot-status">
                <h2 id="bot-status" className="text-lg font-medium text-gray-900 mb-4">
                  Bot Status
                </h2>
                <BotStatusPanel status={botStatus} isLoading={!isConnected} />
              </section>

              <section aria-labelledby="execute-trade">
                <h2 id="execute-trade" className="text-lg font-medium text-gray-900 mb-4">
                  Execute Trade
                </h2>
                <ArbitrageExecutionForm
                  onExecute={executeArbitrage}
                  isLoading={!isConnected}
                />
              </section>

              <section aria-labelledby="trade-history">
                <h2 id="trade-history" className="text-lg font-medium text-gray-900 mb-4">
                  Trade History
                </h2>
                <TradeHistoryTable trades={trades} isLoading={!isConnected} />
              </section>
            </div>

            {/* Mobile View */}
            <div className="sm:hidden">
              {activeTab === 'status' && (
                <section aria-labelledby="bot-status-mobile">
                  <h2 id="bot-status-mobile" className="sr-only">Bot Status</h2>
                  <BotStatusPanel status={botStatus} isLoading={!isConnected} />
                </section>
              )}

              {activeTab === 'execute' && (
                <section aria-labelledby="execute-trade-mobile">
                  <h2 id="execute-trade-mobile" className="sr-only">Execute Trade</h2>
                  <ArbitrageExecutionForm
                    onExecute={executeArbitrage}
                    isLoading={!isConnected}
                  />
                </section>
              )}

              {activeTab === 'history' && (
                <section aria-labelledby="trade-history-mobile">
                  <h2 id="trade-history-mobile" className="sr-only">Trade History</h2>
                  <TradeHistoryTable trades={trades} isLoading={!isConnected} />
                </section>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Global Loading Spinner */}
      {!isConnected && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500 mx-auto"></div>
            <p className="mt-4 text-center text-gray-700">Connecting to server...</p>
          </div>
        </div>
      )}
    </div>
  );
}
