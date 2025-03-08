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
    main() #!/usr/bin/env python3
"""
ArbitrageX Extended Live Simulated Trade Test

This script runs an extended test of the ArbitrageX AI system on a mainnet fork,
simulating real-world conditions with a large dataset of at least 100 trades
across multiple token pairs and DEXes.
"""

import os
import sys
import json
import time
import logging
import argparse
import datetime
import concurrent.futures
from typing import Dict, List, Any, Optional

# Import Web3 connector and Strategy Optimizer
from strategy_optimizer_extended import StrategyOptimizerExtended
from learning_loop import LearningLoop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extended_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ExtendedLiveTest")

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run ArbitrageX Extended Live Test on a mainnet fork")
    
    parser.add_argument("--networks", type=str, default="ethereum,arbitrum,polygon",
                        help="Comma-separated list of networks to test (default: ethereum,arbitrum,polygon)")
    
    parser.add_argument("--token-pairs", type=str, default="WETH-USDC,WBTC-DAI,ETH-DAI",
                        help="Comma-separated list of token pairs to test (default: WETH-USDC,WBTC-DAI,ETH-DAI)")
    
    parser.add_argument("--dexes", type=str, default="uniswap_v3,sushiswap,curve",
                        help="Comma-separated list of DEXes to test (default: uniswap_v3,sushiswap,curve)")
    
    parser.add_argument("--min-trades", type=int, default=100,
                        help="Minimum number of trades to execute (default: 100)")
    
    parser.add_argument("--fork-block", type=int, default=0,
                        help="Block number to fork from (0 for latest)")
    
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Number of trades to process in each batch (default: 10)")
    
    parser.add_argument("--gas-strategy", type=str, default="dynamic",
                        choices=["conservative", "aggressive", "dynamic"],
                        help="Gas price strategy to use (default: dynamic)")
    
    parser.add_argument("--output-dir", type=str, default="results",
                        help="Directory to save results (default: results)")
    
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    parser.add_argument("--parallel", action="store_true", default=True,
                        help="Enable parallel processing (default: True)")
    
    parser.add_argument("--max-workers", type=int, default=4,
                        help="Maximum number of worker threads for parallel processing (default: 4)")
    
    parser.add_argument("--enable-learning", action="store_true", default=True,
                        help="Enable AI learning loop (default: True)")
    
    return parser.parse_args()

