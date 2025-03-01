#!/usr/bin/env python3
"""
Command-line interface for the ArbitrageX Trade Analyzer.
This script allows running the trade analyzer with various options.
"""

import argparse
import os
import sys
import logging
import json
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('TradeAnalyzerRunner')

def demonstrate_trade_analysis(testnet=False, days=30, visualize=False):
    """
    Demonstrate the trade analysis functionality using the existing TradeAnalyzer class.
    
    Args:
        testnet (bool): Whether to run in testnet mode
        days (int): Number of days of data to analyze
        visualize (bool): Whether to visualize the results
    """
    try:
        from trade_analyzer import TradeAnalyzer
    except ImportError:
        logger.error("Could not import TradeAnalyzer. Make sure you're in the correct directory.")
        sys.exit(1)
    
    # Create a trade analyzer
    analyzer = TradeAnalyzer()
    
    # Generate example trade data for demonstration
    example_trades = generate_example_trades(days=days)
    
    print("\n===== MARKET CONDITIONS ANALYSIS =====\n")
    
    # Process each trade
    for trade in example_trades:
        analysis = analyzer.analyze_trade(trade)
    
    # Get best trading opportunities
    opportunities = analyzer.get_best_trading_opportunities()
    print(f"Best Trading Opportunities: {len(opportunities)} found")
    
    for i, opportunity in enumerate(opportunities[:3]):  # Show top 3
        print(f"\nOpportunity {i+1}:")
        print(f"  Token Pair: {opportunity.get('token_pair', 'Unknown')}")
        print(f"  Expected Profit: ${opportunity.get('expected_profit', 0):.2f}")
        print(f"  Success Rate: {opportunity.get('success_rate', 0):.2f}")
        print(f"  Best Buy DEX: {opportunity.get('best_buy_dex', 'Unknown')}")
        print(f"  Best Sell DEX: {opportunity.get('best_sell_dex', 'Unknown')}")
    
    # Get time-based patterns
    time_patterns = analyzer.get_time_based_patterns()
    
    print("\n===== TIME-BASED PATTERNS =====\n")
    
    print("Best Hours (UTC):")
    for hour in time_patterns.get('best_hours', [])[:3]:
        print(f"  - Hour {hour}")
    
    print("\nBest Days:")
    for day in time_patterns.get('best_days', [])[:3]:
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        print(f"  - {day_names[day]}")
    
    # Visualize if requested
    if visualize:
        print("\n===== GENERATING VISUALIZATIONS =====\n")
        
        # Visualize time patterns
        analyzer.visualize_time_patterns("backend/ai/data/time_patterns.png")
        print("Time patterns visualization saved to backend/ai/data/time_patterns.png")
        
        # Visualize network comparison
        analyzer.visualize_network_comparison("backend/ai/data/network_comparison.png")
        print("Network comparison visualization saved to backend/ai/data/network_comparison.png")
        
        # Visualize token pair performance
        analyzer.visualize_token_pair_performance(5, "backend/ai/data/token_performance.png")
        print("Token performance visualization saved to backend/ai/data/token_performance.png")

def generate_example_trades(days=30):
    """Generate example trades for demonstration purposes."""
    trades = []
    
    # Networks, DEXes, and token pairs for random generation
    networks = ["ethereum", "arbitrum", "polygon", "optimism"]
    dexes = ["uniswap", "sushiswap", "curve", "balancer", "1inch"]
    token_pairs = ["ETH-USDC", "ETH-USDT", "WBTC-ETH", "LINK-ETH", "UNI-ETH"]
    
    # Generate trades for the past N days
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Generate 100 random trades
    for i in range(100):
        # Random timestamp within the period
        timestamp = start_time.timestamp() + random.random() * (end_time.timestamp() - start_time.timestamp())
        
        # Random trade data
        network = random.choice(networks)
        token_pair = random.choice(token_pairs)
        buy_dex = random.choice(dexes)
        sell_dex = random.choice([d for d in dexes if d != buy_dex])  # Different sell DEX
        
        amount = random.uniform(0.1, 10.0)
        gas_price = random.randint(20, 100) * 1000000000  # 20-100 Gwei
        gas_used = random.randint(100000, 300000)
        
        # 70% chance of success
        success = random.random() < 0.7
        
        # Profit depends on success
        if success:
            profit = random.uniform(0.001, 0.1)  # 0.1% to 10% profit
        else:
            profit = random.uniform(-0.05, 0.001)  # Small loss to small profit
        
        trade = {
            "timestamp": int(timestamp),
            "network": network,
            "token_pair": token_pair,
            "buy_dex": buy_dex,
            "sell_dex": sell_dex,
            "amount": amount,
            "gas_price": gas_price,
            "gas_used": gas_used,
            "profit": profit,
            "success": success
        }
        
        trades.append(trade)
    
    return trades

def main():
    """Run the trade analyzer with command-line arguments."""
    parser = argparse.ArgumentParser(description='Run the ArbitrageX Trade Analyzer')
    parser.add_argument('--testnet', action='store_true', help='Run in testnet mode')
    parser.add_argument('--days', type=int, default=30, help='Number of days of data to analyze')
    parser.add_argument('--visualize', action='store_true', help='Visualize the results')
    args = parser.parse_args()

    # Determine mode
    mode = "TESTNET" if args.testnet else "MAINNET"
    logger.info(f"Running in {mode} mode")

    print(f"\n===== ARBITRAGEX TRADE ANALYZER =====\n")
    print(f"Mode: {mode}\n")
    print(f"This demonstration analyzes trading patterns and market conditions\n")

    # Run the trade analyzer demonstration
    demonstrate_trade_analysis(testnet=args.testnet, days=args.days, visualize=args.visualize)

    # Warning for testnet mode
    if args.testnet:
        print("\n⚠️ TESTNET MODE: No real transactions will be executed")

if __name__ == "__main__":
    main() 