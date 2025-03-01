#!/usr/bin/env python3
"""
ArbitrageX AI Module Runner

This script provides a command-line interface to run all AI modules
with a single command. It supports testnet mode and various options.
"""

import argparse
import os
import sys
import logging
import subprocess
import time
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AIModuleRunner")

def run_module(module_name, args, testnet=False, fork_config=None):
    """
    Run a specific AI module with the given arguments.
    
    Args:
        module_name: Name of the module to run
        args: Additional arguments to pass to the module
        testnet: Whether to run in testnet mode
        fork_config: Path to fork configuration file
    """
    # Special case for integration module
    if module_name == "integration":
        cmd = ["python3", "ai_integration.py"]
    else:
        cmd = ["python3", f"run_{module_name}.py"]
    
    if testnet:
        cmd.append("--testnet")
    
    if args:
        cmd.extend(args)
    
    # Add fork configuration if provided
    if fork_config:
        cmd.extend(["--fork-config", fork_config])
    
    logger.info(f"Running {module_name} module with command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"\n===== {module_name.upper()} OUTPUT =====\n")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {module_name} module: {e}")
        print(f"\n===== {module_name.upper()} ERROR =====\n")
        print(e.stderr)
        return False

def main():
    """Main entry point for the AI module runner."""
    parser = argparse.ArgumentParser(description="ArbitrageX AI Module Runner")
    parser.add_argument("--testnet", action="store_true", help="Run in testnet mode")
    parser.add_argument("--modules", type=str, default="all", 
                        help="Comma-separated list of modules to run (all, strategy_optimizer, backtesting, trade_analyzer, network_adaptation, test_ai_model, integration)")
    parser.add_argument("--visualize", action="store_true", help="Enable visualization for modules that support it")
    parser.add_argument("--save-results", action="store_true", help="Save results to files")
    parser.add_argument("--days", type=int, default=30, help="Number of days for historical data")
    parser.add_argument("--run-time", type=int, default=60, help="How long to run the integration module (in seconds)")
    parser.add_argument("--fork-config", type=str, help="Path to fork configuration file for mainnet fork mode")
    parser.add_argument("--output", type=str, help="Path to save the results JSON file")
    args = parser.parse_args()
    
    # Determine mode
    if args.fork_config:
        try:
            with open(args.fork_config, 'r') as f:
                fork_config = json.load(f)
            if fork_config.get('mode') == 'mainnet_fork':
                mode = "MAINNET FORK"
                logger.info(f"Running in MAINNET FORK mode with block {fork_config.get('blockNumber')}")
            else:
                mode = "CUSTOM MODE"
                logger.info(f"Running in custom mode with configuration from {args.fork_config}")
        except Exception as e:
            logger.error(f"Error loading fork configuration: {str(e)}")
            mode = "TESTNET" if args.testnet else "MAINNET"
    else:
        mode = "TESTNET" if args.testnet else "MAINNET"
    
    logger.info(f"Running in {mode} mode")
    
    # Determine which modules to run
    if args.modules.lower() == "all":
        modules = ["strategy_optimizer", "backtesting", "trade_analyzer", "network_adaptation", "test_ai_model", "integration"]
    else:
        modules = [m.strip() for m in args.modules.split(",")]
    
    logger.info(f"Running modules: {', '.join(modules)}")
    
    # Print header
    print("\n" + "=" * 80)
    print(f"ARBITRAGEX AI MODULE RUNNER - {mode} MODE")
    print("=" * 80 + "\n")
    print(f"Starting time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Running modules: {', '.join(modules)}")
    print(f"Visualization: {'Enabled' if args.visualize else 'Disabled'}")
    print(f"Save results: {'Enabled' if args.save_results else 'Disabled'}")
    print(f"Historical data days: {args.days}")
    print(f"Integration run time: {args.run_time} seconds")
    if args.fork_config:
        print(f"Fork configuration: {args.fork_config}")
    print("\n" + "=" * 80 + "\n")
    
    # Run each module
    results = {}
    
    for module in modules:
        print(f"\n\n{'=' * 40} RUNNING {module.upper()} {'=' * 40}\n")
        
        module_args = []
        
        # Add module-specific arguments
        if args.visualize and module != "integration":
            module_args.append("--visualize")
        
        if args.save_results and module in ["backtesting", "trade_analyzer"]:
            module_args.append("--save-results")
        
        if module in ["backtesting", "trade_analyzer"]:
            module_args.extend(["--days", str(args.days)])
            
        if module == "integration":
            module_args.extend(["--run-time", str(args.run_time)])
        
        # Run the module
        start_time = time.time()
        success = run_module(module, module_args, args.testnet, args.fork_config)
        end_time = time.time()
        
        # Store result
        results[module] = {
            "success": success,
            "execution_time": end_time - start_time
        }
    
    # Save results to file if output path is specified
    if args.output:
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(args.output), exist_ok=True)
            
            # Generate results data
            output_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "mode": mode,
                "modules": modules,
                "results": results,
                "total_execution_time": sum(r["execution_time"] for r in results.values()),
                "success_rate": sum(1 for r in results.values() if r["success"]) / len(results) if results else 0
            }
            
            # Add fork config details if available
            if args.fork_config and os.path.exists(args.fork_config):
                try:
                    with open(args.fork_config, 'r') as f:
                        fork_config = json.load(f)
                    output_data["fork_config"] = fork_config
                except Exception as e:
                    logger.warning(f"Could not load fork config for output: {e}")
            
            # Write to file
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            logger.info(f"Results saved to {args.output}")
        except Exception as e:
            logger.error(f"Error saving results to {args.output}: {e}")
    
    # Print summary
    print("\n\n" + "=" * 80)
    print("ARBITRAGEX AI MODULE RUNNER - SUMMARY")
    print("=" * 80 + "\n")
    
    for module, result in results.items():
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"{module.ljust(20)}: {status} ({result['execution_time']:.2f}s)")
    
    print("\n" + "=" * 80)
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    # Warning for testnet mode
    if args.testnet:
        print("\n⚠️ TESTNET MODE: No real transactions were executed")
    elif mode == "MAINNET FORK":
        print("\n🔄 MAINNET FORK MODE: Transactions were simulated on a mainnet fork (no real transactions executed)")
    elif mode == "MAINNET":
        print("\n⚠️ MAINNET MODE: Real transactions may have been executed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 