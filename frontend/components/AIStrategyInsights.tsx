import React from 'react';

export interface AIStrategy {
  id: string;
  name: string;
  description: string;
  confidence: number;
  expectedReturn: string;
  timeFrame: string;
  tokenPairs: string[];
  networks: string[];
  riskLevel: 'Low' | 'Medium' | 'High';
}

interface AIStrategyInsightsProps {
  strategies: AIStrategy[];
  isLoading: boolean;
  onApplyStrategy: (strategy: AIStrategy) => void;
}

export const AIStrategyInsights: React.FC<AIStrategyInsightsProps> = ({
  strategies,
  isLoading,
  onApplyStrategy
}) => {
  const getRiskBadgeColor = (risk: string) => {
    switch (risk) {
      case 'Low':
        return 'bg-green-100 text-green-800';
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'High':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-500';
    if (confidence >= 0.5) return 'text-yellow-500';
    return 'text-red-500';
  };

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-100 rounded w-full"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (strategies.length === 0) {
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
        <h3 className="mt-2 text-sm font-medium text-gray-900">No strategies available</h3>
        <p className="mt-1 text-sm text-gray-500">
          The AI hasn't generated any trading strategies yet.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-lg font-medium text-gray-900 mb-4">AI Strategy Recommendations</h3>
      <div className="space-y-6">
        {strategies.map((strategy) => (
          <div key={strategy.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between mb-4">
              <div>
                <h4 className="text-lg font-medium text-gray-900">{strategy.name}</h4>
                <div className="flex items-center mt-1">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskBadgeColor(strategy.riskLevel)}`}>
                    {strategy.riskLevel} Risk
                  </span>
                  <span className="ml-2 text-sm text-gray-500">
                    {strategy.timeFrame} • {strategy.expectedReturn} expected return
                  </span>
                </div>
              </div>
              <button
                onClick={() => onApplyStrategy(strategy)}
                className="mt-2 md:mt-0 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Apply Strategy
              </button>
            </div>
            
            <p className="text-sm text-gray-600 mb-4">{strategy.description}</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Target Token Pairs</h5>
                <div className="flex flex-wrap gap-2">
                  {strategy.tokenPairs.map((pair, index) => (
                    <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {pair}
                    </span>
                  ))}
                </div>
              </div>
              
              <div>
                <h5 className="text-sm font-medium text-gray-700 mb-2">Target Networks</h5>
                <div className="flex flex-wrap gap-2">
                  {strategy.networks.map((network, index) => (
                    <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      {network}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">AI Confidence</span>
                <span className={`text-sm font-medium ${getConfidenceColor(strategy.confidence)}`}>
                  {(strategy.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full ${
                    strategy.confidence >= 0.8
                      ? 'bg-green-500'
                      : strategy.confidence >= 0.5
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${strategy.confidence * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 