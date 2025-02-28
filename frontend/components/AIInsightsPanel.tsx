import React from 'react';

export interface AIOpportunity {
  id: string;
  tokenPair: string;
  confidence: number;
  estimatedProfit: string;
  executionTime: number;
  gasCost: string;
  netProfit: string;
  timestamp: Date;
  network: string;
  isRecommended: boolean;
}

interface AIInsightsPanelProps {
  opportunities: AIOpportunity[];
  isLoading: boolean;
  onSimulateTrade: (opportunity: AIOpportunity) => void;
  onExecuteTrade: (opportunity: AIOpportunity) => void;
}

export const AIInsightsPanel: React.FC<AIInsightsPanelProps> = ({
  opportunities,
  isLoading,
  onSimulateTrade,
  onExecuteTrade
}) => {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-500';
    if (confidence >= 0.5) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  };

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-full mb-4"></div>
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-32 bg-gray-100 rounded w-full mb-2"></div>
        ))}
      </div>
    );
  }

  if (opportunities.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No opportunities found</h3>
        <p className="mt-1 text-sm text-gray-500">
          The AI hasn't detected any arbitrage opportunities yet.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <h3 className="text-lg font-medium text-gray-900 mb-4">AI-Predicted Opportunities</h3>
        <div className="space-y-4">
          {opportunities.map((opportunity) => (
            <div
              key={opportunity.id}
              className={`p-4 rounded-lg border ${
                opportunity.isRecommended
                  ? 'border-green-200 bg-green-50'
                  : 'border-gray-200 bg-white'
              }`}
            >
              {opportunity.isRecommended && (
                <div className="flex items-center mb-2">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <svg className="-ml-0.5 mr-1.5 h-2 w-2 text-green-400" fill="currentColor" viewBox="0 0 8 8">
                      <circle cx="4" cy="4" r="3" />
                    </svg>
                    AI Recommended
                  </span>
                </div>
              )}
              
              <div className="flex flex-col md:flex-row md:items-center justify-between">
                <div>
                  <div className="flex items-center">
                    <h4 className="text-lg font-medium text-gray-900">{opportunity.tokenPair}</h4>
                    <span className="ml-2 px-2 py-1 text-xs rounded-full bg-gray-100">
                      {opportunity.network}
                    </span>
                  </div>
                  
                  <div className="mt-1 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    <div>
                      <span className="text-gray-500">Confidence:</span>{' '}
                      <span className={getConfidenceColor(opportunity.confidence)}>
                        {(opportunity.confidence * 100).toFixed(1)}% ({getConfidenceLabel(opportunity.confidence)})
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Est. Profit:</span>{' '}
                      <span className="text-green-600">{opportunity.estimatedProfit}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Gas Cost:</span>{' '}
                      <span className="text-red-600">{opportunity.gasCost}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Net Profit:</span>{' '}
                      <span className={parseFloat(opportunity.netProfit) > 0 ? 'text-green-600' : 'text-red-600'}>
                        {opportunity.netProfit}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Execution Time:</span>{' '}
                      <span>{opportunity.executionTime}ms</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Detected:</span>{' '}
                      <span>{new Date(opportunity.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
                
                <div className="mt-4 md:mt-0 flex space-x-2">
                  <button
                    onClick={() => onSimulateTrade(opportunity)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Simulate
                  </button>
                  <button
                    onClick={() => onExecuteTrade(opportunity)}
                    className={`inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md shadow-sm text-white ${
                      opportunity.isRecommended
                        ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500'
                        : 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-500'
                    } focus:outline-none focus:ring-2 focus:ring-offset-2`}
                  >
                    Execute
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}; 