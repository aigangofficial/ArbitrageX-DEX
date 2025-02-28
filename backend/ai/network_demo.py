"""
Network Adaptation Demo for ArbitrageX AI

This module demonstrates how the AI model adapts to different network conditions
and optimizes arbitrage strategies accordingly.
"""

from strategy_optimizer_demo import StrategyOptimizer
import time
import random
from datetime import datetime
from typing import Dict, List

class NetworkAdaptation:
    """
    Demonstrates how the AI adapts to different network conditions.
    """
    
    def __init__(self):
        """Initialize the network adaptation module."""
        self.optimizer = StrategyOptimizer()
        self.networks = {
            "ethereum": {
                "name": "Ethereum Mainnet",
                "gas_price_gwei": 20,
                "block_time_sec": 12,
                "congestion_factor": 1.0,
                "liquidity_depth": 1.0,
                "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap
            },
            "arbitrum": {
                "name": "Arbitrum One",
                "gas_price_gwei": 0.1,
                "block_time_sec": 0.25,
                "congestion_factor": 0.2,
                "liquidity_depth": 0.7,
                "router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"  # SushiSwap on Arbitrum
            },
            "polygon": {
                "name": "Polygon PoS",
                "gas_price_gwei": 50,
                "block_time_sec": 2,
                "congestion_factor": 0.5,
                "liquidity_depth": 0.8,
                "router": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"  # QuickSwap
            },
            "bsc": {
                "name": "BNB Smart Chain",
                "gas_price_gwei": 5,
                "block_time_sec": 3,
                "congestion_factor": 0.3,
                "liquidity_depth": 0.9,
                "router": "0x10ED43C718714eb63d5aA57B78B54704E256024E"  # PancakeSwap
            }
        }
        
        # Standard opportunity template
        self.base_opportunity = {
            "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            "token_out": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "amount": 1000000000000000000,  # 1 ETH
        }
    
    def simulate_network_conditions(self, network_id: str, time_of_day: int) -> Dict:
        """
        Simulate network conditions based on network and time of day.
        
        Args:
            network_id: Network identifier (ethereum, arbitrum, polygon, bsc)
            time_of_day: Hour of day (0-23)
            
        Returns:
            Dictionary with network conditions
        """
        network = self.networks[network_id]
        
        # Time-based congestion patterns
        peak_hours = [9, 10, 11, 14, 15, 16, 17]  # UTC
        off_peak_multiplier = 0.7
        time_multiplier = 1.0 if time_of_day in peak_hours else off_peak_multiplier
        
        # Randomize conditions slightly
        gas_variance = random.uniform(0.8, 1.2)
        congestion_variance = random.uniform(0.9, 1.1)
        
        conditions = {
            "network_name": network["name"],
            "gas_price_gwei": network["gas_price_gwei"] * gas_variance * time_multiplier,
            "block_time_sec": network["block_time_sec"],
            "congestion_level": network["congestion_factor"] * congestion_variance * time_multiplier,
            "liquidity_depth": network["liquidity_depth"],
            "time_of_day": time_of_day,
            "is_peak_hour": time_of_day in peak_hours
        }
        
        return conditions
    
    def adapt_strategy(self, network_id: str, time_of_day: int) -> Dict:
        """
        Adapt arbitrage strategy based on network conditions.
        
        Args:
            network_id: Network identifier
            time_of_day: Hour of day (0-23)
            
        Returns:
            Dictionary with strategy results
        """
        network = self.networks[network_id]
        conditions = self.simulate_network_conditions(network_id, time_of_day)
        
        # Adapt opportunity based on network conditions
        opportunity = self.base_opportunity.copy()
        opportunity["router"] = network["router"]
        
        # Adjust amount based on liquidity depth
        opportunity["amount"] = int(opportunity["amount"] * conditions["liquidity_depth"])
        
        # Get prediction from AI model
        prediction = self.optimizer.predict_opportunity(opportunity)
        
        # Calculate network-specific metrics
        gas_cost_usd = prediction["gas_cost_usd"] * (conditions["gas_price_gwei"] / 20)
        execution_time_ms = prediction["execution_time_ms"] * conditions["congestion_level"]
        
        # Adjust profit expectations based on network conditions
        adjusted_profit = prediction["estimated_profit_usd"] * conditions["liquidity_depth"]
        adjusted_net_profit = adjusted_profit - gas_cost_usd
        
        # Determine if profitable with network-specific conditions
        is_profitable = adjusted_net_profit > 0 and prediction["confidence"] > 0.7
        
        result = {
            "network": conditions["network_name"],
            "time_of_day": time_of_day,
            "is_peak_hour": conditions["is_peak_hour"],
            "gas_price_gwei": round(conditions["gas_price_gwei"], 2),
            "congestion_level": round(conditions["congestion_level"], 2),
            "execution_time_ms": round(execution_time_ms, 2),
            "estimated_profit_usd": round(adjusted_profit, 2),
            "gas_cost_usd": round(gas_cost_usd, 2),
            "net_profit_usd": round(adjusted_net_profit, 2),
            "confidence": round(prediction["confidence"], 4),
            "is_profitable": is_profitable,
            "token_pair": prediction["token_pair"]
        }
        
        return result

