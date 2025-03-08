#!/usr/bin/env python3
"""
ArbitrageX Small-Scale Simulated Trade Test

This script runs a focused test of the ArbitrageX AI system on a mainnet fork,
simulating a small number of trades to verify:
1. AI-optimized trades are executed profitably
2. MEV protection works as intended
3. Gas price estimation is accurate
"""

import os
import sys
import json
import time
import logging
import argparse
import datetime
import subprocess
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("small_scale_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SmallScaleTest")

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run a small-scale ArbitrageX test on a mainnet fork")
    
    parser.add_argument("--network", type=str, default="ethereum",
                        help="Network to test (default: ethereum)")
    
    parser.add_argument("--token-pair", type=str, default="WETH-USDC",
                        help="Token pair to test (default: WETH-USDC)")
    
    parser.add_argument("--dex", type=str, default="uniswap_v3",
                        help="DEX to test (default: uniswap_v3)")
    
    parser.add_argument("--trade-count", type=int, default=5,
                        help="Number of trades to simulate (default: 5)")
    
    parser.add_argument("--trade-size", type=str, default="small",
                        choices=["small", "medium", "large"],
                        help="Size of trades to simulate (default: small)")
    
    parser.add_argument("--gas-strategy", type=str, default="dynamic",
                        choices=["static", "dynamic", "aggressive"],
                        help="Gas price strategy (default: dynamic)")
    
    parser.add_argument("--mev-protection", action="store_true",
                        help="Enable MEV protection")
    
    parser.add_argument("--detailed-logging", action="store_true",
                        help="Enable detailed logging")
    
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    return parser.parse_args()

def create_test_config(args):
    """
    Create a test configuration from the parsed arguments.
    
    Args:
        args: Parsed command line arguments
    
    Returns:
        Test configuration dictionary and path to the config file
    """
    # Map trade size to actual amounts
    trade_size_map = {
        "small": {"eth_amount": 0.1, "usdc_amount": 100},
        "medium": {"eth_amount": 1.0, "usdc_amount": 1000},
        "large": {"eth_amount": 10.0, "usdc_amount": 10000}
    }
    
    # Create the test configuration
    config = {
        "network": args.network,
        "token_pair": args.token_pair.split("-"),
        "dex": args.dex,
        "trade_count": args.trade_count,
        "trade_size": trade_size_map[args.trade_size],
        "gas_strategy": args.gas_strategy,
        "mev_protection": args.mev_protection,
        "detailed_logging": args.detailed_logging,
        "debug": args.debug,
        "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    }
    
    # Save the configuration to a file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "small_scale_test_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Test configuration saved to {config_path}")
    
    return config, config_path

def run_ai_optimization(config_path):
    """
    Run the AI optimization process.
    
    Args:
        config_path: Path to the test configuration file
    
    Returns:
        Path to the AI optimization results file
    """
    logger.info("Running AI optimization...")
    
    # Import the strategy optimizer directly
    try:
        from strategy_optimizer_demo import StrategyOptimizerDemo
        
        optimizer = StrategyOptimizerDemo(config_path)
        results_file = optimizer.optimize_for_token_pair()
        
        logger.info("AI optimization completed successfully")
        logger.info(f"AI optimization results saved to {results_file}")
        
        return results_file
    except Exception as e:
        logger.error(f"Error running AI optimization: {e}")
        sys.exit(1)

def run_mev_protection_test(config_path, ai_results_path):
    """
    Run the MEV protection test.
    
    Args:
        config_path: Path to the test configuration file
        ai_results_path: Path to the AI optimization results file
    
    Returns:
        Path to the MEV protection results file
    """
    logger.info("Running MEV protection test...")
    
    # Import the MEV protection module directly
    try:
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "security"))
        from mev_protection import MEVProtection
        
        mev = MEVProtection(config_path=config_path)
        results_file = mev.protect_trades(ai_results_path)
        
        logger.info("MEV protection test completed successfully")
        logger.info(f"MEV protection results saved to {results_file}")
        
        return results_file
    except Exception as e:
        logger.error(f"Error running MEV protection test: {e}")
        sys.exit(1)

