#!/usr/bin/env python3
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
    main()