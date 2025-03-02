import React, { useState } from 'react';
import { useArbitrageX } from '../hooks/useArbitrageX';
import { TradeHistoryTable } from '../components/TradeHistoryTable';
import { BotStatusPanel } from '../components/BotStatusPanel';
import { ArbitrageExecutionForm } from '../components/ArbitrageExecutionForm';
import { DashboardLayout } from '../components/DashboardLayout';

export default function Dashboard() {
  const {
    isConnected,
    trades,
    botStatus,
    error,
    executeArbitrage: originalExecuteArbitrage,
    reconnectAttempts,
    connectionState
  } = useArbitrageX();

  // Create a wrapper function that returns void
  const executeArbitrage = async (params: {
    tokenIn: string;
    tokenOut: string;
    amount: string;
    router: string;
  }): Promise<void> => {
    await originalExecuteArbitrage(params);
    // Return void
  };

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
    <DashboardLayout>
      <div className="grid grid-cols-1 gap-6">
        <div className="bg-white shadow-sm rounded-lg p-6">
          <div className="mb-4">
            <div className="flex border-b">
              <button
                className={`px-4 py-2 font-medium ${
                  activeTab === 'status' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'
                }`}
                onClick={() => setActiveTab('status')}
              >
                Bot Status
              </button>
              <button
                className={`px-4 py-2 font-medium ${
                  activeTab === 'execute' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'
                }`}
                onClick={() => setActiveTab('execute')}
              >
                Execute Trade
              </button>
              <button
                className={`px-4 py-2 font-medium ${
                  activeTab === 'history' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'
                }`}
                onClick={() => setActiveTab('history')}
              >
                Trade History
              </button>
            </div>
          </div>

          {activeTab === 'status' && <BotStatusPanel status={botStatus} isLoading={!isConnected} />}
          {activeTab === 'execute' && <ArbitrageExecutionForm onExecute={executeArbitrage} isLoading={!isConnected} />}
          {activeTab === 'history' && <TradeHistoryTable trades={trades} isLoading={!isConnected} />}
        </div>
      </div>
    </DashboardLayout>
  );
}