def run_gas_estimation_test(config_path, mev_results_path):
    """
    Run the gas estimation test.
    
    Args:
        config_path: Path to the test configuration file
        mev_results_path: Path to the MEV protection results file
    
    Returns:
        Path to the gas estimation results file
    """
    logger.info("Running gas estimation test...")
    
    # Import the gas optimizer module directly
    try:
        from gas_optimizer import GasOptimizer
        
        gas = GasOptimizer(config_path=config_path)
        results_file = gas.optimize_gas_for_trades(mev_results_path)
        
        logger.info("Gas estimation test completed successfully")
        logger.info(f"Gas estimation results saved to {results_file}")
        
        return results_file
    except Exception as e:
        logger.error(f"Error running gas estimation test: {e}")
        sys.exit(1)

def execute_simulated_trades(config_path, gas_results_path):
    """
    Execute simulated trades on the mainnet fork.
    
    Args:
        config_path: Path to the test configuration file
        gas_results_path: Path to the gas estimation results file
    
    Returns:
        Path to the trade execution results file
    """
    logger.info("Executing simulated trades...")
    
    # Import the trade executor module directly
    try:
        from trade_executor import TradeExecutor
        
        executor = TradeExecutor(config_path=config_path)
        results_file = executor.execute_trades(gas_results_path)
        
        logger.info("Trade execution completed successfully")
        logger.info(f"Trade execution results saved to {results_file}")
        
        return results_file
    except Exception as e:
        logger.error(f"Error executing simulated trades: {e}")
        sys.exit(1)

