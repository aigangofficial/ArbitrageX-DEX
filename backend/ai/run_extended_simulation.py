#!/usr/bin/env python3
"""
ArbitrageX Extended Simulation (3-Month Backtest)

This script runs a comprehensive 3-month simulation using historical market data
to evaluate the ArbitrageX bot's maximum performance and learning capabilities.
"""

import os
import sys
import json
import time
import logging
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extended_simulation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ExtendedSimulation")

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Handle command-line arguments first before importing modules that might have their own parsers
def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run a 3-month extended simulation of ArbitrageX")
    
    parser.add_argument("--start-date", type=str, default=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
                        help="Start date for the simulation in YYYY-MM-DD format")
    
    parser.add_argument("--end-date", type=str, default=datetime.now().strftime("%Y-%m-%d"),
                        help="End date for the simulation in YYYY-MM-DD format")
    
    parser.add_argument("--data-dir", type=str, default="backend/ai/data/historical",
                        help="Directory with historical market data")
    
    parser.add_argument("--metrics-dir", type=str, default="backend/ai/metrics/extended_simulation",
                        help="Directory to store metrics")
    
    parser.add_argument("--results-dir", type=str, default="backend/ai/results/extended_simulation",
                        help="Directory to store results")
    
    parser.add_argument("--trades-per-day", type=int, default=48,
                        help="Number of trades to simulate per day (default: 48)")
    
    parser.add_argument("--learning-interval", type=int, default=4,
                        help="How often to run the learning loop in hours (default: 4)")
    
    parser.add_argument("--synthetic-data", action="store_true",
                        help="Force the use of synthetic data even if historical data exists")
    
    # Add these arguments to avoid conflicts with other modules
    parser.add_argument("--market-data", type=str, help=argparse.SUPPRESS)
    parser.add_argument("--mainnet-fork", type=str, help=argparse.SUPPRESS)
    parser.add_argument("--testnet", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--version", action="store_true", help=argparse.SUPPRESS)
    
    return parser.parse_args()

# Parse arguments before importing potentially conflicting modules
args = parse_arguments()

# Now import modules that might have their own argument parsers
from backend.ai.enhanced_monitoring import EnhancedMonitoring
from backend.ai.learning_loop import LearningLoop
from backend.ai.strategy_optimizer import StrategyOptimizer
from backend.ai.system_monitor import SystemMonitor

class ExtendedSimulation:
    """
    Runs an extended 3-month simulation of ArbitrageX using historical data.
    """
    
    def __init__(self, 
                 start_date: str,  # Format: "YYYY-MM-DD"
                 end_date: str,    # Format: "YYYY-MM-DD"
                 data_dir: str = "backend/ai/data/historical",
                 metrics_dir: str = "backend/ai/metrics/extended_simulation",
                 results_dir: str = "backend/ai/results/extended_simulation",
                 trades_per_day: int = 48,  # Simulate 48 trades per day (1 per 30 min)
                 learning_interval_hours: int = 4):  # Run learning loop every 4 hours
        """
        Initialize the extended simulation.
        
        Args:
            start_date: Start date for the simulation in "YYYY-MM-DD" format
            end_date: End date for the simulation in "YYYY-MM-DD" format
            data_dir: Directory with historical market data
            metrics_dir: Directory to store metrics
            results_dir: Directory to store results
            trades_per_day: Number of trades to simulate per day
            learning_interval_hours: How often to run the learning loop (in hours)
        """
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.data_dir = data_dir
        self.metrics_dir = metrics_dir
        self.results_dir = results_dir
        self.trades_per_day = trades_per_day
        self.learning_interval_hours = learning_interval_hours
        
        # Validate dates
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        
        # Calculate total days
        self.total_days = (self.end_date - self.start_date).days
        if self.total_days < 1:
            raise ValueError("Simulation must span at least 1 day")
        
        # Create directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.metrics_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize monitoring
        self.monitoring = EnhancedMonitoring(
            metrics_dir=self.metrics_dir,
            save_interval_seconds=600,  # Save metrics every 10 minutes
            monitor_interval_seconds=60  # Monitor system every minute
        )
        
        # Initialize learning loop
        self.learning_loop = LearningLoop(
            config_path="backend/ai/config/learning_loop_config.json",
            results_dir=self.results_dir
        )
        
        # Initialize strategy optimizer
        self.strategy_optimizer = StrategyOptimizer()
        
        # Track simulation progress
        self.current_date = self.start_date
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = 0.0
        self.running = False
        self.simulation_start_time = None
        self.simulation_end_time = None
        
        # Store daily metrics for analysis
        self.daily_metrics = []
        
        logger.info(f"Initialized simulation from {start_date} to {end_date} ({self.total_days} days)")
        logger.info(f"Will simulate {self.trades_per_day} trades per day with learning every {self.learning_interval_hours} hours") 

    def load_historical_data(self):
        """
        Load historical market data for the simulation period.
        
        Returns:
            Dict: Historical market data indexed by date
        """
        logger.info(f"Loading historical market data from {self.data_dir}...")
        
        # Check if historical data exists
        market_data_file = os.path.join(self.data_dir, "market_data.json")
        
        if os.path.exists(market_data_file):
            with open(market_data_file, 'r') as f:
                all_market_data = json.load(f)
            
            # Filter data for our simulation period
            simulation_data = {}
            for date_str, data in all_market_data.items():
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if self.start_date <= date <= self.end_date:
                        simulation_data[date_str] = data
                except ValueError:
                    continue
            
            if not simulation_data:
                logger.warning("No historical data found for the specified simulation period.")
                # Generate synthetic data instead
                return self.generate_synthetic_data()
            
            logger.info(f"Loaded historical data for {len(simulation_data)} days")
            return simulation_data
        else:
            logger.warning(f"Historical data file not found at {market_data_file}")
            # Generate synthetic data instead
            return self.generate_synthetic_data()
    
    def generate_synthetic_data(self):
        """
        Generate synthetic market data when historical data is not available.
        
        Returns:
            Dict: Synthetic market data indexed by date
        """
        logger.info("Generating synthetic market data...")
        
        synthetic_data = {}
        current_date = self.start_date
        
        # Base price levels for common tokens
        base_prices = {
            "WETH": 2500.0,
            "WBTC": 40000.0,
            "USDC": 1.0,
            "USDT": 1.0,
            "DAI": 1.0,
            "LINK": 15.0,
            "UNI": 8.0,
            "AAVE": 100.0
        }
        
        # Volatility parameters
        daily_volatility = {
            "WETH": 0.03,
            "WBTC": 0.035,
            "USDC": 0.001,
            "USDT": 0.001,
            "DAI": 0.001,
            "LINK": 0.04,
            "UNI": 0.05,
            "AAVE": 0.06
        }
        
        # Volume parameters
        base_volume = {
            "WETH": 1000000000,
            "WBTC": 500000000,
            "USDC": 2000000000,
            "USDT": 2000000000,
            "DAI": 500000000,
            "LINK": 200000000,
            "UNI": 100000000,
            "AAVE": 50000000
        }
        
        # Market trend (overall bullish/bearish)
        trend = np.random.normal(0.0005, 0.001)  # Slight bullish bias
        
        # Generate data for each day
        prices = base_prices.copy()
        volumes = base_volume.copy()
        
        while current_date <= self.end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Update prices with random walk and trend
            for token, price in prices.items():
                daily_return = np.random.normal(trend, daily_volatility[token])
                prices[token] = price * (1 + daily_return)
            
            # Daily volatility changes
            for token in daily_volatility:
                # Volatility clustering effect
                volatility_change = np.random.normal(0, 0.1)
                daily_volatility[token] = max(0.001, daily_volatility[token] * (1 + volatility_change))
            
            # Generate token pairs data
            pairs_data = {}
            for base_token in ["WETH", "WBTC"]:
                for quote_token in ["USDC", "USDT", "DAI"]:
                    pair_name = f"{base_token}-{quote_token}"
                    
                    # Bid/ask spread varies by pair
                    if base_token == "WETH":
                        spread = 0.001  # 0.1% spread for ETH pairs
                    else:
                        spread = 0.002  # 0.2% spread for BTC pairs
                    
                    # Calculate volumes with random variation
                    pair_volume = (volumes[base_token] + volumes[quote_token]) / 2
                    daily_volume = pair_volume * np.random.lognormal(0, 0.2)
                    
                    # Calculate price with spread
                    mid_price = prices[base_token] / prices[quote_token]
                    bid_price = mid_price * (1 - spread/2)
                    ask_price = mid_price * (1 + spread/2)
                    
                    # Generate DEX-specific data
                    dexes = {
                        "uniswap_v3": {
                            "liquidity": daily_volume * 0.4,
                            "fees": 0.0003,
                            "bid": bid_price * np.random.uniform(0.999, 1.001),
                            "ask": ask_price * np.random.uniform(0.999, 1.001)
                        },
                        "sushiswap": {
                            "liquidity": daily_volume * 0.2,
                            "fees": 0.0003,
                            "bid": bid_price * np.random.uniform(0.998, 1.002),
                            "ask": ask_price * np.random.uniform(0.998, 1.002)
                        },
                        "curve": {
                            "liquidity": daily_volume * 0.3,
                            "fees": 0.0004,
                            "bid": bid_price * np.random.uniform(0.997, 1.003),
                            "ask": ask_price * np.random.uniform(0.997, 1.003)
                        },
                        "balancer": {
                            "liquidity": daily_volume * 0.1,
                            "fees": 0.0002,
                            "bid": bid_price * np.random.uniform(0.996, 1.004),
                            "ask": ask_price * np.random.uniform(0.996, 1.004)
                        }
                    }
                    
                    pairs_data[pair_name] = {
                        "price": mid_price,
                        "daily_volume": daily_volume,
                        "daily_volatility": (daily_volatility[base_token] + daily_volatility[quote_token]) / 2,
                        "dexes": dexes
                    }
            
            # Store data for this day
            synthetic_data[date_str] = {
                "token_prices": prices.copy(),
                "token_volumes": volumes.copy(),
                "pairs": pairs_data,
                "gas_price_gwei": np.random.lognormal(3, 0.5),  # Gas price in gwei
                "block_number": 15000000 + (current_date - self.start_date).days * 7200  # ~7200 blocks per day
            }
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Save synthetic data for future use
        os.makedirs(self.data_dir, exist_ok=True)
        synthetic_data_file = os.path.join(self.data_dir, "synthetic_market_data.json")
        
        with open(synthetic_data_file, 'w') as f:
            json.dump(synthetic_data, f, indent=2)
        
        logger.info(f"Generated synthetic market data for {len(synthetic_data)} days")
        logger.info(f"Saved synthetic data to {synthetic_data_file}")
        
        return synthetic_data
    
    def generate_trade_opportunity(self, date_data):
        """
        Generate a realistic trade opportunity based on the market data for a specific date.
        
        Args:
            date_data: Market data for the specific date
            
        Returns:
            Dict: A trade opportunity
        """
        # Select random pair
        pairs = list(date_data["pairs"].keys())
        pair = np.random.choice(pairs)
        base_token, quote_token = pair.split('-')
        
        # Select random DEXes
        dexes = list(date_data["pairs"][pair]["dexes"].keys())
        dex1 = np.random.choice(dexes)
        
        # Choose second DEX that's different from the first
        remaining_dexes = [dex for dex in dexes if dex != dex1]
        dex2 = np.random.choice(remaining_dexes)
        
        # Calculate potential arbitrage
        dex1_ask = date_data["pairs"][pair]["dexes"][dex1]["ask"]
        dex2_bid = date_data["pairs"][pair]["dexes"][dex2]["bid"]
        
        # Not all opportunities are profitable
        profit_factor = 1.0
        if np.random.random() < 0.7:  # 70% of opportunities are not profitable
            profit_factor = np.random.uniform(0.95, 0.999)  # Loss-making opportunities
        else:
            profit_factor = np.random.uniform(1.001, 1.05)  # Profitable opportunities
        
        dex2_bid *= profit_factor
        
        # Calculate potential profit percentage
        profit_percentage = (dex2_bid / dex1_ask - 1) * 100
        
        # Estimate gas cost
        gas_limit = np.random.randint(150000, 300000)
        gas_price_gwei = date_data["gas_price_gwei"]
        eth_price = date_data["token_prices"]["WETH"]
        gas_cost_usd = (gas_limit * gas_price_gwei * 1e-9) * eth_price
        
        # Set trade amount
        amount_in = np.random.uniform(0.1, 10.0) if base_token == "WETH" else np.random.uniform(0.01, 0.5)
        
        # Calculate estimated profit
        estimated_profit_usd = (profit_percentage / 100) * amount_in * date_data["token_prices"][base_token]
        
        # Create opportunity
        opportunity = {
            "network": "ethereum",
            "token_in": base_token,
            "token_out": quote_token,
            "amount_in": amount_in,
            "amount_out_expected": amount_in * dex1_ask,
            "estimated_profit_usd": estimated_profit_usd,
            "gas_cost_usd": gas_cost_usd,
            "net_profit_usd": estimated_profit_usd - gas_cost_usd,
            "is_profitable": estimated_profit_usd > gas_cost_usd,
            "route": [
                {"dex": dex1, "token_in": base_token, "token_out": quote_token, "price": dex1_ask},
                {"dex": dex2, "token_in": quote_token, "token_out": base_token, "price": 1/dex2_bid}
            ],
            "gas_estimate": gas_limit,
            "gas_price_gwei": gas_price_gwei,
            "execution_priority": "high" if estimated_profit_usd > 3 * gas_cost_usd else "medium",
            "slippage_tolerance": 0.005,
            "timestamp": int(time.time()),
            "block_number": date_data["block_number"]
        }
        
        return opportunity 

    def execute_trade(self, opportunity):
        """
        Simulate the execution of a trade based on the strategy optimizer's prediction.
        
        Args:
            opportunity: The trade opportunity to execute
            
        Returns:
            Dict: The execution result
        """
        # Predict the opportunity
        prediction = self.strategy_optimizer.predict_opportunity(opportunity)
        
        # Execute the opportunity if it's profitable
        if prediction.get("is_profitable", False) or np.random.random() < 0.1:  # Sometimes execute unprofitable trades for learning
            # In simulation, we determine success probabilistically
            success_probability = min(0.95, max(0.3, 0.5 + opportunity["net_profit_usd"] / 20))
            success = np.random.random() < success_probability
            
            # Execution time varies with complexity
            execution_time_ms = np.random.lognormal(5, 0.5)  # Typical ~150ms
            
            # Gas used may be different from estimate
            gas_used = opportunity["gas_estimate"] * np.random.uniform(0.9, 1.1)
            
            # Actual profit may differ from expected
            profit_deviation = np.random.normal(0, 0.1)  # 10% standard deviation
            actual_profit = opportunity["estimated_profit_usd"] * (1 + profit_deviation)
            
            # Gas cost may also vary
            actual_gas_cost = opportunity["gas_cost_usd"] * np.random.uniform(0.9, 1.2)
            
            # Net profit
            net_profit = actual_profit - actual_gas_cost
            
            # Create result
            result = {
                "success": success,
                "profit": actual_profit if success else 0.0,
                "gas_cost": actual_gas_cost if success else opportunity["gas_cost_usd"],
                "gas_used": gas_used if success else 0,
                "net_profit": net_profit if success else -opportunity["gas_cost_usd"],
                "execution_time_ms": execution_time_ms,
                "timestamp": opportunity["timestamp"],
                "block_number": opportunity["block_number"],
                "token_in": opportunity["token_in"],
                "token_out": opportunity["token_out"],
                "amount_in": opportunity["amount_in"],
                "amount_out": opportunity["amount_out_expected"] * (1 + profit_deviation) if success else 0,
                "network": opportunity["network"],
                "dexes": [r["dex"] for r in opportunity["route"]],
                "reason": None if success else "Slippage too high" if np.random.random() < 0.6 else "Transaction reverted"
            }
            
            # Update metrics
            self.total_trades += 1
            if success:
                self.successful_trades += 1
                self.total_profit += net_profit
            
            # Log the trade
            self.monitoring.log_trade(result)
            
            # Add to learning loop
            self.learning_loop.add_execution_result(result)
            
            return result
        else:
            # Not profitable, skip execution
            logger.info("Opportunity not profitable, skipping execution")
            
            # Create a skipped trade result for monitoring
            result = {
                "success": False,
                "reason": "Not profitable",
                "profit": 0.0,
                "gas_cost": 0.0,
                "gas_used": 0,
                "net_profit": 0.0,
                "execution_time_ms": 0.0,
                "timestamp": opportunity["timestamp"],
                "block_number": opportunity["block_number"],
                "token_in": opportunity["token_in"],
                "token_out": opportunity["token_out"],
                "amount_in": opportunity["amount_in"],
                "amount_out": 0.0,
                "network": opportunity["network"],
                "dexes": [r["dex"] for r in opportunity["route"]],
            }
            
            # Update metrics
            self.total_trades += 1
            
            # Log the skipped trade
            self.monitoring.log_trade(result)
            
            return result
    
    def run_learning_loop_iteration(self):
        """
        Run one iteration of the learning loop.
        """
        logger.info("Running learning loop iteration...")
        
        # Process execution results
        self.learning_loop._process_execution_results()
        
        # Check and update models
        self.learning_loop._check_and_update_models()
        
        # Check and adapt strategies
        self.learning_loop._check_and_adapt_strategies()
        
        # Get learning stats
        stats = self.learning_loop.get_learning_stats()
        logger.info(f"Learning stats: {json.dumps(stats, indent=2)}")
        
        # Log ML update
        self.monitoring.log_ml_update({
            "model_updates": stats.get("model_updates", 0),
            "strategy_adaptations": stats.get("strategy_adaptations", 0),
            "prediction_accuracy": stats.get("prediction_accuracy", 0.0)
        })
        
        # Return stats for analysis
        return stats
    
    def simulate_day(self, date_str, market_data):
        """
        Simulate a day of trading.
        
        Args:
            date_str: The date string in "YYYY-MM-DD" format
            market_data: Market data for this day
            
        Returns:
            Dict: Daily metrics
        """
        logger.info(f"Simulating trading for {date_str}...")
        
        # Calculate trades per day
        trades_per_hour = max(1, self.trades_per_day // 24)
        
        # Simulate each hour of the day
        for hour in range(24):
            logger.info(f"Day {date_str}, Hour {hour+1}: Simulating {trades_per_hour} trades")
            
            # Execute trades for this hour
            for _ in range(trades_per_hour):
                opportunity = self.generate_trade_opportunity(market_data[date_str])
                result = self.execute_trade(opportunity)
                
                # Add some delay for better performance
                time.sleep(0.01)
            
            # Run learning loop if it's time
            if hour % self.learning_interval_hours == 0:
                self.run_learning_loop_iteration()
            
            # Log system metrics
            system_metrics = SystemMonitor.get_system_metrics()
            self.monitoring.log_system_metrics(system_metrics)
            
            # Save metrics
            self.monitoring.metrics.save_metrics()
        
        # Save daily metrics
        daily_metrics = self.monitoring.get_metrics_summary()
        self.daily_metrics.append(daily_metrics)
        
        # Save daily metrics to file
        daily_metrics_file = os.path.join(self.results_dir, f"day_{date_str}_metrics.json")
        with open(daily_metrics_file, 'w') as f:
            json.dump(daily_metrics, f, indent=2)
        
        logger.info(f"Day {date_str} completed. Trades: {self.total_trades}, Successful: {self.successful_trades}, Profit: ${self.total_profit:.2f}")
        
        return daily_metrics 

    def generate_report(self):
        """
        Generate a comprehensive report of the simulation.
        
        Returns:
            Dict: The simulation report
        """
        logger.info("Generating simulation report...")
        
        # Calculate overall metrics
        total_days = len(self.daily_metrics)
        if total_days == 0:
            logger.warning("No daily metrics found. Cannot generate report.")
            return {}
        
        # Calculate trade metrics
        total_trades = sum(day["trades"]["total"] for day in self.daily_metrics)
        successful_trades = sum(day["trades"]["successful"] for day in self.daily_metrics)
        success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate profit metrics
        total_profit = sum(day["profit"]["net_profit_usd"] for day in self.daily_metrics)
        total_gas_cost = sum(day["profit"]["gas_cost_usd"] for day in self.daily_metrics)
        avg_profit_per_day = total_profit / total_days if total_days > 0 else 0
        avg_profit_per_trade = total_profit / successful_trades if successful_trades > 0 else 0
        
        # Calculate performance metrics
        avg_execution_times = [day["performance"]["avg_execution_time_ms"] for day in self.daily_metrics]
        avg_execution_time = sum(avg_execution_times) / len(avg_execution_times) if avg_execution_times else 0
        
        # Calculate ML metrics
        total_model_updates = sum(day["ml"]["model_updates"] for day in self.daily_metrics)
        total_strategy_adaptations = sum(day["ml"]["strategy_adaptations"] for day in self.daily_metrics)
        
        # Calculate prediction accuracy over time
        prediction_accuracies = [day["ml"]["prediction_accuracy"] for day in self.daily_metrics]
        avg_prediction_accuracy = sum(prediction_accuracies) / len(prediction_accuracies) if prediction_accuracies else 0
        
        # Calculate prediction accuracy improvement
        initial_accuracy = prediction_accuracies[0] if prediction_accuracies else 0
        final_accuracy = prediction_accuracies[-1] if prediction_accuracies else 0
        accuracy_improvement = final_accuracy - initial_accuracy
        
        # Calculate system metrics
        avg_cpu_usage = sum(day["system"]["cpu_usage_percent"] for day in self.daily_metrics) / total_days
        avg_memory_usage = sum(day["system"]["memory_usage_mb"] for day in self.daily_metrics) / total_days
        
        # Calculate network-specific metrics
        networks = {}
        for day in self.daily_metrics:
            for network, data in day.get("networks", {}).items():
                if network not in networks:
                    networks[network] = {
                        "trades": 0,
                        "successful_trades": 0,
                        "net_profit_usd": 0
                    }
                networks[network]["trades"] += data.get("trades", 0)
                networks[network]["successful_trades"] += data.get("successful_trades", 0)
                networks[network]["net_profit_usd"] += data.get("net_profit_usd", 0)
        
        # Calculate token pair specific metrics
        token_pairs = {}
        for day in self.daily_metrics:
            for pair, data in day.get("token_pairs", {}).items():
                if pair not in token_pairs:
                    token_pairs[pair] = {
                        "trades": 0,
                        "successful_trades": 0,
                        "net_profit_usd": 0
                    }
                token_pairs[pair]["trades"] += data.get("trades", 0)
                token_pairs[pair]["successful_trades"] += data.get("successful_trades", 0)
                token_pairs[pair]["net_profit_usd"] += data.get("net_profit_usd", 0)
        
        # Calculate DEX-specific metrics
        dexes = {}
        for day in self.daily_metrics:
            for dex, data in day.get("dexes", {}).items():
                if dex not in dexes:
                    dexes[dex] = {
                        "trades": 0,
                        "successful_trades": 0,
                        "net_profit_usd": 0
                    }
                dexes[dex]["trades"] += data.get("trades", 0)
                dexes[dex]["successful_trades"] += data.get("successful_trades", 0)
                dexes[dex]["net_profit_usd"] += data.get("net_profit_usd", 0)
        
        # Create monthly breakdown
        monthly_breakdown = {}
        for i, day in enumerate(self.daily_metrics):
            date = self.start_date + timedelta(days=i)
            month_key = date.strftime("%Y-%m")
            
            if month_key not in monthly_breakdown:
                monthly_breakdown[month_key] = {
                    "trades": 0,
                    "successful_trades": 0,
                    "net_profit_usd": 0.0,
                    "gas_cost_usd": 0.0,
                    "model_updates": 0,
                    "strategy_adaptations": 0,
                    "prediction_accuracy": 0.0,
                    "days": 0
                }
            
            monthly_breakdown[month_key]["trades"] += day["trades"]["total"]
            monthly_breakdown[month_key]["successful_trades"] += day["trades"]["successful"]
            monthly_breakdown[month_key]["net_profit_usd"] += day["profit"]["net_profit_usd"]
            monthly_breakdown[month_key]["gas_cost_usd"] += day["profit"]["gas_cost_usd"]
            monthly_breakdown[month_key]["model_updates"] += day["ml"]["model_updates"]
            monthly_breakdown[month_key]["strategy_adaptations"] += day["ml"]["strategy_adaptations"]
            monthly_breakdown[month_key]["prediction_accuracy"] += day["ml"]["prediction_accuracy"]
            monthly_breakdown[month_key]["days"] += 1
        
        # Calculate averages for monthly data
        for month, data in monthly_breakdown.items():
            if data["days"] > 0:
                data["prediction_accuracy"] /= data["days"]
                data["avg_profit_per_day"] = data["net_profit_usd"] / data["days"]
                data["success_rate"] = (data["successful_trades"] / data["trades"]) * 100 if data["trades"] > 0 else 0
        
        # Create report
        report = {
            "simulation_period": {
                "start_date": self.start_date.strftime("%Y-%m-%d"),
                "end_date": self.end_date.strftime("%Y-%m-%d"),
                "total_days": total_days
            },
            "simulation_runtime": {
                "start_time": self.simulation_start_time.isoformat() if self.simulation_start_time else None,
                "end_time": self.simulation_end_time.isoformat() if self.simulation_end_time else None,
                "duration_seconds": (self.simulation_end_time - self.simulation_start_time).total_seconds() if self.simulation_start_time and self.simulation_end_time else None
            },
            "overall_metrics": {
                "total_trades": total_trades,
                "successful_trades": successful_trades,
                "success_rate": success_rate,
                "total_profit_usd": total_profit,
                "total_gas_cost_usd": total_gas_cost,
                "avg_profit_per_day_usd": avg_profit_per_day,
                "avg_profit_per_trade_usd": avg_profit_per_trade,
                "avg_execution_time_ms": avg_execution_time
            },
            "ml_metrics": {
                "total_model_updates": total_model_updates,
                "total_strategy_adaptations": total_strategy_adaptations,
                "avg_prediction_accuracy": avg_prediction_accuracy,
                "initial_prediction_accuracy": initial_accuracy,
                "final_prediction_accuracy": final_accuracy,
                "accuracy_improvement": accuracy_improvement,
                "accuracy_improvement_percent": (accuracy_improvement / initial_accuracy * 100) if initial_accuracy > 0 else 0
            },
            "system_metrics": {
                "avg_cpu_usage_percent": avg_cpu_usage,
                "avg_memory_usage_mb": avg_memory_usage
            },
            "network_metrics": networks,
            "token_pair_metrics": token_pairs,
            "dex_metrics": dexes,
            "monthly_breakdown": monthly_breakdown,
            "top_profitable_pairs": sorted(
                [{"pair": pair, **data} for pair, data in token_pairs.items()],
                key=lambda x: x["net_profit_usd"],
                reverse=True
            )[:10],
            "top_profitable_dexes": sorted(
                [{"dex": dex, **data} for dex, data in dexes.items()],
                key=lambda x: x["net_profit_usd"],
                reverse=True
            )[:5]
        }
        
        # Save report to file
        report_path = os.path.join(self.results_dir, "simulation_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create summary markdown
        summary_path = os.path.join(self.results_dir, "simulation_summary.md")
        with open(summary_path, 'w') as f:
            f.write(f"# ArbitrageX 3-Month Simulation Summary\n\n")
            f.write(f"## Overview\n\n")
            f.write(f"Simulation period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')} ({total_days} days)\n\n")
            f.write(f"## Overall Performance\n\n")
            f.write(f"- Total Trades: {total_trades}\n")
            f.write(f"- Successful Trades: {successful_trades}\n")
            f.write(f"- Success Rate: {success_rate:.2f}%\n")
            f.write(f"- Total Profit: ${total_profit:.2f}\n")
            f.write(f"- Total Gas Cost: ${total_gas_cost:.2f}\n")
            f.write(f"- Average Profit per Day: ${avg_profit_per_day:.2f}\n")
            f.write(f"- Average Profit per Trade: ${avg_profit_per_trade:.2f}\n\n")
            f.write(f"## ML Metrics\n\n")
            f.write(f"- Total Model Updates: {total_model_updates}\n")
            f.write(f"- Total Strategy Adaptations: {total_strategy_adaptations}\n")
            f.write(f"- Initial Prediction Accuracy: {initial_accuracy:.2f}%\n")
            f.write(f"- Final Prediction Accuracy: {final_accuracy:.2f}%\n")
            f.write(f"- Accuracy Improvement: {accuracy_improvement:.2f}% ({(accuracy_improvement / initial_accuracy * 100) if initial_accuracy > 0 else 0:.2f}%)\n\n")
            f.write(f"## Monthly Breakdown\n\n")
            f.write(f"| Month | Trades | Success Rate | Net Profit | Avg Profit/Day | Model Updates | Strategy Adaptations | Prediction Accuracy |\n")
            f.write(f"|-------|--------|-------------|------------|----------------|---------------|----------------------|---------------------|\n")
            for month, data in sorted(monthly_breakdown.items()):
                f.write(f"| {month} | {data['trades']} | {data['success_rate']:.2f}% | ${data['net_profit_usd']:.2f} | ${data['avg_profit_per_day']:.2f} | {data['model_updates']} | {data['strategy_adaptations']} | {data['prediction_accuracy']:.2f}% |\n")
            f.write(f"\n## Top 5 Most Profitable Token Pairs\n\n")
            f.write(f"| Token Pair | Trades | Success Rate | Net Profit |\n")
            f.write(f"|------------|--------|-------------|------------|\n")
            for item in report["top_profitable_pairs"][:5]:
                success_rate = (item["successful_trades"] / item["trades"] * 100) if item["trades"] > 0 else 0
                f.write(f"| {item['pair']} | {item['trades']} | {success_rate:.2f}% | ${item['net_profit_usd']:.2f} |\n")
            f.write(f"\n## Top 3 Most Profitable DEXes\n\n")
            f.write(f"| DEX | Trades | Success Rate | Net Profit |\n")
            f.write(f"|-----|--------|-------------|------------|\n")
            for item in report["top_profitable_dexes"][:3]:
                success_rate = (item["successful_trades"] / item["trades"] * 100) if item["trades"] > 0 else 0
                f.write(f"| {item['dex']} | {item['trades']} | {success_rate:.2f}% | ${item['net_profit_usd']:.2f} |\n")
        
        logger.info(f"Simulation report saved to {report_path}")
        logger.info(f"Simulation summary saved to {summary_path}")
        
        # Print summary
        logger.info("=== Simulation Summary ===")
        logger.info(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')} ({total_days} days)")
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Successful Trades: {successful_trades} ({success_rate:.2f}%)")
        logger.info(f"Total Profit: ${total_profit:.2f}")
        logger.info(f"Average Profit per Day: ${avg_profit_per_day:.2f}")
        logger.info(f"Final Prediction Accuracy: {final_accuracy:.2f}%")
        logger.info(f"Accuracy Improvement: {accuracy_improvement:.2f}%")
        
        return report
    
    def run(self):
        """
        Run the extended simulation.
        
        Returns:
            Dict: The simulation report
        """
        logger.info(f"Starting extended simulation from {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}...")
        self.running = True
        self.simulation_start_time = datetime.now()
        
        try:
            # Load historical market data
            market_data = self.load_historical_data()
            
            # Start monitoring
            self.monitoring.start()
            
            # Start learning loop
            self.learning_loop.start()
            
            # Simulate each day
            current_date = self.start_date
            while current_date <= self.end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                
                # Simulate this day
                self.simulate_day(date_str, market_data)
                
                # Move to next day
                current_date += timedelta(days=1)
            
            # Generate report
            report = self.generate_report()
            
            logger.info("Simulation completed successfully")
            return report
            
        except Exception as e:
            logger.exception(f"Error during simulation: {e}")
            return None
            
        finally:
            # Stop monitoring
            self.monitoring.stop()
            
            # Stop learning loop
            self.learning_loop.stop()
            
            self.running = False
            self.simulation_end_time = datetime.now()
            
            # Calculate duration
            duration = self.simulation_end_time - self.simulation_start_time
            logger.info(f"Total simulation duration: {duration}")
            
            # Try to generate report even if simulation failed
            if not hasattr(self, 'daily_metrics') or not self.daily_metrics:
                logger.warning("No daily metrics found. Cannot generate report.")
            else:
                try:
                    self.generate_report()
                except Exception as e:
                    logger.exception(f"Error generating report: {e}")

def main():
    """
    Main function to run the extended simulation.
    """
    # Args have already been parsed at the top of the file
    global args
    
    # Print banner
    print("=" * 80)
    print(f"ArbitrageX 3-Month Extended Simulation")
    print("=" * 80)
    print(f"Start Date: {args.start_date}")
    print(f"End Date: {args.end_date}")
    print(f"Trades Per Day: {args.trades_per_day}")
    print(f"Learning Interval: {args.learning_interval} hours")
    print(f"Data Directory: {args.data_dir}")
    print(f"Metrics Directory: {args.metrics_dir}")
    print(f"Results Directory: {args.results_dir}")
    print(f"Using Synthetic Data: {args.synthetic_data}")
    print("=" * 80)
    print()
    
    # Create directories
    os.makedirs(args.data_dir, exist_ok=True)
    os.makedirs(args.metrics_dir, exist_ok=True)
    os.makedirs(args.results_dir, exist_ok=True)
    
    # Create and run simulation
    simulation = ExtendedSimulation(
        start_date=args.start_date,
        end_date=args.end_date,
        data_dir=args.data_dir,
        metrics_dir=args.metrics_dir,
        results_dir=args.results_dir,
        trades_per_day=args.trades_per_day,
        learning_interval_hours=args.learning_interval
    )
    
    # Run simulation
    report = simulation.run()
    
    # Exit with appropriate code
    sys.exit(0 if report else 1)

if __name__ == "__main__":
    main() 