def create_fork_config(args):
    """
    Create configuration for the extended live test.
    
    Args:
        args: Command line arguments
        
    Returns:
        Configuration dictionary
    """
    networks = args.networks.split(",")
    token_pairs = [pair.split("-") for pair in args.token_pairs.split(",")]
    dexes = args.dexes.split(",")
    
    config = {
        "networks": networks,
        "token_pairs": token_pairs,
        "dexes": dexes,
        "min_trades": args.min_trades,
        "fork_block": args.fork_block,
        "batch_size": args.batch_size,
        "gas_strategy": args.gas_strategy,
        "output_dir": args.output_dir,
        "debug": args.debug,
        "parallel": args.parallel,
        "max_workers": args.max_workers,
        "enable_learning": args.enable_learning,
        "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    }
    
    # Save configuration to file
    os.makedirs(args.output_dir, exist_ok=True)
    config_file = os.path.join(args.output_dir, f"extended_test_config_{config['timestamp']}.json")
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Configuration saved to {config_file}")
    
    return config

def run_extended_test(args=None):
    """
    Run the extended live simulated trade test.
    
    Args:
        args: Command line arguments
    """
    if args is None:
        args = parse_arguments()
    
    # Create configuration
    config = create_fork_config(args)
    
    # Initialize Strategy Optimizer directly without Web3 connector
    logger.info("Initializing Strategy Optimizer Extended")
    optimizer = StrategyOptimizerExtended(
        networks=config["networks"],
        token_pairs=config["token_pairs"],
        dexes=config["dexes"],
        gas_strategy=config["gas_strategy"],
        results_dir=config["output_dir"],
        max_workers=config["max_workers"],
        enable_parallel=config["parallel"]
    )
    
    # Initialize Learning Loop if enabled
    learning_loop = None
    if config["enable_learning"]:
        logger.info("Initializing AI Learning Loop")
        learning_loop = LearningLoop(
            config_path="backend/ai/config/learning_loop_config.json",
            models_dir="backend/ai/models",
            data_dir="backend/ai/data",
            results_dir=config["output_dir"]
        )
        learning_loop.start()
    
    logger.info(f"Starting extended live test with minimum {config['min_trades']} trades")
    
    # Initialize results dictionary
    results = {
        "timestamp": config["timestamp"],
        "config": config,
        "predictions": [],
        "protected_trades": [],
        "execution_results": [],
        "analysis": {}
    }
    
    # Track metrics
    prediction_count = 0
    profitable_count = 0
    trade_count = 0
    successful_trade_count = 0
    total_profit = 0.0
    
    # Generate test combinations
    test_combinations = []
    for network in config["networks"]:
        for token_pair in config["token_pairs"]:
            for dex in config["dexes"]:
                test_combinations.append({
                    "network": network,
                    "token_pair": token_pair,
                    "dex": dex
                })
    
    # Use batch optimization for faster processing
    if config["parallel"]:
        logger.info("Using parallel batch optimization")
        
        # Run batch optimization
        aggregated_results = optimizer.batch_optimize(
            batch_size=config["batch_size"],
            min_trades=config["min_trades"]
        )
        
        # Extract results
        for result in aggregated_results.get("all_results", []):
            results["predictions"].extend([{"opportunity": opp, "prediction": pred} 
                                          for opp, pred in zip(result["opportunities"], result["predictions"])])
            results["protected_trades"].extend(result["protected_trades"])
            results["execution_results"].extend(result["execution_results"])
        
        # Update metrics
        for execution_result in results["execution_results"]:
            trade_count += 1
            if execution_result["status"] == "success":
                successful_trade_count += 1
                total_profit += execution_result["actual_profit"]
        
        # Update prediction count
        prediction_count = len(results["predictions"])
        profitable_count = len(results["protected_trades"])
    else:
        # Main test loop - continue until we've executed the minimum number of trades
        while trade_count < config["min_trades"]:
            # Process in batches
            for _ in range(config["batch_size"]):
                if trade_count >= config["min_trades"]:
                    break
                
                # Select a test combination
                combination_index = prediction_count % len(test_combinations)
                combination = test_combinations[combination_index]
                
                logger.info(f"Processing trade {prediction_count + 1}: {combination['network']} {'-'.join(combination['token_pair'])} {combination['dex']}")
                
                # Generate a test opportunity
                opportunity = optimizer.generate_opportunity(
                    network=combination["network"],
                    token_pair=combination["token_pair"],
                    dex=combination["dex"]
                )
                
                # Predict if the opportunity is profitable
                prediction = optimizer.predict_opportunity(opportunity)
                prediction_count += 1
                
                # Add prediction to results
                results["predictions"].append({
                    "opportunity": opportunity,
                    "prediction": prediction
                })
                
                # If profitable, apply MEV protection and execute the trade
                if prediction["is_profitable"]:
                    profitable_count += 1
                    
                    # Apply MEV protection
                    protected_trade = optimizer.apply_mev_protection(prediction)
                    results["protected_trades"].append(protected_trade)
                    
                    # Execute the trade
                    execution_result = optimizer.execute_trade(protected_trade)
                    trade_count += 1
                    
                    # Add execution result to results
                    results["execution_results"].append(execution_result)
                    
                    # Update metrics
                    if execution_result["status"] == "success":
                        successful_trade_count += 1
                        total_profit += execution_result["actual_profit"]
                    
                    logger.info(f"Trade {trade_count} executed: {execution_result['status']}, profit: ${execution_result.get('actual_profit', 0):.2f}")
                    
                    # Add to learning loop if enabled
                    if learning_loop:
                        learning_loop.add_execution_result(execution_result)
                
                # Save intermediate results every 10 trades
                if trade_count % 10 == 0 and trade_count > 0:
                    save_intermediate_results(results, config)
    
    # Analyze results
    results["analysis"] = analyze_results(results)
    
    # Generate report
    report_file = generate_report(results, config)
    
    # Save final results
    save_final_results(results, config)
    
    # Stop learning loop if enabled
    if learning_loop:
        # Force model update with the new data
        learning_loop.force_model_update()
        
        # Wait for model update to complete
        logger.info("Waiting for AI learning loop to process results...")
        time.sleep(10)
        
        # Get learning stats
        learning_stats = learning_loop.get_learning_stats()
        logger.info(f"Learning loop stats: {json.dumps(learning_stats, indent=2)}")
        
        # Stop learning loop
        learning_loop.stop()
    
    logger.info(f"Extended live test completed with {trade_count} trades")
    logger.info(f"Report generated at {report_file}")
    
    return results

def save_intermediate_results(results, config):
    """
    Save intermediate results to file.
    
    Args:
        results: Test results
        config: Configuration dictionary
    """
    output_dir = config["output_dir"]
    timestamp = config["timestamp"]
    
    # Save to JSON file
    results_file = os.path.join(output_dir, f"extended_test_intermediate_{timestamp}_{len(results['execution_results'])}.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Intermediate results saved to {results_file}")

def save_final_results(results, config):
    """
    Save final results to file.
    
    Args:
        results: Test results
        config: Configuration dictionary
    """
    output_dir = config["output_dir"]
    timestamp = config["timestamp"]
    
    # Save to JSON file
    results_file = os.path.join(output_dir, f"extended_test_results_{timestamp}.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Final results saved to {results_file}")

def analyze_results(results):
    """
    Analyze test results.
    
    Args:
        results: Test results
        
    Returns:
        Analysis dictionary
    """
    logger.info("Analyzing results")
    
    predictions = results["predictions"]
    protected_trades = results["protected_trades"]
    execution_results = results["execution_results"]
    
    # Calculate overall metrics
    total_predictions = len(predictions)
    profitable_predictions = len(protected_trades)
    total_trades = len(execution_results)
    successful_trades = sum(1 for result in execution_results if result["status"] == "success")
    
    # Calculate success rate
    success_rate = successful_trades / total_trades if total_trades > 0 else 0
    
    # Calculate profit metrics
    total_profit_usd = sum(result["actual_profit"] for result in execution_results if result["status"] == "success")
    avg_profit_per_trade_usd = total_profit_usd / total_trades if total_trades > 0 else 0
    avg_profit_per_successful_trade_usd = total_profit_usd / successful_trades if successful_trades > 0 else 0
    
    # Calculate gas metrics
    total_gas_cost_usd = sum(result["actual_gas_cost"] for result in execution_results)
    avg_gas_cost_usd = total_gas_cost_usd / total_trades if total_trades > 0 else 0
    
    # Calculate net profit
    net_profit_usd = total_profit_usd - total_gas_cost_usd
    
    # Calculate metrics by network
    networks = {}
    for result in execution_results:
        network = result["network"]
        if network not in networks:
            networks[network] = {
                "total_trades": 0,
                "successful_trades": 0,
                "total_profit": 0,
                "total_gas_cost": 0,
                "execution_times": []
            }
        
        networks[network]["total_trades"] += 1
        
        if result["status"] == "success":
            networks[network]["successful_trades"] += 1
            networks[network]["total_profit"] += result["actual_profit"]
        
        networks[network]["total_gas_cost"] += result["actual_gas_cost"]
        networks[network]["execution_times"].append(result["execution_time"])
    
    # Calculate success rate and average execution time for each network
    for network in networks:
        networks[network]["success_rate"] = (
            networks[network]["successful_trades"] / networks[network]["total_trades"]
            if networks[network]["total_trades"] > 0 else 0
        )
        networks[network]["avg_execution_time"] = (
            sum(networks[network]["execution_times"]) / len(networks[network]["execution_times"])
            if networks[network]["execution_times"] else 0
        )
    
    # Calculate metrics by token pair
    token_pairs = {}
    for result in execution_results:
        token_pair = "-".join(result["token_pair"])
        if token_pair not in token_pairs:
            token_pairs[token_pair] = {
                "total_trades": 0,
                "successful_trades": 0,
                "total_profit": 0
            }
        
        token_pairs[token_pair]["total_trades"] += 1
        
        if result["status"] == "success":
            token_pairs[token_pair]["successful_trades"] += 1
            token_pairs[token_pair]["total_profit"] += result["actual_profit"]
    
    # Calculate success rate for each token pair
    for token_pair in token_pairs:
        token_pairs[token_pair]["success_rate"] = (
            token_pairs[token_pair]["successful_trades"] / token_pairs[token_pair]["total_trades"]
            if token_pairs[token_pair]["total_trades"] > 0 else 0
        )
    
    # Calculate metrics by DEX
    dexes = {}
    for result in execution_results:
        dex = result["dex"]
        if dex not in dexes:
            dexes[dex] = {
                "total_trades": 0,
                "successful_trades": 0,
                "total_profit": 0
            }
        
        dexes[dex]["total_trades"] += 1
        
        if result["status"] == "success":
            dexes[dex]["successful_trades"] += 1
            dexes[dex]["total_profit"] += result["actual_profit"]
    
    # Calculate success rate for each DEX
    for dex in dexes:
        dexes[dex]["success_rate"] = (
            dexes[dex]["successful_trades"] / dexes[dex]["total_trades"]
            if dexes[dex]["total_trades"] > 0 else 0
        )
    
    # Find best performing combinations
    best_network = max(networks.items(), key=lambda x: x[1]["total_profit"])[0] if networks else None
    best_token_pair = max(token_pairs.items(), key=lambda x: x[1]["total_profit"])[0] if token_pairs else None
    best_dex = max(dexes.items(), key=lambda x: x[1]["total_profit"])[0] if dexes else None
    
    # Calculate execution speed metrics
    execution_times = [result["execution_time"] for result in execution_results]
    avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
    min_execution_time = min(execution_times) if execution_times else 0
    max_execution_time = max(execution_times) if execution_times else 0
    
    # Calculate throughput (trades per second)
    throughput = 1000 / avg_execution_time if avg_execution_time > 0 else 0
    
    # Compile analysis
    analysis = {
        "total_predictions": total_predictions,
        "profitable_predictions": profitable_predictions,
        "profitable_prediction_rate": profitable_predictions / total_predictions if total_predictions > 0 else 0,
        "total_trades": total_trades,
        "successful_trades": successful_trades,
        "success_rate": success_rate,
        "total_profit_usd": total_profit_usd,
        "avg_profit_per_trade_usd": avg_profit_per_trade_usd,
        "avg_profit_per_successful_trade_usd": avg_profit_per_successful_trade_usd,
        "total_gas_cost_usd": total_gas_cost_usd,
        "avg_gas_cost_usd": avg_gas_cost_usd,
        "net_profit_usd": net_profit_usd,
        "networks": networks,
        "token_pairs": token_pairs,
        "dexes": dexes,
        "best_network": best_network,
        "best_token_pair": best_token_pair,
        "best_dex": best_dex,
        "execution_speed": {
            "avg_execution_time_ms": avg_execution_time,
            "min_execution_time_ms": min_execution_time,
            "max_execution_time_ms": max_execution_time,
            "throughput_trades_per_second": throughput
        }
    }
    
    return analysis

def generate_report(results, config):
    """
    Generate a report of the test results.
    
    Args:
        results: Test results
        config: Configuration dictionary
        
    Returns:
        Path to the generated report file
    """
    logger.info("Generating report")
    
    # Create output directory if it doesn't exist
    output_dir = config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for report filename
    timestamp = config["timestamp"]
    report_file = os.path.join(output_dir, f"extended_test_report_{timestamp}.txt")
    
    # Extract analysis
    analysis = results["analysis"]
    
    # Write report
    with open(report_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("ArbitrageX Extended Live Simulated Trade Test Report\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Test Configuration:\n")
        f.write(f"  Networks: {', '.join(config['networks'])}\n")
        f.write(f"  Token Pairs: {', '.join(['-'.join(pair) for pair in config['token_pairs']])}\n")
        f.write(f"  DEXes: {', '.join(config['dexes'])}\n")
        f.write(f"  Minimum Trades: {config['min_trades']}\n")
        f.write(f"  Batch Size: {config['batch_size']}\n")
        f.write(f"  Gas Strategy: {config['gas_strategy']}\n")
        f.write(f"  Parallel Processing: {'Enabled' if config.get('parallel', config.get('max_workers', 1) > 1) else 'Disabled'}\n")
        f.write(f"  Max Workers: {config['max_workers']}\n")
        f.write(f"  AI Learning Loop: {'Enabled' if config.get('enable_learning', True) else 'Disabled'}\n\n")
        
        f.write("Summary:\n")
        f.write(f"  Total Predictions: {analysis['total_predictions']}\n")
        f.write(f"  Profitable Predictions: {analysis['profitable_predictions']} ({analysis['profitable_prediction_rate']:.2%})\n")
        f.write(f"  Executed Trades: {analysis['total_trades']}\n")
        f.write(f"  Successful Trades: {analysis['successful_trades']}\n")
        f.write(f"  Success Rate: {analysis['success_rate']:.2%}\n")
        f.write(f"  Total Profit: ${analysis['total_profit_usd']:.2f}\n")
        f.write(f"  Total Gas Cost: ${analysis['total_gas_cost_usd']:.2f}\n")
        f.write(f"  Net Profit: ${analysis['net_profit_usd']:.2f}\n")
        f.write(f"  Average Profit per Successful Trade: ${analysis['avg_profit_per_successful_trade_usd']:.2f}\n\n")
        
        f.write("Execution Speed:\n")
        f.write(f"  Average Execution Time: {analysis['execution_speed']['avg_execution_time_ms']:.2f} ms\n")
        f.write(f"  Minimum Execution Time: {analysis['execution_speed']['min_execution_time_ms']:.2f} ms\n")
        f.write(f"  Maximum Execution Time: {analysis['execution_speed']['max_execution_time_ms']:.2f} ms\n")
        f.write(f"  Throughput: {analysis['execution_speed']['throughput_trades_per_second']:.2f} trades/second\n\n")
        
        f.write("Performance by Network:\n")
        for network, stats in analysis["networks"].items():
            f.write(f"  {network}:\n")
            f.write(f"    Total Trades: {stats['total_trades']}\n")
            f.write(f"    Successful Trades: {stats['successful_trades']}\n")
            f.write(f"    Success Rate: {stats['success_rate']:.2%}\n")
            f.write(f"    Total Profit: ${stats['total_profit']:.2f}\n")
            f.write(f"    Total Gas Cost: ${stats['total_gas_cost']:.2f}\n")
            f.write(f"    Net Profit: ${stats['total_profit'] - stats['total_gas_cost']:.2f}\n")
            f.write(f"    Average Execution Time: {stats['avg_execution_time']:.2f} ms\n\n")
        
        f.write("Performance by Token Pair:\n")
        for token_pair, stats in analysis["token_pairs"].items():
            f.write(f"  {token_pair}:\n")
            f.write(f"    Total Trades: {stats['total_trades']}\n")
            f.write(f"    Successful Trades: {stats['successful_trades']}\n")
            f.write(f"    Success Rate: {stats['success_rate']:.2%}\n")
            f.write(f"    Total Profit: ${stats['total_profit']:.2f}\n\n")
        
        f.write("Performance by DEX:\n")
        for dex, stats in analysis["dexes"].items():
            f.write(f"  {dex}:\n")
            f.write(f"    Total Trades: {stats['total_trades']}\n")
            f.write(f"    Successful Trades: {stats['successful_trades']}\n")
            f.write(f"    Success Rate: {stats['success_rate']:.2%}\n")
            f.write(f"    Total Profit: ${stats['total_profit']:.2f}\n\n")
        
        f.write("Best Performing Combinations:\n")
        f.write(f"  Best Network: {analysis['best_network']}\n")
        f.write(f"  Best Token Pair: {analysis['best_token_pair']}\n")
        f.write(f"  Best DEX: {analysis['best_dex']}\n\n")
        
        f.write("Conclusion:\n")
        if analysis['success_rate'] > 0.8 and analysis['net_profit_usd'] > 0:
            f.write("  The ArbitrageX AI system performed exceptionally well, identifying profitable arbitrage\n")
            f.write("  opportunities and executing them successfully. The high success rate and significant\n")
            f.write("  profit demonstrate the effectiveness of the system.\n\n")
        elif analysis['success_rate'] > 0.6 and analysis['net_profit_usd'] > 0:
            f.write("  The ArbitrageX AI system performed well, identifying profitable arbitrage opportunities\n")
            f.write("  and executing them with a good success rate. The system is profitable but could benefit\n")
            f.write("  from further optimization.\n\n")
        else:
            f.write("  The ArbitrageX AI system identified some profitable opportunities, but the success rate\n")
            f.write("  or profitability needs improvement. Further optimization and testing are recommended.\n\n")
        
        f.write("Recommendations:\n")
        f.write(f"  1. Focus on {analysis['best_network']} for better profitability\n")
        f.write(f"  2. Prioritize {analysis['best_token_pair']} trades\n")
        f.write(f"  3. Utilize {analysis['best_dex']} for better execution\n")
        f.write("  4. Optimize gas strategy to reduce costs\n")
        f.write("  5. Refine MEV protection strategies for higher success rates\n")
        
        if analysis['execution_speed']['avg_execution_time_ms'] > 1000:
            f.write("  6. Further optimize execution speed to increase throughput\n")
        
        if config['enable_learning']:
            f.write("  7. Continue training the AI models with more real-world data\n")
        else:
            f.write("  7. Enable AI learning loop for continuous improvement\n")
        
        f.write("\n")
        
        f.write("Note: All transactions were simulated on a mainnet fork. No real transactions were executed.\n")
    
    logger.info(f"Report generated at {report_file}")
    
    return report_file

def main():
    """
    Main function.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting ArbitrageX extended live simulated trade test")
    
    # Run the test
    run_extended_test(args=args)
    
    logger.info("ArbitrageX extended live simulated trade test completed")

if __name__ == "__main__":
    main() #!/usr/bin/env python3
"""
ArbitrageX Final Extended Test

This script runs a comprehensive final test of the ArbitrageX AI system with all improvements:
1. AI Learning Loop for automatic adjustments
2. Optimized trade execution speed with parallel processing
3. Network prioritization based on performance

The test simulates real-world conditions with a large dataset of trades across multiple
networks, token pairs, and DEXes, and validates the effectiveness of the improvements.
"""

import os
import sys
import json
import time
import logging
import argparse
import datetime
import concurrent.futures
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import required modules
from strategy_optimizer_extended import StrategyOptimizerExtended
from learning_loop import LearningLoop
from run_extended_test import analyze_results, generate_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("final_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FinalTest")

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run ArbitrageX Final Extended Test with all improvements")
    
    parser.add_argument("--networks", type=str, default="ethereum,arbitrum,polygon,optimism,base",
                        help="Comma-separated list of networks to test (default: ethereum,arbitrum,polygon,optimism,base)")
    
    parser.add_argument("--token-pairs", type=str, default="WETH-USDC,WBTC-DAI,ETH-DAI,USDC-USDT,WETH-WBTC",
                        help="Comma-separated list of token pairs to test (default: WETH-USDC,WBTC-DAI,ETH-DAI,USDC-USDT,WETH-WBTC)")
    
    parser.add_argument("--dexes", type=str, default="uniswap_v3,sushiswap,curve,balancer,1inch",
                        help="Comma-separated list of DEXes to test (default: uniswap_v3,sushiswap,curve,balancer,1inch)")
    
    parser.add_argument("--min-trades", type=int, default=200,
                        help="Minimum number of trades to execute (default: 200)")
    
    parser.add_argument("--batch-size", type=int, default=20,
                        help="Number of trades to process in each batch (default: 20)")
    
    parser.add_argument("--gas-strategy", type=str, default="dynamic",
                        choices=["conservative", "aggressive", "dynamic"],
                        help="Gas price strategy to use (default: dynamic)")
    
    parser.add_argument("--output-dir", type=str, default="results",
                        help="Directory to save results (default: results)")
    
    parser.add_argument("--max-workers", type=int, default=8,
                        help="Maximum number of worker threads for parallel processing (default: 8)")
    
    parser.add_argument("--learning-interval", type=int, default=30,
                        help="Interval in minutes for AI learning updates (default: 30)")
    
    parser.add_argument("--adaptation-interval", type=int, default=60,
                        help="Interval in minutes for strategy adaptation (default: 60)")
    
    parser.add_argument("--compare-baseline", action="store_true",
                        help="Compare results with baseline (non-optimized) version")
    
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    return parser.parse_args() 

def create_test_config(args):
    """
    Create configuration for the final test.
    
    Args:
        args: Command line arguments
        
    Returns:
        Configuration dictionary
    """
    networks = args.networks.split(",")
    token_pairs = [pair.split("-") for pair in args.token_pairs.split(",")]
    dexes = args.dexes.split(",")
    
    config = {
        "networks": networks,
        "token_pairs": token_pairs,
        "dexes": dexes,
        "min_trades": args.min_trades,
        "batch_size": args.batch_size,
        "gas_strategy": args.gas_strategy,
        "output_dir": args.output_dir,
        "max_workers": args.max_workers,
        "learning_interval": args.learning_interval,
        "adaptation_interval": args.adaptation_interval,
        "compare_baseline": args.compare_baseline,
        "debug": args.debug,
        "enable_learning": True,
        "parallel": args.max_workers > 1,
        "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    }
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Save configuration to file
    config_file = os.path.join(args.output_dir, f"final_test_config_{config['timestamp']}.json")
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Configuration saved to {config_file}")
    
    return config 

def save_intermediate_results(results, config, iteration=None):
    """
    Save intermediate results to file.
    
    Args:
        results: Test results
        config: Configuration dictionary
        iteration: Iteration number (optional)
    """
    output_dir = config["output_dir"]
    timestamp = config["timestamp"]
    
    # Create filename with iteration if provided
    if iteration is not None:
        results_file = os.path.join(output_dir, f"final_test_intermediate_{timestamp}_iteration_{iteration}.json")
    else:
        results_file = os.path.join(output_dir, f"final_test_intermediate_{timestamp}_{len(results['execution_results'])}.json")
    
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Intermediate results saved to {results_file}")

def save_final_results(results, config):
    """
    Save final results to file.
    
    Args:
        results: Test results
        config: Configuration dictionary
    """
    output_dir = config["output_dir"]
    timestamp = config["timestamp"]
    
    # Save to JSON file
    results_file = os.path.join(output_dir, f"final_test_results_{timestamp}.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Final results saved to {results_file}")
    
    return results_file 

def run_baseline_test(config):
    """
    Run a baseline test without optimizations for comparison.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Baseline test results
    """
    logger.info("Running baseline test without optimizations for comparison")
    
    # Create a copy of the config with optimizations disabled
    baseline_config = config.copy()
    baseline_config["max_workers"] = 1  # Disable parallel processing
    baseline_config["timestamp"] = f"{config['timestamp']}_baseline"
    
    # Initialize Strategy Optimizer without optimizations
    optimizer = StrategyOptimizerExtended(
        networks=baseline_config["networks"],
        token_pairs=baseline_config["token_pairs"],
        dexes=baseline_config["dexes"],
        gas_strategy=baseline_config["gas_strategy"],
        results_dir=baseline_config["output_dir"],
        max_workers=1,
        enable_parallel=False
    )
    
    # Initialize results dictionary
    results = {
        "timestamp": baseline_config["timestamp"],
        "config": baseline_config,
        "predictions": [],
        "protected_trades": [],
        "execution_results": [],
        "analysis": {}
    }
    
    # Track metrics
    prediction_count = 0
    profitable_count = 0
    trade_count = 0
    successful_trade_count = 0
    total_profit = 0.0
    
    # Generate test combinations
    test_combinations = []
    for network in baseline_config["networks"]:
        for token_pair in baseline_config["token_pairs"]:
            for dex in baseline_config["dexes"]:
                test_combinations.append({
                    "network": network,
                    "token_pair": token_pair,
                    "dex": dex
                })
    
    # Set a lower trade count for baseline to save time
    min_trades = min(baseline_config["min_trades"], 50)
    
    # Main test loop - continue until we've executed the minimum number of trades
    start_time = time.time()
    
    while trade_count < min_trades:
        # Process in batches
        for _ in range(baseline_config["batch_size"]):
            if trade_count >= min_trades:
                break
            
            # Select a test combination
            combination_index = prediction_count % len(test_combinations)
            combination = test_combinations[combination_index]
            
            # Generate a test opportunity
            opportunity = optimizer.generate_opportunity(
                network=combination["network"],
                token_pair=combination["token_pair"],
                dex=combination["dex"]
            )
            
            # Predict if the opportunity is profitable
            prediction = optimizer.predict_opportunity(opportunity)
            prediction_count += 1
            
            # Add prediction to results
            results["predictions"].append({
                "opportunity": opportunity,
                "prediction": prediction
            })
            
            # If profitable, apply MEV protection and execute the trade
            if prediction["is_profitable"]:
                profitable_count += 1
                
                # Apply MEV protection
                protected_trade = optimizer.apply_mev_protection(prediction)
                results["protected_trades"].append(protected_trade)
                
                # Execute the trade
                execution_result = optimizer.execute_trade(protected_trade)
                trade_count += 1
                
                # Add execution result to results
                results["execution_results"].append(execution_result)
                
                # Update metrics
                if execution_result["status"] == "success":
                    successful_trade_count += 1
                    total_profit += execution_result["actual_profit"]
            
            # Save intermediate results every 10 trades
            if trade_count % 10 == 0 and trade_count > 0:
                save_intermediate_results(results, baseline_config)
    
    # Calculate total execution time
    execution_time = time.time() - start_time
    
    # Add execution time to results
    results["execution_time"] = execution_time
    results["trades_per_second"] = trade_count / execution_time if execution_time > 0 else 0
    
    # Analyze results
    results["analysis"] = analyze_results(results)
    
    # Generate report
    report_file = os.path.join(baseline_config["output_dir"], f"baseline_test_report_{baseline_config['timestamp']}.txt")
    with open(report_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("ArbitrageX Baseline Test Report (Without Optimizations)\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Test Configuration:\n")
        f.write(f"  Networks: {', '.join(baseline_config['networks'])}\n")
        f.write(f"  Token Pairs: {', '.join(['-'.join(pair) for pair in baseline_config['token_pairs']])}\n")
        f.write(f"  DEXes: {', '.join(baseline_config['dexes'])}\n")
        f.write(f"  Minimum Trades: {min_trades}\n")
        f.write(f"  Batch Size: {baseline_config['batch_size']}\n")
        f.write(f"  Gas Strategy: {baseline_config['gas_strategy']}\n")
        f.write(f"  Parallel Processing: Disabled\n")
        f.write(f"  AI Learning Loop: Disabled\n\n")
        
        f.write("Summary:\n")
        f.write(f"  Total Predictions: {prediction_count}\n")
        f.write(f"  Profitable Predictions: {profitable_count} ({profitable_count/prediction_count:.2%})\n")
        f.write(f"  Executed Trades: {trade_count}\n")
        f.write(f"  Successful Trades: {successful_trade_count}\n")
        f.write(f"  Success Rate: {successful_trade_count/trade_count:.2%}\n")
        f.write(f"  Total Profit: ${total_profit:.2f}\n")
        f.write(f"  Total Execution Time: {execution_time:.2f} seconds\n")
        f.write(f"  Trades Per Second: {results['trades_per_second']:.2f}\n\n")
        
        f.write("Note: This is a baseline test without optimizations for comparison purposes.\n")
    
    # Save final results
    save_final_results(results, baseline_config)
    
    logger.info(f"Baseline test completed with {trade_count} trades in {execution_time:.2f} seconds")
    logger.info(f"Baseline report generated at {report_file}")
    
    return results 

def run_optimized_test(config):
    """
    Run the optimized test with all improvements.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Optimized test results
    """
    logger.info("Running optimized test with all improvements")
    
    # Initialize Strategy Optimizer with optimizations
    optimizer = StrategyOptimizerExtended(
        networks=config["networks"],
        token_pairs=config["token_pairs"],
        dexes=config["dexes"],
        gas_strategy=config["gas_strategy"],
        results_dir=config["output_dir"],
        max_workers=config["max_workers"],
        enable_parallel=True
    )
    
    # Initialize Learning Loop
    learning_loop = LearningLoop(
        config_path="backend/ai/config/learning_loop_config.json",
        models_dir="backend/ai/models",
        data_dir="backend/ai/data",
        results_dir=config["output_dir"]
    )
    
    # Configure learning loop with custom intervals
    learning_loop.config["update_interval_minutes"] = config["learning_interval"]
    learning_loop.config["adaptation_interval_hours"] = config["adaptation_interval"] / 60  # Convert minutes to hours
    
    # Start learning loop
    learning_loop.start()
    
    # Initialize results dictionary
    results = {
        "timestamp": config["timestamp"],
        "config": config,
        "predictions": [],
        "protected_trades": [],
        "execution_results": [],
        "analysis": {},
        "learning_stats": {}
    }
    
    # Track metrics
    prediction_count = 0
    profitable_count = 0
    trade_count = 0
    successful_trade_count = 0
    total_profit = 0.0
    
    # Record start time
    start_time = time.time()
    
    # Use batch optimization for faster processing
    logger.info("Using parallel batch optimization")
    
    # Run batch optimization
    aggregated_results = optimizer.batch_optimize(
        batch_size=config["batch_size"],
        min_trades=config["min_trades"]
    )
    
    # Extract results
    for result in aggregated_results.get("all_results", []):
        results["predictions"].extend([{"opportunity": opp, "prediction": pred} 
                                      for opp, pred in zip(result["opportunities"], result["predictions"])])
        results["protected_trades"].extend(result["protected_trades"])
        results["execution_results"].extend(result["execution_results"])
    
    # Update metrics
    for execution_result in results["execution_results"]:
        trade_count += 1
        if execution_result["status"] == "success":
            successful_trade_count += 1
            total_profit += execution_result["actual_profit"]
        
        # Add to learning loop
        learning_loop.add_execution_result(execution_result)
    
    # Update prediction count
    prediction_count = len(results["predictions"])
    profitable_count = len(results["protected_trades"])
    
    # Calculate total execution time
    execution_time = time.time() - start_time
    
    # Add execution time to results
    results["execution_time"] = execution_time
    results["trades_per_second"] = trade_count / execution_time if execution_time > 0 else 0
    
    # Force model update with the new data
    learning_loop.force_model_update()
    
    # Wait for model update to complete
    logger.info("Waiting for AI learning loop to process results...")
    time.sleep(10)
    
    # Get learning stats
    learning_stats = learning_loop.get_learning_stats()
    results["learning_stats"] = learning_stats
    
    # Force strategy adaptation
    learning_loop.force_strategy_adaptation()
    
    # Wait for adaptation to complete
    logger.info("Waiting for strategy adaptation to complete...")
    time.sleep(10)
    
    # Get updated learning stats
    learning_stats = learning_loop.get_learning_stats()
    results["learning_stats"] = learning_stats
    
    # Stop learning loop
    learning_loop.stop()
    
    # Analyze results
    results["analysis"] = analyze_results(results)
    
    # Generate report
    report_file = generate_report(results, config)
    
    # Save final results
    save_final_results(results, config)
    
    logger.info(f"Optimized test completed with {trade_count} trades in {execution_time:.2f} seconds")
    logger.info(f"Trades per second: {results['trades_per_second']:.2f}")
    logger.info(f"Report generated at {report_file}")
    
    return results 

def compare_results(baseline_results, optimized_results, config):
    """
    Compare baseline and optimized test results.
    
    Args:
        baseline_results: Baseline test results
        optimized_results: Optimized test results
        config: Configuration dictionary
    """
    logger.info("Comparing baseline and optimized test results")
    
    # Extract metrics
    baseline_trades = len(baseline_results["execution_results"])
    optimized_trades = len(optimized_results["execution_results"])
    
    baseline_time = baseline_results["execution_time"]
    optimized_time = optimized_results["execution_time"]
    
    baseline_tps = baseline_results["trades_per_second"]
    optimized_tps = optimized_results["trades_per_second"]
    
    baseline_success_rate = baseline_results["analysis"]["success_rate"]
    optimized_success_rate = optimized_results["analysis"]["success_rate"]
    
    baseline_profit = baseline_results["analysis"]["total_profit_usd"]
    optimized_profit = optimized_results["analysis"]["total_profit_usd"]
    
    # Calculate improvements
    speed_improvement = (optimized_tps / baseline_tps) if baseline_tps > 0 else float('inf')
    success_rate_improvement = (optimized_success_rate / baseline_success_rate) if baseline_success_rate > 0 else float('inf')
    profit_improvement = (optimized_profit / baseline_profit) if baseline_profit > 0 else float('inf')
    
    # Create comparison report
    output_dir = config["output_dir"]
    timestamp = config["timestamp"]
    comparison_file = os.path.join(output_dir, f"comparison_report_{timestamp}.txt")
    
    with open(comparison_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("ArbitrageX Optimization Comparison Report\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Performance Comparison:\n\n")
        
        f.write("1. Execution Speed:\n")
        f.write(f"   Baseline: {baseline_trades} trades in {baseline_time:.2f} seconds ({baseline_tps:.2f} trades/second)\n")
        f.write(f"   Optimized: {optimized_trades} trades in {optimized_time:.2f} seconds ({optimized_tps:.2f} trades/second)\n")
        f.write(f"   Improvement: {speed_improvement:.2f}x faster\n\n")
        
        f.write("2. Success Rate:\n")
        f.write(f"   Baseline: {baseline_success_rate:.2%}\n")
        f.write(f"   Optimized: {optimized_success_rate:.2%}\n")
        f.write(f"   Improvement: {(optimized_success_rate - baseline_success_rate) * 100:.2f}% higher\n\n")
        
        f.write("3. Profitability:\n")
        f.write(f"   Baseline: ${baseline_profit:.2f}\n")
        f.write(f"   Optimized: ${optimized_profit:.2f}\n")
        f.write(f"   Improvement: {profit_improvement:.2f}x more profitable\n\n")
        
        f.write("4. AI Learning Loop:\n")
        f.write(f"   Baseline: Not enabled\n")
        f.write(f"   Optimized: Enabled\n")
        f.write(f"   Learning Stats: {json.dumps(optimized_results['learning_stats'], indent=2)}\n\n")
        
        f.write("Conclusion:\n")
        if speed_improvement > 1.5 and success_rate_improvement > 1.1 and profit_improvement > 1.2:
            f.write("The optimized version shows significant improvements in all key metrics:\n")
            f.write(f"- {speed_improvement:.2f}x faster execution\n")
            f.write(f"- {(optimized_success_rate - baseline_success_rate) * 100:.2f}% higher success rate\n")
            f.write(f"- {profit_improvement:.2f}x more profitable\n")
            f.write("The AI learning loop and parallel processing optimizations have proven highly effective.\n")
        elif speed_improvement > 1.5:
            f.write("The optimized version shows significant speed improvements, but other metrics need further optimization.\n")
        else:
            f.write("The optimizations show some improvements, but further refinement is needed to achieve optimal performance.\n")
    
    logger.info(f"Comparison report generated at {comparison_file}")
    
    return comparison_file

def run_final_test(args=None):
    """
    Run the final test with all improvements.
    
    Args:
        args: Command line arguments
    """
    if args is None:
        args = parse_arguments()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create configuration
    config = create_test_config(args)
    
    # Run baseline test if requested
    baseline_results = None
    if config["compare_baseline"]:
        baseline_results = run_baseline_test(config)
    
    # Run optimized test
    optimized_results = run_optimized_test(config)
    
    # Compare results if baseline test was run
    if baseline_results:
        compare_results(baseline_results, optimized_results, config)
    
    logger.info("Final test completed successfully")
    
    return optimized_results

def main():
    """
    Main function.
    """
    logger.info("Starting ArbitrageX final extended test")
    
    # Run the test
    run_final_test()
    
    logger.info("ArbitrageX final extended test completed")

if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
ArbitrageX Mainnet Fork Test Wrapper

This script is a wrapper for run_mainnet_fork_test.py that handles argument parsing
and configuration for the mainnet fork test.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fork_test_wrapper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ForkTestWrapper")

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run ArbitrageX on a mainnet fork")
    
    parser.add_argument("--networks", type=str, default="arbitrum,polygon",
                        help="Comma-separated list of networks to test (default: arbitrum,polygon)")
    
    parser.add_argument("--tokens", type=str, default="WETH,USDC,DAI,WBTC",
                        help="Comma-separated list of tokens to test")
    
    parser.add_argument("--dexes", type=str, default="uniswap_v3,sushiswap,curve,balancer",
                        help="Comma-separated list of DEXes to test")
    
    parser.add_argument("--fork-block", type=int, default=0,
                        help="Block number to fork from (default: 0 = latest)")
    
    parser.add_argument("--run-time", type=int, default=300,
                        help="How long to run the test in seconds (default: 300)")
    
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Number of trades to process in each batch (default: 10)")
    
    parser.add_argument("--gas-strategy", type=str, default="dynamic",
                        choices=["static", "dynamic", "aggressive"],
                        help="Gas price strategy (default: dynamic)")
    
    parser.add_argument("--modules", type=str, default="all",
                        help="Comma-separated list of modules to run (default: all)")
    
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    return parser.parse_args()

def create_fork_config(args):
    """
    Create a fork configuration from the parsed arguments.
    
    Args:
        args: Parsed command line arguments
    
    Returns:
        Fork configuration dictionary
    """
    networks = [n.strip() for n in args.networks.split(",")]
    tokens = [t.strip() for t in args.tokens.split(",")]
    dexes = [d.strip() for d in args.dexes.split(",")]
    
    config = {
        "networks": networks,
        "tokens": tokens,
        "dexes": dexes,
        "fork_block": args.fork_block,
        "run_time": args.run_time,
        "batch_size": args.batch_size,
        "gas_strategy": args.gas_strategy,
        "modules": args.modules.split(",") if args.modules != "all" else "all",
        "debug": args.debug
    }
    
    # Save the configuration to a file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fork_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Fork configuration saved to {config_path}")
    
    return config, config_path

def main():
    """
    Main function.
    """
    logger.info("Starting ArbitrageX mainnet fork test wrapper")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create fork configuration
    config, config_path = create_fork_config(args)
    
    # Initialize the StrategyOptimizer with the fork configuration
    logger.info("Initializing StrategyOptimizer with fork configuration")
    cmd = f"python3 -c \"import sys; sys.path.append('.'); from strategy_optimizer import StrategyOptimizer; optimizer = StrategyOptimizer(fork_config_path='{config_path}'); print('StrategyOptimizer initialized successfully')\""
    
    logger.info(f"Running command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"StrategyOptimizer initialization failed: {result.stderr}")
        sys.exit(1)
    
    logger.info(result.stdout.strip())
    
    # Run the mainnet fork test
    logger.info("Running mainnet fork test with configuration:")
    logger.info(f"  Networks: {', '.join(config['networks'])}")
    logger.info(f"  Tokens: {', '.join(config['tokens'])}")
    logger.info(f"  DEXes: {', '.join(config['dexes'])}")
    logger.info(f"  Fork block: {config['fork_block']}")
    logger.info(f"  Run time: {config['run_time']}")
    logger.info(f"  Batch size: {config['batch_size']}")
    logger.info(f"  Gas strategy: {config['gas_strategy']}")
    logger.info(f"  Modules: {config['modules']}")
    logger.info(f"  Debug: {config['debug']}")
    
    # Run the mainnet fork test script
    cmd = f"python3 -c \"import sys; sys.path.append('.'); sys.argv = ['run_mainnet_fork_test.py']; import run_mainnet_fork_test; from argparse import Namespace; args = Namespace(networks='{args.networks}', tokens='{args.tokens}', dexes='{args.dexes}', fork_block={args.fork_block}, run_time={args.run_time}, batch_size={args.batch_size}, gas_strategy='{args.gas_strategy}', modules='{args.modules}', debug={args.debug}, fork_config_path='{config_path}'); run_mainnet_fork_test.run_mainnet_fork_test(args=args)\""
    
    logger.info(f"Running command: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Mainnet fork test failed: {result.stderr}")
        sys.exit(1)
    
    logger.info(result.stdout.strip())
    logger.info("ArbitrageX mainnet fork test wrapper completed")

if __name__ == "__main__":
    main() #!/usr/bin/env python3
"""
ArbitrageX Mainnet Fork Test

This script runs a test of the ArbitrageX AI system on a mainnet fork,
simulating real-world conditions without risking real funds.
"""

import os
import sys
import json
import time
import logging
import argparse
import datetime
from typing import Dict, List, Any, Optional

# Import Web3 connector and Strategy Optimizer
from web3_connector import Web3Connector
from strategy_optimizer import StrategyOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mainnet_fork_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MainnetForkTest")

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run ArbitrageX on a mainnet fork")
    
    parser.add_argument("--networks", type=str, default="arbitrum,polygon",
                        help="Comma-separated list of networks to test (default: arbitrum,polygon)")
    
    parser.add_argument("--tokens", type=str, default="WETH,USDC,DAI,WBTC",
                        help="Comma-separated list of tokens to test")
    
    parser.add_argument("--dexes", type=str, default="uniswap_v3,sushiswap,curve,balancer",
                        help="Comma-separated list of DEXes to test")
    
    parser.add_argument("--fork-block", type=int, default=0,
                        help="Block number to fork from (0 for latest)")
    
    parser.add_argument("--run-time", type=int, default=300,
                        help="How long to run the test in seconds (default: 300)")
    
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Number of trades to process in each batch (default: 10)")
    
    parser.add_argument("--gas-strategy", type=str, default="dynamic",
                        choices=["conservative", "aggressive", "dynamic"],
                        help="Gas price strategy to use (default: dynamic)")
    
    parser.add_argument("--modules", type=str, default="all",
                        help="Comma-separated list of AI modules to test (default: all)")
    
    parser.add_argument("--output-dir", type=str, default="results",
                        help="Directory to save results (default: results)")
    
    parser.add_argument("--config-file", type=str, default="",
                        help="Path to configuration file")
    
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    return parser.parse_args()

def create_fork_config(args):
    """
    Create configuration for the mainnet fork test.
    
    Args:
        args: Command line arguments
        
    Returns:
        Configuration dictionary
    """
    # Parse networks, tokens, and DEXes
    networks = [n.strip() for n in args.networks.split(",")]
    tokens = [t.strip() for t in args.tokens.split(",")]
    dexes = [d.strip() for d in args.dexes.split(",")]
    
    # Check for trade selection and MEV protection configurations
    trade_selection_path = os.path.join(os.getcwd(), "config", "trade_selection_config.json")
    mev_protection_path = os.path.join(os.getcwd(), "config", "mev_protection_config.json")
    
    trade_selection_config = None
    mev_protection_config = None
    
    if os.path.exists(trade_selection_path):
        try:
            with open(trade_selection_path, "r") as f:
                trade_selection_config = json.load(f)
            logger.info(f"Loaded trade selection configuration from {trade_selection_path}")
        except Exception as e:
            logger.error(f"Error loading trade selection configuration: {e}")
    
    if os.path.exists(mev_protection_path):
        try:
            with open(mev_protection_path, "r") as f:
                mev_protection_config = json.load(f)
            logger.info(f"Loaded MEV protection configuration from {mev_protection_path}")
        except Exception as e:
            logger.error(f"Error loading MEV protection configuration: {e}")
    
    # Create fork configuration
    fork_config = {
        "mode": "mainnet_fork",
        "fork_url": "http://localhost:8545",
        "fork_block_number": args.fork_block if args.fork_block > 0 else "latest",
        "networks": networks,
        "tokens": {network: tokens for network in networks},
        "dexes": {network: dexes for network in networks},
        "gas_price_multiplier": 1.1,
        "slippage_tolerance": 0.005,
        "execution_timeout_ms": 5000,
        "simulation_only": False,  # Set to False to execute real transactions
        "log_level": "INFO"
    }
    
    # Add trade selection and MEV protection configurations if available
    if trade_selection_config:
        fork_config["trade_selection"] = trade_selection_config
    
    if mev_protection_config:
        fork_config["mev_protection"] = mev_protection_config
    
    # Save the configuration to a file
    config_path = os.path.join(os.getcwd(), "fork_config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(fork_config, f, indent=2)
        logger.info(f"Fork configuration saved to {config_path}")
    except Exception as e:
        logger.error(f"Error saving fork configuration: {e}")
    
    return fork_config, config_path

def run_mainnet_fork_test(args):
    """
    Run the mainnet fork test.
    
    Args:
        args: Command line arguments
    """
    # Create fork configuration
    fork_config, config_path = create_fork_config(args)
    
    # Initialize Web3 connector
    web3_connector = Web3Connector(config_path)
    
    if not web3_connector.is_connected():
        logger.error("Failed to connect to Hardhat fork. Make sure the Hardhat node is running.")
        return
    
    logger.info(f"Connected to Hardhat fork at block {web3_connector.web3.eth.block_number}")
    
    # Check if contracts are deployed
    if not web3_connector.contract_addresses:
        logger.error("No contract addresses found. Make sure contracts are deployed to the fork.")
        logger.info("You can deploy contracts using: npx hardhat run scripts/deploy.ts --network localhost")
        return
    
    # Initialize Strategy Optimizer with fork configuration
    optimizer = StrategyOptimizer(fork_config_path=config_path)
    
    if not optimizer.use_web3:
        logger.error("Strategy Optimizer failed to initialize Web3 connection.")
        return
    
    logger.info("Strategy Optimizer initialized with Web3 connection to Hardhat fork")
    
    # Determine which modules to run
    modules = args.modules.lower().split(",") if args.modules.lower() != "all" else ["strategy_optimizer", "backtesting", "trade_analyzer", "network_adaptation", "integration"]
    
    # Run the test
    start_time = time.time()
    end_time = start_time + args.run_time
    
    # Create results directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize results
    results = {
        "test_id": f"mainnet_fork_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "start_time": datetime.datetime.now().isoformat(),
        "configuration": {
            "networks": fork_config["networks"],
            "tokens": fork_config["tokens"],
            "dexes": fork_config["dexes"],
            "batch_size": args.batch_size,
            "gas_strategy": args.gas_strategy
        },
        "predictions": [],
        "trades": [],
        "summary": {}
    }
    
    # Run the test until the time is up
    logger.info(f"Starting mainnet fork test for {args.run_time} seconds")
    
    prediction_count = 0
    profitable_count = 0
    trade_count = 0
    successful_trade_count = 0
    total_profit = 0.0
    
    # Generate token pairs for testing
    token_pairs = []
    for network in fork_config["networks"]:
        network_tokens = fork_config["tokens"][network]
        for i in range(len(network_tokens)):
            for j in range(i + 1, len(network_tokens)):
                token_pairs.append({
                    "network": network,
                    "token_in": network_tokens[i],
                    "token_out": network_tokens[j]
                })
    
    # Main test loop
    while time.time() < end_time:
        # Process in batches
        for _ in range(args.batch_size):
            if time.time() >= end_time:
                break
            
            # Generate a test opportunity
            opportunity = generate_test_opportunity(token_pairs, web3_connector)
            
            # Predict if the opportunity is profitable
            prediction = optimizer.predict_opportunity(opportunity)
            prediction_count += 1
            
            # Add prediction to results
            results["predictions"].append({
                "opportunity": opportunity,
                "prediction": prediction
            })
            
            # If profitable, execute the trade
            if prediction["is_profitable"]:
                profitable_count += 1
                
                # Execute the trade
                trade_result = optimizer.execute_opportunity(opportunity)
                trade_count += 1
                
                # Add trade to results
                results["trades"].append({
                    "opportunity": opportunity,
                    "prediction": prediction,
                    "result": trade_result
                })
                
                # Update statistics
                if trade_result["success"]:
                    successful_trade_count += 1
                    total_profit += prediction["net_profit_usd"]
            
            # Sleep briefly to avoid overwhelming the node
            time.sleep(0.1)
        
        # Log progress
        elapsed = time.time() - start_time
        logger.info(f"Progress: {elapsed:.1f}/{args.run_time} seconds, "
                   f"{prediction_count} predictions, {profitable_count} profitable, "
                   f"{successful_trade_count}/{trade_count} trades successful")
    
    # Calculate summary statistics
    test_duration = time.time() - start_time
    
    # Network-specific statistics
    network_stats = {}
    for network in fork_config["networks"]:
        network_trades = [t for t in results["trades"] if t["opportunity"]["network"] == network]
        successful_network_trades = [t for t in network_trades if t["result"]["success"]]
        
        network_profit = sum(t["prediction"]["net_profit_usd"] for t in successful_network_trades)
        network_gas_cost = sum(t["prediction"]["gas_cost_usd"] for t in successful_network_trades)
        
        network_stats[network] = {
            "total_trades": len(network_trades),
            "successful_trades": len(successful_network_trades),
            "success_rate": len(successful_network_trades) / len(network_trades) if network_trades else 0,
            "total_profit_usd": sum(t["prediction"]["estimated_profit_usd"] for t in successful_network_trades),
            "total_gas_cost_usd": network_gas_cost,
            "net_profit_usd": network_profit
        }
    
    # Token pair statistics
    pair_stats = {}
    for trade in results["trades"]:
        if trade["result"]["success"]:
            pair = f"{trade['opportunity']['token_in']}-{trade['opportunity']['token_out']}"
            if pair not in pair_stats:
                pair_stats[pair] = {
                    "total_trades": 0,
                    "successful_trades": 0,
                    "total_profit_usd": 0.0
                }
            
            pair_stats[pair]["total_trades"] += 1
            pair_stats[pair]["successful_trades"] += 1
            pair_stats[pair]["total_profit_usd"] += trade["prediction"]["net_profit_usd"]
    
    # Find best performing network and token pair
    best_network = max(network_stats.items(), key=lambda x: x[1]["net_profit_usd"]) if network_stats else None
    best_pair = max(pair_stats.items(), key=lambda x: x[1]["total_profit_usd"]) if pair_stats else None
    
    # Create summary
    results["summary"] = {
        "test_duration_seconds": test_duration,
        "total_predictions": prediction_count,
        "profitable_predictions": profitable_count,
        "total_trades": trade_count,
        "successful_trades": successful_trade_count,
        "success_rate": successful_trade_count / trade_count if trade_count > 0 else 0,
        "total_profit_usd": total_profit,
        "network_stats": network_stats,
        "pair_stats": pair_stats,
        "best_network": best_network[0] if best_network else None,
        "best_pair": best_pair[0] if best_pair else None
    }
    
    # Save results
    results_file = os.path.join(args.output_dir, f"mainnet_fork_report_{results['test_id']}.json")
    try:
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {results_file}")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
    
    # Generate human-readable report
    report_file = os.path.join(args.output_dir, f"mainnet_fork_report_{results['test_id']}.txt")
    generate_report(results, report_file)
    
    logger.info(f"Test completed in {test_duration:.1f} seconds")
    logger.info(f"Total predictions: {prediction_count}, Profitable: {profitable_count}")
    logger.info(f"Total trades: {trade_count}, Successful: {successful_trade_count}")
    logger.info(f"Total profit: ${total_profit:.2f}")
    logger.info(f"Report saved to {report_file}")

def generate_test_opportunity(token_pairs, web3_connector):
    """
    Generate a test opportunity using real blockchain data.
    
    Args:
        token_pairs: List of token pairs to choose from
        web3_connector: Web3 connector instance
        
    Returns:
        Dictionary with opportunity details
    """
    # Choose a random token pair
    pair = token_pairs[int(time.time() * 1000) % len(token_pairs)]
    
    # Get token addresses
    token_addresses = {
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
    }
    
    # Router addresses
    router_addresses = {
        "uniswap_v2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "sushiswap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
    }
    
    # Choose a random router
    router_name = list(router_addresses.keys())[int(time.time() * 10000) % len(router_addresses)]
    
    # Create opportunity
    opportunity = {
        "network": pair["network"],
        "token_in": token_addresses.get(pair["token_in"], pair["token_in"]),
        "token_out": token_addresses.get(pair["token_out"], pair["token_out"]),
        "amount": web3_connector.web3.to_wei(1, "ether"),  # 1 ETH equivalent
        "router": router_addresses.get(router_name, router_name),
        "gas_price": 20,  # 20 Gwei
        "slippage": 0.5,  # 0.5%
        "deadline": int(time.time()) + 300  # 5 minutes
    }
    
    return opportunity

def generate_report(results, config):
    """
    Generate a report of the test results.
    
    Args:
        results: Test results
        config: Configuration dictionary
    """
    logger.info("Generating report")
    
    # Create output directory if it doesn't exist
    output_dir = config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for report filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_file = os.path.join(output_dir, f"mainnet_fork_report_{timestamp}.txt")
    
    # Extract analysis
    analysis = results["analysis"]
    
    # Write report
    with open(report_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("ArbitrageX Mainnet Fork Test Report\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Test Configuration:\n")
        f.write(f"  Networks: {', '.join(config['networks'])}\n")
        f.write(f"  Batch Size: {config['batch_size']}\n")
        f.write(f"  Gas Strategy: {config['gas_strategy']}\n\n")
        
        f.write("Summary:\n")
        f.write(f"  Total Predictions: {len(results['predictions'])}\n")
        f.write(f"  Profitable Predictions: {len(results['protected_trades'])}\n")
        f.write(f"  Executed Trades: {len(results['execution_results'])}\n")
        f.write(f"  Successful Trades: {analysis['successful_trades']}\n")
        f.write(f"  Success Rate: {analysis['success_rate']:.2%}\n")
        f.write(f"  Total Profit: ${analysis['total_profit_usd']:.2f}\n")
        f.write(f"  Average Profit per Successful Trade: ${analysis['avg_profit_per_successful_trade_usd']:.2f}\n\n")
        
        f.write("Performance by Network:\n")
        for network, stats in analysis["networks"].items():
            f.write(f"  {network}:\n")
            f.write(f"    Total Trades: {stats['total_trades']}\n")
            f.write(f"    Successful Trades: {stats['successful_trades']}\n")
            f.write(f"    Success Rate: {stats['success_rate']:.2%}\n")
            f.write(f"    Total Profit: ${stats['total_profit']:.2f}\n")
            f.write(f"    Total Gas Cost: ${stats['total_gas_cost']:.2f}\n")
            f.write(f"    Net Profit: ${stats['total_profit'] - stats['total_gas_cost']:.2f}\n")
            f.write(f"    Average Execution Time: {stats['avg_execution_time_ms']:.2f} ms\n\n")
        
        f.write("Best Performing:\n")
        f.write(f"  Network: {analysis['best_network']}\n")
        f.write(f"  Token Pair: {analysis['best_token_pair']}\n")
        f.write(f"  DEX: {analysis['best_dex']}\n\n")
        
        f.write("Conclusion:\n")
        if analysis['total_profit_usd'] > 0:
            f.write("  The AI system performed well in the mainnet fork test, identifying profitable\n")
            f.write("  arbitrage opportunities and executing them successfully.\n\n")
            
            # Recommendations
            f.write("  Recommendations:\n")
            
            # Network recommendations
            best_network = analysis['best_network']
            f.write(f"  - Focus on {best_network} for better profitability\n")
            
            # Token pair recommendations
            best_token_pair = analysis['best_token_pair']
            f.write(f"  - Prioritize {best_token_pair} trades\n")
            
            # DEX recommendations
            best_dex = analysis['best_dex']
            f.write(f"  - Utilize {best_dex} for better execution\n")
        else:
            f.write("  The AI system performed poorly in the mainnet fork test, identifying few\n")
            f.write("  profitable arbitrage opportunities. Further optimization is needed.\n\n")
            
            # Recommendations for improvement
            f.write("  Recommendations for Improvement:\n")
            f.write("  - Adjust trade selection criteria to be more selective\n")
            f.write("  - Optimize gas price strategy to reduce costs\n")
            f.write("  - Focus on networks with lower gas costs\n")
        
        f.write("\n")
        f.write("Note: All transactions were simulated on a mainnet fork. No real transactions were executed.\n")
    
    logger.info(f"Report generated at {report_file}")
    
    return report_file

def main(args=None):
    """
    Main function.
    
    Args:
        args: Command line arguments (optional). If None, arguments will be parsed from command line.
    """
    # Parse command line arguments if not provided
    if args is None:
        args = parse_arguments()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting ArbitrageX mainnet fork test")
    
    # Run the test
    run_mainnet_fork_test(args=args)
    
    logger.info("ArbitrageX mainnet fork test completed")

if __name__ == "__main__":
    main() 