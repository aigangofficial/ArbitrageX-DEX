import React, { useState } from 'react';

export interface Network {
  id: string;
  name: string;
  icon: string;
  color: string;
  isActive: boolean;
}

interface NetworkSelectorProps {
  networks: Network[];
  onNetworkChange: (networkId: string) => void;
  selectedNetwork: string;
}

export const NetworkSelector: React.FC<NetworkSelectorProps> = ({
  networks,
  onNetworkChange,
  selectedNetwork
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  const handleNetworkSelect = (networkId: string) => {
    onNetworkChange(networkId);
    setIsOpen(false);
  };

  const selectedNetworkData = networks.find(network => network.id === selectedNetwork) || networks[0];

  return (
    <div className="relative">
      <button
        type="button"
        className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        onClick={toggleDropdown}
      >
        <img
          src={selectedNetworkData.icon}
          alt={selectedNetworkData.name}
          className="h-5 w-5 mr-2 rounded-full"
        />
        {selectedNetworkData.name}
        <svg
          className="ml-2 -mr-0.5 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
          <div className="py-1" role="menu" aria-orientation="vertical" aria-labelledby="options-menu">
            {networks.map(network => (
              <button
                key={network.id}
                className={`w-full text-left block px-4 py-2 text-sm ${
                  network.id === selectedNetwork
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
                role="menuitem"
                onClick={() => handleNetworkSelect(network.id)}
              >
                <div className="flex items-center">
                  <img src={network.icon} alt={network.name} className="h-5 w-5 mr-2 rounded-full" />
                  <span>{network.name}</span>
                  {network.isActive ? (
                    <span className="ml-auto inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Active
                    </span>
                  ) : (
                    <span className="ml-auto inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      Inactive
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}; 