def demonstrate_network_adaptation():
    """Run a demonstration of network adaptation capabilities"""
    adapter = NetworkAdaptation()
    
    # Test times (peak and off-peak)
    test_times = [3, 10, 15, 21]  # 3am, 10am, 3pm, 9pm UTC
    
    print("\n===== ARBITRAGEX NETWORK ADAPTATION DEMONSTRATION =====\n")
    print("This demonstration shows how the AI model adapts to different networks")
    print("and time-based patterns to optimize arbitrage strategies.\n")
    
    # Compare networks at different times
    for time_of_day in test_times:
        print(f"\n⏰ TIME OF DAY: {time_of_day}:00 UTC {'(PEAK TRADING HOURS)' if time_of_day in [9, 10, 11, 14, 15, 16, 17] else '(OFF-PEAK HOURS)'}")
        print("-" * 80)
        print(f"{'NETWORK':<15} {'GAS (GWEI)':<12} {'CONGESTION':<12} {'EXEC TIME':<12} {'PROFIT':<10} {'GAS COST':<10} {'NET PROFIT':<12} {'PROFITABLE':<12}")
        print("-" * 80)
        
        results = []
        for network_id in ["ethereum", "arbitrum", "polygon", "bsc"]:
            result = adapter.adapt_strategy(network_id, time_of_day)
            results.append(result)
            
            profit_status = "✅ YES" if result["is_profitable"] else "❌ NO"
            print(f"{result['network']:<15} {result['gas_price_gwei']:<12.2f} {result['congestion_level']:<12.2f} {result['execution_time_ms']:<12.2f} ${result['estimated_profit_usd']:<9.2f} ${result['gas_cost_usd']:<9.2f} ${result['net_profit_usd']:<11.2f} {profit_status:<12}")
        
        # Find best network for this time
        best_network = max(results, key=lambda x: x["net_profit_usd"] if x["is_profitable"] else -1000)
        if best_network["is_profitable"]:
            print(f"\n🏆 BEST NETWORK AT {time_of_day}:00 UTC: {best_network['network']} (${best_network['net_profit_usd']:.2f} profit)")
        else:
            print(f"\n⚠️ NO PROFITABLE OPPORTUNITIES AT {time_of_day}:00 UTC")
    
    print("\n===== AI NETWORK ADAPTATION SUMMARY =====\n")
    print("The AI model demonstrated the following capabilities:")
    print("1. Adapting to different gas prices across networks")
    print("2. Accounting for network congestion and block times")
    print("3. Adjusting for liquidity depth variations between chains")
    print("4. Recognizing time-based patterns in trading activity")
    print("5. Selecting the optimal network for execution at different times")
    print("\nThis capability allows ArbitrageX to dynamically shift between networks")
    print("to maximize profitability and minimize execution risks.")

if __name__ == "__main__":
    demonstrate_network_adaptation() 