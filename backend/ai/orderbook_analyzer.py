"""
OrderBook Analyzer Module for ArbitrageX

This module analyzes DEX orderbooks and liquidity pools to predict:
- Price impact of trades
- Optimal trade sizes
- Liquidity shifts
- Slippage estimation
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import time
from datetime import datetime, timedelta
import requests
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OrderbookAnalyzer")

class OrderbookAnalyzer:
    """
    Analyzes DEX orderbooks and liquidity pools to predict price impacts and optimal trade sizes.
    """
    
    def __init__(self, config_path: str = "config/dex_config.json"):
        """
        Initialize the orderbook analyzer.
        
        Args:
            config_path: Path to the DEX configuration file
        """
        self.config = self._load_config(config_path)
        self.dex_adapters = {
            "uniswap": self._analyze_uniswap_pool,
            "sushiswap": self._analyze_sushiswap_pool,
            "curve": self._analyze_curve_pool,
            "balancer": self._analyze_balancer_pool,
        }
        
    def _load_config(self, config_path: str) -> Dict:
        """Load DEX configuration from file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Config file not found at {config_path}, using default values")
                return {
                    "default_slippage": 0.5,  # 0.5% default slippage
                    "max_price_impact": 2.0,  # 2% maximum price impact
                    "min_liquidity_threshold": 100000,  # $100k minimum liquidity
                    "api_endpoints": {
                        "uniswap": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
                        "sushiswap": "https://api.thegraph.com/subgraphs/name/sushi-v2/sushiswap-ethereum",
                        "curve": "https://api.curve.fi/api/getPools/ethereum/main",
                        "balancer": "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2"
                    }
                }
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def analyze_pool(self, 
                    dex: str, 
                    pool_address: str, 
                    token_in: str, 
                    token_out: str, 
                    amount_in: float) -> Dict:
        """
        Analyze a specific liquidity pool and predict price impact.
        
        Args:
            dex: DEX name (uniswap, sushiswap, etc.)
            pool_address: Address of the liquidity pool
            token_in: Address or symbol of the input token
            token_out: Address or symbol of the output token
            amount_in: Amount of input token to trade
            
        Returns:
            Dictionary with price impact analysis
        """
        logger.info(f"Analyzing {dex} pool {pool_address} for {token_in} -> {token_out} trade")
        
        if dex.lower() not in self.dex_adapters:
            logger.error(f"Unsupported DEX: {dex}")
            return {
                "error": f"Unsupported DEX: {dex}",
                "supported_dexes": list(self.dex_adapters.keys())
            }
        
        try:
            # Call the appropriate DEX-specific analyzer
            return self.dex_adapters[dex.lower()](pool_address, token_in, token_out, amount_in)
        except Exception as e:
            logger.error(f"Error analyzing {dex} pool: {e}")
            return {
                "error": str(e),
                "dex": dex,
                "pool_address": pool_address
            }
    
    def _analyze_uniswap_pool(self, 
                             pool_address: str, 
                             token_in: str, 
                             token_out: str, 
                             amount_in: float) -> Dict:
        """Analyze Uniswap V3 pool"""
        # In a real implementation, this would query the Uniswap V3 subgraph or contract
        # For this simplified version, we'll return mock data
        
        # Simulate API call delay
        time.sleep(0.1)
        
        # Mock pool data
        pool_data = {
            "liquidity": 1000000,  # Mock liquidity value
            "sqrtPriceX96": "1234567890123456789",
            "tick": -74652,
            "feeTier": 3000,  # 0.3%
            "token0": {
                "symbol": token_in if token_in < token_out else token_out,
                "decimals": 18
            },
            "token1": {
                "symbol": token_out if token_in < token_out else token_in,
                "decimals": 18
            }
        }
        
        # Calculate mock price impact based on amount_in and pool liquidity
        price_impact = min(amount_in / pool_data["liquidity"] * 100, 10)  # Cap at 10%
        
        # Calculate expected output amount (simplified)
        output_amount = amount_in * (1 - price_impact/100) * 0.997  # 0.3% fee
        
        return {
            "dex": "uniswap",
            "pool_address": pool_address,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "expected_output": output_amount,
            "price_impact_percent": price_impact,
            "fee_percent": 0.3,
            "liquidity": pool_data["liquidity"],
            "is_stable_pool": False,
            "recommended_max_trade": pool_data["liquidity"] * 0.02,  # 2% of liquidity
            "timestamp": int(time.time())
        }
    
    def _analyze_sushiswap_pool(self, 
                               pool_address: str, 
                               token_in: str, 
                               token_out: str, 
                               amount_in: float) -> Dict:
        """Analyze SushiSwap pool"""
        # Similar to Uniswap but with SushiSwap-specific logic
        # For simplicity, we'll use similar mock data with slight differences
        
        # Simulate API call delay
        time.sleep(0.1)
        
        # Mock pool data with slightly different values
        pool_data = {
            "liquidity": 800000,  # Less liquidity than Uniswap
            "reserve0": 400000,
            "reserve1": 400000,
            "fee": 0.003  # 0.3%
        }
        
        # Calculate mock price impact
        price_impact = min(amount_in / pool_data["liquidity"] * 120, 15)  # Higher impact than Uniswap
        
        # Calculate expected output amount (simplified)
        output_amount = amount_in * (1 - price_impact/100) * 0.997  # 0.3% fee
        
        return {
            "dex": "sushiswap",
            "pool_address": pool_address,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "expected_output": output_amount,
            "price_impact_percent": price_impact,
            "fee_percent": 0.3,
            "liquidity": pool_data["liquidity"],
            "is_stable_pool": False,
            "recommended_max_trade": pool_data["liquidity"] * 0.015,  # 1.5% of liquidity
            "timestamp": int(time.time())
        }
    
    def _analyze_curve_pool(self, 
                           pool_address: str, 
                           token_in: str, 
                           token_out: str, 
                           amount_in: float) -> Dict:
        """Analyze Curve pool"""
        # Curve pools are typically stable pools with lower price impact
        
        # Simulate API call delay
        time.sleep(0.1)
        
        # Mock pool data for a stable pool
        pool_data = {
            "liquidity": 5000000,  # Higher liquidity for stable pools
            "A": 100,  # Amplification parameter
            "fee": 0.0004,  # 0.04% fee
            "is_stable": True
        }
        
        # Calculate mock price impact (lower for stable pools)
        price_impact = min(amount_in / pool_data["liquidity"] * 20, 5)  # Lower impact for stable pools
        
        # Calculate expected output amount (simplified)
        output_amount = amount_in * (1 - price_impact/100) * 0.9996  # 0.04% fee
        
        return {
            "dex": "curve",
            "pool_address": pool_address,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "expected_output": output_amount,
            "price_impact_percent": price_impact,
            "fee_percent": 0.04,
            "liquidity": pool_data["liquidity"],
            "is_stable_pool": True,
            "recommended_max_trade": pool_data["liquidity"] * 0.05,  # 5% of liquidity for stable pools
            "timestamp": int(time.time())
        }
    
    def _analyze_balancer_pool(self, 
                              pool_address: str, 
                              token_in: str, 
                              token_out: str, 
                              amount_in: float) -> Dict:
        """Analyze Balancer pool"""
        # Balancer pools can have multiple tokens and custom weights
        
        # Simulate API call delay
        time.sleep(0.1)
        
        # Mock pool data for a weighted pool
        pool_data = {
            "liquidity": 1200000,
            "tokens": [
                {"symbol": "WETH", "weight": 0.8, "balance": 500},
                {"symbol": "DAI", "weight": 0.2, "balance": 1000000}
            ],
            "swapFee": 0.002  # 0.2% fee
        }
        
        # Calculate mock price impact
        price_impact = min(amount_in / pool_data["liquidity"] * 90, 8)
        
        # Calculate expected output amount (simplified)
        output_amount = amount_in * (1 - price_impact/100) * 0.998  # 0.2% fee
        
        return {
            "dex": "balancer",
            "pool_address": pool_address,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "expected_output": output_amount,
            "price_impact_percent": price_impact,
            "fee_percent": 0.2,
            "liquidity": pool_data["liquidity"],
            "is_stable_pool": False,
            "recommended_max_trade": pool_data["liquidity"] * 0.025,  # 2.5% of liquidity
            "timestamp": int(time.time())
        }
    
    def compare_pools(self, 
                     token_in: str, 
                     token_out: str, 
                     amount_in: float, 
                     dexes: List[str] = None) -> List[Dict]:
        """
        Compare multiple pools across different DEXes for the same token pair.
        
        Args:
            token_in: Input token symbol or address
            token_out: Output token symbol or address
            amount_in: Amount of input token to trade
            dexes: List of DEXes to compare (default: all supported DEXes)
            
        Returns:
            List of pool analyses sorted by expected output (best first)
        """
        if dexes is None:
            dexes = list(self.dex_adapters.keys())
        
        logger.info(f"Comparing pools for {token_in} -> {token_out} trade across {dexes}")
        
        # Mock pool addresses for each DEX
        pool_addresses = {
            "uniswap": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",  # ETH-USDC
            "sushiswap": "0x397ff1542f962076d0bfe58ea045ffa2d347aca0",
            "curve": "0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7",  # 3pool
            "balancer": "0x5c6ee304399dbdb9c8ef030ab642b10820db8f56"
        }
        
        results = []
        
        for dex in dexes:
            if dex in pool_addresses:
                try:
                    pool_analysis = self.analyze_pool(
                        dex=dex,
                        pool_address=pool_addresses[dex],
                        token_in=token_in,
                        token_out=token_out,
                        amount_in=amount_in
                    )
                    results.append(pool_analysis)
                except Exception as e:
                    logger.error(f"Error analyzing {dex} pool: {e}")
        
        # Sort by expected output (descending)
        results.sort(key=lambda x: x.get("expected_output", 0), reverse=True)
        
        return results
    
    def predict_price_impact(self, 
                            dex: str, 
                            pool_address: str, 
                            token_in: str, 
                            token_out: str, 
                            amounts: List[float]) -> Dict:
        """
        Predict price impact for different trade sizes.
        
        Args:
            dex: DEX name
            pool_address: Pool address
            token_in: Input token
            token_out: Output token
            amounts: List of input amounts to analyze
            
        Returns:
            Dictionary with price impact predictions for each amount
        """
        logger.info(f"Predicting price impact for {dex} pool {pool_address}")
        
        results = {}
        
        for amount in amounts:
            analysis = self.analyze_pool(dex, pool_address, token_in, token_out, amount)
            results[str(amount)] = {
                "price_impact_percent": analysis.get("price_impact_percent", 0),
                "expected_output": analysis.get("expected_output", 0)
            }
        
        return {
            "dex": dex,
            "pool_address": pool_address,
            "token_in": token_in,
            "token_out": token_out,
            "predictions": results,
            "timestamp": int(time.time())
        }
    
    def find_optimal_trade_size(self, 
                               dex: str, 
                               pool_address: str, 
                               token_in: str, 
                               token_out: str, 
                               max_price_impact: float = None) -> Dict:
        """
        Find the optimal trade size that maximizes output while keeping price impact below threshold.
        
        Args:
            dex: DEX name
            pool_address: Pool address
            token_in: Input token
            token_out: Output token
            max_price_impact: Maximum acceptable price impact (%)
            
        Returns:
            Dictionary with optimal trade size and expected output
        """
        if max_price_impact is None:
            max_price_impact = self.config.get("max_price_impact", 2.0)
        
        logger.info(f"Finding optimal trade size for {dex} pool with max impact {max_price_impact}%")
        
        # Get pool analysis to determine liquidity
        initial_analysis = self.analyze_pool(dex, pool_address, token_in, token_out, 1.0)
        liquidity = initial_analysis.get("liquidity", 0)
        
        if liquidity <= 0:
            return {
                "error": "Could not determine pool liquidity",
                "dex": dex,
                "pool_address": pool_address
            }
        
        # Start with a conservative estimate
        estimated_optimal = liquidity * (max_price_impact / 100) / 2
        
        # Test a range around the estimate
        test_amounts = [
            estimated_optimal * 0.5,
            estimated_optimal * 0.75,
            estimated_optimal,
            estimated_optimal * 1.25,
            estimated_optimal * 1.5
        ]
        
        # Analyze each test amount
        results = []
        for amount in test_amounts:
            analysis = self.analyze_pool(dex, pool_address, token_in, token_out, amount)
            impact = analysis.get("price_impact_percent", 100)
            
            if impact <= max_price_impact:
                results.append({
                    "amount_in": amount,
                    "expected_output": analysis.get("expected_output", 0),
                    "price_impact_percent": impact
                })
        
        if not results:
            return {
                "error": f"Could not find a trade size with impact below {max_price_impact}%",
                "dex": dex,
                "pool_address": pool_address,
                "max_tested_amount": max(test_amounts)
            }
        
        # Find the amount with the highest expected output
        optimal = max(results, key=lambda x: x["expected_output"])
        
        return {
            "dex": dex,
            "pool_address": pool_address,
            "token_in": token_in,
            "token_out": token_out,
            "optimal_amount_in": optimal["amount_in"],
            "expected_output": optimal["expected_output"],
            "price_impact_percent": optimal["price_impact_percent"],
            "max_price_impact_threshold": max_price_impact,
            "timestamp": int(time.time())
        }

# Example usage
if __name__ == "__main__":
    analyzer = OrderbookAnalyzer()
    
    # Analyze a single pool
    result = analyzer.analyze_pool(
        dex="uniswap",
        pool_address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        token_in="ETH",
        token_out="USDC",
        amount_in=10.0
    )
    print(f"Single pool analysis: {json.dumps(result, indent=2)}")
    
    # Compare multiple pools
    comparison = analyzer.compare_pools(
        token_in="ETH",
        token_out="USDC",
        amount_in=10.0,
        dexes=["uniswap", "sushiswap", "curve"]
    )
    print(f"Pool comparison: {json.dumps(comparison, indent=2)}")
    
    # Find optimal trade size
    optimal = analyzer.find_optimal_trade_size(
        dex="uniswap",
        pool_address="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
        token_in="ETH",
        token_out="USDC",
        max_price_impact=1.0
    )
    print(f"Optimal trade size: {json.dumps(optimal, indent=2)}")
