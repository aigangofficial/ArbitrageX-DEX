"""
Bot Core Module for ArbitrageX

This module serves as the main orchestrator for the arbitrage bot, coordinating:
- Network scanning for opportunities
- Trade execution
- Profit analysis
- Gas optimization
- Competitor tracking
"""

import logging
import json
import os
import time
import sys
import signal
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import threading
import queue
import importlib
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_core.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BotCore")

class BotCore:
    """
    Main orchestrator for the ArbitrageX arbitrage bot.
    Coordinates all components and manages the bot's lifecycle.
    """
    
    def __init__(self, config_path: str = "backend/bot/bot_settings.json"):
        """
        Initialize the bot core.
        
        Args:
            config_path: Path to the bot configuration file
        """
        logger.info("Initializing ArbitrageX Bot Core")
        self.config = self._load_config(config_path)
        self.running = False
        self.paused = False
        
        # Initialize components
        self._init_components()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Opportunity queue for passing data between components
        self.opportunity_queue = queue.Queue(maxsize=100)
        
        # Statistics and metrics
        self.stats = {
            "start_time": None,
            "opportunities_found": 0,
            "trades_executed": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit": 0.0,
            "total_gas_spent": 0.0,
            "net_profit": 0.0
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """Load bot configuration from file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded bot configuration from {config_path}")
                return config
            else:
                logger.warning(f"Config file not found at {config_path}, using default values")
                # Create default config
                default_config = {
                    "bot_name": "ArbitrageX",
                    "version": "1.0.0",
                    "networks": ["ethereum", "arbitrum", "polygon", "optimism"],
                    "default_network": "ethereum",
                    "scan_interval": 5,  # seconds
                    "execution": {
                        "max_concurrent_trades": 3,
                        "min_profit_threshold": 0.01,  # ETH
                        "max_slippage": 1.0,  # %
                        "use_flashloans": True,
                        "max_gas_price": 100  # Gwei
                    },
                    "risk_management": {
                        "max_trade_size": 10.0,  # ETH
                        "daily_profit_target": 1.0,  # ETH
                        "daily_loss_limit": 0.5,  # ETH
                        "circuit_breaker_enabled": True,
                        "circuit_breaker_threshold": 3  # consecutive failed trades
                    },
                    "ai_integration": {
                        "use_ai_predictions": True,
                        "confidence_threshold": 0.7,
                        "model_path": "models/opportunity_model.h5"
                    },
                    "competitor_tracking": {
                        "enabled": True,
                        "track_interval": 60  # seconds
                    },
                    "logging": {
                        "level": "INFO",
                        "log_trades": True,
                        "log_opportunities": True
                    }
                }
                
                # Save default config
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                
                logger.info(f"Created default configuration at {config_path}")
                return default_config
                
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def _init_components(self):
        """Initialize bot components"""
        try:
            # Import components dynamically
            # This allows for easier testing and component replacement
            
            # Network Scanner
            network_scanner_module = importlib.import_module("backend.bot.network_scanner")
            self.network_scanner = network_scanner_module.NetworkScanner(self.config)
            logger.info("Initialized Network Scanner")
            
            # Trade Executor
            trade_executor_module = importlib.import_module("backend.bot.trade_executor")
            self.trade_executor = trade_executor_module.TradeExecutor(self.config)
            logger.info("Initialized Trade Executor")
            
            # Profit Analyzer
            profit_analyzer_module = importlib.import_module("backend.bot.profit_analyzer")
            self.profit_analyzer = profit_analyzer_module.ProfitAnalyzer(self.config)
            logger.info("Initialized Profit Analyzer")
            
            # Gas Optimizer
            gas_optimizer_module = importlib.import_module("backend.bot.gas_optimizer")
            self.gas_optimizer = gas_optimizer_module.GasOptimizer(self.config)
            logger.info("Initialized Gas Optimizer")
            
            # Competitor Tracker
            competitor_tracker_module = importlib.import_module("backend.bot.competitor_tracker")
            self.competitor_tracker = competitor_tracker_module.CompetitorTracker(self.config)
            logger.info("Initialized Competitor Tracker")
            
            # AI Integration
            try:
                ai_module = importlib.import_module("backend.ai.strategy_optimizer")
                self.ai_strategy = ai_module.StrategyOptimizer()
                logger.info("Initialized AI Strategy Optimizer")
            except ImportError as e:
                logger.warning(f"AI Strategy Optimizer not available: {e}")
                self.ai_strategy = None
            
        except ImportError as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def start(self):
        """Start the bot"""
        if self.running:
            logger.warning("Bot is already running")
            return
        
        logger.info("Starting ArbitrageX Bot")
        self.running = True
        self.paused = False
        self.stats["start_time"] = datetime.now()
        
        # Start component threads
        self.scanner_thread = threading.Thread(target=self._scanner_loop)
        self.executor_thread = threading.Thread(target=self._executor_loop)
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        
        self.scanner_thread.daemon = True
        self.executor_thread.daemon = True
        self.monitor_thread.daemon = True
        
        self.scanner_thread.start()
        self.executor_thread.start()
        self.monitor_thread.start()
        
        logger.info("ArbitrageX Bot started successfully")
    
    def stop(self):
        """Stop the bot"""
        if not self.running:
            logger.warning("Bot is not running")
            return
        
        logger.info("Stopping ArbitrageX Bot")
        self.running = False
        
        # Wait for threads to finish
        if hasattr(self, 'scanner_thread') and self.scanner_thread.is_alive():
            self.scanner_thread.join(timeout=5)
        
        if hasattr(self, 'executor_thread') and self.executor_thread.is_alive():
            self.executor_thread.join(timeout=5)
        
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        # Save final stats
        self._save_stats()
        
        logger.info("ArbitrageX Bot stopped successfully")
    
    def pause(self):
        """Pause the bot"""
        if not self.running:
            logger.warning("Bot is not running")
            return
        
        if self.paused:
            logger.warning("Bot is already paused")
            return
        
        logger.info("Pausing ArbitrageX Bot")
        self.paused = True
    
    def resume(self):
        """Resume the bot"""
        if not self.running:
            logger.warning("Bot is not running")
            return
        
        if not self.paused:
            logger.warning("Bot is not paused")
            return
        
        logger.info("Resuming ArbitrageX Bot")
        self.paused = False
    
    def _scanner_loop(self):
        """Main loop for scanning networks for arbitrage opportunities"""
        logger.info("Starting network scanner loop")
        
        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Scan for opportunities
                opportunities = self.network_scanner.scan_networks()
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} potential arbitrage opportunities")
                    self.stats["opportunities_found"] += len(opportunities)
                    
                    # Apply AI filtering if enabled
                    if self.config.get("ai_integration", {}).get("use_ai_predictions", False) and self.ai_strategy:
                        opportunities = self._filter_with_ai(opportunities)
                    
                    # Analyze profitability
                    for opportunity in opportunities:
                        # Get optimal gas price
                        gas_price = self.gas_optimizer.get_optimal_gas_price(opportunity["network"])
                        opportunity["gas_price"] = gas_price
                        
                        # Calculate expected profit
                        profit_analysis = self.profit_analyzer.analyze_opportunity(opportunity)
                        opportunity.update(profit_analysis)
                        
                        # Add to queue if profitable
                        if profit_analysis["is_profitable"]:
                            try:
                                self.opportunity_queue.put(opportunity, block=False)
                                logger.info(f"Added profitable opportunity to queue: {opportunity['id']}")
                            except queue.Full:
                                logger.warning("Opportunity queue is full, skipping opportunity")
                
                # Sleep for scan interval
                time.sleep(self.config.get("scan_interval", 5))
                
            except Exception as e:
                logger.error(f"Error in scanner loop: {e}")
                time.sleep(5)  # Sleep on error to prevent rapid retries
    
    def _executor_loop(self):
        """Main loop for executing arbitrage trades"""
        logger.info("Starting trade executor loop")
        
        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Get opportunity from queue
                try:
                    opportunity = self.opportunity_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                logger.info(f"Processing opportunity: {opportunity['id']}")
                
                # Execute trade
                result = self.trade_executor.execute_trade(opportunity)
                
                # Update stats
                self.stats["trades_executed"] += 1
                if result["success"]:
                    self.stats["successful_trades"] += 1
                    self.stats["total_profit"] += result["profit"]
                    self.stats["total_gas_spent"] += result["gas_cost"]
                    self.stats["net_profit"] = self.stats["total_profit"] - self.stats["total_gas_spent"]
                    logger.info(f"Trade successful: {result['profit']} ETH profit")
                else:
                    self.stats["failed_trades"] += 1
                    self.stats["total_gas_spent"] += result.get("gas_cost", 0)
                    self.stats["net_profit"] = self.stats["total_profit"] - self.stats["total_gas_spent"]
                    logger.warning(f"Trade failed: {result.get('error', 'Unknown error')}")
                
                # Check circuit breaker
                if self._check_circuit_breaker():
                    logger.warning("Circuit breaker triggered, pausing bot")
                    self.pause()
                
                # Mark task as done
                self.opportunity_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in executor loop: {e}")
                time.sleep(5)  # Sleep on error to prevent rapid retries
    
    def _monitor_loop(self):
        """Monitor loop for tracking competitors and updating strategies"""
        logger.info("Starting monitor loop")
        
        last_competitor_track = 0
        last_stats_save = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Track competitors
                if self.config.get("competitor_tracking", {}).get("enabled", True):
                    track_interval = self.config.get("competitor_tracking", {}).get("track_interval", 60)
                    if current_time - last_competitor_track >= track_interval:
                        self.competitor_tracker.track_competitors()
                        last_competitor_track = current_time
                
                # Save stats periodically
                if current_time - last_stats_save >= 300:  # Every 5 minutes
                    self._save_stats()
                    last_stats_save = current_time
                
                # Sleep to prevent high CPU usage
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(5)  # Sleep on error to prevent rapid retries
    
    def _filter_with_ai(self, opportunities: List[Dict]) -> List[Dict]:
        """Filter opportunities using AI predictions"""
        if not self.ai_strategy:
            return opportunities
        
        filtered_opportunities = []
        confidence_threshold = self.config.get("ai_integration", {}).get("confidence_threshold", 0.7)
        
        for opportunity in opportunities:
            try:
                # Get AI prediction
                prediction = self.ai_strategy.predict_opportunity(opportunity)
                opportunity["ai_confidence"] = prediction[1]  # Confidence score
                
                if prediction[1] >= confidence_threshold:
                    filtered_opportunities.append(opportunity)
                    logger.debug(f"AI approved opportunity with confidence {prediction[1]}")
                else:
                    logger.debug(f"AI rejected opportunity with confidence {prediction[1]}")
                    
            except Exception as e:
                logger.error(f"Error in AI filtering: {e}")
                # Include opportunity if AI fails
                filtered_opportunities.append(opportunity)
        
        logger.info(f"AI filtered {len(opportunities) - len(filtered_opportunities)} opportunities")
        return filtered_opportunities
    
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should be triggered"""
        if not self.config.get("risk_management", {}).get("circuit_breaker_enabled", True):
            return False
        
        threshold = self.config.get("risk_management", {}).get("circuit_breaker_threshold", 3)
        
        # Get recent trade history from executor
        recent_trades = self.trade_executor.get_recent_trades(threshold)
        
        # Count consecutive failures
        consecutive_failures = 0
        for trade in recent_trades:
            if not trade["success"]:
                consecutive_failures += 1
            else:
                break  # Reset on success
        
        return consecutive_failures >= threshold
    
    def _save_stats(self):
        """Save bot statistics to file"""
        stats_file = "bot_stats.json"
        
        # Add runtime
        if self.stats["start_time"]:
            runtime = datetime.now() - self.stats["start_time"]
            self.stats["runtime_seconds"] = runtime.total_seconds()
            self.stats["runtime_formatted"] = str(runtime).split('.')[0]  # HH:MM:SS
        
        # Save to file
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=4, default=str)
            logger.debug(f"Saved bot statistics to {stats_file}")
        except Exception as e:
            logger.error(f"Error saving statistics: {e}")
    
    def _signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {sig}, shutting down")
        self.stop()
        sys.exit(0)
    
    def get_status(self) -> Dict:
        """Get current bot status"""
        return {
            "running": self.running,
            "paused": self.paused,
            "stats": self.stats,
            "queue_size": self.opportunity_queue.qsize(),
            "config": self.config
        }

# Example usage
if __name__ == "__main__":
    bot = BotCore()
    
    try:
        bot.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
        bot.stop()
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        bot.stop()
