#!/usr/bin/env python3
"""
AI Integration Module for ArbitrageX

This module serves as the integration point between the AI system and the rest of the ArbitrageX platform,
including the execution engine and frontend dashboard.

It provides:
1. API endpoints for the frontend to access AI predictions and insights
2. Websocket connections for real-time updates
3. Integration with the execution engine for automated trading
4. Monitoring and logging of AI system performance
"""

import os
import sys
import json
import time
import logging
import argparse
import threading
import datetime
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AI-Integration")

class AIIntegration:
    """
    Main class for integrating the AI system with the execution engine and frontend dashboard.
    """
    
    def __init__(self, testnet: bool = True, fork_config: Optional[str] = None):
        """
        Initialize the AI Integration module.
        
        Args:
            testnet: Whether to run in testnet mode (default: True)
            fork_config: Path to fork configuration file (optional)
        """
        self.testnet = testnet
        self.fork_config = None
        
        # Load fork configuration if provided
        if fork_config and os.path.exists(fork_config):
            try:
                with open(fork_config, 'r') as f:
                    self.fork_config = json.load(f)
                logger.info(f"Loaded fork configuration from {fork_config}")
                
                # If we're in fork mode, we're simulating mainnet
                if self.fork_config.get('mode') == 'mainnet_fork':
                    self.testnet = False
                    logger.info(f"Running in MAINNET FORK mode with block {self.fork_config.get('blockNumber')}")
            except Exception as e:
                logger.error(f"Error loading fork configuration: {str(e)}")
        
        self.mode = "TESTNET" if testnet else ("MAINNET FORK" if self.fork_config else "MAINNET")
        logger.info(f"Initializing AI Integration in {self.mode} mode")
        
        # Initialize state variables
        self.running = False
        self.last_prediction = None
        self.prediction_history = []
        self.execution_history = []
        
        # Create directories if they don't exist
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("results", exist_ok=True)
        
        # Load contract addresses if available
        self.contract_addresses = {}
        if self.fork_config and 'contractAddresses' in self.fork_config:
            self.contract_addresses = self.fork_config['contractAddresses']
            logger.info(f"Loaded contract addresses from fork configuration")
        else:
            # Try to load from the standard location
            contract_addresses_path = os.path.join("..", "..", "backend", "config", "contractAddresses.json")
            if os.path.exists(contract_addresses_path):
                try:
                    with open(contract_addresses_path, 'r') as f:
                        self.contract_addresses = json.load(f)
                    logger.info(f"Loaded contract addresses from {contract_addresses_path}")
                except Exception as e:
                    logger.error(f"Error loading contract addresses: {str(e)}")
        
        logger.info("AI Integration initialized successfully")
    
    def start(self):
        """Start the AI Integration service."""
        if self.running:
            logger.warning("AI Integration is already running")
            return
        
        logger.info(f"Starting AI Integration service in {self.mode} mode")
        self.running = True
        
        # Start the main processing loop in a separate thread
        self.thread = threading.Thread(target=self._processing_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("AI Integration service started")
    
    def stop(self):
        """Stop the AI Integration service."""
        if not self.running:
            logger.warning("AI Integration is not running")
            return
        
        logger.info("Stopping AI Integration service")
        self.running = False
        self.thread.join(timeout=5.0)
        logger.info("AI Integration service stopped")
    
    def _processing_loop(self):
        """Main processing loop for the AI Integration service."""
        logger.info("Starting AI processing loop")
        
        while self.running:
            try:
                # 1. Get market data
                market_data = self._get_market_data()
                
                # 2. Run AI prediction
                prediction = self._run_ai_prediction(market_data)
                
                # 3. Evaluate execution criteria
                should_execute, reason = self._evaluate_execution_criteria(prediction)
                
                # 4. Execute trade if criteria are met
                if should_execute:
                    self._execute_trade(prediction)
                else:
                    logger.info(f"Trade execution skipped: {reason}")
                
                # 5. Update frontend
                self._update_frontend(prediction, should_execute, reason)
                
                # 6. Store results
                self._store_results(prediction, should_execute, reason)
                
                # Sleep for a short period before the next iteration
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in AI processing loop: {str(e)}")
                time.sleep(10)  # Sleep longer on error
    
    def _get_market_data(self) -> Dict[str, Any]:
        """
        Get current market data from various sources.
        
        Returns:
            Dict containing market data
        """
        logger.debug("Getting market data")
        
        # In a real implementation, this would fetch data from DEXes, price oracles, etc.
        # For mainnet fork mode, we would use the forked blockchain state
        
        # If we're in fork mode, we can use more realistic data based on the fork
        if self.fork_config and self.fork_config.get('mode') == 'mainnet_fork':
            # In a real implementation, this would query the forked blockchain
            # For now, we'll use slightly modified synthetic data to simulate real conditions
            
            # Add some randomness to simulate real market conditions
            import random
            
            # Base prices with slight variations to simulate real market conditions
            eth_price = 1820.0 + random.uniform(-10, 10)
            btc_price = 62150.0 + random.uniform(-100, 100)
            link_price = 15.85 + random.uniform(-0.2, 0.2)
            
            # Create price variations across DEXes (more realistic spreads)
            market_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "networks": {
                    "ethereum": {
                        "gas_price": 45 + random.uniform(-5, 15),  # gwei
                        "congestion": random.choice(["low", "medium", "high"]),
                        "block_time": 12 + random.uniform(-1, 2)  # seconds
                    },
                    "arbitrum": {
                        "gas_price": 0.1 + random.uniform(0, 0.2),  # gwei
                        "congestion": random.choice(["low", "medium"]),
                        "block_time": 0.25 + random.uniform(0, 0.1)  # seconds
                    },
                    "polygon": {
                        "gas_price": 80 + random.uniform(-10, 40),  # gwei
                        "congestion": random.choice(["medium", "high"]),
                        "block_time": 2 + random.uniform(-0.2, 0.5)  # seconds
                    }
                },
                "token_pairs": {
                    "WETH-USDC": {
                        "uniswap": eth_price + random.uniform(-0.5, 0.5),
                        "sushiswap": eth_price + random.uniform(-0.7, 0.3),
                        "curve": eth_price + random.uniform(-0.3, 0.6),
                        "balancer": eth_price + random.uniform(-0.4, 0.4),
                        "1inch": eth_price + random.uniform(-0.2, 0.2)
                    },
                    "WBTC-USDC": {
                        "uniswap": btc_price + random.uniform(-15, 15),
                        "sushiswap": btc_price + random.uniform(-20, 10),
                        "curve": btc_price + random.uniform(-10, 20),
                        "balancer": btc_price + random.uniform(-12, 18),
                        "1inch": btc_price + random.uniform(-8, 8)
                    },
                    "LINK-USDC": {
                        "uniswap": link_price + random.uniform(-0.05, 0.05),
                        "sushiswap": link_price + random.uniform(-0.08, 0.03),
                        "curve": link_price + random.uniform(-0.03, 0.06),
                        "balancer": link_price + random.uniform(-0.04, 0.04),
                        "1inch": link_price + random.uniform(-0.02, 0.02)
                    }
                }
            }
            
            # Add block number from fork if available
            if 'blockNumber' in self.fork_config:
                market_data["blockNumber"] = self.fork_config['blockNumber']
            
            return market_data
        else:
            # Use the original synthetic data for testnet/demo mode
            market_data = {
                "timestamp": datetime.datetime.now().isoformat(),
                "networks": {
                    "ethereum": {
                        "gas_price": 50,  # gwei
                        "congestion": "medium",
                        "block_time": 12  # seconds
                    },
                    "arbitrum": {
                        "gas_price": 0.1,  # gwei
                        "congestion": "low",
                        "block_time": 0.25  # seconds
                    },
                    "polygon": {
                        "gas_price": 100,  # gwei
                        "congestion": "high",
                        "block_time": 2  # seconds
                    }
                },
                "token_pairs": {
                    "WETH-USDC": {
                        "uniswap": 1820.45,
                        "sushiswap": 1819.87,
                        "curve": 1820.12,
                        "balancer": 1820.32,
                        "1inch": 1820.05
                    },
                    "WBTC-USDC": {
                        "uniswap": 62150.25,
                        "sushiswap": 62145.87,
                        "curve": 62148.32,
                        "balancer": 62152.18,
                        "1inch": 62149.75
                    },
                    "LINK-USDC": {
                        "uniswap": 15.87,
                        "sushiswap": 15.85,
                        "curve": 15.86,
                        "balancer": 15.88,
                        "1inch": 15.87
                    }
                }
            }
            
            return market_data
    
    def _run_ai_prediction(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run AI prediction based on market data.
        
        Args:
            market_data: Current market data
            
        Returns:
            Dict containing AI prediction results
        """
        logger.debug("Running AI prediction")
        
        # In a real implementation, this would call the actual AI models
        # For demonstration purposes, we'll simulate AI predictions
        
        # Find the best arbitrage opportunity
        best_opportunity = None
        best_profit = 0
        
        for pair, prices in market_data["token_pairs"].items():
            # Find min and max prices
            min_price = min(prices.values())
            max_price = max(prices.values())
            
            # Find exchanges with min and max prices
            min_exchange = next(exchange for exchange, price in prices.items() if price == min_price)
            max_exchange = next(exchange for exchange, price in prices.items() if price == max_price)
            
            # Calculate potential profit (simplified)
            profit = (max_price - min_price) / min_price * 100  # percentage
            
            if profit > best_profit:
                best_profit = profit
                best_opportunity = {
                    "pair": pair,
                    "buy_exchange": min_exchange,
                    "sell_exchange": max_exchange,
                    "buy_price": min_price,
                    "sell_price": max_price,
                    "profit_percentage": profit
                }
        
        # Calculate confidence score (simplified)
        confidence = min(best_profit / 0.5, 0.95)  # Cap at 0.95
        
        # Estimate gas costs
        network = "ethereum"  # Default
        gas_price = market_data["networks"][network]["gas_price"]
        estimated_gas = 250000  # Typical gas for a complex swap
        gas_cost_eth = gas_price * estimated_gas / 1e9
        gas_cost_usd = gas_cost_eth * market_data["token_pairs"]["WETH-USDC"]["uniswap"]
        
        # Calculate net profit
        amount_in = 1.0  # ETH
        gross_profit_usd = amount_in * best_opportunity["profit_percentage"] / 100
        net_profit_usd = gross_profit_usd - gas_cost_usd
        
        # Determine if trade is profitable
        is_profitable = net_profit_usd > 0
        
        # In mainnet fork mode, we apply more realistic constraints
        if self.fork_config and self.fork_config.get('mode') == 'mainnet_fork':
            # Add slippage impact (more realistic in production)
            slippage_impact = gross_profit_usd * 0.05  # 5% slippage impact
            net_profit_usd -= slippage_impact
            
            # Recalculate profitability with slippage
            is_profitable = net_profit_usd > 0
            
            # Add MEV protection costs if profitable
            if is_profitable:
                mev_protection_cost = gross_profit_usd * 0.02  # 2% for MEV protection
                net_profit_usd -= mev_protection_cost
                
                # Recalculate profitability with MEV protection
                is_profitable = net_profit_usd > 0
        
        prediction = {
            "timestamp": market_data["timestamp"],
            "network": network,
            "token_pair": best_opportunity["pair"],
            "buy_exchange": best_opportunity["buy_exchange"],
            "sell_exchange": best_opportunity["sell_exchange"],
            "amount_in": amount_in,
            "expected_profit_usd": gross_profit_usd,
            "gas_cost_usd": gas_cost_usd,
            "net_profit_usd": net_profit_usd,
            "confidence_score": confidence,
            "is_profitable": is_profitable,
            "execution_time_ms": 120.5,  # Simulated execution time
            "recommendations": {
                "optimal_gas_price": gas_price * 1.1,  # 10% higher for faster inclusion
                "recommended_dex": best_opportunity["buy_exchange"],
                "slippage_tolerance": 0.5,  # percentage
                "execution_priority": "high" if is_profitable and confidence > 0.7 else "medium"
            }
        }
        
        # Add block number if available
        if "blockNumber" in market_data:
            prediction["blockNumber"] = market_data["blockNumber"]
        
        self.last_prediction = prediction
        self.prediction_history.append(prediction)
        
        logger.info(f"AI Prediction: {prediction['token_pair']} - Profitable: {'YES' if is_profitable else 'NO'} - Confidence: {confidence:.4f}")
        
        return prediction
    
    def _evaluate_execution_criteria(self, prediction: Dict[str, Any]) -> tuple:
        """
        Evaluate whether a trade should be executed based on the AI prediction.
        
        Args:
            prediction: AI prediction results
            
        Returns:
            Tuple of (should_execute, reason)
        """
        logger.debug("Evaluating execution criteria")
        
        # In testnet mode, never execute real trades
        if self.testnet:
            return False, "TESTNET mode - no real execution"
        
        # In mainnet fork mode, we simulate execution but don't actually execute
        if self.fork_config and self.fork_config.get('mode') == 'mainnet_fork':
            # Check if trade is profitable
            if not prediction["is_profitable"]:
                return False, f"Trade not profitable (${prediction['net_profit_usd']:.2f})"
            
            # Check confidence score
            if prediction["confidence_score"] < 0.7:
                return False, f"Confidence too low ({prediction['confidence_score']:.2f})"
            
            # Check minimum profit threshold (higher in mainnet fork for realism)
            if prediction["net_profit_usd"] < 10.0:
                return False, f"Profit too small (${prediction['net_profit_usd']:.2f})"
            
            # All criteria passed - in fork mode, we simulate execution
            return True, "All criteria passed (FORK MODE - simulated execution)"
        
        # In real mainnet mode, apply strict criteria
        # Check if trade is profitable
        if not prediction["is_profitable"]:
            return False, f"Trade not profitable (${prediction['net_profit_usd']:.2f})"
        
        # Check confidence score
        if prediction["confidence_score"] < 0.7:
            return False, f"Confidence too low ({prediction['confidence_score']:.2f})"
        
        # Check minimum profit threshold
        if prediction["net_profit_usd"] < 5.0:
            return False, f"Profit too small (${prediction['net_profit_usd']:.2f})"
        
        # All criteria passed
        return True, "All criteria passed"
    
    def _execute_trade(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trade based on the AI prediction.
        
        Args:
            prediction: AI prediction results
            
        Returns:
            Dict containing execution results
        """
        logger.info(f"Executing trade: {prediction['token_pair']} on {prediction['network']}")
        
        # In a real implementation, this would call the execution engine
        # For demonstration purposes, we'll simulate execution
        
        # Simulate execution success/failure
        success = True  # In a real system, this would be the actual result
        
        # In mainnet fork mode, we simulate more realistic execution results
        if self.fork_config and self.fork_config.get('mode') == 'mainnet_fork':
            # Simulate occasional failures
            import random
            success_rate = 0.85  # 85% success rate
            success = random.random() < success_rate
            
            # Simulate varying execution times
            execution_time_ms = 120 + random.uniform(0, 80)
            
            # Simulate varying gas usage
            gas_used = int(245000 + random.uniform(-20000, 30000))
            
            # Simulate varying actual profit (due to slippage, etc.)
            profit_factor = 0.85 + random.uniform(0, 0.2)  # 85-105% of expected profit
            actual_profit_usd = prediction["net_profit_usd"] * profit_factor if success else 0
            
            # Generate a realistic tx hash
            tx_hash = "0x" + "".join([f"{random.randint(0, 15):x}" for _ in range(64)])
        else:
            # Standard simulation values
            execution_time_ms = 150.2
            gas_used = 245000
            actual_profit_usd = prediction["net_profit_usd"] * 0.95
            tx_hash = "0x" + "".join([f"{i:x}" for i in os.urandom(32)])
        
        execution_result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "prediction": prediction,
            "success": success,
            "tx_hash": tx_hash,
            "actual_profit_usd": actual_profit_usd,
            "execution_time_ms": execution_time_ms,
            "gas_used": gas_used,
        }
        
        # Add block number if available
        if "blockNumber" in prediction:
            execution_result["blockNumber"] = prediction["blockNumber"]
        
        self.execution_history.append(execution_result)
        
        logger.info(f"Trade execution {'successful' if success else 'failed'}")
        
        return execution_result
    
    def _update_frontend(self, prediction: Dict[str, Any], should_execute: bool, reason: str) -> None:
        """
        Update the frontend with the latest AI prediction and execution status.
        
        Args:
            prediction: AI prediction results
            should_execute: Whether the trade should be executed
            reason: Reason for execution decision
        """
        logger.debug("Updating frontend")
        
        # In a real implementation, this would send data to the frontend via WebSocket
        # For demonstration purposes, we'll just log the update
        
        frontend_update = {
            "timestamp": datetime.datetime.now().isoformat(),
            "prediction": prediction,
            "should_execute": should_execute,
            "reason": reason,
            "execution_history": self.execution_history[-5:] if self.execution_history else [],
            "mode": self.mode
        }
        
        logger.debug(f"Frontend update: {json.dumps(frontend_update, indent=2)}")
    
    def _store_results(self, prediction: Dict[str, Any], should_execute: bool, reason: str) -> None:
        """
        Store AI prediction and execution results for later analysis.
        
        Args:
            prediction: AI prediction results
            should_execute: Whether the trade should be executed
            reason: Reason for execution decision
        """
        logger.debug("Storing results")
        
        # Create a results object
        result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "prediction": prediction,
            "should_execute": should_execute,
            "reason": reason,
            "mode": self.mode
        }
        
        # In a real implementation, this would store data in a database
        # For demonstration purposes, we'll write to a JSON file
        
        results_file = os.path.join("results", f"ai_results_{datetime.date.today().isoformat()}.json")
        
        try:
            # Read existing results
            if os.path.exists(results_file):
                with open(results_file, "r") as f:
                    results = json.load(f)
            else:
                results = []
            
            # Append new result
            results.append(result)
            
            # Write updated results
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error storing results: {str(e)}")
    
    def get_latest_prediction(self) -> Dict[str, Any]:
        """
        Get the latest AI prediction.
        
        Returns:
            Dict containing the latest AI prediction
        """
        return self.last_prediction
    
    def get_prediction_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of AI predictions.
        
        Returns:
            List of AI predictions
        """
        return self.prediction_history
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of trade executions.
        
        Returns:
            List of trade executions
        """
        return self.execution_history

