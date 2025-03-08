"""
ArbitrageX AI Learning Loop

This module implements a continuous learning loop that processes execution results,
updates AI models, and adapts strategies based on real-world performance data.
The learning loop enables the AI system to automatically improve over time.
"""

import os
import json
import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import joblib
import threading
import queue

# Import related modules
from .model_training import ModelTrainer
from .feature_extractor import FeatureExtractor
from .trade_analyzer import TradeAnalyzer
from .gas_optimizer import GasOptimizer
from .trade_validator import TradeValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("learning_loop.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LearningLoop")

class LearningLoop:
    """
    Learning loop for processing execution results, updating AI models,
    and adapting strategies based on real-world performance data.
    """
    
    def __init__(self, config_path: str = "backend/ai/config/learning_loop_config.json",
                 models_dir: str = "backend/ai/models",
                 data_dir: str = "backend/ai/data",
                 results_dir: str = "backend/ai/results"):
        """
        Initialize the learning loop.
        
        Args:
            config_path: Path to configuration file
            models_dir: Directory for storing models
            data_dir: Directory for storing data
            results_dir: Directory for storing results
        """
        logger.info("Initializing AI Learning Loop")
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config(config_path)
        self.models_dir = models_dir
        self.data_dir = data_dir
        self.results_dir = results_dir
        
        # Initialize components
        self.model_trainer = ModelTrainer(models_dir=models_dir)
        self.feature_extractor = FeatureExtractor(config_path="backend/ai/config/feature_extraction.json")
        self.trade_analyzer = None
        self.gas_optimizer = None
        self.trade_validator = None
        
        if self.config.get("enable_trade_analyzer", True):
            self.trade_analyzer = TradeAnalyzer(
                config_path=self.config.get("trade_analyzer_config", "backend/ai/config/trade_analyzer_config.json")
            )
            logger.info("Trade Analyzer enabled")
        
        if self.config.get("enable_gas_optimizer", True):
            gas_optimizer_config = self.config.get("gas_optimizer_config", "backend/ai/config/gas_optimizer_config.json")
            # Create the gas optimizer config file if it doesn't exist
            if not os.path.exists(gas_optimizer_config):
                os.makedirs(os.path.dirname(gas_optimizer_config), exist_ok=True)
                with open(gas_optimizer_config, 'w') as f:
                    json.dump({
                        "gas_strategy": "dynamic",
                        "network": "ethereum",
                        "max_gas_price": 100,
                        "min_gas_price": 10,
                        "gas_price_multiplier": 1.1
                    }, f, indent=2)
            self.gas_optimizer = GasOptimizer(config_path=gas_optimizer_config)
            logger.info("Gas Optimizer enabled")
            
        if self.config.get("enable_trade_validator", True):
            self.trade_validator = TradeValidator()
            logger.info("Trade Validator enabled")
        
        # Initialize data structures
        self.execution_results_queue = queue.Queue()
        self.model_update_queue = queue.Queue()
        self.strategy_update_queue = queue.Queue()
        self.last_model_update = datetime.now()
        self.last_strategy_adaptation = datetime.now()
        self.learning_stats = {
            "total_processed_results": 0,
            "successful_model_updates": 0,
            "failed_model_updates": 0,
            "strategy_adaptations": 0,
            "last_update_time": None
        }
        
        # Initialize model performance tracking
        self.model_performance = {
            "profit_predictor": {"accuracy": [], "mae": [], "r2": []},
            "gas_optimizer": {"accuracy": [], "mae": [], "r2": []},
            "network_selector": {"accuracy": [], "mae": [], "r2": []},
            "time_optimizer": {"accuracy": [], "mae": [], "r2": []}
        }
        
        # Load existing execution results if available
        self.historical_execution_results = self._load_historical_results()
        
        # Initialize flags
        self.running = False
        self.learning_thread = None
        
        logger.info("AI Learning Loop initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file or create default."""
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {config_path}")
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return self._get_default_config()
        else:
            # Create default configuration
            default_config = self._get_default_config()
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default configuration at {config_path}")
            return default_config
    
    def _get_default_config(self) -> Dict:
        """Get default configuration values."""
        return {
            "update_interval_minutes": 60,
            "min_samples_for_update": 10,
            "max_samples_per_update": 1000,
            "learning_rate": 0.01,
            "batch_size": 32,
            "epochs_per_update": 5,
            "network_config_path": "backend/config/network_settings.json",
            "trade_analyzer_config": "backend/ai/config/trade_analyzer_config.json",
            "model_update_threshold": 0.05,  # Minimum improvement required to update model
            "adaptation_interval_hours": 6,
            "enable_continuous_learning": True,
            "enable_automatic_adaptation": True,
            "enable_performance_tracking": True,
            "max_historical_results": 10000,
            "enable_trade_analyzer": True,
            "enable_gas_optimizer": True,
            "enable_trade_validator": True,
            "enable_adaptive_validation": True
        }
    
    def _load_historical_results(self) -> List[Dict]:
        """Load historical execution results."""
        results_file = os.path.join(self.data_dir, "historical_execution_results.json")
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                logger.info(f"Loaded {len(results)} historical execution results")
                return results
            except Exception as e:
                logger.error(f"Error loading historical results: {e}")
                return []
        else:
            logger.info("No historical execution results found")
            return []
    
    def _save_historical_results(self):
        """Save historical execution results."""
        results_file = os.path.join(self.data_dir, "historical_execution_results.json")
        try:
            # Limit the number of results to prevent file size issues
            max_results = self.config.get("max_historical_results", 10000)
            if len(self.historical_execution_results) > max_results:
                self.historical_execution_results = self.historical_execution_results[-max_results:]
            
            with open(results_file, 'w') as f:
                json.dump(self.historical_execution_results, f)
            logger.info(f"Saved {len(self.historical_execution_results)} historical execution results")
        except Exception as e:
            logger.error(f"Error saving historical results: {e}")
    
    def add_execution_result(self, execution_result: Dict):
        """
        Add an execution result to the learning queue.
        
        Args:
            execution_result: Execution result data
        """
        # Add timestamp if not present
        if "timestamp" not in execution_result:
            execution_result["timestamp"] = datetime.now().isoformat()
        
        # Add to queue for processing
        self.execution_results_queue.put(execution_result)
        logger.debug(f"Added execution result to queue: {execution_result.get('opportunity_id', 'unknown')}")
    
    def start(self):
        """Start the learning loop in a background thread."""
        if self.running:
            logger.warning("Learning loop is already running")
            return
        
        self.running = True
        self.learning_thread = threading.Thread(target=self._learning_loop, daemon=True)
        self.learning_thread.start()
        logger.info("Learning loop started")
    
    def stop(self):
        """Stop the learning loop."""
        if not self.running:
            logger.warning("Learning loop is not running")
            return
        
        self.running = False
        if self.learning_thread:
            self.learning_thread.join(timeout=5)
        logger.info("Learning loop stopped")
    
    def _learning_loop(self):
        """Main learning loop that runs continuously."""
        logger.info("Learning loop thread started")
        
        while self.running:
            try:
                # Process any pending execution results
                self._process_execution_results()
                
                # Check if it's time to update models
                self._check_and_update_models()
                
                # Check if it's time to adapt strategies
                self._check_and_adapt_strategies()
                
                # Sleep to prevent high CPU usage
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in learning loop: {e}")
                time.sleep(5)  # Sleep longer on error
    
    def _process_execution_results(self):
        """
        Process execution results from the queue.
        
        This method processes up to 100 results at a time to avoid blocking.
        """
        processed_count = 0
        max_results_per_batch = 100
        
        try:
            while not self.execution_results_queue.empty() and processed_count < max_results_per_batch:
                # Get result from queue
                result = self.execution_results_queue.get()
                
                # Add to historical results
                self.historical_execution_results.append(result)
                
                # Analyze trade if trade analyzer is enabled
                if self.trade_analyzer:
                    self.trade_analyzer.analyze_trade(result)
                
                # Validate trade if trade validator is enabled
                if self.trade_validator and result.get("status") == "completed":
                    # Extract trade details for validation
                    trade_details = {
                        "trade_id": result.get("trade_id", f"trade_{int(time.time())}"),
                        "token_pair": result.get("token_pair", "unknown"),
                        "dex": result.get("dex", "unknown"),
                        "network": result.get("network", "unknown"),
                        "amount": result.get("amount", 0),
                        "expected_profit": result.get("expected_profit", 0),
                        "actual_profit": result.get("actual_profit", 0),
                        "gas_price": result.get("gas_price", 0),
                        "gas_used": result.get("gas_used", 0),
                        "gas_cost": result.get("gas_cost", 0),
                        "expected_slippage": result.get("expected_slippage", 0),
                        "actual_slippage": result.get("actual_slippage", 0),
                        "liquidity_score": result.get("liquidity_score", 1.0),
                        "historical_success_rate": result.get("historical_success_rate", 1.0),
                        "front_running_risk": result.get("front_running_risk", 0.0),
                        "network_congestion": result.get("network_congestion", 0.0)
                    }
                    
                    # Validate the trade
                    validation_result = self.trade_validator.validate_trade(trade_details)
                    
                    # Add validation result to the original result
                    result["validation_result"] = validation_result
                    
                    # Log validation result
                    if validation_result["is_valid"]:
                        logger.info(f"Trade {result.get('trade_id')} passed validation with score {validation_result['validation_score']:.2f}")
                    else:
                        logger.warning(f"Trade {result.get('trade_id')} failed validation with score {validation_result['validation_score']:.2f}: {validation_result['failure_reasons']}")
                
                # Extract features for model update
                features = self.feature_extractor.extract_features(result)
                if features:
                    self.model_update_queue.put(features)
                
                # Mark as processed
                self.execution_results_queue.task_done()
                processed_count += 1
            
            # Log processing summary
            if processed_count > 0:
                logger.info(f"Processed {processed_count} execution results")
                
                # Save historical results
                self._save_historical_results()
        except Exception as e:
            logger.error(f"Error processing execution results: {e}")
    
    def _check_and_update_models(self):
        """Check if it's time to update models and do so if needed."""
        if not self.config.get("enable_continuous_learning", True):
            return
        
        # Check if enough time has passed since last update
        update_interval = timedelta(minutes=self.config.get("update_interval_minutes", 60))
        if datetime.now() - self.last_model_update < update_interval:
            return
        
        # Check if we have enough samples for an update
        min_samples = self.config.get("min_samples_for_update", 10)
        if self.model_update_queue.qsize() < min_samples:
            return
        
        logger.info("Updating AI models with new execution data")
        
        try:
            # Collect samples from queue
            max_samples = self.config.get("max_samples_per_update", 1000)
            samples = []
            sample_count = min(self.model_update_queue.qsize(), max_samples)
            
            for _ in range(sample_count):
                try:
                    sample = self.model_update_queue.get(block=False)
                    samples.append(sample)
                    self.model_update_queue.task_done()
                except queue.Empty:
                    break
            
            if len(samples) < min_samples:
                logger.warning(f"Not enough valid samples for model update: {len(samples)}")
                return
            
            # Convert samples to feature set
            feature_set = self.feature_extractor.create_feature_set_from_samples(samples)
            
            # Update models
            self._update_models(feature_set)
            
            # Update timestamp
            self.last_model_update = datetime.now()
            self.learning_stats["last_update_time"] = self.last_model_update.isoformat()
            
            logger.info(f"Successfully updated AI models with {len(samples)} samples")
            self.learning_stats["successful_model_updates"] += 1
        except Exception as e:
            logger.error(f"Error updating models: {e}")
            self.learning_stats["failed_model_updates"] += 1
    
    def _update_models(self, feature_set):
        """Update all AI models with new data."""
        # Update profit predictor model
        profit_result = self.model_trainer.train_profit_predictor(feature_set)
        self._track_model_performance("profit_predictor", profit_result)
        
        # Update gas optimizer model
        gas_result = self.model_trainer.train_gas_optimizer(feature_set)
        self._track_model_performance("gas_optimizer", gas_result)
        
        # Update network selector model
        network_result = self.model_trainer.train_network_selector(feature_set)
        self._track_model_performance("network_selector", network_result)
        
        # Update time optimizer model
        time_result = self.model_trainer.train_time_optimizer(feature_set)
        self._track_model_performance("time_optimizer", time_result)
        
        # Save performance metrics
        self._save_performance_metrics()
    
    def _track_model_performance(self, model_name: str, training_result: Dict):
        """Track model performance metrics over time."""
        if not self.config.get("enable_performance_tracking", True):
            return
        
        if model_name in self.model_performance and training_result:
            metrics = self.model_performance[model_name]
            
            if "accuracy" in training_result:
                metrics["accuracy"].append({
                    "timestamp": datetime.now().isoformat(),
                    "value": training_result["accuracy"]
                })
            
            if "mae" in training_result:
                metrics["mae"].append({
                    "timestamp": datetime.now().isoformat(),
                    "value": training_result["mae"]
                })
            
            if "r2" in training_result:
                metrics["r2"].append({
                    "timestamp": datetime.now().isoformat(),
                    "value": training_result["r2"]
                })
    
    def _save_performance_metrics(self):
        """Save model performance metrics to file."""
        metrics_file = os.path.join(self.results_dir, "model_performance_metrics.json")
        try:
            with open(metrics_file, 'w') as f:
                json.dump(self.model_performance, f, indent=2)
            logger.info("Saved model performance metrics")
        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")
    
    def _check_and_adapt_strategies(self):
        """Check if it's time to adapt strategies and do so if needed."""
        if not self.config.get("enable_automatic_adaptation", True):
            return
        
        # Check if enough time has passed since last adaptation
        adaptation_interval = timedelta(hours=self.config.get("adaptation_interval_hours", 6))
        if datetime.now() - self.last_strategy_adaptation < adaptation_interval:
            return
        
        logger.info("Adapting strategies based on recent performance")
        
        try:
            # Update network stats
            if self.trade_analyzer:
                self.trade_analyzer.update_network_stats(force_update=True)
            
            # Get time-based patterns
            time_patterns = self.trade_analyzer.get_time_based_patterns()
            
            # Get best trading opportunities
            opportunities = self.trade_analyzer.get_best_trading_opportunities()
            
            # Adapt strategies based on this data
            self._adapt_strategies(time_patterns, opportunities)
            
            # Update timestamp
            self.last_strategy_adaptation = datetime.now()
            self.learning_stats["strategy_adaptations"] += 1
            
            logger.info("Successfully adapted strategies")
        except Exception as e:
            logger.error(f"Error adapting strategies: {e}")
    
    def _adapt_strategies(self, time_patterns: Dict[str, Any], opportunities: List[Dict[str, Any]]):
        """
        Adapt strategies based on time patterns and best trading opportunities.
        
        Args:
            time_patterns: Dictionary of time-based patterns
            opportunities: List of best trading opportunities
        """
        try:
            # Update network priorities based on performance
            if opportunities:
                # Count occurrences of each network in top opportunities
                network_counts = {}
                for opportunity in opportunities:
                    network = opportunity.get("network")
                    if network:
                        network_counts[network] = network_counts.get(network, 0) + 1
                
                # Sort networks by count
                sorted_networks = sorted(network_counts.items(), key=lambda x: x[1], reverse=True)
                
                # Get network configuration path
                network_config_path = self.config.get("network_config_path")
                if network_config_path and os.path.exists(network_config_path):
                    try:
                        # Read existing configuration
                        with open(network_config_path, 'r') as f:
                            network_config = json.load(f)
                        
                        # Update network priorities
                        network_config["network_priorities"] = [network for network, _ in sorted_networks]
                        
                        # Save updated configuration
                        with open(network_config_path, 'w') as f:
                            json.dump(network_config, f, indent=2)
                        
                        logger.info(f"Updated network priorities: {network_config['network_priorities']}")
                    except Exception as e:
                        logger.error(f"Error updating network configuration: {e}")
                
                # Update trade validator thresholds based on market conditions if enabled
                if self.trade_validator and self.config.get("enable_adaptive_validation", True):
                    # Calculate average network congestion
                    network_congestion = 0.0
                    congestion_count = 0
                    
                    for opportunity in opportunities:
                        if "network_congestion" in opportunity:
                            network_congestion += opportunity["network_congestion"]
                            congestion_count += 1
                    
                    if congestion_count > 0:
                        network_congestion /= congestion_count
                    
                    # Calculate market volatility based on price changes
                    market_volatility = 0.0
                    volatility_count = 0
                    
                    for opportunity in opportunities:
                        if "price_volatility" in opportunity:
                            market_volatility += opportunity["price_volatility"]
                            volatility_count += 1
                    
                    if volatility_count > 0:
                        market_volatility /= volatility_count
                    
                    # Adjust trade validator thresholds
                    market_conditions = {
                        "market_volatility": market_volatility,
                        "network_congestion": network_congestion
                    }
                    
                    self.trade_validator.adjust_thresholds(market_conditions)
                    logger.info(f"Adjusted trade validator thresholds based on market conditions: "
                                f"volatility={market_volatility:.2f}, congestion={network_congestion:.2f}")
        except Exception as e:
            logger.error(f"Error adapting strategies: {e}")
    
    def get_learning_stats(self) -> Dict:
        """Get learning loop statistics."""
        return {
            **self.learning_stats,
            "queue_size": self.execution_results_queue.qsize(),
            "model_update_queue_size": self.model_update_queue.qsize(),
            "historical_results_count": len(self.historical_execution_results),
            "is_running": self.running,
            "next_model_update": (self.last_model_update + timedelta(minutes=self.config.get("update_interval_minutes", 60))).isoformat(),
            "next_strategy_adaptation": (self.last_strategy_adaptation + timedelta(hours=self.config.get("adaptation_interval_hours", 6))).isoformat()
        }
    
    def get_model_performance(self) -> Dict:
        """Get model performance metrics."""
        return self.model_performance
    
    def force_model_update(self):
        """Force an immediate model update."""
        if not self.running:
            logger.warning("Learning loop is not running")
            return False
        
        try:
            # Reset last update time to trigger update
            self.last_model_update = datetime.now() - timedelta(days=1)
            logger.info("Forced model update scheduled")
            return True
        except Exception as e:
            logger.error(f"Error scheduling forced model update: {e}")
            return False
    
    def force_strategy_adaptation(self):
        """Force an immediate strategy adaptation."""
        if not self.running:
            logger.warning("Learning loop is not running")
            return False
        
        try:
            # Reset last adaptation time to trigger adaptation
            self.last_strategy_adaptation = datetime.now() - timedelta(days=1)
            logger.info("Forced strategy adaptation scheduled")
            return True
        except Exception as e:
            logger.error(f"Error scheduling forced strategy adaptation: {e}")
            return False
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Validation statistics dictionary
        """
        if self.trade_validator:
            return self.trade_validator.get_validation_stats()
        else:
            return {"error": "Trade validator not enabled"}
    
    def save_validation_stats(self):
        """Save validation statistics to file."""
        if self.trade_validator:
            self.trade_validator.save_validation_stats()
            logger.info("Saved validation statistics")
        else:
            logger.warning("Trade validator not enabled, cannot save validation statistics")

# Example usage
if __name__ == "__main__":
    learning_loop = LearningLoop()
    learning_loop.start()
    
    # Simulate adding some execution results
    for i in range(5):
        result = {
            "opportunity_id": f"test_{i}",
            "network": "ethereum",
            "token_pair": ["WETH", "USDC"],
            "dex": "uniswap_v3",
            "expected_profit": 100.0 + i * 10,
            "actual_profit": 90.0 + i * 8,
            "gas_cost": 10.0,
            "status": "success",
            "execution_time": 500 + i * 50,
            "timestamp": datetime.now().isoformat()
        }
        learning_loop.add_execution_result(result)
        time.sleep(1)
    
    # Wait for processing
    time.sleep(10)
    
    # Print stats
    print(json.dumps(learning_loop.get_learning_stats(), indent=2))
    
    # Stop the learning loop
    learning_loop.stop() 