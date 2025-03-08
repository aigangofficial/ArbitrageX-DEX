#!/usr/bin/env python3
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