#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Backtesting CLI

This module provides a command-line interface for the ArbitrageX backtesting
framework, allowing users to run backtests with various configurations.
"""

import os
import sys
import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from backtesting.backtester import Backtester, BacktestConfig, BacktestResult
except ImportError:
    # Try relative import for when running from parent directory
    from backtester import Backtester, BacktestConfig, BacktestResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/ai/logs/backtesting_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backtest_cli")

def parse_date(date_str: str) -> datetime:
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")
        sys.exit(1)

def load_config_file(config_file: str) -> Dict[str, Any]:
    """Load a configuration file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_file}")
        sys.exit(1)

def create_default_config(strategy: str) -> Dict[str, Any]:
    """Create a default configuration for the specified strategy."""
    config = {
        "strategy_name": strategy,
        "start_date": (datetime.now() - timedelta(days=90)).isoformat(),
        "end_date": datetime.now().isoformat(),
        "initial_capital": 10.0,
        "data_source": "simulated",
        "exchange_fees": {
            "uniswap": 0.003,
            "sushiswap": 0.0025,
            "balancer": 0.002,
            "curve": 0.0004
        },
        "gas_price_gwei": 30.0,
        "slippage_tolerance": 0.005,
        "token_pairs": [
            "WETH-USDC", "WETH-USDT", "WETH-DAI", "WBTC-USDC", 
            "WBTC-WETH", "LINK-WETH", "UNI-WETH", "AAVE-WETH"
        ],
        "trade_size_eth": 1.0,
        "max_concurrent_trades": 5,
        "metrics_dir": f"backend/ai/metrics/backtest/{strategy}",
        "l2_networks_enabled": True,
        "flash_loans_enabled": True,
        "mev_protection_enabled": True,
        "ml_enhancements_enabled": True
    }
    
    # Add strategy-specific configurations
    if strategy == "base":
        config["l2_networks_enabled"] = False
        config["flash_loans_enabled"] = False
        config["mev_protection_enabled"] = False
        config["ml_enhancements_enabled"] = False
    elif strategy == "l2":
        config["flash_loans_enabled"] = False
        config["ml_enhancements_enabled"] = False
    elif strategy == "flash":
        config["l2_networks_enabled"] = False
        config["ml_enhancements_enabled"] = False
    elif strategy == "mev_protected":
        config["flash_loans_enabled"] = False
        config["ml_enhancements_enabled"] = False
    elif strategy == "combined":
        config["ml_enhancements_enabled"] = False
    
    return config

def save_default_config(strategy: str) -> str:
    """Save a default configuration file for the specified strategy."""
    config = create_default_config(strategy)
    
    # Create directories
    os.makedirs("backend/ai/config/backtest", exist_ok=True)
    config_file = f"backend/ai/config/backtest/{strategy}_default.json"
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
        
    logger.info(f"Default configuration saved to {config_file}")
    return config_file

def compare_strategies(configs: List[Dict[str, Any]], start_date: datetime, end_date: datetime) -> None:
    """Run backtests for multiple strategies and compare results."""
    results = []
    
    for config_dict in configs:
        # Update date range
        config_dict["start_date"] = start_date.isoformat()
        config_dict["end_date"] = end_date.isoformat()
        
        # Create config object
        config = BacktestConfig.from_dict(config_dict)
        
        # Run backtest
        backtester = Backtester(config)
        result = backtester.run_backtest()
        results.append(result)
    
    # Generate comparison report
    generate_comparison_report(results)

def generate_comparison_report(results: List[BacktestResult]) -> None:
    """Generate a report comparing multiple backtest results."""
    # Create timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create output directory
    output_dir = "backend/ai/metrics/backtest/comparison"
    os.makedirs(output_dir, exist_ok=True)
    report_file = f"{output_dir}/comparison_{timestamp}.html"
    
    # Generate summary table rows
    table_rows = ""
    for result in results:
        profit_loss_class = "positive" if result.total_profit_loss > 0 else "negative"
        avg_profit_class = "positive" if result.avg_profit_per_trade > 0 else "negative"
        
        table_rows += f"""
        <tr>
            <td>{result.strategy_name}</td>
            <td>{result.total_trades}</td>
            <td>{result.win_rate:.2%}</td>
            <td class="{profit_loss_class}">{result.total_profit_loss:.4f} ETH</td>
            <td class="{avg_profit_class}">{result.avg_profit_per_trade:.6f} ETH</td>
            <td>{result.sharpe_ratio:.2f}</td>
            <td>{result.max_drawdown:.2%}</td>
            <td>{((result.final_capital/result.initial_capital)-1)*100:.2f}%</td>
        </tr>
        """
    
    # Build HTML report
    html_content = f"""
    <html>
    <head>
        <title>Strategy Comparison Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: #333366; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .positive {{ color: green; }}
            .negative {{ color: red; }}
            .chart {{ margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>ArbitrageX Strategy Comparison Report</h1>
        <p>Period: {results[0].start_date.strftime('%Y-%m-%d')} to {results[0].end_date.strftime('%Y-%m-%d')}</p>
        
        <h2>Performance Summary</h2>
        <table>
            <tr>
                <th>Strategy</th>
                <th>Total Trades</th>
                <th>Win Rate</th>
                <th>Total Profit/Loss</th>
                <th>Avg Profit/Trade</th>
                <th>Sharpe Ratio</th>
                <th>Max Drawdown</th>
                <th>Total Return</th>
            </tr>
            {table_rows}
        </table>
        
        <h2>Strategy Descriptions</h2>
        <ul>
            <li><strong>base</strong>: Standard trading strategy without enhancements</li>
            <li><strong>l2</strong>: Layer 2 enabled strategy for reduced gas costs</li>
            <li><strong>flash</strong>: Flash Loan enabled strategy for capital efficiency</li>
            <li><strong>mev_protected</strong>: MEV protected strategy to prevent front-running</li>
            <li><strong>combined</strong>: Combined strategy with Layer 2 and Flash Loans</li>
            <li><strong>ml_enhanced</strong>: ML enhanced strategy with all features enabled</li>
        </ul>
        
        <p><small>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
    </body>
    </html>
    """
    
    # Write report to file
    with open(report_file, 'w') as f:
        f.write(html_content)
        
    logger.info(f"Comparison report generated at {report_file}")
    print(f"Comparison report available at: {report_file}")

