#!/usr/bin/env python3
"""
Advanced Test Simulation for ArbitrageX

This script runs a more advanced simulation with learning loop adaptation
and ML metrics, but still keeps it simplified for faster execution.
"""

import os
import sys
import json
import time
import random
import logging
import argparse
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_simulation_advanced.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestSimulationAdvanced")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Advanced test simulation for ArbitrageX")
    
    parser.add_argument("--start-date", type=str, default="2025-03-01",
                        help="Start date for the simulation in YYYY-MM-DD format")
    
    parser.add_argument("--end-date", type=str, default="2025-03-07",
                        help="End date for the simulation in YYYY-MM-DD format")
    
    parser.add_argument("--trades-per-day", type=int, default=24,
                        help="Number of trades to simulate per day")
    
    parser.add_argument("--learning-interval", type=int, default=6,
                        help="How often to run the learning loop in hours")
    
    parser.add_argument("--metrics-dir", type=str, default="backend/ai/metrics/advanced_test",
                        help="Directory to store metrics")
    
    parser.add_argument("--results-dir", type=str, default="backend/ai/results/advanced_test",
                        help="Directory to store results")
    
    return parser.parse_args()

class SimpleLearningLoop:
    """A simplified learning loop for simulation purposes."""
    
    def __init__(self):
        self.model_updates = 0
        self.strategy_adaptations = 0
        self.prediction_accuracy = 60.0  # Start at 60% accuracy
        self.execution_results = []
        self.learning_rate = 0.5
    
    def add_execution_result(self, result):
        """Add an execution result for later processing."""
        self.execution_results.append(result)
    
    def process_results(self):
        """Process execution results and update models."""
        if len(self.execution_results) < 5:
            # Not enough data to learn from
            return
        
        # Simulate model update
        self.model_updates += 1
        
        # Improve prediction accuracy with diminishing returns
        accuracy_gain = self.learning_rate * (100 - self.prediction_accuracy) / 10
        self.prediction_accuracy = min(95, self.prediction_accuracy + accuracy_gain)
        
        # Adapt strategy
        self.strategy_adaptations += 1
        
        # Clear processed results
        self.execution_results = []
        
        logger.info(f"Learning loop update: accuracy now {self.prediction_accuracy:.2f}%")
        
    def get_stats(self):
        """Get learning loop statistics."""
        return {
            "model_updates": self.model_updates,
            "strategy_adaptations": self.strategy_adaptations,
            "prediction_accuracy": self.prediction_accuracy
        }

class TokenPair:
    """A token pair with its market characteristics."""
    
    def __init__(self, base_token, quote_token, base_price, volatility=0.02):
        self.base_token = base_token
        self.quote_token = quote_token
        self.base_price = base_price
        self.volatility = volatility
        self.name = f"{base_token}-{quote_token}"
        self.trades = 0
        self.successful_trades = 0
        self.profit = 0.0
    
    def update_price(self):
        """Update the price with random movement."""
        price_change = np.random.normal(0, self.volatility)
        self.base_price *= (1 + price_change)
        return self.base_price
    
    def get_stats(self):
        """Get token pair statistics."""
        return {
            "trades": self.trades,
            "successful_trades": self.successful_trades,
            "net_profit_usd": self.profit
        }

class DEX:
    """A decentralized exchange."""
    
    def __init__(self, name, fee=0.003, price_impact=0.001):
        self.name = name
        self.fee = fee
        self.price_impact = price_impact
        self.trades = 0
        self.successful_trades = 0
        self.profit = 0.0
    
    def get_price(self, base_price, is_buy):
        """Get price with slippage."""
        slippage = np.random.uniform(0, self.price_impact)
        if is_buy:
            # Buy price is higher (less favorable)
            return base_price * (1 + slippage + self.fee)
        else:
            # Sell price is lower (less favorable)
            return base_price * (1 - slippage - self.fee)
    
    def get_stats(self):
        """Get DEX statistics."""
        return {
            "trades": self.trades,
            "successful_trades": self.successful_trades,
            "net_profit_usd": self.profit
        }

