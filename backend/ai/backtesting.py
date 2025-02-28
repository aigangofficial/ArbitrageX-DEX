import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
import json
import os
import time
from datetime import datetime, timedelta
import joblib
from dataclasses import dataclass
from tqdm import tqdm
from feature_extractor import FeatureExtractor, FeatureSet
from model_training import ModelTrainer
from network_adaptation import NetworkAdaptation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtesting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradeResult:
    """Data class for storing trade results"""
    timestamp: datetime
    network: str
    token_in: str
    token_out: str
    amount_in: float
    amount_out: float
    expected_profit_usd: float
    actual_profit_usd: float
    gas_cost_usd: float
    net_profit_usd: float
    execution_time_ms: float
    success: bool
    error: Optional[str] = None

@dataclass
class BacktestResult:
    """Data class for storing backtest results"""
    start_time: datetime
    end_time: datetime
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_profit_usd: float
    total_gas_cost_usd: float
    net_profit_usd: float
    avg_profit_per_trade_usd: float
    max_profit_usd: float
    max_loss_usd: float
    sharpe_ratio: float
    win_rate: float
    trades: List[TradeResult]

class ArbitrageBacktester:
    """Backtests arbitrage strategies against historical data"""
    
    def __init__(self, data_dir: str = "backend/ai/data", 
                models_dir: str = "backend/ai/models",
                results_dir: str = "backend/ai/results"):
        self.data_dir = data_dir
        self.models_dir = models_dir
        self.results_dir = results_dir
        
        # Create directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        
        # Initialize components
        self.feature_extractor = FeatureExtractor(data_dir=data_dir, models_dir=models_dir)
        self.model_trainer = ModelTrainer(models_dir=models_dir)
        self.network_adaptation = NetworkAdaptation(data_dir=data_dir, models_dir=models_dir)
        
        # Load best models
        self.profit_model_id = self.model_trainer.get_best_model("profit")
        self.gas_model_id = self.model_trainer.get_best_model("gas_price")
        self.network_model_id = self.model_trainer.get_best_model("network")
        self.timing_model_id = self.model_trainer.get_best_model("execution_timing")
        
        logger.info(f"Initialized backtester with models: profit={self.profit_model_id}, gas={self.gas_model_id}, network={self.network_model_id}, timing={self.timing_model_id}")
    
    def load_historical_data(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Load historical arbitrage opportunity data
        
        Args:
            file_path: Path to historical data file (optional)
            
        Returns:
            DataFrame with historical data
        """
        if file_path and os.path.exists(file_path):
            # Load from specified file
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} historical opportunities from {file_path}")
            return df
        
        # Check for default files
        default_path = os.path.join(self.data_dir, "historical_opportunities.csv")
        if os.path.exists(default_path):
            df = pd.read_csv(default_path)
            logger.info(f"Loaded {len(df)} historical opportunities from {default_path}")
            return df
        
        # Generate synthetic data if no file exists
        logger.info("No historical data found, generating synthetic data")
        return self._generate_synthetic_data()
    
    def _generate_synthetic_data(self, num_samples: int = 1000) -> pd.DataFrame:
        """
        Generate synthetic arbitrage opportunity data for testing
        
        Args:
            num_samples: Number of synthetic samples to generate
            
        Returns:
            DataFrame with synthetic data
        """
        # Time range (6 months)
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()
        date_range = (end_date - start_date).total_seconds()
        
        # Generate random timestamps
        timestamps = [start_date + timedelta(seconds=np.random.randint(0, date_range)) 
                     for _ in range(num_samples)]
        timestamps.sort()
        
        # Token pairs
        token_pairs = [
            ("WETH", "USDC"),
            ("WETH", "USDT"),
            ("WETH", "DAI"),
            ("WBTC", "USDC"),
            ("WBTC", "USDT"),
            ("LINK", "USDC"),
            ("UNI", "USDC"),
            ("AAVE", "USDC")
        ]
        
        # Networks
        networks = ["ethereum", "arbitrum", "polygon", "optimism", "base"]
        
        # Generate data
        data = []
        for timestamp in timestamps:
            # Select random token pair
            token_in, token_out = token_pairs[np.random.randint(0, len(token_pairs))]
            
            # Select random network
            network = networks[np.random.randint(0, len(networks))]
            
            # Generate trade details
            amount_in = np.random.uniform(0.1, 10.0) if token_in == "WETH" else np.random.uniform(0.01, 1.0) if token_in == "WBTC" else np.random.uniform(10, 1000)
            price_diff_pct = np.random.uniform(0.1, 3.0)  # 0.1% to 3% price difference
            
            # Base price (approximate)
            base_price = 1800 if token_in == "WETH" else 30000 if token_in == "WBTC" else 100 if token_in == "LINK" else 5 if token_in == "UNI" else 80
            
            # Calculate expected profit
            amount_in_usd = amount_in * base_price
            expected_profit_usd = amount_in_usd * (price_diff_pct / 100)
            
            # Gas costs vary by network
            gas_multipliers = {
                "ethereum": 1.0,
                "arbitrum": 0.3,
                "polygon": 0.1,
                "optimism": 0.2,
                "base": 0.15
            }
            
            base_gas_cost = np.random.uniform(20, 100)  # Base gas cost in USD
            gas_cost_usd = base_gas_cost * gas_multipliers[network]
            
            # Net profit
            net_profit_usd = expected_profit_usd - gas_cost_usd
            
            # Success rate varies by network and profit margin
            success_probability = min(0.95, 0.5 + (net_profit_usd / 100))
            success = np.random.random() < success_probability
            
            # If failed, adjust actual profit
            actual_profit_usd = expected_profit_usd if success else -gas_cost_usd
            
            # Execution time (milliseconds)
            execution_time_ms = np.random.uniform(100, 5000)
            
            # Add to data
            data.append({
                "timestamp": timestamp.isoformat(),
                "network": network,
                "token_in": token_in,
                "token_out": token_out,
                "amount_in": amount_in,
                "price_diff_pct": price_diff_pct,
                "expected_profit_usd": expected_profit_usd,
                "gas_cost_usd": gas_cost_usd,
                "net_profit_usd": net_profit_usd,
                "execution_time_ms": execution_time_ms,
                "success": success,
                "hour": timestamp.hour,
                "day_of_week": timestamp.weekday(),
                "is_weekend": 1 if timestamp.weekday() >= 5 else 0
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Save synthetic data
        output_path = os.path.join(self.data_dir, "synthetic_opportunities.csv")
        df.to_csv(output_path, index=False)
        logger.info(f"Generated and saved {len(df)} synthetic opportunities to {output_path}")
        
        return df
    
    def prepare_features(self, data: pd.DataFrame) -> FeatureSet:
        """
        Prepare features for model input
        
        Args:
            data: DataFrame with historical data
            
        Returns:
            FeatureSet with prepared features
        """
        # Convert timestamp strings to datetime
        if "timestamp" in data.columns and isinstance(data["timestamp"].iloc[0], str):
            data["timestamp"] = pd.to_datetime(data["timestamp"])
        
        # Extract time features
        data["hour_sin"] = np.sin(2 * np.pi * data["hour"] / 24)
        data["hour_cos"] = np.cos(2 * np.pi * data["hour"] / 24)
        data["day_of_week_sin"] = np.sin(2 * np.pi * data["day_of_week"] / 7)
        data["day_of_week_cos"] = np.cos(2 * np.pi * data["day_of_week"] / 7)
        
        # Network one-hot encoding
        networks = data["network"].unique()
        for network in networks:
            data[f"network_{network}"] = (data["network"] == network).astype(int)
        
        # Token pair one-hot encoding
        token_pairs = [f"{row.token_in}_{row.token_out}" for _, row in data.iterrows()]
        unique_pairs = list(set(token_pairs))
        for pair in unique_pairs:
            data[f"pair_{pair}"] = [(row.token_in + "_" + row.token_out) == pair for _, row in data.iterrows()]
        
        # Select features
        feature_columns = [
            "price_diff_pct", "gas_cost_usd", "amount_in",
            "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos", "is_weekend"
        ]
        
        # Add network and token pair columns
        feature_columns.extend([col for col in data.columns if col.startswith("network_")])
        feature_columns.extend([col for col in data.columns if col.startswith("pair_")])
        
        # Create feature matrix
        X = data[feature_columns].values
        
        # Create target (net profit)
        y = data["net_profit_usd"].values
        
        # Normalize features
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return FeatureSet(
            X=X_scaled,
            y=y,
            feature_names=feature_columns,
            target_name="net_profit_usd",
            scaler=scaler
        )
    
    def backtest(self, data: pd.DataFrame, use_ai: bool = True) -> BacktestResult:
        """
        Backtest arbitrage strategy on historical data
        
        Args:
            data: DataFrame with historical opportunities
            use_ai: Whether to use AI models for decision making
            
        Returns:
            BacktestResult with backtest results
        """
        logger.info(f"Starting backtest on {len(data)} opportunities")
        
        # Prepare features if using AI
        if use_ai and (self.profit_model_id or self.gas_model_id or self.network_model_id or self.timing_model_id):
            features = self.prepare_features(data)
            logger.info(f"Prepared {features.X.shape[1]} features for AI models")
        
        # Results tracking
        trades = []
        total_profit = 0.0
        total_gas = 0.0
        successful_trades = 0
        failed_trades = 0
        
        # Track profit/loss for Sharpe ratio calculation
        daily_returns = {}
        
        # Process each opportunity
        for i, row in tqdm(data.iterrows(), total=len(data), desc="Backtesting"):
            timestamp = pd.to_datetime(row["timestamp"]) if isinstance(row["timestamp"], str) else row["timestamp"]
            
            # Decision making
            execute_trade = True
            expected_profit = row["expected_profit_usd"]
            gas_cost = row["gas_cost_usd"]
            
            if use_ai:
                # Extract features for this opportunity
                opportunity_features = features.X[i].reshape(1, -1)
                
                # Predict profit if model available
                if self.profit_model_id:
                    predicted_profit = self.model_trainer.predict(self.profit_model_id, opportunity_features)[0]
                    expected_profit = predicted_profit
                
                # Predict gas cost if model available
                if self.gas_model_id:
                    predicted_gas = self.model_trainer.predict(self.gas_model_id, opportunity_features)[0]
                    gas_cost = predicted_gas
                
                # Decide whether to execute based on profit and gas
                net_profit = expected_profit - gas_cost
                
                # Use timing model if available
                if self.timing_model_id:
                    timing_score = self.model_trainer.predict(self.timing_model_id, opportunity_features)[0]
                    execute_trade = timing_score > 0.5 and net_profit > 0
                else:
                    execute_trade = net_profit > 0
            
            # Simple strategy without AI: execute if expected profit > gas cost
            else:
                execute_trade = row["expected_profit_usd"] > row["gas_cost_usd"]
            
            # Skip trades we decide not to execute
            if not execute_trade:
                continue
            
            # Simulate trade execution
            success = row["success"]  # In real backtest, this would be determined by the simulation
            
            if success:
                actual_profit = expected_profit
                net_profit = actual_profit - gas_cost
                successful_trades += 1
            else:
                actual_profit = 0
                net_profit = -gas_cost
                failed_trades += 1
            
            # Track daily returns for Sharpe ratio
            day_key = timestamp.strftime("%Y-%m-%d")
            if day_key not in daily_returns:
                daily_returns[day_key] = 0
            daily_returns[day_key] += net_profit
            
            # Update totals
            total_profit += actual_profit
            total_gas += gas_cost
            
            # Record trade result
            trade_result = TradeResult(
                timestamp=timestamp,
                network=row["network"],
                token_in=row["token_in"],
                token_out=row["token_out"],
                amount_in=row["amount_in"],
                amount_out=row["amount_in"] * (1 + row["price_diff_pct"]/100),
                expected_profit_usd=expected_profit,
                actual_profit_usd=actual_profit,
                gas_cost_usd=gas_cost,
                net_profit_usd=net_profit,
                execution_time_ms=row["execution_time_ms"],
                success=success,
                error=None if success else "Transaction failed"
            )
            
            trades.append(trade_result)
        
        # Calculate metrics
        total_trades = successful_trades + failed_trades
        net_profit = total_profit - total_gas
        
        # Calculate Sharpe ratio (if we have daily returns)
        daily_return_values = list(daily_returns.values())
        sharpe_ratio = 0.0
        if daily_return_values:
            mean_return = np.mean(daily_return_values)
            std_return = np.std(daily_return_values) if len(daily_return_values) > 1 else 1.0
            sharpe_ratio = mean_return / std_return if std_return > 0 else 0.0
        
        # Calculate win rate
        win_rate = successful_trades / total_trades if total_trades > 0 else 0.0
        
        # Calculate max profit and loss
        profits = [t.net_profit_usd for t in trades]
        max_profit = max(profits) if profits else 0.0
        max_loss = min(profits) if profits else 0.0
        
        # Create result object
        result = BacktestResult(
            start_time=min([t.timestamp for t in trades]) if trades else datetime.now(),
            end_time=max([t.timestamp for t in trades]) if trades else datetime.now(),
            total_trades=total_trades,
            successful_trades=successful_trades,
            failed_trades=failed_trades,
            total_profit_usd=total_profit,
            total_gas_cost_usd=total_gas,
            net_profit_usd=net_profit,
            avg_profit_per_trade_usd=net_profit / total_trades if total_trades > 0 else 0.0,
            max_profit_usd=max_profit,
            max_loss_usd=max_loss,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            trades=trades
        )
        
        logger.info(f"Backtest completed: {total_trades} trades, {successful_trades} successful, ${net_profit:.2f} net profit")
        
        return result
    
    def save_backtest_results(self, result: BacktestResult, filename: Optional[str] = None) -> str:
        """
        Save backtest results to file
        
        Args:
            result: BacktestResult to save
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_result_{timestamp}.json"
        
        file_path = os.path.join(self.results_dir, filename)
        
        # Convert result to dictionary
        result_dict = {
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat(),
            "total_trades": result.total_trades,
            "successful_trades": result.successful_trades,
            "failed_trades": result.failed_trades,
            "total_profit_usd": result.total_profit_usd,
            "total_gas_cost_usd": result.total_gas_cost_usd,
            "net_profit_usd": result.net_profit_usd,
            "avg_profit_per_trade_usd": result.avg_profit_per_trade_usd,
            "max_profit_usd": result.max_profit_usd,
            "max_loss_usd": result.max_loss_usd,
            "sharpe_ratio": result.sharpe_ratio,
            "win_rate": result.win_rate,
            "trades": [
                {
                    "timestamp": trade.timestamp.isoformat(),
                    "network": trade.network,
                    "token_in": trade.token_in,
                    "token_out": trade.token_out,
                    "amount_in": trade.amount_in,
                    "amount_out": trade.amount_out,
                    "expected_profit_usd": trade.expected_profit_usd,
                    "actual_profit_usd": trade.actual_profit_usd,
                    "gas_cost_usd": trade.gas_cost_usd,
                    "net_profit_usd": trade.net_profit_usd,
                    "execution_time_ms": trade.execution_time_ms,
                    "success": trade.success,
                    "error": trade.error
                }
                for trade in result.trades
            ]
        }
        
        # Save to file
        with open(file_path, "w") as f:
            json.dump(result_dict, f, indent=2)
        
        logger.info(f"Saved backtest results to {file_path}")
        
        return file_path
    
    def visualize_results(self, result: BacktestResult, save_path: Optional[str] = None):
        """
        Visualize backtest results
        
        Args:
            result: BacktestResult to visualize
            save_path: Optional path to save visualization
        """
        # Set up the figure
        plt.figure(figsize=(20, 15))
        
        # 1. Profit over time
        plt.subplot(3, 2, 1)
        
        # Convert trades to DataFrame for easier plotting
        trades_df = pd.DataFrame([
            {
                "timestamp": trade.timestamp,
                "net_profit_usd": trade.net_profit_usd,
                "success": trade.success,
                "network": trade.network
            }
            for trade in result.trades
        ])
        
        if not trades_df.empty:
            trades_df = trades_df.sort_values("timestamp")
            trades_df["cumulative_profit"] = trades_df["net_profit_usd"].cumsum()
            
            plt.plot(trades_df["timestamp"], trades_df["cumulative_profit"])
            plt.title("Cumulative Profit Over Time")
            plt.xlabel("Date")
            plt.ylabel("Profit (USD)")
            plt.grid(True)
        
        # 2. Profit distribution
        plt.subplot(3, 2, 2)
        if not trades_df.empty:
            sns.histplot(trades_df["net_profit_usd"], kde=True)
            plt.title("Profit Distribution")
            plt.xlabel("Profit (USD)")
            plt.ylabel("Frequency")
            plt.grid(True)
        
        # 3. Success rate by network
        plt.subplot(3, 2, 3)
        if not trades_df.empty:
            network_success = trades_df.groupby("network")["success"].mean()
            network_success.plot(kind="bar")
            plt.title("Success Rate by Network")
            plt.xlabel("Network")
            plt.ylabel("Success Rate")
            plt.grid(True)
        
        # 4. Profit by network
        plt.subplot(3, 2, 4)
        if not trades_df.empty:
            network_profit = trades_df.groupby("network")["net_profit_usd"].sum()
            network_profit.plot(kind="bar")
            plt.title("Total Profit by Network")
            plt.xlabel("Network")
            plt.ylabel("Profit (USD)")
            plt.grid(True)
        
        # 5. Profit by hour of day
        plt.subplot(3, 2, 5)
        if not trades_df.empty:
            trades_df["hour"] = trades_df["timestamp"].dt.hour
            hour_profit = trades_df.groupby("hour")["net_profit_usd"].mean()
            hour_profit.plot(kind="bar")
            plt.title("Average Profit by Hour of Day")
            plt.xlabel("Hour")
            plt.ylabel("Avg Profit (USD)")
            plt.grid(True)
        
        # 6. Profit by day of week
        plt.subplot(3, 2, 6)
        if not trades_df.empty:
            trades_df["day_of_week"] = trades_df["timestamp"].dt.dayofweek
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_profit = trades_df.groupby("day_of_week")["net_profit_usd"].mean()
            day_profit.index = [day_names[i] for i in day_profit.index]
            day_profit.plot(kind="bar")
            plt.title("Average Profit by Day of Week")
            plt.xlabel("Day")
            plt.ylabel("Avg Profit (USD)")
            plt.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved visualization to {save_path}")
        else:
            plt.show()
    
    def compare_strategies(self, data: pd.DataFrame) -> Dict:
        """
        Compare AI strategy with baseline strategy
        
        Args:
            data: DataFrame with historical opportunities
            
        Returns:
            Dictionary with comparison results
        """
        logger.info("Comparing AI strategy with baseline strategy")
        
        # Run backtest with AI
        ai_result = self.backtest(data, use_ai=True)
        
        # Run backtest without AI (baseline)
        baseline_result = self.backtest(data, use_ai=False)
        
        # Calculate improvement
        ai_profit = ai_result.net_profit_usd
        baseline_profit = baseline_result.net_profit_usd
        
        profit_improvement = ai_profit - baseline_profit
        profit_improvement_pct = (profit_improvement / abs(baseline_profit)) * 100 if baseline_profit != 0 else float('inf')
        
        # Create comparison result
        comparison = {
            "ai_strategy": {
                "net_profit_usd": ai_profit,
                "total_trades": ai_result.total_trades,
                "win_rate": ai_result.win_rate,
                "sharpe_ratio": ai_result.sharpe_ratio
            },
            "baseline_strategy": {
                "net_profit_usd": baseline_profit,
                "total_trades": baseline_result.total_trades,
                "win_rate": baseline_result.win_rate,
                "sharpe_ratio": baseline_result.sharpe_ratio
            },
            "improvement": {
                "net_profit_usd": profit_improvement,
                "net_profit_pct": profit_improvement_pct,
                "win_rate": ai_result.win_rate - baseline_result.win_rate,
                "sharpe_ratio": ai_result.sharpe_ratio - baseline_result.sharpe_ratio
            }
        }
        
        logger.info(f"Strategy comparison: AI profit=${ai_profit:.2f}, Baseline profit=${baseline_profit:.2f}, Improvement=${profit_improvement:.2f} ({profit_improvement_pct:.2f}%)")
        
        return comparison

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ArbitrageX Backtesting Tool")
    parser.add_argument("--data", type=str, help="Path to historical data CSV file")
    parser.add_argument("--compare", action="store_true", help="Compare AI strategy with baseline")
    parser.add_argument("--visualize", action="store_true", help="Visualize backtest results")
    parser.add_argument("--save-results", action="store_true", help="Save backtest results to file")
    parser.add_argument("--output", type=str, help="Output file path for results and visualizations")
    
    args = parser.parse_args()
    
    # Initialize backtester
    backtester = ArbitrageBacktester()
    
    # Load data
    data = backtester.load_historical_data(args.data)
    
    if args.compare:
        # Compare strategies
        comparison = backtester.compare_strategies(data)
        print(json.dumps(comparison, indent=2))
        
        if args.save_results and args.output:
            with open(args.output, "w") as f:
                json.dump(comparison, f, indent=2)
    else:
        # Run backtest with AI
        result = backtester.backtest(data, use_ai=True)
        
        # Print summary
        print(f"Backtest Results:")
        print(f"  Total Trades: {result.total_trades}")
        print(f"  Successful Trades: {result.successful_trades}")
        print(f"  Failed Trades: {result.failed_trades}")
        print(f"  Win Rate: {result.win_rate:.2%}")
        print(f"  Total Profit: ${result.total_profit_usd:.2f}")
        print(f"  Total Gas Cost: ${result.total_gas_cost_usd:.2f}")
        print(f"  Net Profit: ${result.net_profit_usd:.2f}")
        print(f"  Avg Profit per Trade: ${result.avg_profit_per_trade_usd:.2f}")
        print(f"  Max Profit: ${result.max_profit_usd:.2f}")
        print(f"  Max Loss: ${result.max_loss_usd:.2f}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.4f}")
        
        # Save results if requested
        if args.save_results:
            output_path = args.output if args.output else None
            backtester.save_backtest_results(result, output_path)
        
        # Visualize if requested
        if args.visualize:
            viz_path = args.output.replace(".json", ".png") if args.output and args.output.endswith(".json") else args.output
            backtester.visualize_results(result, viz_path if args.save_results else None) 