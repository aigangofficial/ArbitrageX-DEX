"""
Comprehensive Testing Framework for ArbitrageX

This script runs extended tests for the ArbitrageX system with multiple token pairs,
networks, and DEXes to ensure the system performs well under various market conditions.
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
import multiprocessing
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("comprehensive_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ComprehensiveTest")

# Import required modules
from backend.ai.web3_connector import Web3Connector
from backend.ai.strategy_optimizer import StrategyOptimizer
from backend.ai.learning_loop import LearningLoop
from backend.ai.trade_validator import TradeValidator

class ComprehensiveTest:
    """
    Comprehensive testing framework for ArbitrageX.
    """
    
    def __init__(self, 
                 duration_seconds: int = 3600,
                 networks: List[str] = ["ethereum"],
                 token_pairs: List[str] = ["WETH-USDC"],
                 dexes: List[str] = ["uniswap_v3", "sushiswap"],
                 fork_config_path: str = "backend/ai/hardhat_fork_config.json",
                 results_dir: str = "backend/ai/results/comprehensive_test"):
        """
        Initialize the comprehensive test.
        
        Args:
            duration_seconds: Test duration in seconds
            networks: List of networks to test
            token_pairs: List of token pairs to test
            dexes: List of DEXes to test
            fork_config_path: Path to the fork configuration file
            results_dir: Directory to store test results
        """
        self.duration_seconds = duration_seconds
        self.networks = networks
        self.token_pairs = token_pairs
        self.dexes = dexes
        self.fork_config_path = fork_config_path
        self.results_dir = results_dir
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize components
        self.web3_connector = None
        self.strategy_optimizer = None
        self.learning_loop = None
        self.trade_validator = None
        
        # Initialize test metrics
        self.test_metrics = {
            "start_time": None,
            "end_time": None,
            "total_opportunities": 0,
            "valid_opportunities": 0,
            "executed_trades": 0,
            "successful_trades": 0,
            "total_profit_usd": 0.0,
            "total_gas_cost_usd": 0.0,
            "net_profit_usd": 0.0,
            "avg_execution_time_ms": 0.0,
            "network_metrics": {},
            "token_pair_metrics": {},
            "dex_metrics": {}
        }
        
        # Initialize network-specific metrics
        for network in self.networks:
            self.test_metrics["network_metrics"][network] = {
                "opportunities": 0,
                "valid_opportunities": 0,
                "executed_trades": 0,
                "successful_trades": 0,
                "profit_usd": 0.0,
                "gas_cost_usd": 0.0,
                "net_profit_usd": 0.0
            }
        
        # Initialize token pair-specific metrics
        for token_pair in self.token_pairs:
            self.test_metrics["token_pair_metrics"][token_pair] = {
                "opportunities": 0,
                "valid_opportunities": 0,
                "executed_trades": 0,
                "successful_trades": 0,
                "profit_usd": 0.0,
                "gas_cost_usd": 0.0,
                "net_profit_usd": 0.0
            }
        
        # Initialize DEX-specific metrics
        for dex in self.dexes:
            self.test_metrics["dex_metrics"][dex] = {
                "opportunities": 0,
                "valid_opportunities": 0,
                "executed_trades": 0,
                "successful_trades": 0,
                "profit_usd": 0.0,
                "gas_cost_usd": 0.0,
                "net_profit_usd": 0.0
            }
        
        # Initialize stop event
        self.stop_event = threading.Event()
    
    def initialize_components(self):
        """
        Initialize all required components.
        """
        logger.info("Initializing components...")
        
        # Initialize Web3 connector
        self.web3_connector = Web3Connector(self.fork_config_path)
        if not self.web3_connector.is_connected():
            logger.error("Failed to connect to Hardhat fork")
            return False
        
        logger.info(f"Connected to Hardhat fork at block {self.web3_connector.web3.eth.block_number}")
        
        # Initialize Strategy Optimizer
        self.strategy_optimizer = StrategyOptimizer(fork_config_path=self.fork_config_path)
        
        # Initialize Learning Loop
        self.learning_loop = LearningLoop()
        self.learning_loop.start()
        
        # Initialize Trade Validator
        self.trade_validator = TradeValidator()
        
        logger.info("All components initialized successfully")
        return True
    
    def generate_opportunity(self, network: str, token_pair: str, dex: str) -> Dict[str, Any]:
        """
        Generate a synthetic arbitrage opportunity.
        
        Args:
            network: Network for the opportunity
            token_pair: Token pair for the opportunity
            dex: DEX for the opportunity
            
        Returns:
            Dictionary representing the opportunity
        """
        # Parse token pair
        token_in, token_out = token_pair.split("-")
        
        # Generate random amount (between 0.1 and 10)
        amount_in = 0.1 + (10 - 0.1) * (hash(f"{network}-{token_pair}-{dex}-{time.time()}") % 1000) / 1000
        
        # Generate estimated profit (between 0.001 and 0.05)
        estimated_profit = 0.001 + (0.05 - 0.001) * (hash(f"{network}-{token_pair}-{dex}-{time.time()+1}") % 1000) / 1000
        
        # Create opportunity
        opportunity = {
            "network": network,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount_in,
            "estimated_profit": estimated_profit,
            "route": [
                {"dex": dex, "token_in": token_in, "token_out": token_out},
                {"dex": "sushiswap" if dex != "sushiswap" else "uniswap_v3", "token_in": token_out, "token_out": token_in}
            ],
            "gas_estimate": 200000 + (hash(f"{network}-{token_pair}-{dex}-{time.time()+2}") % 100000),
            "execution_priority": "medium",
            "slippage_tolerance": 0.005,
            "timestamp": int(time.time())
        }
        
        return opportunity
    
    def process_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an arbitrage opportunity.
        
        Args:
            opportunity: Opportunity to process
            
        Returns:
            Dictionary with processing results
        """
        # Update metrics
        self.test_metrics["total_opportunities"] += 1
        self.test_metrics["network_metrics"][opportunity["network"]]["opportunities"] += 1
        token_pair = f"{opportunity['token_in']}-{opportunity['token_out']}"
        self.test_metrics["token_pair_metrics"][token_pair]["opportunities"] += 1
        dex = opportunity["route"][0]["dex"]
        self.test_metrics["dex_metrics"][dex]["opportunities"] += 1
        
        # Validate opportunity
        validation_result = self.trade_validator.validate_trade(opportunity)
        
        if not validation_result["is_valid"]:
            logger.info(f"Opportunity validation failed: {validation_result['failure_reasons']}")
            return {
                "success": False,
                "validation_result": validation_result,
                "reason": "Validation failed"
            }
        
        # Update metrics for valid opportunities
        self.test_metrics["valid_opportunities"] += 1
        self.test_metrics["network_metrics"][opportunity["network"]]["valid_opportunities"] += 1
        self.test_metrics["token_pair_metrics"][token_pair]["valid_opportunities"] += 1
        self.test_metrics["dex_metrics"][dex]["valid_opportunities"] += 1
        
        # Predict opportunity
        prediction = self.strategy_optimizer.predict_opportunity(opportunity)
        
        if not prediction.get("is_profitable", False):
            logger.info(f"Opportunity not profitable: {prediction}")
            return {
                "success": False,
                "prediction": prediction,
                "reason": "Not profitable"
            }
        
        # Execute opportunity
        logger.info(f"Executing opportunity: {opportunity}")
        self.test_metrics["executed_trades"] += 1
        self.test_metrics["network_metrics"][opportunity["network"]]["executed_trades"] += 1
        self.test_metrics["token_pair_metrics"][token_pair]["executed_trades"] += 1
        self.test_metrics["dex_metrics"][dex]["executed_trades"] += 1
        
        # Simulate execution (since we're in a test environment)
        execution_result = {
            "success": True,
            "profit_usd": prediction["estimated_profit_usd"],
            "gas_cost_usd": prediction["gas_cost_usd"],
            "net_profit_usd": prediction["net_profit_usd"],
            "execution_time_ms": prediction["execution_time_ms"],
            "tx_hash": f"0x{hash(str(opportunity) + str(time.time())):x}",
            "block_number": self.web3_connector.web3.eth.block_number,
            "timestamp": int(time.time())
        }
        
        # Update metrics for successful trades
        if execution_result["success"]:
            self.test_metrics["successful_trades"] += 1
            self.test_metrics["network_metrics"][opportunity["network"]]["successful_trades"] += 1
            self.test_metrics["token_pair_metrics"][token_pair]["successful_trades"] += 1
            self.test_metrics["dex_metrics"][dex]["successful_trades"] += 1
            
            self.test_metrics["total_profit_usd"] += execution_result["profit_usd"]
            self.test_metrics["network_metrics"][opportunity["network"]]["profit_usd"] += execution_result["profit_usd"]
            self.test_metrics["token_pair_metrics"][token_pair]["profit_usd"] += execution_result["profit_usd"]
            self.test_metrics["dex_metrics"][dex]["profit_usd"] += execution_result["profit_usd"]
            
            self.test_metrics["total_gas_cost_usd"] += execution_result["gas_cost_usd"]
            self.test_metrics["network_metrics"][opportunity["network"]]["gas_cost_usd"] += execution_result["gas_cost_usd"]
            self.test_metrics["token_pair_metrics"][token_pair]["gas_cost_usd"] += execution_result["gas_cost_usd"]
            self.test_metrics["dex_metrics"][dex]["gas_cost_usd"] += execution_result["gas_cost_usd"]
            
            self.test_metrics["net_profit_usd"] += execution_result["net_profit_usd"]
            self.test_metrics["network_metrics"][opportunity["network"]]["net_profit_usd"] += execution_result["net_profit_usd"]
            self.test_metrics["token_pair_metrics"][token_pair]["net_profit_usd"] += execution_result["net_profit_usd"]
            self.test_metrics["dex_metrics"][dex]["net_profit_usd"] += execution_result["net_profit_usd"]
            
            # Add execution result to learning loop
            self.learning_loop.add_execution_result(execution_result)
        
        return {
            "success": True,
            "execution_result": execution_result
        }
    
    def run_test(self):
        """
        Run the comprehensive test.
        """
        logger.info(f"Starting comprehensive test for {self.duration_seconds} seconds")
        logger.info(f"Networks: {self.networks}")
        logger.info(f"Token pairs: {self.token_pairs}")
        logger.info(f"DEXes: {self.dexes}")
        
        # Initialize components
        if not self.initialize_components():
            logger.error("Failed to initialize components, aborting test")
            return
        
        # Set start time
        self.test_metrics["start_time"] = datetime.now().isoformat()
        start_time = time.time()
        
        # Run test until duration is reached or stop event is set
        try:
            while time.time() - start_time < self.duration_seconds and not self.stop_event.is_set():
                # Generate and process opportunities for each network, token pair, and DEX
                for network in self.networks:
                    for token_pair in self.token_pairs:
                        for dex in self.dexes:
                            # Generate opportunity
                            opportunity = self.generate_opportunity(network, token_pair, dex)
                            
                            # Process opportunity
                            result = self.process_opportunity(opportunity)
                            
                            # Log result
                            if result["success"]:
                                logger.info(f"Trade executed successfully: profit={result['execution_result']['profit_usd']:.2f} USD, gas={result['execution_result']['gas_cost_usd']:.2f} USD, net={result['execution_result']['net_profit_usd']:.2f} USD")
                            else:
                                logger.info(f"Trade not executed: {result['reason']}")
                            
                            # Sleep to avoid overwhelming the system
                            time.sleep(1)
                
                # Log progress every minute
                if int(time.time() - start_time) % 60 == 0:
                    elapsed_seconds = int(time.time() - start_time)
                    remaining_seconds = self.duration_seconds - elapsed_seconds
                    logger.info(f"Test progress: {elapsed_seconds}/{self.duration_seconds} seconds ({elapsed_seconds/self.duration_seconds*100:.1f}%), remaining: {remaining_seconds} seconds")
                    logger.info(f"Metrics so far: {self.test_metrics['successful_trades']}/{self.test_metrics['executed_trades']} successful trades, net profit: {self.test_metrics['net_profit_usd']:.2f} USD")
        
        except KeyboardInterrupt:
            logger.info("Test interrupted by user")
        except Exception as e:
            logger.error(f"Error during test: {e}")
        finally:
            # Set end time
            self.test_metrics["end_time"] = datetime.now().isoformat()
            
            # Calculate average execution time
            if self.test_metrics["executed_trades"] > 0:
                self.test_metrics["avg_execution_time_ms"] = sum([result["execution_time_ms"] for result in self.test_metrics.get("execution_results", [])]) / self.test_metrics["executed_trades"]
            
            # Stop learning loop
            if self.learning_loop:
                self.learning_loop.stop()
            
            # Save test metrics
            self.save_test_metrics()
            
            # Log test summary
            self.log_test_summary()
    
    def save_test_metrics(self):
        """
        Save test metrics to a JSON file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = os.path.join(self.results_dir, f"test_metrics_{timestamp}.json")
        
        with open(metrics_file, 'w') as f:
            json.dump(self.test_metrics, f, indent=2)
        
        logger.info(f"Test metrics saved to {metrics_file}")
    
    def log_test_summary(self):
        """
        Log a summary of the test results.
        """
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Test duration: {self.duration_seconds} seconds")
        logger.info(f"Start time: {self.test_metrics['start_time']}")
        logger.info(f"End time: {self.test_metrics['end_time']}")
        logger.info(f"Total opportunities: {self.test_metrics['total_opportunities']}")
        logger.info(f"Valid opportunities: {self.test_metrics['valid_opportunities']} ({self.test_metrics['valid_opportunities']/self.test_metrics['total_opportunities']*100:.1f}%)")
        logger.info(f"Executed trades: {self.test_metrics['executed_trades']}")
        logger.info(f"Successful trades: {self.test_metrics['successful_trades']} ({self.test_metrics['successful_trades']/self.test_metrics['executed_trades']*100:.1f}% success rate)")
        logger.info(f"Total profit: {self.test_metrics['total_profit_usd']:.2f} USD")
        logger.info(f"Total gas cost: {self.test_metrics['total_gas_cost_usd']:.2f} USD")
        logger.info(f"Net profit: {self.test_metrics['net_profit_usd']:.2f} USD")
        logger.info(f"Average execution time: {self.test_metrics['avg_execution_time_ms']:.2f} ms")
        
        logger.info("-" * 80)
        logger.info("NETWORK METRICS")
        for network, metrics in self.test_metrics["network_metrics"].items():
            logger.info(f"Network: {network}")
            logger.info(f"  Opportunities: {metrics['opportunities']}")
            logger.info(f"  Valid opportunities: {metrics['valid_opportunities']} ({metrics['valid_opportunities']/metrics['opportunities']*100:.1f}%)")
            logger.info(f"  Executed trades: {metrics['executed_trades']}")
            logger.info(f"  Successful trades: {metrics['successful_trades']} ({metrics['successful_trades']/metrics['executed_trades']*100:.1f}% success rate)")
            logger.info(f"  Net profit: {metrics['net_profit_usd']:.2f} USD")
        
        logger.info("-" * 80)
        logger.info("TOKEN PAIR METRICS")
        for token_pair, metrics in self.test_metrics["token_pair_metrics"].items():
            logger.info(f"Token pair: {token_pair}")
            logger.info(f"  Opportunities: {metrics['opportunities']}")
            logger.info(f"  Valid opportunities: {metrics['valid_opportunities']} ({metrics['valid_opportunities']/metrics['opportunities']*100:.1f}%)")
            logger.info(f"  Executed trades: {metrics['executed_trades']}")
            logger.info(f"  Successful trades: {metrics['successful_trades']} ({metrics['successful_trades']/metrics['executed_trades']*100:.1f}% success rate)")
            logger.info(f"  Net profit: {metrics['net_profit_usd']:.2f} USD")
        
        logger.info("-" * 80)
        logger.info("DEX METRICS")
        for dex, metrics in self.test_metrics["dex_metrics"].items():
            logger.info(f"DEX: {dex}")
            logger.info(f"  Opportunities: {metrics['opportunities']}")
            logger.info(f"  Valid opportunities: {metrics['valid_opportunities']} ({metrics['valid_opportunities']/metrics['opportunities']*100:.1f}%)")
            logger.info(f"  Executed trades: {metrics['executed_trades']}")
            logger.info(f"  Successful trades: {metrics['successful_trades']} ({metrics['successful_trades']/metrics['executed_trades']*100:.1f}% success rate)")
            logger.info(f"  Net profit: {metrics['net_profit_usd']:.2f} USD")
        
        logger.info("=" * 80)

def main():
    """
    Main function to run the comprehensive test.
    """
    parser = argparse.ArgumentParser(description='Comprehensive Test for ArbitrageX')
    parser.add_argument('--duration', type=int, default=3600, help='Test duration in seconds')
    parser.add_argument('--networks', type=str, default='ethereum', help='Comma-separated list of networks to test')
    parser.add_argument('--token-pairs', type=str, default='WETH-USDC', help='Comma-separated list of token pairs to test')
    parser.add_argument('--dexes', type=str, default='uniswap_v3,sushiswap', help='Comma-separated list of DEXes to test')
    parser.add_argument('--fork-config', type=str, default='backend/ai/hardhat_fork_config.json', help='Path to fork configuration file')
    parser.add_argument('--results-dir', type=str, default='backend/ai/results/comprehensive_test', help='Directory to store test results')
    
    args = parser.parse_args()
    
    # Parse arguments
    networks = args.networks.split(',')
    token_pairs = args.token_pairs.split(',')
    dexes = args.dexes.split(',')
    
    # Create and run test
    test = ComprehensiveTest(
        duration_seconds=args.duration,
        networks=networks,
        token_pairs=token_pairs,
        dexes=dexes,
        fork_config_path=args.fork_config,
        results_dir=args.results_dir
    )
    
    test.run_test()

if __name__ == "__main__":
    main() 