class TradeSimulator:
    """Simulates trades with market conditions."""
    
    def __init__(self, token_pairs, dexes, learning_loop, success_probability=0.3):
        self.token_pairs = token_pairs
        self.dexes = dexes
        self.learning_loop = learning_loop
        self.success_probability = success_probability
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = 0.0
        self.total_gas_cost = 0.0
        self.execution_times = []
    
    def update_success_probability(self):
        """Update success probability based on learning."""
        # As the model learns, success rate improves
        accuracy_factor = self.learning_loop.prediction_accuracy / 100
        self.success_probability = 0.3 + (accuracy_factor * 0.5)  # Max 80% success rate
    
    def execute_trade(self):
        """Execute a simulated trade."""
        # Select random token pair and DEXes
        token_pair = random.choice(list(self.token_pairs.values()))
        dex1 = random.choice(list(self.dexes.values()))
        dex2 = random.choice([dex for dex in self.dexes.values() if dex.name != dex1.name])
        
        # Update token price
        token_price = token_pair.update_price()
        
        # Get prices on different DEXes
        buy_price = dex1.get_price(token_price, True)
        sell_price = dex2.get_price(token_price, False)
        
        # Calculate potential profit
        amount = 1.0  # 1 unit of base token
        potential_profit = (sell_price - buy_price) * amount
        
        # Estimated gas cost (in USD)
        eth_price = 2500.0  # Assume ETH price is $2500
        gas_price_gwei = 50  # 50 gwei
        gas_limit = random.randint(150000, 300000)
        gas_cost = (gas_limit * gas_price_gwei * 1e-9) * eth_price
        
        # Determine if profitable and successful
        is_profitable = potential_profit > gas_cost
        
        # Apply learning model's improved prediction
        prediction_accuracy = self.learning_loop.prediction_accuracy / 100
        is_profitable_predicted = is_profitable if random.random() < prediction_accuracy else not is_profitable
        
        # Only execute if predicted to be profitable
        if is_profitable_predicted:
            # Actually successful?
            is_successful = random.random() < self.success_probability
            
            # Execution time (ms)
            execution_time = np.random.lognormal(5, 0.5)  # ~150ms typical
            self.execution_times.append(execution_time)
            
            # Calculate actual profit
            actual_profit = potential_profit * 0.9 if is_successful else 0  # 10% slippage on actual execution
            
            # Record metrics
            self.total_trades += 1
            token_pair.trades += 1
            dex1.trades += 1
            dex2.trades += 1
            
            if is_successful:
                self.successful_trades += 1
                self.total_profit += actual_profit
                self.total_gas_cost += gas_cost
                token_pair.successful_trades += 1
                token_pair.profit += actual_profit - gas_cost
                dex1.successful_trades += 1
                dex2.successful_trades += 1
                dex1.profit += (actual_profit - gas_cost) / 2  # Split profit between DEXes
                dex2.profit += (actual_profit - gas_cost) / 2
            else:
                self.total_gas_cost += gas_cost  # Still pay gas even if trade fails
            
            # Create execution result for learning
            result = {
                "token_pair": token_pair.name,
                "dex1": dex1.name,
                "dex2": dex2.name,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "amount": amount,
                "potential_profit": potential_profit,
                "gas_cost": gas_cost,
                "is_profitable": is_profitable,
                "is_successful": is_successful,
                "actual_profit": actual_profit,
                "execution_time": execution_time
            }
            
            # Add to learning loop
            self.learning_loop.add_execution_result(result)
            
            return result
        
        return None
    
    def get_metrics(self):
        """Get trading metrics."""
        success_rate = (self.successful_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        avg_execution_time = sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0
        max_execution_time = max(self.execution_times) if self.execution_times else 0
        min_execution_time = min(self.execution_times) if self.execution_times else 0
        
        return {
            "trades": {
                "total": self.total_trades,
                "successful": self.successful_trades,
                "failed": self.total_trades - self.successful_trades,
                "success_rate": success_rate
            },
            "profit": {
                "total_usd": self.total_profit,
                "gas_cost_usd": self.total_gas_cost,
                "net_profit_usd": self.total_profit - self.total_gas_cost,
                "avg_profit_per_trade_usd": (self.total_profit - self.total_gas_cost) / self.successful_trades if self.successful_trades else 0
            },
            "performance": {
                "avg_execution_time_ms": avg_execution_time,
                "max_execution_time_ms": max_execution_time,
                "min_execution_time_ms": min_execution_time
            },
            "token_pairs": {pair.name: pair.get_stats() for pair in self.token_pairs.values()},
            "dexes": {dex.name: dex.get_stats() for dex in self.dexes.values()}
        }

def run_simulation(args):
    """Run the advanced simulation."""
    print(f"Running advanced simulation from {args.start_date} to {args.end_date}")
    print(f"Trades per day: {args.trades_per_day}")
    print(f"Learning interval: {args.learning_interval} hours")
    
    # Create directories
    os.makedirs(args.metrics_dir, exist_ok=True)
    os.makedirs(args.results_dir, exist_ok=True)
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    # Calculate number of days
    num_days = (end_date - start_date).days + 1
    print(f"Total days: {num_days}")
    
    # Initialize token pairs
    token_pairs = {
        "WETH-USDC": TokenPair("WETH", "USDC", 2500.0, 0.03),
        "WBTC-USDC": TokenPair("WBTC", "USDC", 40000.0, 0.035),
        "WETH-DAI": TokenPair("WETH", "DAI", 2500.0, 0.025),
        "WBTC-DAI": TokenPair("WBTC", "DAI", 40000.0, 0.03),
        "LINK-USDC": TokenPair("LINK", "USDC", 15.0, 0.04)
    }
    
    # Initialize DEXes
    dexes = {
        "uniswap_v3": DEX("uniswap_v3", 0.0003, 0.0005),
        "sushiswap": DEX("sushiswap", 0.0003, 0.001),
        "curve": DEX("curve", 0.0004, 0.0008),
        "balancer": DEX("balancer", 0.0002, 0.0012)
    }
    
    # Initialize learning loop
    learning_loop = SimpleLearningLoop()
    
    # Initialize trade simulator
    simulator = TradeSimulator(token_pairs, dexes, learning_loop)
    
    # Store daily metrics for analysis
    daily_metrics = []
    
    # Simulate each day
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"Simulating day: {date_str}")
        
        # trades per hour
        trades_per_hour = max(1, args.trades_per_day // 24)
        
        # Simulate each hour
        for hour in range(24):
            # Execute trades for this hour
            for _ in range(trades_per_hour):
                simulator.execute_trade()
                time.sleep(0.01)  # Small delay for better performance
            
            # Run learning loop if it's time
            if hour % args.learning_interval == 0:
                print(f"Running learning loop at {date_str} {hour:02d}:00")
                learning_loop.process_results()
                simulator.update_success_probability()
        
        # Get metrics for this day
        metrics = simulator.get_metrics()
        metrics["ml"] = learning_loop.get_stats()
        
        # Add system metrics
        metrics["system"] = {
            "cpu_usage_percent": random.uniform(20, 40),
            "memory_usage_mb": random.uniform(4000, 8000),
            "disk_usage_mb": random.uniform(8000, 12000)
        }
        
        # Save metrics for this day
        daily_metrics.append(metrics)
        
        # Save daily metrics to file
        daily_file = os.path.join(args.results_dir, f"day_{date_str}_metrics.json")
        with open(daily_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Move to next day
        current_date += timedelta(days=1)
    
    # Generate final report
    total_trades = simulator.total_trades
    successful_trades = simulator.successful_trades
    success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
    total_profit = simulator.total_profit - simulator.total_gas_cost
    avg_profit_per_day = total_profit / num_days if num_days > 0 else 0
    
    # Get initial and final ML metrics
    initial_accuracy = daily_metrics[0]["ml"]["prediction_accuracy"] if daily_metrics else 0
    final_accuracy = daily_metrics[-1]["ml"]["prediction_accuracy"] if daily_metrics else 0
    accuracy_improvement = final_accuracy - initial_accuracy
    
    # Create monthly breakdown
    monthly_breakdown = {}
    for i, day_metrics in enumerate(daily_metrics):
        date = start_date + timedelta(days=i)
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
        
        monthly_breakdown[month_key]["trades"] += day_metrics["trades"]["total"]
        monthly_breakdown[month_key]["successful_trades"] += day_metrics["trades"]["successful"]
        monthly_breakdown[month_key]["net_profit_usd"] += day_metrics["profit"]["net_profit_usd"]
        monthly_breakdown[month_key]["gas_cost_usd"] += day_metrics["profit"]["gas_cost_usd"]
        monthly_breakdown[month_key]["model_updates"] += day_metrics["ml"]["model_updates"]
        monthly_breakdown[month_key]["strategy_adaptations"] += day_metrics["ml"]["strategy_adaptations"]
        monthly_breakdown[month_key]["prediction_accuracy"] += day_metrics["ml"]["prediction_accuracy"]
        monthly_breakdown[month_key]["days"] += 1
    
    # Calculate averages for monthly data
    for month, data in monthly_breakdown.items():
        if data["days"] > 0:
            data["prediction_accuracy"] /= data["days"]
            data["avg_profit_per_day"] = data["net_profit_usd"] / data["days"]
            data["success_rate"] = (data["successful_trades"] / data["trades"]) * 100 if data["trades"] > 0 else 0
    
    # Sort token pairs and DEXes by profit
    sorted_pairs = sorted(
        [{"pair": name, **pair.get_stats()} for name, pair in token_pairs.items()],
        key=lambda x: x["net_profit_usd"],
        reverse=True
    )
    
    sorted_dexes = sorted(
        [{"dex": name, **dex.get_stats()} for name, dex in dexes.items()],
        key=lambda x: x["net_profit_usd"],
        reverse=True
    )
    
    # Create final report
    report = {
        "simulation_period": {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_days": num_days
        },
        "overall_metrics": {
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "success_rate": success_rate,
            "total_profit_usd": total_profit,
            "avg_profit_per_day_usd": avg_profit_per_day
        },
        "ml_metrics": {
            "total_model_updates": learning_loop.model_updates,
            "total_strategy_adaptations": learning_loop.strategy_adaptations,
            "avg_prediction_accuracy": learning_loop.prediction_accuracy,
            "initial_prediction_accuracy": initial_accuracy,
            "final_prediction_accuracy": final_accuracy,
            "accuracy_improvement": accuracy_improvement
        },
        "monthly_breakdown": monthly_breakdown,
        "top_profitable_pairs": sorted_pairs[:5],
        "top_profitable_dexes": sorted_dexes[:3]
    }
    
    # Save report to file
    report_path = os.path.join(args.results_dir, "simulation_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate markdown summary
    summary_path = os.path.join(args.results_dir, "simulation_summary.md")
    with open(summary_path, 'w') as f:
        f.write(f"# ArbitrageX Simulation Summary\n\n")
        f.write(f"## Overview\n\n")
        f.write(f"Simulation period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({num_days} days)\n\n")
        f.write(f"## Overall Performance\n\n")
        f.write(f"- Total Trades: {total_trades}\n")
        f.write(f"- Successful Trades: {successful_trades}\n")
        f.write(f"- Success Rate: {success_rate:.2f}%\n")
        f.write(f"- Total Profit: ${total_profit:.2f}\n")
        f.write(f"- Average Profit per Day: ${avg_profit_per_day:.2f}\n\n")
        f.write(f"## ML Metrics\n\n")
        f.write(f"- Total Model Updates: {learning_loop.model_updates}\n")
        f.write(f"- Total Strategy Adaptations: {learning_loop.strategy_adaptations}\n")
        f.write(f"- Initial Prediction Accuracy: {initial_accuracy:.2f}%\n")
        f.write(f"- Final Prediction Accuracy: {final_accuracy:.2f}%\n")
        f.write(f"- Accuracy Improvement: {accuracy_improvement:.2f}%\n\n")
        f.write(f"## Monthly Breakdown\n\n")
        f.write(f"| Month | Trades | Success Rate | Net Profit | Avg Profit/Day | Model Updates | Strategy Adaptations | Prediction Accuracy |\n")
        f.write(f"|-------|--------|-------------|------------|----------------|---------------|----------------------|---------------------|\n")
        for month, data in sorted(monthly_breakdown.items()):
            f.write(f"| {month} | {data['trades']} | {data['success_rate']:.2f}% | ${data['net_profit_usd']:.2f} | ${data['avg_profit_per_day']:.2f} | {data['model_updates']} | {data['strategy_adaptations']} | {data['prediction_accuracy']:.2f}% |\n")
        f.write(f"\n## Top 5 Most Profitable Token Pairs\n\n")
        f.write(f"| Token Pair | Trades | Success Rate | Net Profit |\n")
        f.write(f"|------------|--------|-------------|------------|\n")
        for item in sorted_pairs[:5]:
            success_rate = (item["successful_trades"] / item["trades"] * 100) if item["trades"] > 0 else 0
            f.write(f"| {item['pair']} | {item['trades']} | {success_rate:.2f}% | ${item['net_profit_usd']:.2f} |\n")
        f.write(f"\n## Top 3 Most Profitable DEXes\n\n")
        f.write(f"| DEX | Trades | Success Rate | Net Profit |\n")
        f.write(f"|-----|--------|-------------|------------|\n")
        for item in sorted_dexes[:3]:
            success_rate = (item["successful_trades"] / item["trades"] * 100) if item["trades"] > 0 else 0
            f.write(f"| {item['dex']} | {item['trades']} | {success_rate:.2f}% | ${item['net_profit_usd']:.2f} |\n")
    
    print(f"Simulation completed. Reports saved to:")
    print(f"  - {report_path}")
    print(f"  - {summary_path}")
    
    print(f"Total trades: {total_trades}")
    print(f"Successful trades: {successful_trades}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Total profit: ${total_profit:.2f}")
    print(f"Average profit per day: ${avg_profit_per_day:.2f}")
    print(f"Final prediction accuracy: {final_accuracy:.2f}%")
    print(f"Accuracy improvement: {accuracy_improvement:.2f}%")
    
    return report

def main():
    """Main function to run the test."""
    args = parse_arguments()
    report = run_simulation(args)
    return 0 if report else 1

if __name__ == "__main__":
    sys.exit(main()) 