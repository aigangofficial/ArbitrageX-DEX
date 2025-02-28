"""
Gas Optimizer Module for ArbitrageX

This module is responsible for optimizing gas prices for arbitrage transactions
to ensure they are executed efficiently while minimizing costs.
"""

import logging
import json
import time
import os
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import random
import math
import requests
from web3 import Web3
import numpy as np
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gas_optimizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GasOptimizer")

class GasOptimizer:
    """
    Optimizes gas prices for arbitrage transactions to balance
    execution speed and cost efficiency.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the gas optimizer.
        
        Args:
            config: Bot configuration dictionary
        """
        logger.info("Initializing Gas Optimizer")
        self.config = config
        
        # Initialize web3 connections
        self.web3_connections = self._init_web3_connections()
        
        # Gas price history for each network
        self.gas_price_history = {
            network: deque(maxlen=100) for network in config.get("networks", ["ethereum"])
        }
        
        # Last gas price update time for each network
        self.last_update_time = {
            network: 0 for network in config.get("networks", ["ethereum"])
        }
        
        # Gas price update interval (seconds)
        self.update_interval = config.get("gas_update_interval", 15)
        
        # Maximum gas price (in Gwei)
        self.max_gas_price = config.get("execution", {}).get("max_gas_price", 100)
        
        # Gas price API endpoints
        self.gas_apis = {
            "ethereum": "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=YOUR_API_KEY",
            "polygon": "https://api.polygonscan.com/api?module=gastracker&action=gasoracle&apikey=YOUR_API_KEY",
            "arbitrum": "https://api.arbiscan.io/api?module=gastracker&action=gasoracle&apikey=YOUR_API_KEY",
            "optimism": "https://api-optimistic.etherscan.io/api?module=gastracker&action=gasoracle&apikey=YOUR_API_KEY",
            "bsc": "https://api.bscscan.com/api?module=gastracker&action=gasoracle&apikey=YOUR_API_KEY"
        }
        
        # Load historical gas data
        self.historical_gas_data = self._load_historical_gas_data()
        
        # Initialize gas price models
        self.gas_models = self._init_gas_models()
        
        logger.info("Gas Optimizer initialized")
    
    def _init_web3_connections(self) -> Dict[str, Web3]:
        """Initialize Web3 connections for each network"""
        connections = {}
        
        # Network RPC endpoints - in production, these would be loaded from secure config
        network_rpcs = {
            "ethereum": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
            "arbitrum": "https://arb1.arbitrum.io/rpc",
            "polygon": "https://polygon-rpc.com",
            "optimism": "https://mainnet.optimism.io",
            "bsc": "https://bsc-dataseed.binance.org/",
            # Add more networks as needed
        }
        
        # For testing/development, use mock connections
        if self.config.get("use_mock_connections", True):
            networks = self.config.get("networks", ["ethereum"])
            for network in networks:
                connections[network] = None
                logger.info(f"Using mock connection for {network}")
            return connections
        
        # Initialize real connections
        networks = self.config.get("networks", ["ethereum"])
        for network in networks:
            try:
                if network in network_rpcs:
                    web3 = Web3(Web3.HTTPProvider(network_rpcs[network]))
                    if web3.is_connected():
                        connections[network] = web3
                        logger.info(f"Connected to {network}")
                    else:
                        logger.warning(f"Failed to connect to {network}")
                        connections[network] = None
                else:
                    logger.warning(f"No RPC endpoint configured for {network}")
                    connections[network] = None
            except Exception as e:
                logger.error(f"Error connecting to {network}: {e}")
                connections[network] = None
        
        return connections
    
    def _load_historical_gas_data(self) -> Dict:
        """Load historical gas price data"""
        try:
            gas_data_path = "backend/bot/data/historical_gas.json"
            if os.path.exists(gas_data_path):
                with open(gas_data_path, 'r') as f:
                    historical_gas_data = json.load(f)
                logger.info(f"Loaded historical gas data from {gas_data_path}")
                return historical_gas_data
            else:
                logger.warning(f"Historical gas data file not found at {gas_data_path}")
                return self._generate_default_gas_data()
        except Exception as e:
            logger.error(f"Error loading historical gas data: {e}")
            return self._generate_default_gas_data()
    
    def _generate_default_gas_data(self) -> Dict:
        """Generate default historical gas data"""
        # Default gas data structure
        default_data = {}
        
        # Generate for each network
        for network in self.config.get("networks", ["ethereum"]):
            # Base gas prices for different networks
            base_prices = {
                "ethereum": {"low": 20, "average": 30, "high": 50, "fastest": 80},
                "arbitrum": {"low": 0.1, "average": 0.3, "high": 0.5, "fastest": 1.0},
                "polygon": {"low": 30, "average": 50, "high": 100, "fastest": 200},
                "optimism": {"low": 0.001, "average": 0.01, "high": 0.1, "fastest": 0.5},
                "bsc": {"low": 5, "average": 6, "high": 7, "fastest": 10}
            }
            
            # Get base price for this network
            base_price = base_prices.get(network, {"low": 10, "average": 20, "high": 40, "fastest": 60})
            
            # Generate hourly data for the past week
            hourly_data = []
            now = datetime.now()
            
            for hour in range(24 * 7):
                timestamp = int((now - timedelta(hours=hour)).timestamp())
                
                # Add some randomness to the base prices
                variation = random.uniform(0.7, 1.3)
                
                hourly_data.append({
                    "timestamp": timestamp,
                    "datetime": (now - timedelta(hours=hour)).isoformat(),
                    "low": base_price["low"] * variation,
                    "average": base_price["average"] * variation,
                    "high": base_price["high"] * variation,
                    "fastest": base_price["fastest"] * variation
                })
            
            default_data[network] = hourly_data
        
        return default_data
    
    def _init_gas_models(self) -> Dict:
        """Initialize gas price prediction models"""
        # In a real implementation, this would load or train ML models
        # For now, return empty dict
        return {}
    
    def get_optimal_gas_price(self, network: str) -> float:
        """
        Get the optimal gas price for a transaction on the specified network.
        
        Args:
            network: Network name
            
        Returns:
            Optimal gas price in Gwei
        """
        # Check if we need to update gas prices
        current_time = time.time()
        if current_time - self.last_update_time.get(network, 0) > self.update_interval:
            self._update_gas_prices(network)
            self.last_update_time[network] = current_time
        
        # Get current gas prices
        gas_prices = self._get_current_gas_prices(network)
        
        # Determine optimal gas price based on strategy
        gas_strategy = self.config.get("gas_strategy", "balanced")
        
        if gas_strategy == "aggressive":
            # Use high gas price to ensure quick execution
            optimal_price = gas_prices.get("high", 0)
        elif gas_strategy == "conservative":
            # Use low gas price to minimize costs
            optimal_price = gas_prices.get("low", 0)
        else:  # balanced
            # Use average gas price
            optimal_price = gas_prices.get("average", 0)
        
        # Apply AI adjustment if available
        optimal_price = self._apply_ai_adjustment(network, optimal_price)
        
        # Ensure gas price is within limits
        optimal_price = min(optimal_price, self.max_gas_price)
        
        logger.info(f"Optimal gas price for {network}: {optimal_price:.2f} Gwei")
        
        return optimal_price
    
    def _update_gas_prices(self, network: str):
        """Update gas prices for the specified network"""
        try:
            # For real implementation, query gas price API or node
            if not self.config.get("use_mock_data", True):
                gas_prices = self._fetch_gas_prices(network)
            else:
                gas_prices = self._generate_mock_gas_prices(network)
            
            # Add to history
            self.gas_price_history[network].append({
                "timestamp": int(time.time()),
                "prices": gas_prices
            })
            
            logger.debug(f"Updated gas prices for {network}: {gas_prices}")
            
        except Exception as e:
            logger.error(f"Error updating gas prices for {network}: {e}")
    
    def _fetch_gas_prices(self, network: str) -> Dict:
        """Fetch current gas prices from API or node"""
        # Try to get from Web3 connection first
        web3 = self.web3_connections.get(network)
        if web3 and web3.is_connected():
            try:
                # Different networks have different gas price methods
                if network == "ethereum":
                    # Ethereum mainnet
                    gas_price = web3.eth.gas_price / 1e9  # Convert to Gwei
                    return {
                        "low": gas_price * 0.8,
                        "average": gas_price,
                        "high": gas_price * 1.2,
                        "fastest": gas_price * 1.5
                    }
                else:
                    # Other networks
                    gas_price = web3.eth.gas_price / 1e9  # Convert to Gwei
                    return {
                        "low": gas_price * 0.8,
                        "average": gas_price,
                        "high": gas_price * 1.2,
                        "fastest": gas_price * 1.5
                    }
            except Exception as e:
                logger.warning(f"Error getting gas price from Web3 for {network}: {e}")
        
        # Fall back to API
        api_url = self.gas_apis.get(network)
        if api_url:
            try:
                response = requests.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "1":
                        result = data.get("result", {})
                        return {
                            "low": float(result.get("SafeGasPrice", 0)),
                            "average": float(result.get("ProposeGasPrice", 0)),
                            "high": float(result.get("FastGasPrice", 0)),
                            "fastest": float(result.get("FastGasPrice", 0)) * 1.2
                        }
            except Exception as e:
                logger.warning(f"Error fetching gas prices from API for {network}: {e}")
        
        # If all else fails, use mock data
        return self._generate_mock_gas_prices(network)
    
    def _generate_mock_gas_prices(self, network: str) -> Dict:
        """Generate mock gas prices for testing"""
        # Base gas prices for different networks
        base_prices = {
            "ethereum": {"low": 20, "average": 30, "high": 50, "fastest": 80},
            "arbitrum": {"low": 0.1, "average": 0.3, "high": 0.5, "fastest": 1.0},
            "polygon": {"low": 30, "average": 50, "high": 100, "fastest": 200},
            "optimism": {"low": 0.001, "average": 0.01, "high": 0.1, "fastest": 0.5},
            "bsc": {"low": 5, "average": 6, "high": 7, "fastest": 10}
        }
        
        # Get base price for this network
        base_price = base_prices.get(network, {"low": 10, "average": 20, "high": 40, "fastest": 60})
        
        # Add some randomness
        variation = random.uniform(0.8, 1.2)
        
        return {
            "low": base_price["low"] * variation,
            "average": base_price["average"] * variation,
            "high": base_price["high"] * variation,
            "fastest": base_price["fastest"] * variation
        }
    
    def _get_current_gas_prices(self, network: str) -> Dict:
        """Get the most recent gas prices for the specified network"""
        if network in self.gas_price_history and self.gas_price_history[network]:
            return self.gas_price_history[network][-1]["prices"]
        else:
            # No history, generate new prices
            return self._generate_mock_gas_prices(network)
    
    def _apply_ai_adjustment(self, network: str, base_price: float) -> float:
        """Apply AI-based adjustment to the gas price"""
        # In a real implementation, this would use ML models to predict optimal gas price
        # For now, apply a simple adjustment based on time of day
        
        # Get current hour (0-23)
        current_hour = datetime.now().hour
        
        # Adjust based on typical network congestion patterns
        if network == "ethereum":
            # Ethereum tends to be busier during US business hours
            if 13 <= current_hour <= 21:  # 9 AM - 5 PM EST
                adjustment = 1.1  # Increase by 10%
            elif 1 <= current_hour <= 9:  # Night in US
                adjustment = 0.9  # Decrease by 10%
            else:
                adjustment = 1.0
        elif network == "polygon" or network == "bsc":
            # These networks tend to be busier during Asian business hours
            if 1 <= current_hour <= 9:  # 9 AM - 5 PM Asia
                adjustment = 1.1
            elif 13 <= current_hour <= 21:  # Night in Asia
                adjustment = 0.9
            else:
                adjustment = 1.0
        else:
            # Default adjustment
            adjustment = 1.0
        
        # Apply adjustment
        adjusted_price = base_price * adjustment
        
        return adjusted_price
    
    def estimate_gas_usage(self, network: str, operation_type: str) -> int:
        """
        Estimate gas usage for a specific operation type.
        
        Args:
            network: Network name
            operation_type: Type of operation (e.g., 'swap', 'flash_loan', 'arbitrage')
            
        Returns:
            Estimated gas usage in gas units
        """
        # Default gas usage estimates
        gas_estimates = {
            "swap": 150000,
            "flash_loan": 300000,
            "arbitrage": 500000,
            "approval": 50000
        }
        
        # Network-specific adjustments
        network_multipliers = {
            "ethereum": 1.0,
            "arbitrum": 1.2,  # Arbitrum can use more gas
            "polygon": 0.8,  # Polygon typically uses less gas
            "optimism": 0.9,
            "bsc": 0.7
        }
        
        # Get base estimate
        base_estimate = gas_estimates.get(operation_type, 200000)
        
        # Apply network multiplier
        multiplier = network_multipliers.get(network, 1.0)
        
        # Calculate final estimate
        gas_estimate = int(base_estimate * multiplier)
        
        return gas_estimate
    
    def calculate_gas_cost(self, network: str, gas_price: float, gas_used: int) -> float:
        """
        Calculate the gas cost in ETH for a transaction.
        
        Args:
            network: Network name
            gas_price: Gas price in Gwei
            gas_used: Gas used in gas units
            
        Returns:
            Gas cost in ETH
        """
        # Convert gas price from Gwei to ETH
        gas_price_eth = gas_price * 1e-9
        
        # Calculate gas cost
        gas_cost = gas_price_eth * gas_used
        
        return gas_cost
    
    def should_bundle_transactions(self, transactions: List[Dict]) -> bool:
        """
        Determine if transactions should be bundled for gas efficiency.
        
        Args:
            transactions: List of transaction details
            
        Returns:
            True if transactions should be bundled, False otherwise
        """
        # If only one transaction, no need to bundle
        if len(transactions) <= 1:
            return False
        
        # Check if all transactions are on the same network
        networks = set(tx.get("network") for tx in transactions)
        if len(networks) > 1:
            return False
        
        # Get the network
        network = list(networks)[0]
        
        # Calculate total gas cost if executed separately
        total_gas_separate = 0
        for tx in transactions:
            gas_price = tx.get("gas_price", self.get_optimal_gas_price(network))
            gas_used = tx.get("gas_used", self.estimate_gas_usage(network, tx.get("type", "swap")))
            total_gas_separate += self.calculate_gas_cost(network, gas_price, gas_used)
        
        # Estimate gas cost if bundled
        # Bundling typically saves ~30% on gas
        bundled_gas_used = sum(tx.get("gas_used", self.estimate_gas_usage(network, tx.get("type", "swap"))) for tx in transactions)
        bundled_gas_used = int(bundled_gas_used * 0.7)  # 30% savings
        
        # Use the highest gas price among transactions
        bundled_gas_price = max(tx.get("gas_price", self.get_optimal_gas_price(network)) for tx in transactions)
        
        # Calculate bundled gas cost
        bundled_gas_cost = self.calculate_gas_cost(network, bundled_gas_price, bundled_gas_used)
        
        # Determine if bundling is more efficient
        return bundled_gas_cost < total_gas_separate
    
    def get_gas_price_trend(self, network: str, hours: int = 24) -> Dict:
        """
        Get gas price trend for the specified network over a time period.
        
        Args:
            network: Network name
            hours: Number of hours to look back
            
        Returns:
            Dictionary with gas price trend data
        """
        # Get historical data for this network
        network_data = self.historical_gas_data.get(network, [])
        
        # Calculate start time
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        # Filter data to the specified time period
        filtered_data = [entry for entry in network_data if entry["timestamp"] >= start_time]
        
        if not filtered_data:
            return {
                "trend": "stable",
                "change_pct": 0,
                "current": self._get_current_gas_prices(network),
                "data": []
            }
        
        # Extract average gas prices
        timestamps = [entry["timestamp"] for entry in filtered_data]
        average_prices = [entry["average"] for entry in filtered_data]
        
        # Calculate trend
        if len(average_prices) >= 2:
            first_price = average_prices[0]
            last_price = average_prices[-1]
            change_pct = ((last_price - first_price) / first_price) * 100 if first_price > 0 else 0
            
            if change_pct > 10:
                trend = "rising"
            elif change_pct < -10:
                trend = "falling"
            else:
                trend = "stable"
        else:
            trend = "stable"
            change_pct = 0
        
        return {
            "trend": trend,
            "change_pct": change_pct,
            "current": self._get_current_gas_prices(network),
            "data": [{"timestamp": t, "price": p} for t, p in zip(timestamps, average_prices)]
        }
    
    def save_gas_data(self):
        """Save gas price history to file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs("backend/bot/data", exist_ok=True)
            
            # Convert deque to list for serialization
            data_to_save = {}
            for network, history in self.gas_price_history.items():
                data_to_save[network] = list(history)
            
            # Save to file
            with open("backend/bot/data/gas_price_history.json", 'w') as f:
                json.dump(data_to_save, f, indent=2)
            
            logger.info("Saved gas price history to file")
            
        except Exception as e:
            logger.error(f"Error saving gas price history: {e}")

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        "networks": ["ethereum", "arbitrum", "polygon"],
        "gas_strategy": "balanced",
        "execution": {
            "max_gas_price": 100  # Gwei
        },
        "use_mock_data": True
    }
    
    optimizer = GasOptimizer(config)
    
    # Get optimal gas prices for each network
    for network in config["networks"]:
        gas_price = optimizer.get_optimal_gas_price(network)
        print(f"Optimal gas price for {network}: {gas_price:.2f} Gwei")
        
        # Estimate gas cost for an arbitrage operation
        gas_used = optimizer.estimate_gas_usage(network, "arbitrage")
        gas_cost = optimizer.calculate_gas_cost(network, gas_price, gas_used)
        print(f"Estimated gas cost for arbitrage on {network}: {gas_cost:.6f} ETH")
        
        # Get gas price trend
        trend = optimizer.get_gas_price_trend(network, hours=24)
        print(f"Gas price trend for {network}: {trend['trend']} ({trend['change_pct']:.2f}%)")
        print()