def generate_report(config, ai_results_path, mev_results_path, gas_results_path, execution_results_path):
    """
    Generate a report of the small-scale test.
    
    Args:
        config: Test configuration
        ai_results_path: Path to the AI optimization results file
        mev_results_path: Path to the MEV protection results file
        gas_results_path: Path to the gas estimation results file
        execution_results_path: Path to the trade execution results file
    
    Returns:
        Path to the report file
    """
    logger.info("Generating report...")
    
    # Load the results files
    try:
        with open(ai_results_path, "r") as f:
            ai_results = json.load(f)
        
        with open(mev_results_path, "r") as f:
            mev_results = json.load(f)
        
        with open(gas_results_path, "r") as f:
            gas_results = json.load(f)
        
        with open(execution_results_path, "r") as f:
            execution_results = json.load(f)
    except Exception as e:
        logger.error(f"Error loading results files: {e}")
        sys.exit(1)
    
    # Create the report
    report = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "config": config,
        "ai_optimization": {
            "total_opportunities": len(ai_results.get("opportunities", [])),
            "profitable_opportunities": len([o for o in ai_results.get("opportunities", []) if o.get("expected_profit", 0) > 0]),
            "average_expected_profit": sum([o.get("expected_profit", 0) for o in ai_results.get("opportunities", [])]) / len(ai_results.get("opportunities", [])) if ai_results.get("opportunities", []) else 0,
            "best_opportunity": max(ai_results.get("opportunities", []), key=lambda o: o.get("expected_profit", 0)) if ai_results.get("opportunities", []) else None
        },
        "mev_protection": {
            "total_trades": len(mev_results.get("trades", [])),
            "protected_trades": len([t for t in mev_results.get("trades", []) if t.get("mev_protected", False)]),
            "average_protection_cost": sum([t.get("protection_cost", 0) for t in mev_results.get("trades", [])]) / len(mev_results.get("trades", [])) if mev_results.get("trades", []) else 0
        },
        "gas_estimation": {
            "total_trades": len(gas_results.get("trades", [])),
            "average_gas_price": sum([t.get("gas_price", 0) for t in gas_results.get("trades", [])]) / len(gas_results.get("trades", [])) if gas_results.get("trades", []) else 0,
            "average_gas_used": sum([t.get("gas_used", 0) for t in gas_results.get("trades", [])]) / len(gas_results.get("trades", [])) if gas_results.get("trades", []) else 0,
            "average_gas_cost": sum([t.get("gas_cost", 0) for t in gas_results.get("trades", [])]) / len(gas_results.get("trades", [])) if gas_results.get("trades", []) else 0
        },
        "trade_execution": {
            "total_trades": len(execution_results.get("trades", [])),
            "successful_trades": len([t for t in execution_results.get("trades", []) if t.get("status", "") == "success"]),
            "failed_trades": len([t for t in execution_results.get("trades", []) if t.get("status", "") == "failed"]),
            "average_execution_time": sum([t.get("execution_time", 0) for t in execution_results.get("trades", [])]) / len(execution_results.get("trades", [])) if execution_results.get("trades", []) else 0,
            "total_profit": sum([t.get("actual_profit", 0) for t in execution_results.get("trades", []) if t.get("status", "") == "success"]),
            "average_profit": sum([t.get("actual_profit", 0) for t in execution_results.get("trades", []) if t.get("status", "") == "success"]) / len([t for t in execution_results.get("trades", []) if t.get("status", "") == "success"]) if [t for t in execution_results.get("trades", []) if t.get("status", "") == "success"] else 0
        }
    }
    
    # Save the report to a file
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    report_file = os.path.join(results_dir, f"small_scale_test_report_{config['timestamp']}.json")
    
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {report_file}")
    
    # Generate a human-readable report
    report_txt = os.path.join(results_dir, f"small_scale_test_report_{config['timestamp']}.txt")
    
    with open(report_txt, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("ArbitrageX Small-Scale Simulated Trade Test Report\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Date: {report['timestamp']}\n\n")
        
        f.write("Test Configuration:\n")
        f.write(f"  Network: {config['network']}\n")
        f.write(f"  Token Pair: {'-'.join(config['token_pair'])}\n")
        f.write(f"  DEX: {config['dex']}\n")
        f.write(f"  Trade Count: {config['trade_count']}\n")
        f.write(f"  Trade Size: {args.trade_size} (ETH: {config['trade_size']['eth_amount']}, USDC: {config['trade_size']['usdc_amount']})\n")
        f.write(f"  Gas Strategy: {config['gas_strategy']}\n")
        f.write(f"  MEV Protection: {'Enabled' if config['mev_protection'] else 'Disabled'}\n\n")
        
        f.write("AI Optimization Results:\n")
        f.write(f"  Total Opportunities: {report['ai_optimization']['total_opportunities']}\n")
        f.write(f"  Profitable Opportunities: {report['ai_optimization']['profitable_opportunities']}\n")
        f.write(f"  Average Expected Profit: ${report['ai_optimization']['average_expected_profit']:.2f}\n")
        if report['ai_optimization']['best_opportunity']:
            f.write(f"  Best Opportunity: ${report['ai_optimization']['best_opportunity'].get('expected_profit', 0):.2f}\n\n")
        
        f.write("MEV Protection Results:\n")
        f.write(f"  Total Trades: {report['mev_protection']['total_trades']}\n")
        f.write(f"  Protected Trades: {report['mev_protection']['protected_trades']}\n")
        f.write(f"  Average Protection Cost: ${report['mev_protection']['average_protection_cost']:.2f}\n\n")
        
        f.write("Gas Estimation Results:\n")
        f.write(f"  Total Trades: {report['gas_estimation']['total_trades']}\n")
        f.write(f"  Average Gas Price: {report['gas_estimation']['average_gas_price']:.2f} Gwei\n")
        f.write(f"  Average Gas Used: {report['gas_estimation']['average_gas_used']:.2f}\n")
        f.write(f"  Average Gas Cost: ${report['gas_estimation']['average_gas_cost']:.2f}\n\n")
        
        f.write("Trade Execution Results:\n")
        f.write(f"  Total Trades: {report['trade_execution']['total_trades']}\n")
        f.write(f"  Successful Trades: {report['trade_execution']['successful_trades']}\n")
        f.write(f"  Failed Trades: {report['trade_execution']['failed_trades']}\n")
        f.write(f"  Average Execution Time: {report['trade_execution']['average_execution_time']:.2f} ms\n")
        f.write(f"  Total Profit: ${report['trade_execution']['total_profit']:.2f}\n")
        f.write(f"  Average Profit per Trade: ${report['trade_execution']['average_profit']:.2f}\n\n")
        
        # Calculate success metrics
        ai_success = report['ai_optimization']['profitable_opportunities'] / report['ai_optimization']['total_opportunities'] if report['ai_optimization']['total_opportunities'] > 0 else 0
        mev_success = report['mev_protection']['protected_trades'] / report['mev_protection']['total_trades'] if report['mev_protection']['total_trades'] > 0 else 0
        execution_success = report['trade_execution']['successful_trades'] / report['trade_execution']['total_trades'] if report['trade_execution']['total_trades'] > 0 else 0
        
        f.write("Success Metrics:\n")
        f.write(f"  AI Optimization Success Rate: {ai_success:.2%}\n")
        f.write(f"  MEV Protection Success Rate: {mev_success:.2%}\n")
        f.write(f"  Trade Execution Success Rate: {execution_success:.2%}\n\n")
        
        f.write("Conclusion:\n")
        if report['trade_execution']['total_profit'] > 0 and execution_success > 0.8:
            f.write("  ✅ AI-optimized trades are executed profitably.\n")
        else:
            f.write("  ❌ AI-optimized trades are not consistently profitable.\n")
        
        if mev_success > 0.9:
            f.write("  ✅ MEV protection works as intended.\n")
        else:
            f.write("  ❌ MEV protection needs improvement.\n")
        
        # Calculate gas price accuracy by comparing estimated vs actual
        gas_price_accuracy = 0
        gas_used_accuracy = 0
        
        for trade in execution_results.get("trades", []):
            if trade.get("status", "") == "success":
                estimated_gas_price = trade.get("gas_price", 0)
                actual_gas_price = trade.get("actual_gas_price", 0)
                
                estimated_gas_used = trade.get("gas_used", 0)
                actual_gas_used = trade.get("actual_gas_used", 0)
                
                if estimated_gas_price > 0 and actual_gas_price > 0:
                    gas_price_accuracy += min(estimated_gas_price, actual_gas_price) / max(estimated_gas_price, actual_gas_price)
                
                if estimated_gas_used > 0 and actual_gas_used > 0:
                    gas_used_accuracy += min(estimated_gas_used, actual_gas_used) / max(estimated_gas_used, actual_gas_used)
        
        successful_trades_count = len([t for t in execution_results.get("trades", []) if t.get("status", "") == "success"])
        
        if successful_trades_count > 0:
            gas_price_accuracy /= successful_trades_count
            gas_used_accuracy /= successful_trades_count
            
            gas_accuracy = (gas_price_accuracy + gas_used_accuracy) / 2
        else:
            gas_accuracy = 0
        
        if gas_accuracy > 0.9:
            f.write("  ✅ Gas price estimation is accurate.\n")
        else:
            f.write("  ❌ Gas price estimation needs improvement.\n\n")
        
        f.write("Note: All transactions were simulated on a mainnet fork. No real transactions were executed.\n")
    
    logger.info(f"Human-readable report saved to {report_txt}")
    
    return report_txt

def main():
    """
    Main function.
    """
    logger.info("Starting ArbitrageX small-scale simulated trade test")
    
    # Parse command line arguments
    global args
    args = parse_arguments()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create test configuration
    config, config_path = create_test_config(args)
    
    try:
        # Run AI optimization
        ai_results_path = run_ai_optimization(config_path)
        
        # Run MEV protection test
        mev_results_path = run_mev_protection_test(config_path, ai_results_path)
        
        # Run gas estimation test
        gas_results_path = run_gas_estimation_test(config_path, mev_results_path)
        
        # Execute simulated trades
        execution_results_path = execute_simulated_trades(config_path, gas_results_path)
        
        # Generate report
        report_path = generate_report(config, ai_results_path, mev_results_path, gas_results_path, execution_results_path)
        
        # Print report path
        logger.info(f"Small-scale test completed successfully. Report saved to {report_path}")
        
        # Print summary
        with open(report_path, "r") as f:
            print("\n" + f.read())
    
    except Exception as e:
        logger.error(f"Error running small-scale test: {e}")
        sys.exit(1)
    
    logger.info("ArbitrageX small-scale simulated trade test completed")

if __name__ == "__main__":
    main() 