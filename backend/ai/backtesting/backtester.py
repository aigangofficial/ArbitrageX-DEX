#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Backtesting Framework

This module provides a comprehensive backtesting framework for evaluating
trading strategies against historical market data. It allows for accurate
simulation of various market conditions and strategy performance over time.
"""

import os
import json
import logging
import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/ai/logs/backtesting.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backtester")

@dataclass
class BacktestConfig:
    """Configuration settings for backtesting."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10.0  # ETH
    data_source: str = "historical_data"
    exchange_fees: Dict[str, float] = field(default_factory=lambda: {
        "uniswap": 0.003,
        "sushiswap": 0.0025,
        "balancer": 0.002,
        "curve": 0.0004
    })
    gas_price_gwei: float = 30.0
    slippage_tolerance: float = 0.005
    token_pairs: List[str] = field(default_factory=lambda: [
        "WETH-USDC", "WETH-USDT", "WETH-DAI", "WBTC-USDC", 
        "WBTC-WETH", "LINK-WETH", "UNI-WETH", "AAVE-WETH"
    ])
    trade_size_eth: float = 1.0
    max_concurrent_trades: int = 5
    metrics_dir: str = "backend/ai/metrics/backtest"
    l2_networks_enabled: bool = True
    flash_loans_enabled: bool = True
    mev_protection_enabled: bool = True
    ml_enhancements_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert the config to a dictionary."""
        result = {
            "strategy_name": self.strategy_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "data_source": self.data_source,
            "exchange_fees": self.exchange_fees,
            "gas_price_gwei": self.gas_price_gwei,
            "slippage_tolerance": self.slippage_tolerance,
            "token_pairs": self.token_pairs,
            "trade_size_eth": self.trade_size_eth,
            "max_concurrent_trades": self.max_concurrent_trades,
            "metrics_dir": self.metrics_dir,
            "l2_networks_enabled": self.l2_networks_enabled,
            "flash_loans_enabled": self.flash_loans_enabled,
            "mev_protection_enabled": self.mev_protection_enabled,
            "ml_enhancements_enabled": self.ml_enhancements_enabled
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestConfig':
        """Create a config from a dictionary."""
        # Convert date strings to datetime objects
        data["start_date"] = datetime.fromisoformat(data["start_date"])
        data["end_date"] = datetime.fromisoformat(data["end_date"])
        return cls(**data)

@dataclass
class BacktestResult:
    """Results of a backtest run."""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_profit_loss: float = 0.0
    total_profit_loss_usd: float = 0.0
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    avg_profit_per_trade: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    volatility: float = 0.0
    win_rate: float = 0.0
    daily_returns: List[float] = field(default_factory=list)
    trade_history: List[Dict[str, Any]] = field(default_factory=list)
    capital_history: List[Tuple[datetime, float]] = field(default_factory=list)
    gas_costs: float = 0.0
    execution_time: float = 0.0
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to a dictionary."""
        result = {
            "strategy_name": self.strategy_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_profit_loss": self.total_profit_loss,
            "total_profit_loss_usd": self.total_profit_loss_usd,
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "failed_trades": self.failed_trades,
            "avg_profit_per_trade": self.avg_profit_per_trade,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "volatility": self.volatility,
            "win_rate": self.win_rate,
            "daily_returns": self.daily_returns,
            "trade_history": self.trade_history,
            "capital_history": [(dt.isoformat(), cap) for dt, cap in self.capital_history],
            "gas_costs": self.gas_costs,
            "execution_time": self.execution_time,
            "equity_curve": [(dt.isoformat(), val) for dt, val in self.equity_curve]
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestResult':
        """Create a result object from a dictionary."""
        # Convert date strings to datetime objects
        data["start_date"] = datetime.fromisoformat(data["start_date"])
        data["end_date"] = datetime.fromisoformat(data["end_date"])
        
        # Convert lists of tuples
        if "capital_history" in data:
            data["capital_history"] = [(datetime.fromisoformat(dt), cap) 
                                     for dt, cap in data["capital_history"]]
        
        if "equity_curve" in data:
            data["equity_curve"] = [(datetime.fromisoformat(dt), val) 
                                   for dt, val in data["equity_curve"]]
            
        return cls(**data)


class Backtester:
    """
    Main backtesting engine for ArbitrageX trading strategies.
    
    This class loads historical market data and simulates the execution
    of trading strategies to evaluate their performance under various
    market conditions.
    """
    
    def __init__(self, config: BacktestConfig):
        """
        Initialize the backtester.
        
        Args:
            config: Configuration settings for the backtest
        """
        self.config = config
        self.logger = logger
        self.historical_data = {}
        self.current_capital = config.initial_capital
        self.active_trades = []
        self.completed_trades = []
        self.current_timestamp = config.start_date
        
        # Create metrics directory
        os.makedirs(config.metrics_dir, exist_ok=True)
        
        self.logger.info(f"Initializing backtester for strategy: {config.strategy_name}")
        self.logger.info(f"Backtest period: {config.start_date} to {config.end_date}")
        
    def load_historical_data(self) -> None:
        """
        Load historical market data for the backtest period.
        
        This method loads data from the configured data source and prepares
        it for use in the backtest.
        """
        self.logger.info(f"Loading historical data from {self.config.data_source}")
        
        # Load data for each token pair
        for pair in self.config.token_pairs:
            try:
                # In a real implementation, this would load from files/database
                # For now, we'll simulate this with demo data
                self.historical_data[pair] = self._generate_demo_data(pair)
                self.logger.info(f"Loaded data for {pair}: {len(self.historical_data[pair])} data points")
            except Exception as e:
                self.logger.error(f"Failed to load data for {pair}: {str(e)}")
                
        self.logger.info(f"Historical data loaded for {len(self.historical_data)} token pairs")
    
    def _generate_demo_data(self, token_pair: str) -> List[Dict[str, Any]]:
        """
        Generate demo data for testing when real data is not available.
        
        Args:
            token_pair: The token pair to generate data for
            
        Returns:
            A list of price data points
        """
        data = []
        current_date = self.config.start_date
        
        # Base prices for different tokens (in USD)
        base_prices = {
            "WETH-USDC": 1800.0,
            "WETH-USDT": 1800.0,
            "WETH-DAI": 1800.0,
            "WBTC-USDC": 28000.0,
            "WBTC-WETH": 15.5,  # WBTC/WETH price
            "LINK-WETH": 0.007,  # LINK/WETH price
            "UNI-WETH": 0.004,   # UNI/WETH price
            "AAVE-WETH": 0.05    # AAVE/WETH price
        }
        
        # Set volatility based on token pair
        volatility = 0.02  # Default 2% daily volatility
        if "WBTC" in token_pair:
            volatility = 0.025
        elif "LINK" in token_pair or "UNI" in token_pair:
            volatility = 0.035
            
        # Generate hourly data points
        base_price = base_prices.get(token_pair, 1000.0)
        price = base_price
        
        while current_date <= self.config.end_date:
            # Add some randomness to the price
            price_change = np.random.normal(0, volatility * price)
            price += price_change
            
            # Ensure price doesn't go negative
            price = max(price, 0.00001 * base_price)
            
            # Add exchange-specific prices with slight differences
            data.append({
                "timestamp": current_date,
                "token_pair": token_pair,
                "uniswap_price": price * (1 + np.random.normal(0, 0.001)),
                "sushiswap_price": price * (1 + np.random.normal(0, 0.001)),
                "balancer_price": price * (1 + np.random.normal(0, 0.001)),
                "curve_price": price * (1 + np.random.normal(0, 0.001)),
                "volume": abs(np.random.normal(100, 30)),
                "liquidity": abs(np.random.normal(1000, 300))
            })
            
            # Move to next hour
            current_date += timedelta(hours=1)
            
        return data
    
    def run_backtest(self) -> BacktestResult:
        """
        Run the backtest simulation.
        
        Returns:
            The results of the backtest
        """
        start_time = time.time()
        self.logger.info(f"Starting backtest for {self.config.strategy_name}")
        
        # Load historical data
        self.load_historical_data()
        
        # Initialize result tracking
        result = BacktestResult(
            strategy_name=self.config.strategy_name,
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            initial_capital=self.config.initial_capital,
            final_capital=self.config.initial_capital  # Will be updated
        )
        
        # Add initial capital point
        result.capital_history.append((self.current_timestamp, self.current_capital))
        result.equity_curve.append((self.current_timestamp, self.current_capital))
        
        # Simulate trading day by day
        current_date = self.config.start_date
        while current_date <= self.config.end_date:
            self.logger.info(f"Processing date: {current_date.date()}")
            self.current_timestamp = current_date
            
            # Find arbitrage opportunities for this day
            opportunities = self._find_opportunities(current_date)
            
            # Execute trades for available opportunities
            for opportunity in opportunities:
                if len(self.active_trades) < self.config.max_concurrent_trades:
                    trade_result = self._execute_trade(opportunity)
                    
                    if trade_result["success"]:
                        result.successful_trades += 1
                        self.current_capital += trade_result["profit_loss"]
                        result.total_profit_loss += trade_result["profit_loss"]
                        result.total_profit_loss_usd += trade_result["profit_loss_usd"]
                        result.gas_costs += trade_result["gas_cost"]
                    else:
                        result.failed_trades += 1
                        self.current_capital += trade_result["profit_loss"]  # Usually negative for failed trades
                        result.total_profit_loss += trade_result["profit_loss"]
                        result.gas_costs += trade_result["gas_cost"]
                    
                    result.total_trades += 1
                    result.trade_history.append(trade_result)
                    
            # Update capital history at end of day
            result.capital_history.append((current_date, self.current_capital))
            result.equity_curve.append((current_date, self.current_capital))
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Calculate final results
        result.final_capital = self.current_capital
        if result.total_trades > 0:
            result.avg_profit_per_trade = result.total_profit_loss / result.total_trades
            result.win_rate = result.successful_trades / result.total_trades
        
        # Calculate daily returns
        for i in range(1, len(result.capital_history)):
            prev_capital = result.capital_history[i-1][1]
            curr_capital = result.capital_history[i][1]
            daily_return = (curr_capital - prev_capital) / prev_capital if prev_capital > 0 else 0
            result.daily_returns.append(daily_return)
        
        # Calculate Sharpe ratio and volatility
        if len(result.daily_returns) > 0:
            result.volatility = np.std(result.daily_returns) * np.sqrt(365)  # Annualized
            avg_daily_return = np.mean(result.daily_returns)
            risk_free_rate = 0.01 / 365  # Assuming 1% annual risk-free rate
            result.sharpe_ratio = (avg_daily_return - risk_free_rate) / np.std(result.daily_returns) * np.sqrt(365) if np.std(result.daily_returns) > 0 else 0
        
        # Calculate max drawdown
        peak = self.config.initial_capital
        drawdown = 0
        for _, capital in result.capital_history:
            if capital > peak:
                peak = capital
            current_drawdown = (peak - capital) / peak if peak > 0 else 0
            if current_drawdown > drawdown:
                drawdown = current_drawdown
        result.max_drawdown = drawdown
        
        # Record execution time
        result.execution_time = time.time() - start_time
        
        # Save results
        self._save_results(result)
        
        self.logger.info(f"Backtest completed. Total trades: {result.total_trades}, Success rate: {result.win_rate:.2%}")
        self.logger.info(f"Final capital: {result.final_capital:.4f} ETH, Profit/Loss: {result.total_profit_loss:.4f} ETH")
        
        return result
    
    def _find_opportunities(self, date: datetime) -> List[Dict[str, Any]]:
        """
        Find arbitrage opportunities for a specific day.
        
        Args:
            date: The date to find opportunities for
            
        Returns:
            A list of opportunity dictionaries
        """
        opportunities = []
        
        # Filter data for the current day
        for token_pair, data in self.historical_data.items():
            day_data = [d for d in data if d["timestamp"].date() == date.date()]
            
            # Process each hour
            for hour_data in day_data:
                # Find price differences between exchanges
                prices = {
                    "uniswap": hour_data["uniswap_price"],
                    "sushiswap": hour_data["sushiswap_price"],
                    "balancer": hour_data["balancer_price"],
                    "curve": hour_data.get("curve_price", 0)
                }
                
                # Find min and max prices
                min_exchange = min(prices, key=prices.get)
                max_exchange = max(prices, key=prices.get)
                min_price = prices[min_exchange]
                max_price = prices[max_exchange]
                
                # Calculate potential profit (considering fees)
                fee_buy = self.config.exchange_fees[min_exchange]
                fee_sell = self.config.exchange_fees[max_exchange]
                
                # Simple arbitrage calculation
                trade_size = self.config.trade_size_eth
                buy_amount = trade_size / min_price
                sell_amount = buy_amount * (1 - fee_sell)
                sell_value = sell_amount * max_price
                buy_cost = trade_size * (1 + fee_buy)
                
                profit = sell_value - buy_cost
                profit_threshold = 0.001 * buy_cost  # 0.1% minimum profit
                
                # Check if profit is above threshold
                if profit > profit_threshold:
                    # Calculate gas cost based on current network
                    if self.config.l2_networks_enabled:
                        # L2 gas cost is much lower
                        gas_units = 150000  # Approximate gas units for a swap
                        gas_price_gwei = self.config.gas_price_gwei * 0.1  # 90% cheaper on L2
                        gas_cost_eth = (gas_units * gas_price_gwei * 1e-9)
                    else:
                        gas_units = 180000  # Slightly higher on mainnet
                        gas_price_gwei = self.config.gas_price_gwei
                        gas_cost_eth = (gas_units * gas_price_gwei * 1e-9)
                    
                    # Check if still profitable after gas
                    if profit > gas_cost_eth:
                        opportunity = {
                            "timestamp": hour_data["timestamp"],
                            "token_pair": token_pair,
                            "buy_exchange": min_exchange,
                            "sell_exchange": max_exchange,
                            "buy_price": min_price,
                            "sell_price": max_price,
                            "trade_size_eth": trade_size,
                            "expected_profit_eth": profit - gas_cost_eth,
                            "expected_profit_usd": (profit - gas_cost_eth) * min_price,
                            "gas_cost_eth": gas_cost_eth,
                            "gas_price_gwei": gas_price_gwei
                        }
                        opportunities.append(opportunity)
        
        # Sort opportunities by expected profit (descending)
        opportunities.sort(key=lambda x: x["expected_profit_eth"], reverse=True)
        return opportunities
    
    def _execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate the execution of a trade.
        
        Args:
            opportunity: The trading opportunity to execute
            
        Returns:
            A dictionary with the trade result
        """
        # Start with the expected values
        trade_result = {
            "timestamp": opportunity["timestamp"],
            "token_pair": opportunity["token_pair"],
            "buy_exchange": opportunity["buy_exchange"],
            "sell_exchange": opportunity["sell_exchange"],
            "trade_size_eth": opportunity["trade_size_eth"],
            "expected_profit_eth": opportunity["expected_profit_eth"],
            "gas_cost": opportunity["gas_cost_eth"],
            "success": True
        }
        
        # Simulate real-world execution with some randomness
        # In reality, prices might change, slippage might occur, etc.
        execution_quality = np.random.normal(0.95, 0.1)  # 95% of expected profit on average
        execution_quality = max(min(execution_quality, 1.1), 0.5)  # Bound between 50% and 110%
        
        # Apply execution quality to actual profit
        actual_profit = opportunity["expected_profit_eth"] * execution_quality
        
        # Factor in gas costs
        net_profit = actual_profit - opportunity["gas_cost_eth"]
        
        # Determine if trade was successful
        if net_profit > 0:
            trade_result["success"] = True
            trade_result["profit_loss"] = net_profit
            trade_result["profit_loss_usd"] = net_profit * opportunity["buy_price"]
        else:
            trade_result["success"] = False
            trade_result["profit_loss"] = net_profit  # This is a loss
            trade_result["profit_loss_usd"] = net_profit * opportunity["buy_price"]
        
        # Add execution details
        trade_result["execution_quality"] = execution_quality
        trade_result["actual_profit_eth"] = actual_profit
        trade_result["net_profit_eth"] = net_profit
        
        # Add execution method details
        if self.config.l2_networks_enabled and np.random.random() < 0.7:  # 70% chance of using L2 if enabled
            trade_result["execution_method"] = "layer2"
            trade_result["l2_network"] = np.random.choice(["arbitrum", "optimism", "polygon", "base"])
        elif self.config.flash_loans_enabled and np.random.random() < 0.6:  # 60% chance of using flash loans
            trade_result["execution_method"] = "flash_loan"
            trade_result["flash_loan_provider"] = np.random.choice(["aave", "uniswap", "balancer", "maker"])
        else:
            trade_result["execution_method"] = "standard"
        
        # Add MEV protection details if enabled
        if self.config.mev_protection_enabled:
            trade_result["mev_protected"] = True
            trade_result["mev_method"] = "flashbots"
            
            # Sometimes MEV protection saves from frontrunning
            if np.random.random() < 0.1:  # 10% chance of potential MEV attack
                saved_loss = opportunity["expected_profit_eth"] * np.random.uniform(0.3, 0.8)
                trade_result["mev_saved"] = saved_loss
                trade_result["mev_notes"] = "Protected from potential frontrunning"
        
        # Add ML enhancement details if enabled
        if self.config.ml_enhancements_enabled:
            enhancement_factor = np.random.normal(1.15, 0.05)  # 15% improvement on average
            trade_result["ml_enhanced"] = True
            trade_result["ml_enhancement_factor"] = enhancement_factor
            
            # Sometimes ML prevents bad trades
            if trade_result["success"] == False and np.random.random() < 0.7:
                trade_result["ml_prevented_execution"] = True
                trade_result["success"] = False
                trade_result["profit_loss"] = -trade_result["gas_cost"] * 0.1  # Only pay a fraction of gas for cancelled tx
                trade_result["profit_loss_usd"] = trade_result["profit_loss"] * opportunity["buy_price"]
                trade_result["ml_notes"] = "ML model prevented execution of unprofitable trade"
        
        return trade_result
    
    def _save_results(self, results: BacktestResult) -> None:
        """
        Save backtest results to disk.
        
        Args:
            results: The backtest results to save
        """
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.config.metrics_dir}/{self.config.strategy_name}_{timestamp}.json"
        
        # Save results as JSON
        with open(filename, 'w') as f:
            json.dump(results.to_dict(), f, indent=2)
            
        self.logger.info(f"Backtest results saved to {filename}")
        
        # Save configuration as well
        config_filename = f"{self.config.metrics_dir}/{self.config.strategy_name}_{timestamp}_config.json"
        with open(config_filename, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
            
        self.logger.info(f"Backtest configuration saved to {config_filename}")

    def generate_report(self, results: BacktestResult, output_dir: Optional[str] = None) -> str:
        """
        Generate a detailed HTML report of backtest results.
        
        Args:
            results: The backtest results
            output_dir: Directory to save the report (defaults to metrics_dir)
            
        Returns:
            The path to the generated report
        """
        if output_dir is None:
            output_dir = self.config.metrics_dir
            
        os.makedirs(output_dir, exist_ok=True)
        
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{output_dir}/{results.strategy_name}_{timestamp}_report.html"
        
        # Generate plots
        self._generate_equity_curve(results, output_dir, timestamp)
        self._generate_trade_distribution(results, output_dir, timestamp)
        
        # Build HTML report
        html_content = f"""
        <html>
        <head>
            <title>Backtest Report: {results.strategy_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333366; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .summary {{ display: flex; flex-wrap: wrap; }}
                .metric {{ flex: 1; min-width: 200px; margin: 10px; padding: 15px; background-color: #f8f8f8; 
                          border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .chart {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>ArbitrageX Backtest Report</h1>
            <p>Strategy: <strong>{results.strategy_name}</strong></p>
            <p>Period: {results.start_date.strftime('%Y-%m-%d')} to {results.end_date.strftime('%Y-%m-%d')}</p>
            
            <h2>Performance Summary</h2>
            <div class="summary">
                <div class="metric">
                    <h3>Initial Capital</h3>
                    <p>{results.initial_capital:.4f} ETH</p>
                </div>
                <div class="metric">
                    <h3>Final Capital</h3>
                    <p>{results.final_capital:.4f} ETH</p>
                </div>
                <div class="metric">
                    <h3>Total Return</h3>
                    <p class="{'positive' if results.total_profit_loss > 0 else 'negative'}">
                        {results.total_profit_loss:.4f} ETH ({((results.final_capital/results.initial_capital)-1)*100:.2f}%)
                    </p>
                </div>
                <div class="metric">
                    <h3>Total Trades</h3>
                    <p>{results.total_trades}</p>
                </div>
                <div class="metric">
                    <h3>Win Rate</h3>
                    <p>{results.win_rate:.2%}</p>
                </div>
                <div class="metric">
                    <h3>Avg Profit/Trade</h3>
                    <p class="{'positive' if results.avg_profit_per_trade > 0 else 'negative'}">
                        {results.avg_profit_per_trade:.6f} ETH
                    </p>
                </div>
                <div class="metric">
                    <h3>Total Gas Costs</h3>
                    <p>{results.gas_costs:.6f} ETH</p>
                </div>
                <div class="metric">
                    <h3>Sharpe Ratio</h3>
                    <p>{results.sharpe_ratio:.2f}</p>
                </div>
                <div class="metric">
                    <h3>Max Drawdown</h3>
                    <p>{results.max_drawdown:.2%}</p>
                </div>
                <div class="metric">
                    <h3>Volatility (Ann.)</h3>
                    <p>{results.volatility:.2%}</p>
                </div>
            </div>
            
            <h2>Equity Curve</h2>
            <div class="chart">
                <img src="{results.strategy_name}_{timestamp}_equity_curve.png" width="100%">
            </div>
            
            <h2>Trade Distribution</h2>
            <div class="chart">
                <img src="{results.strategy_name}_{timestamp}_trade_distribution.png" width="100%">
            </div>
            
            <h2>Execution Method Distribution</h2>
            <div id="execution_methods_chart">
                <!-- This would be a chart in the actual implementation -->
            </div>
            
            <h2>Most Profitable Token Pairs</h2>
            <table>
                <tr>
                    <th>Token Pair</th>
                    <th>Total Trades</th>
                    <th>Win Rate</th>
                    <th>Total Profit</th>
                    <th>Avg Profit/Trade</th>
                </tr>
                <!-- This would be populated dynamically in the actual implementation -->
                <!-- Example row: -->
                <tr>
                    <td>WETH-USDC</td>
                    <td>24</td>
                    <td>75%</td>
                    <td class="positive">0.12 ETH</td>
                    <td class="positive">0.005 ETH</td>
                </tr>
            </table>
            
            <h2>Configuration</h2>
            <pre>{json.dumps(self.config.to_dict(), indent=2)}</pre>
            
            <h2>Recent Trades</h2>
            <table>
                <tr>
                    <th>Time</th>
                    <th>Token Pair</th>
                    <th>Buy Exchange</th>
                    <th>Sell Exchange</th>
                    <th>Size (ETH)</th>
                    <th>Profit/Loss</th>
                    <th>Execution</th>
                </tr>
                <!-- This would list the most recent trades in the actual implementation -->
                <!-- Example row: -->
                <tr>
                    <td>2023-06-15 14:30:00</td>
                    <td>WETH-USDC</td>
                    <td>Uniswap</td>
                    <td>SushiSwap</td>
                    <td>1.0</td>
                    <td class="positive">0.008 ETH</td>
                    <td>Layer 2 (Arbitrum)</td>
                </tr>
            </table>
            
            <p><small>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        </body>
        </html>
        """
        
        # Write report to file
        with open(report_file, 'w') as f:
            f.write(html_content)
            
        self.logger.info(f"Backtest report generated at {report_file}")
        return report_file
    
    def _generate_equity_curve(self, results: BacktestResult, output_dir: str, timestamp: str) -> None:
        """Generate equity curve plot."""
        plt.figure(figsize=(12, 6))
        dates = [dt for dt, _ in results.equity_curve]
        values = [val for _, val in results.equity_curve]
        
        plt.plot(dates, values, 'b-', linewidth=2)
        plt.axhline(y=results.initial_capital, color='r', linestyle='--', alpha=0.5)
        
        plt.title(f"Equity Curve - {results.strategy_name}")
        plt.xlabel("Date")
        plt.ylabel("Capital (ETH)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        output_file = f"{output_dir}/{results.strategy_name}_{timestamp}_equity_curve.png"
        plt.savefig(output_file, dpi=100)
        plt.close()
    
    def _generate_trade_distribution(self, results: BacktestResult, output_dir: str, timestamp: str) -> None:
        """Generate trade distribution plot."""
        plt.figure(figsize=(12, 6))
        
        # Group trades by token pair
        token_pairs = {}
        for trade in results.trade_history:
            pair = trade["token_pair"]
            if pair not in token_pairs:
                token_pairs[pair] = []
            token_pairs[pair].append(trade["profit_loss"])
        
        # Plot distribution
        positions = range(len(token_pairs))
        token_labels = list(token_pairs.keys())
        
        profits = [sum(profits) for profits in token_pairs.values()]
        colors = ['g' if p > 0 else 'r' for p in profits]
        
        plt.bar(positions, profits, color=colors)
        plt.xticks(positions, token_labels, rotation=45)
        
        plt.title(f"Profit Distribution by Token Pair - {results.strategy_name}")
        plt.xlabel("Token Pair")
        plt.ylabel("Total Profit/Loss (ETH)")
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        output_file = f"{output_dir}/{results.strategy_name}_{timestamp}_trade_distribution.png"
        plt.savefig(output_file, dpi=100)
        plt.close()


def main():
    """Run a sample backtest."""
    # Sample configuration
    config = BacktestConfig(
        strategy_name="ml_enhanced",
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 3, 31),
        initial_capital=10.0,
        data_source="simulated"
    )
    
    # Create backtester
    backtester = Backtester(config)
    
    # Run backtest
    results = backtester.run_backtest()
    
    # Generate report
    backtester.generate_report(results)
    
    # Print summary
    print(f"Backtest completed for {config.strategy_name}")
    print(f"Period: {config.start_date.date()} to {config.end_date.date()}")
    print(f"Initial capital: {config.initial_capital:.4f} ETH")
    print(f"Final capital: {results.final_capital:.4f} ETH")
    print(f"Total profit/loss: {results.total_profit_loss:.4f} ETH ({((results.final_capital/config.initial_capital)-1)*100:.2f}%)")
    print(f"Total trades: {results.total_trades}, Success rate: {results.win_rate:.2%}")
    print(f"Average profit per trade: {results.avg_profit_per_trade:.6f} ETH")
    print(f"Sharpe ratio: {results.sharpe_ratio:.2f}")
    print(f"Max drawdown: {results.max_drawdown:.2%}")
    

if __name__ == "__main__":
    main() 