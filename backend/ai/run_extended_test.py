#!/usr/bin/env python3
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
    main() 