def main():
    """Parse command-line arguments and run backtest."""
    parser = argparse.ArgumentParser(description="ArbitrageX Backtesting CLI")
    
    # Backtest configuration
    parser.add_argument("--strategy", type=str, 
                      choices=["base", "l2", "flash", "combined", "mev_protected", "ml_enhanced"],
                      default="ml_enhanced", 
                      help="Trading strategy to backtest")
    parser.add_argument("--start-date", type=str, 
                      help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, 
                      help="End date (YYYY-MM-DD)")
    parser.add_argument("--initial-capital", type=float, default=10.0,
                      help="Initial capital in ETH")
    parser.add_argument("--trade-size", type=float, default=1.0,
                      help="Trade size in ETH")
    parser.add_argument("--token-pairs", type=str, nargs="+",
                      help="Token pairs to include in the backtest")
    parser.add_argument("--config", type=str,
                      help="Path to config file")
    
    # Feature flags
    parser.add_argument("--disable-l2", action="store_true",
                      help="Disable Layer 2 networks")
    parser.add_argument("--disable-flash", action="store_true",
                      help="Disable Flash Loans")
    parser.add_argument("--disable-mev", action="store_true", 
                      help="Disable MEV protection")
    parser.add_argument("--disable-ml", action="store_true",
                      help="Disable ML enhancements")
    
    # Comparison mode
    parser.add_argument("--compare-all", action="store_true",
                      help="Compare all strategies")
    parser.add_argument("--days", type=int, default=90,
                      help="Number of days to backtest (for comparison mode)")
    
    # Report options
    parser.add_argument("--output-dir", type=str,
                      help="Directory to save reports")
    parser.add_argument("--generate-config", action="store_true",
                      help="Generate a default config file for the specified strategy")
    
    args = parser.parse_args()
    
    # Generate default config if requested
    if args.generate_config:
        config_file = save_default_config(args.strategy)
        print(f"Default configuration file generated: {config_file}")
        return
    
    # Handle comparison mode
    if args.compare_all:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        
        print(f"Comparing all strategies from {start_date.date()} to {end_date.date()}")
        
        # Create configs for all strategies
        configs = []
        for strategy in ["base", "l2", "flash", "mev_protected", "combined", "ml_enhanced"]:
            config_dict = create_default_config(strategy)
            configs.append(config_dict)
        
        # Run comparison
        compare_strategies(configs, start_date, end_date)
        return
    
    # Load config or use command line arguments
    if args.config:
        config_dict = load_config_file(args.config)
    else:
        # Create default config
        config_dict = create_default_config(args.strategy)
        
        # Update with command line arguments
        if args.start_date:
            config_dict["start_date"] = parse_date(args.start_date).isoformat()
        if args.end_date:
            config_dict["end_date"] = parse_date(args.end_date).isoformat()
        if args.initial_capital:
            config_dict["initial_capital"] = args.initial_capital
        if args.trade_size:
            config_dict["trade_size_eth"] = args.trade_size
        if args.token_pairs:
            config_dict["token_pairs"] = args.token_pairs
        if args.output_dir:
            config_dict["metrics_dir"] = args.output_dir
            
        # Apply feature flags
        if args.disable_l2:
            config_dict["l2_networks_enabled"] = False
        if args.disable_flash:
            config_dict["flash_loans_enabled"] = False
        if args.disable_mev:
            config_dict["mev_protection_enabled"] = False
        if args.disable_ml:
            config_dict["ml_enhancements_enabled"] = False
    
    # Create config object
    config = BacktestConfig.from_dict(config_dict)
    
    # Run backtest
    logger.info(f"Running backtest for {config.strategy_name} strategy")
    backtester = Backtester(config)
    results = backtester.run_backtest()
    
    # Generate report
    report_file = backtester.generate_report(results)
    
    # Print summary
    print(f"\nBacktest completed for {config.strategy_name}")
    print(f"Period: {config.start_date.date()} to {config.end_date.date()}")
    print(f"Initial capital: {config.initial_capital:.4f} ETH")
    print(f"Final capital: {results.final_capital:.4f} ETH")
    print(f"Total profit/loss: {results.total_profit_loss:.4f} ETH ({((results.final_capital/config.initial_capital)-1)*100:.2f}%)")
    print(f"Total trades: {results.total_trades}, Success rate: {results.win_rate:.2%}")
    print(f"Sharpe ratio: {results.sharpe_ratio:.2f}")
    print(f"Max drawdown: {results.max_drawdown:.2%}")
    print(f"\nDetailed report available at: {report_file}")


if __name__ == "__main__":
    main() 