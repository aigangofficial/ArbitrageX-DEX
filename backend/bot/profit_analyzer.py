"""
Profit Analyzer Module for ArbitrageX

This module is responsible for analyzing potential arbitrage opportunities
to determine their profitability, taking into account factors such as:
- Gas costs
- Slippage
- Exchange fees
- Price impact
- Risk factors
"""

import logging
import json
import time
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import random
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("profit_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ProfitAnalyzer")

class ProfitAnalyzer:
    """
    Analyzes arbitrage opportunities to determine profitability.
    Takes into account gas costs, slippage, fees, and other factors.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the profit analyzer.
        
        Args:
            config: Bot configuration dictionary
        """
        logger.info("Initializing Profit Analyzer")
        self.config = config
        
        # Load exchange fee data
        self.exchange_fees = self._load_exchange_fees()
        
        # Load historical slippage data
        self.historical_slippage = self._load_historical_slippage()
        
        # Minimum profit threshold (in ETH)
        self.min_profit_threshold = config.get("execution", {}).get("min_profit_threshold", 0.01)
        
        # Maximum acceptable slippage (in percentage)
        self.max_slippage = config.get("execution", {}).get("max_slippage", 1.0)
        
        logger.info(f"Profit Analyzer initialized with min profit threshold: {self.min_profit_threshold} ETH")
    
    def _load_exchange_fees(self) -> Dict:
        """Load exchange fee data"""
        try:
            fee_data_path = "backend/bot/data/exchange_fees.json"
            with open(fee_data_path, 'r') as f:
                exchange_fees = json.load(f)
            logger.info(f"Loaded exchange fee data from {fee_data_path}")
            return exchange_fees
        except Exception as e:
            logger.warning(f"Error loading exchange fee data: {e}")
            # Return default fee data
            return {
                "uniswap_v2": 0.003,  # 0.3%
                "uniswap_v3": 0.003,  # 0.3% (can vary by pool)
                "sushiswap": 0.003,   # 0.3%
                "curve": 0.0004,      # 0.04%
                "balancer": 0.002,    # 0.2%
                "quickswap": 0.003,   # 0.3%
                "pancakeswap": 0.0025, # 0.25%
                "biswap": 0.001,      # 0.1%
                "velodrome": 0.002,   # 0.2%
                "default": 0.003      # Default fee if not specified
            }
    
    def _load_historical_slippage(self) -> Dict:
        """Load historical slippage data"""
        try:
            slippage_data_path = "backend/bot/data/historical_slippage.json"
            with open(slippage_data_path, 'r') as f:
                historical_slippage = json.load(f)
            logger.info(f"Loaded historical slippage data from {slippage_data_path}")
            return historical_slippage
        except Exception as e:
            logger.warning(f"Error loading historical slippage data: {e}")
            # Return default slippage data
            return {
                "ethereum": {
                    "uniswap_v2": {"mean": 0.2, "std_dev": 0.1},
                    "uniswap_v3": {"mean": 0.1, "std_dev": 0.05},
                    "sushiswap": {"mean": 0.25, "std_dev": 0.12},
                    "curve": {"mean": 0.05, "std_dev": 0.02}
                },
                "arbitrum": {
                    "uniswap_v3": {"mean": 0.15, "std_dev": 0.08},
                    "sushiswap": {"mean": 0.3, "std_dev": 0.15},
                    "balancer": {"mean": 0.2, "std_dev": 0.1}
                },
                "polygon": {
                    "quickswap": {"mean": 0.3, "std_dev": 0.15},
                    "sushiswap": {"mean": 0.35, "std_dev": 0.18},
                    "uniswap_v3": {"mean": 0.2, "std_dev": 0.1}
                },
                "bsc": {
                    "pancakeswap": {"mean": 0.25, "std_dev": 0.12},
                    "biswap": {"mean": 0.2, "std_dev": 0.1}
                },
                "default": {"mean": 0.3, "std_dev": 0.15}
            }
    
    def analyze_opportunity(self, opportunity: Dict) -> Dict:
        """
        Analyze an arbitrage opportunity to determine profitability.
        
        Args:
            opportunity: Dictionary containing arbitrage opportunity details
            
        Returns:
            Dictionary with profitability analysis results
        """
        logger.info(f"Analyzing opportunity {opportunity['id']}")
        
        # Extract opportunity details
        network = opportunity["network"]
        token_a = opportunity["token_a"]
        token_b = opportunity["token_b"]
        buy_dex = opportunity["buy_dex"]
        sell_dex = opportunity["sell_dex"]
        buy_price = opportunity["buy_price"]
        sell_price = opportunity["sell_price"]
        trade_amount = opportunity["trade_amount"]
        estimated_gas_cost = opportunity["estimated_gas_cost"]
        
        # Calculate exchange fees
        buy_fee = self._get_exchange_fee(buy_dex)
        sell_fee = self._get_exchange_fee(sell_dex)
        
        # Calculate expected slippage
        buy_slippage = self._estimate_slippage(network, buy_dex, token_a, token_b, trade_amount)
        sell_slippage = self._estimate_slippage(network, sell_dex, token_a, token_b, trade_amount)
        
        # Calculate total slippage
        total_slippage_pct = buy_slippage + sell_slippage
        
        # Check if slippage is acceptable
        if total_slippage_pct > self.max_slippage:
            logger.warning(f"Estimated slippage ({total_slippage_pct:.2f}%) exceeds maximum allowed ({self.max_slippage}%)")
            return {
                "is_profitable": False,
                "reason": f"Estimated slippage ({total_slippage_pct:.2f}%) exceeds maximum allowed ({self.max_slippage}%)",
                "estimated_slippage_pct": total_slippage_pct,
                "buy_slippage_pct": buy_slippage,
                "sell_slippage_pct": sell_slippage,
                "buy_fee_pct": buy_fee * 100,
                "sell_fee_pct": sell_fee * 100
            }
        
        # Calculate effective prices after slippage
        effective_buy_price = buy_price * (1 + buy_slippage / 100)
        effective_sell_price = sell_price * (1 - sell_slippage / 100)
        
        # Calculate amount received after buy (accounting for fees)
        amount_bought = (trade_amount / effective_buy_price) * (1 - buy_fee)
        
        # Calculate amount received after sell (accounting for fees)
        amount_received = amount_bought * effective_sell_price * (1 - sell_fee)
        
        # Calculate gross profit
        gross_profit = amount_received - trade_amount
        
        # Calculate net profit after gas
        net_profit = gross_profit - estimated_gas_cost
        
        # Calculate ROI
        roi = (net_profit / trade_amount) * 100 if trade_amount > 0 else 0
        
        # Determine if profitable
        is_profitable = net_profit >= self.min_profit_threshold
        
        # Calculate risk score (0-100, higher is riskier)
        risk_score = self._calculate_risk_score(
            network, buy_dex, sell_dex, total_slippage_pct, roi, net_profit
        )
        
        # Calculate confidence score (0-1, higher is more confident)
        confidence_score = 1 - (risk_score / 100)
        
        # Create result dictionary
        result = {
            "is_profitable": is_profitable,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "roi_pct": roi,
            "estimated_slippage_pct": total_slippage_pct,
            "buy_slippage_pct": buy_slippage,
            "sell_slippage_pct": sell_slippage,
            "buy_fee_pct": buy_fee * 100,
            "sell_fee_pct": sell_fee * 100,
            "effective_buy_price": effective_buy_price,
            "effective_sell_price": effective_sell_price,
            "amount_bought": amount_bought,
            "amount_received": amount_received,
            "risk_score": risk_score,
            "confidence_score": confidence_score
        }
        
        if not is_profitable:
            result["reason"] = f"Net profit ({net_profit:.6f} ETH) below threshold ({self.min_profit_threshold} ETH)"
        
        logger.info(f"Opportunity analysis result: profitable={is_profitable}, "
                   f"net_profit={net_profit:.6f} ETH, roi={roi:.2f}%")
        
        return result
    
    def _get_exchange_fee(self, exchange: str) -> float:
        """Get the fee rate for a specific exchange"""
        return self.exchange_fees.get(exchange, self.exchange_fees.get("default", 0.003))
    
    def _estimate_slippage(self, network: str, exchange: str, token_a: str, token_b: str, amount: float) -> float:
        """
        Estimate slippage for a trade based on historical data and trade size.
        
        Returns:
            Estimated slippage percentage
        """
        # Get base slippage statistics for this network and exchange
        network_data = self.historical_slippage.get(network, self.historical_slippage.get("default"))
        exchange_data = network_data.get(exchange, network_data.get("default", {"mean": 0.3, "std_dev": 0.15}))
        
        mean_slippage = exchange_data["mean"]
        std_dev = exchange_data["std_dev"]
        
        # Adjust for trade size (larger trades have more slippage)
        # This is a simplified model - in reality, this would be based on liquidity data
        size_factor = 1.0
        if amount <= 0.1:  # Small trade
            size_factor = 0.5
        elif amount <= 1.0:  # Medium trade
            size_factor = 1.0
        elif amount <= 5.0:  # Large trade
            size_factor = 2.0
        else:  # Very large trade
            size_factor = 3.0
        
        # Add some randomness to simulate real-world variation
        # Using a normal distribution centered on the mean slippage
        random_factor = random.normalvariate(mean_slippage, std_dev)
        
        # Calculate final slippage estimate
        estimated_slippage = random_factor * size_factor
        
        # Ensure slippage is not negative
        estimated_slippage = max(0, estimated_slippage)
        
        return estimated_slippage
    
    def _calculate_risk_score(self, network: str, buy_dex: str, sell_dex: str, 
                             slippage: float, roi: float, profit: float) -> float:
        """
        Calculate a risk score for the arbitrage opportunity.
        
        Returns:
            Risk score (0-100, higher is riskier)
        """
        # Base risk score
        risk_score = 50
        
        # Adjust for network (some networks are riskier than others)
        network_risk = {
            "ethereum": -5,  # Less risky (more established)
            "arbitrum": 0,
            "polygon": 5,
            "optimism": 0,
            "bsc": 10  # More risky
        }
        risk_score += network_risk.get(network, 0)
        
        # Adjust for DEXes (some DEXes are riskier than others)
        dex_risk = {
            "uniswap_v3": -10,  # Less risky
            "uniswap_v2": -5,
            "sushiswap": 0,
            "curve": -8,
            "balancer": 0,
            "quickswap": 5,
            "pancakeswap": 8,
            "biswap": 10,
            "velodrome": 5
        }
        risk_score += dex_risk.get(buy_dex, 0) / 2
        risk_score += dex_risk.get(sell_dex, 0) / 2
        
        # Adjust for slippage (higher slippage = higher risk)
        if slippage < 0.1:
            risk_score -= 10
        elif slippage < 0.3:
            risk_score -= 5
        elif slippage > 0.8:
            risk_score += 15
        elif slippage > 0.5:
            risk_score += 10
        
        # Adjust for ROI (higher ROI often means higher risk)
        if roi > 5:
            risk_score += 10
        elif roi > 2:
            risk_score += 5
        elif roi < 0.5:
            risk_score -= 5
        
        # Adjust for profit (very small profits might not be worth the risk)
        if profit < 0.001:
            risk_score += 15
        elif profit < 0.005:
            risk_score += 5
        elif profit > 0.05:
            risk_score -= 10
        elif profit > 0.02:
            risk_score -= 5
        
        # Ensure risk score is within bounds
        risk_score = max(0, min(100, risk_score))
        
        return risk_score
    
    def estimate_optimal_trade_size(self, opportunity: Dict) -> float:
        """
        Estimate the optimal trade size for an arbitrage opportunity.
        
        Args:
            opportunity: Dictionary containing arbitrage opportunity details
            
        Returns:
            Optimal trade size in ETH
        """
        # Extract opportunity details
        network = opportunity["network"]
        buy_dex = opportunity["buy_dex"]
        sell_dex = opportunity["sell_dex"]
        buy_price = opportunity["buy_price"]
        sell_price = opportunity["sell_price"]
        
        # Get maximum trade size from config
        max_trade_size = self.config.get("risk_management", {}).get("max_trade_size", 10.0)
        
        # Calculate price difference percentage
        price_diff_pct = ((sell_price - buy_price) / buy_price) * 100
        
        # Base optimal size on price difference
        # Larger price differences can support larger trades
        if price_diff_pct > 2.0:
            base_size = max_trade_size * 0.8
        elif price_diff_pct > 1.0:
            base_size = max_trade_size * 0.5
        elif price_diff_pct > 0.5:
            base_size = max_trade_size * 0.3
        else:
            base_size = max_trade_size * 0.1
        
        # Adjust for network (some networks can handle larger trades)
        network_factor = {
            "ethereum": 1.0,
            "arbitrum": 0.8,
            "polygon": 0.7,
            "optimism": 0.6,
            "bsc": 0.9
        }
        network_multiplier = network_factor.get(network, 0.5)
        
        # Calculate optimal size
        optimal_size = base_size * network_multiplier
        
        # Ensure within bounds
        optimal_size = min(optimal_size, max_trade_size)
        
        logger.info(f"Estimated optimal trade size for opportunity {opportunity['id']}: {optimal_size:.4f} ETH")
        
        return optimal_size

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        "execution": {
            "min_profit_threshold": 0.005,  # 0.005 ETH
            "max_slippage": 1.0  # 1.0%
        },
        "risk_management": {
            "max_trade_size": 5.0  # 5.0 ETH
        }
    }
    
    analyzer = ProfitAnalyzer(config)
    
    # Example opportunity
    opportunity = {
        "id": "ARB-ethereum-123",
        "network": "ethereum",
        "token_a": "ETH",
        "token_b": "USDC",
        "buy_dex": "uniswap_v2",
        "sell_dex": "sushiswap",
        "buy_price": 3500.0,
        "sell_price": 3520.0,
        "price_diff_pct": 0.57,
        "trade_amount": 1.0,
        "estimated_gas_cost": 0.01,
        "potential_profit": 0.0057,
        "buy_router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "sell_router": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        "timestamp": datetime.now().isoformat()
    }
    
    # Analyze opportunity
    result = analyzer.analyze_opportunity(opportunity)
    
    # Print results
    print(f"Opportunity analysis result: profitable={result['is_profitable']}")
    print(f"Net profit: {result['net_profit']:.6f} ETH")
    print(f"ROI: {result['roi_pct']:.2f}%")
    print(f"Estimated slippage: {result['estimated_slippage_pct']:.2f}%")
    print(f"Risk score: {result['risk_score']:.1f}/100")
    print(f"Confidence score: {result['confidence_score']:.2f}")
    
    if not result['is_profitable']:
        print(f"Reason: {result.get('reason', 'Unknown')}")
    
    # Estimate optimal trade size
    optimal_size = analyzer.estimate_optimal_trade_size(opportunity)
    print(f"\nOptimal trade size: {optimal_size:.4f} ETH")