def main():
    """Main entry point for the AI Integration module."""
    parser = argparse.ArgumentParser(description="ArbitrageX AI Integration")
    parser.add_argument("--testnet", action="store_true", help="Run in testnet mode (no real transactions)")
    parser.add_argument("--run-time", type=int, default=60, help="How long to run the integration (in seconds)")
    parser.add_argument("--fork-config", type=str, help="Path to fork configuration file")
    args = parser.parse_args()
    
    # Determine mode
    mode = "TESTNET" if args.testnet else "MAINNET"
    if args.fork_config:
        try:
            with open(args.fork_config, 'r') as f:
                fork_config = json.load(f)
            if fork_config.get('mode') == 'mainnet_fork':
                mode = "MAINNET FORK"
        except Exception as e:
            print(f"Error loading fork configuration: {str(e)}")
    
    # Print header
    print("\n" + "="*80)
    print(f"ArbitrageX AI Integration - {mode} MODE")
    print("="*80)
    
    # Initialize and start the AI Integration
    ai_integration = AIIntegration(testnet=args.testnet, fork_config=args.fork_config)
    ai_integration.start()
    
    try:
        # Run for the specified time
        print(f"\nRunning AI Integration for {args.run_time} seconds...\n")
        time.sleep(args.run_time)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        # Stop the AI Integration
        ai_integration.stop()
        
        # Print summary
        print("\n" + "="*80)
        print("AI Integration Summary")
        print("="*80)
        print(f"Total predictions: {len(ai_integration.prediction_history)}")
        print(f"Total executions: {len(ai_integration.execution_history)}")
        
        # Calculate profitability metrics
        profitable_predictions = sum(1 for p in ai_integration.prediction_history if p["is_profitable"])
        total_expected_profit = sum(p["net_profit_usd"] for p in ai_integration.prediction_history)
        successful_executions = sum(1 for e in ai_integration.execution_history if e["success"])
        total_actual_profit = sum(e["actual_profit_usd"] for e in ai_integration.execution_history)
        
        print(f"Profitable predictions: {profitable_predictions} ({profitable_predictions/len(ai_integration.prediction_history)*100:.2f}% of total)")
        print(f"Total expected profit: ${total_expected_profit:.2f}")
        
        if ai_integration.execution_history:
            print(f"Successful executions: {successful_executions} ({successful_executions/len(ai_integration.execution_history)*100:.2f}% of total)")
            print(f"Total actual profit: ${total_actual_profit:.2f}")
        
        if args.testnet:
            print("\nWARNING: No real transactions were executed (TESTNET mode)")
        elif mode == "MAINNET FORK":
            print("\nNOTE: Transactions were simulated on a mainnet fork (no real transactions executed)")
        
        print("\nDone!")

if __name__ == "__main__":
    main() 