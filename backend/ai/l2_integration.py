#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Layer 2 Integration

This module provides integration with Layer 2 networks (Arbitrum, Optimism) to
reduce gas costs and improve profitability for the ArbitrageX trading bot.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("l2_integration.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("L2Integration")

class L2Network(Enum):
    """Enum representing supported Layer 2 networks."""
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    POLYGON = "polygon"


@dataclass
class L2GasInfo:
    """Data class for storing gas information for a Layer 2 network."""
    network: L2Network
    gas_price: float  # Gas price in native L2 units
    l1_data_fee: float  # Additional L1 data fee (if applicable)
    eth_price_usd: float  # Current ETH price in USD
    updated_at: float  # Timestamp of last update
    
    def total_gas_cost_usd(self, gas_limit: int) -> float:
        """
        Calculate total gas cost in USD including L1 data fees.
        
        Args:
            gas_limit: Estimated gas limit for the transaction
            
        Returns:
            Total gas cost in USD
        """
        # Convert gas price to ETH and calculate base cost
        gas_cost_eth = (self.gas_price * gas_limit) / 1e9
        
        # Add L1 data fee (in ETH)
        total_cost_eth = gas_cost_eth + self.l1_data_fee
        
        # Convert to USD
        return total_cost_eth * self.eth_price_usd


class L2GasTracker:
    """Tracks and predicts gas prices across Layer 2 networks."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the L2 gas tracker.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = {
            "update_interval": 60,  # Seconds between gas price updates
            "history_size": 100,    # Number of historical data points to keep
            "gas_api_timeout": 10,  # API request timeout in seconds
            "gas_multiplier": 1.1,  # Safety multiplier for gas estimates
        }
        
        # Load configuration if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"Loaded L2 gas tracker configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load L2 gas configuration: {e}")
        
        # Initialize gas data for each network
        self.current_gas_data: Dict[L2Network, L2GasInfo] = {}
        self.gas_history: Dict[L2Network, List[L2GasInfo]] = {
            network: [] for network in L2Network
        }
        self.last_update = 0
        
        # Default gas limits for common operations
        self.default_gas_limits = {
            "swap": 150000,
            "approve": 50000,
            "transfer": 21000,
            "arbitrage": 350000,
        }
        
        # Initialize with default values
        self._initialize_default_values()
    
    def _initialize_default_values(self) -> None:
        """Initialize gas data with default values."""
        eth_price = 3000.0  # Default ETH price if real data not available
        
        default_values = {
            L2Network.ARBITRUM: L2GasInfo(
                network=L2Network.ARBITRUM,
                gas_price=0.1,  # gwei
                l1_data_fee=0.0001,  # ETH
                eth_price_usd=eth_price,
                updated_at=time.time()
            ),
            L2Network.OPTIMISM: L2GasInfo(
                network=L2Network.OPTIMISM,
                gas_price=0.001,  # gwei
                l1_data_fee=0.0002,  # ETH
                eth_price_usd=eth_price,
                updated_at=time.time()
            ),
            L2Network.BASE: L2GasInfo(
                network=L2Network.BASE,
                gas_price=0.0008,  # gwei
                l1_data_fee=0.0001,  # ETH
                eth_price_usd=eth_price,
                updated_at=time.time()
            ),
            L2Network.POLYGON: L2GasInfo(
                network=L2Network.POLYGON,
                gas_price=50,  # gwei (higher but using MATIC)
                l1_data_fee=0,  # No L1 data fee
                eth_price_usd=eth_price,
                updated_at=time.time()
            ),
        }
        
        self.current_gas_data = default_values
    
    def update_gas_prices(self) -> None:
        """
        Update current gas prices from external APIs.
        
        In a production environment, this would call real gas APIs for each L2.
        For this example, we'll simulate gas price updates.
        """
        current_time = time.time()
        
        # Only update if the update interval has elapsed
        if current_time - self.last_update < self.config["update_interval"]:
            return
        
        # In production this would call gas price APIs
        # For this example, we'll simulate updated values
        eth_price = 3000.0  # Would be fetched from price API
        
        # Update gas prices for each network
        for network in L2Network:
            # This simulates a gas price update with slight variations
            # In production, get real values from APIs
            current_info = self.current_gas_data.get(network)
            if not current_info:
                continue
                
            # Simulate gas price fluctuations
            gas_multiplier = 0.9 + (0.2 * (hash(str(current_time) + network.value) % 100) / 100)
            l1_fee_multiplier = 0.95 + (0.1 * (hash(str(current_time + 1) + network.value) % 100) / 100)
            
            updated_info = L2GasInfo(
                network=network,
                gas_price=current_info.gas_price * gas_multiplier,
                l1_data_fee=current_info.l1_data_fee * l1_fee_multiplier,
                eth_price_usd=eth_price,
                updated_at=current_time
            )
            
            # Update current data
            self.current_gas_data[network] = updated_info
            
            # Add to history
            self.gas_history[network].append(updated_info)
            
            # Trim history if needed
            if len(self.gas_history[network]) > self.config["history_size"]:
                self.gas_history[network] = self.gas_history[network][-self.config["history_size"]:]
            
            logger.debug(f"Updated gas price for {network.value}: {updated_info.gas_price} gwei")
        
        self.last_update = current_time
        logger.info("Gas prices updated for all L2 networks")
    
    def get_cheapest_network(self, operation_type: str = "arbitrage") -> Tuple[L2Network, float]:
        """
        Find the L2 network with the lowest gas cost for a given operation.
        
        Args:
            operation_type: Type of operation to get gas limit for
            
        Returns:
            Tuple of (cheapest network, estimated USD cost)
        """
        self.update_gas_prices()
        
        gas_limit = self.default_gas_limits.get(operation_type, 200000)
        
        cheapest_network = None
        lowest_cost = float('inf')
        
        for network, gas_info in self.current_gas_data.items():
            cost = gas_info.total_gas_cost_usd(gas_limit)
            
            if cost < lowest_cost:
                lowest_cost = cost
                cheapest_network = network
        
        if cheapest_network is None:
            # If for some reason no network is found, default to Arbitrum
            cheapest_network = L2Network.ARBITRUM
            lowest_cost = self.current_gas_data[cheapest_network].total_gas_cost_usd(gas_limit)
        
        logger.info(f"Cheapest network for {operation_type}: {cheapest_network.value} (${lowest_cost:.4f})")
        return cheapest_network, lowest_cost
    
    def estimate_gas_cost(self, network: L2Network, operation_type: str = "arbitrage") -> float:
        """
        Estimate gas cost in USD for a given operation on a specific network.
        
        Args:
            network: L2 network to estimate gas for
            operation_type: Type of operation to get gas limit for
            
        Returns:
            Estimated gas cost in USD
        """
        self.update_gas_prices()
        
        gas_limit = self.default_gas_limits.get(operation_type, 200000)
        gas_info = self.current_gas_data.get(network)
        
        if gas_info is None:
            logger.warning(f"No gas data available for {network.value}, using defaults")
            gas_info = L2GasInfo(
                network=network,
                gas_price=0.1,  # gwei
                l1_data_fee=0.0001,  # ETH
                eth_price_usd=3000.0,
                updated_at=time.time()
            )
        
        estimated_cost = gas_info.total_gas_cost_usd(gas_limit)
        
        # Apply safety multiplier
        adjusted_cost = estimated_cost * self.config["gas_multiplier"]
        
        logger.debug(f"Estimated gas cost for {operation_type} on {network.value}: ${adjusted_cost:.4f}")
        return adjusted_cost


class L2OpportunityEvaluator:
    """Evaluates arbitrage opportunities across Layer 2 networks."""
    
    def __init__(self, gas_tracker: L2GasTracker, config_path: Optional[str] = None):
        """
        Initialize the L2 opportunity evaluator.
        
        Args:
            gas_tracker: L2GasTracker instance
            config_path: Path to configuration file (optional)
        """
        self.gas_tracker = gas_tracker
        self.config = {
            "min_profit_threshold_usd": 5.0,  # Minimum profit in USD to consider an opportunity
            "profit_gas_ratio_min": 3.0,  # Minimum ratio of profit to gas cost
            "l2_priority": {
                L2Network.ARBITRUM.value: 1.0,
                L2Network.OPTIMISM.value: 0.9,
                L2Network.BASE.value: 0.85,
                L2Network.POLYGON.value: 0.8,
            },
            "cross_l2_opportunities": True,  # Whether to evaluate cross-L2 opportunities
            "l1_l2_opportunities": True,     # Whether to evaluate L1-L2 opportunities
        }
        
        # Load configuration if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"Loaded L2 opportunity evaluator configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load L2 opportunity configuration: {e}")
    
    def evaluate_l2_opportunity(self, opportunity: Dict[str, Any], network: L2Network) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate an arbitrage opportunity on a specific L2 network.
        
        Args:
            opportunity: Dictionary containing opportunity details
            network: L2 network to evaluate on
            
        Returns:
            Tuple of (should_execute, enhanced_opportunity)
        """
        # Create a copy of the opportunity to avoid modifying the original
        enhanced = opportunity.copy()
        
        # Add L2-specific details
        enhanced["l2_network"] = network.value
        
        # Get expected profit and gas cost
        expected_profit = opportunity.get("expected_profit", 0.0)
        gas_cost = self.gas_tracker.estimate_gas_cost(network, "arbitrage")
        
        # Calculate profit after gas
        net_profit = expected_profit - gas_cost
        profit_gas_ratio = expected_profit / gas_cost if gas_cost > 0 else 0
        
        # Add these calculations to the enhanced opportunity
        enhanced["l2_gas_cost_usd"] = gas_cost
        enhanced["l2_net_profit_usd"] = net_profit
        enhanced["profit_gas_ratio"] = profit_gas_ratio
        
        # Evaluate based on thresholds
        should_execute = (
            net_profit >= self.config["min_profit_threshold_usd"] and
            profit_gas_ratio >= self.config["profit_gas_ratio_min"]
        )
        
        if should_execute:
            logger.info(f"L2 opportunity on {network.value} approved: profit=${net_profit:.2f}, ratio={profit_gas_ratio:.2f}")
        else:
            reason = "insufficient profit" if net_profit < self.config["min_profit_threshold_usd"] else "low profit/gas ratio"
            logger.info(f"L2 opportunity on {network.value} rejected: {reason}, profit=${net_profit:.2f}, ratio={profit_gas_ratio:.2f}")
        
        return should_execute, enhanced
    
    def find_best_l2_network(self, opportunity: Dict[str, Any]) -> Tuple[Optional[L2Network], Dict[str, Any]]:
        """
        Find the best L2 network for a given opportunity.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Tuple of (best_network, enhanced_opportunity)
        """
        best_network = None
        best_net_profit = -float('inf')
        best_enhanced = None
        
        # Check each supported network
        for network in L2Network:
            should_execute, enhanced = self.evaluate_l2_opportunity(opportunity, network)
            
            if should_execute:
                # Apply network priority multiplier
                priority_multiplier = self.config["l2_priority"].get(network.value, 0.7)
                adjusted_profit = enhanced["l2_net_profit_usd"] * priority_multiplier
                
                if adjusted_profit > best_net_profit:
                    best_net_profit = adjusted_profit
                    best_network = network
                    best_enhanced = enhanced
        
        if best_network:
            logger.info(f"Best L2 network for opportunity: {best_network.value} with adjusted profit ${best_net_profit:.2f}")
            return best_network, best_enhanced
        else:
            logger.info("No suitable L2 network found for this opportunity")
            return None, opportunity


class L2Executor:
    """Executes trades on Layer 2 networks."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the L2 executor.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = {
            "wallets": {
                L2Network.ARBITRUM.value: {
                    "address": "0x0000000000000000000000000000000000000000",
                    "private_key_env": "ARBITRUM_PRIVATE_KEY",
                },
                L2Network.OPTIMISM.value: {
                    "address": "0x0000000000000000000000000000000000000000",
                    "private_key_env": "OPTIMISM_PRIVATE_KEY",
                },
                L2Network.BASE.value: {
                    "address": "0x0000000000000000000000000000000000000000",
                    "private_key_env": "BASE_PRIVATE_KEY",
                },
                L2Network.POLYGON.value: {
                    "address": "0x0000000000000000000000000000000000000000",
                    "private_key_env": "POLYGON_PRIVATE_KEY",
                },
            },
            "rpc_urls": {
                L2Network.ARBITRUM.value: "https://arb1.arbitrum.io/rpc",
                L2Network.OPTIMISM.value: "https://mainnet.optimism.io",
                L2Network.BASE.value: "https://mainnet.base.org",
                L2Network.POLYGON.value: "https://polygon-rpc.com",
            },
            "max_retries": 3,
            "retry_delay": 2,  # seconds
            "confirmation_blocks": 2,
        }
        
        # Load configuration if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"Loaded L2 executor configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load L2 executor configuration: {e}")
    
    def execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade on a Layer 2 network.
        
        In a production environment, this would connect to the appropriate
        L2 network and execute the actual transaction.
        
        Args:
            opportunity: Dictionary containing opportunity details
            
        Returns:
            Dictionary with trade results
        """
        # Get the L2 network from the opportunity
        network_str = opportunity.get("l2_network")
        if not network_str:
            logger.error("No L2 network specified in opportunity")
            return {"success": False, "error": "No L2 network specified"}
        
        # Convert string to enum
        try:
            network = L2Network(network_str)
        except ValueError:
            logger.error(f"Invalid L2 network: {network_str}")
            return {"success": False, "error": f"Invalid L2 network: {network_str}"}
        
        # In a production environment, this would:
        # 1. Connect to the appropriate L2 network RPC
        # 2. Create and sign the transaction
        # 3. Submit the transaction
        # 4. Wait for confirmation
        # 5. Return the result
        
        # For this example, we'll simulate the execution
        logger.info(f"Executing trade on {network.value} for {opportunity.get('token_pair', 'unknown')} pair")
        
        # Simulate success/failure (80% success rate)
        import random
        success = random.random() < 0.8
        
        if success:
            actual_profit = opportunity.get("l2_net_profit_usd", 0) * random.uniform(0.8, 1.2)
            gas_used = opportunity.get("l2_gas_cost_usd", 0) * random.uniform(0.9, 1.1)
            
            logger.info(f"Trade on {network.value} successful: profit=${actual_profit:.2f}")
            
            result = {
                "success": True,
                "network": network.value,
                "token_pair": opportunity.get("token_pair", ""),
                "profit": actual_profit,
                "gas_used": gas_used,
                "net_profit": actual_profit - gas_used,
                "timestamp": time.time(),
                "tx_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}"
            }
        else:
            error_reasons = ["Slippage too high", "Insufficient liquidity", "Transaction reverted", "Timeout"]
            error = random.choice(error_reasons)
            
            logger.warning(f"Trade on {network.value} failed: {error}")
            
            result = {
                "success": False,
                "network": network.value,
                "token_pair": opportunity.get("token_pair", ""),
                "error": error,
                "timestamp": time.time()
            }
        
        return result


# Usage example
if __name__ == "__main__":
    # Configure the L2 integration components
    gas_tracker = L2GasTracker()
    opportunity_evaluator = L2OpportunityEvaluator(gas_tracker)
    executor = L2Executor()
    
    # Sample opportunity (would come from the main arbitrage detection system)
    sample_opportunity = {
        "token_pair": "ETH-USDC",
        "dex": "uniswap",
        "expected_profit": 20.0,
        "expected_profit_pct": 0.02,
        "estimated_gas": 250000,
    }
    
    # Find the best L2 network for the opportunity
    best_network, enhanced_opp = opportunity_evaluator.find_best_l2_network(sample_opportunity)
    
    if best_network:
        # Execute the trade on the selected L2 network
        result = executor.execute_trade(enhanced_opp)
        print(f"Trade result: {result}")
    else:
        print("No suitable L2 network found for this opportunity") 