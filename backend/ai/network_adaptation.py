import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
import json
import os
import time
from datetime import datetime, timedelta
import requests
import joblib
from dataclasses import dataclass
from web3 import Web3
import matplotlib.pyplot as plt
from feature_extractor import FeatureExtractor
from model_training import ModelTrainer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_adaptation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class NetworkStats:
    """Data class for storing network statistics"""
    network_id: str
    name: str
    gas_price: float
    block_time: float
    congestion_level: float
    liquidity_score: float
    historical_success_rate: float
    current_arbitrage_opportunities: int
    last_updated: datetime

class NetworkAdaptation:
    """AI logic for multi-chain trading optimization"""
    
    def __init__(self, config_path: str = "backend/config/network_settings.json",
                data_dir: str = "backend/ai/data",
                models_dir: str = "backend/ai/models"):
        self.config_path = config_path
        self.data_dir = data_dir
        self.models_dir = models_dir
        self.networks_file = os.path.join(data_dir, "network_stats.json")
        
        # Create directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Load network configuration
        self.network_config = self._load_network_config()
        
        # Initialize network stats
        self.network_stats = {}
        self._load_network_stats()
        
        # Initialize feature extractor and model trainer
        self.feature_extractor = FeatureExtractor(config_path="backend/ai/config/feature_extraction.json")
        self.model_trainer = ModelTrainer(models_dir=models_dir)
        
        # Initialize network selector model ID
        self.network_selector_model_id = None
        self._load_best_model()
    
    def _load_network_config(self) -> Dict:
        """Load network configuration from JSON file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded network configuration for {len(config['networks'])} networks")
                return config
        else:
            # Create default configuration
            default_config = {
                "networks": [
                    {
                        "id": "ethereum",
                        "name": "Ethereum Mainnet",
                        "chain_id": 1,
                        "rpc_url": "${ETHEREUM_RPC_URL}",
                        "explorer_url": "https://etherscan.io",
                        "enabled": True,
                        "priority": 1
                    },
                    {
                        "id": "arbitrum",
                        "name": "Arbitrum One",
                        "chain_id": 42161,
                        "rpc_url": "${ARBITRUM_RPC_URL}",
                        "explorer_url": "https://arbiscan.io",
                        "enabled": True,
                        "priority": 2
                    },
                    {
                        "id": "polygon",
                        "name": "Polygon",
                        "chain_id": 137,
                        "rpc_url": "${POLYGON_RPC_URL}",
                        "explorer_url": "https://polygonscan.com",
                        "enabled": True,
                        "priority": 3
                    },
                    {
                        "id": "optimism",
                        "name": "Optimism",
                        "chain_id": 10,
                        "rpc_url": "${OPTIMISM_RPC_URL}",
                        "explorer_url": "https://optimistic.etherscan.io",
                        "enabled": True,
                        "priority": 4
                    },
                    {
                        "id": "base",
                        "name": "Base",
                        "chain_id": 8453,
                        "rpc_url": "${BASE_RPC_URL}",
                        "explorer_url": "https://basescan.org",
                        "enabled": True,
                        "priority": 5
                    }
                ],
                "default_network": "ethereum",
                "auto_switch": True,
                "min_liquidity_threshold_usd": 100000,
                "min_profit_threshold_usd": 50,
                "gas_price_weight": 0.3,
                "liquidity_weight": 0.4,
                "historical_success_weight": 0.3
            }
            
            # Save default configuration
            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent=2)
                logger.info(f"Created default network configuration for {len(default_config['networks'])} networks")
            
            return default_config
    
    def _load_network_stats(self):
        """Load network statistics from JSON file"""
        if os.path.exists(self.networks_file):
            with open(self.networks_file, "r") as f:
                stats_data = json.load(f)
                
                for network_id, stats in stats_data.items():
                    # Convert string datetime to datetime object
                    stats["last_updated"] = datetime.fromisoformat(stats["last_updated"])
                    
                    # Create NetworkStats object
                    self.network_stats[network_id] = NetworkStats(**stats)
                
                logger.info(f"Loaded statistics for {len(self.network_stats)} networks")
        else:
            # Initialize empty stats for each network
            for network in self.network_config["networks"]:
                network_id = network["id"]
                self.network_stats[network_id] = NetworkStats(
                    network_id=network_id,
                    name=network["name"],
                    gas_price=0.0,
                    block_time=0.0,
                    congestion_level=0.0,
                    liquidity_score=0.0,
                    historical_success_rate=0.0,
                    current_arbitrage_opportunities=0,
                    last_updated=datetime.now() - timedelta(days=1)  # Set to yesterday to force update
                )
            
            logger.info(f"Initialized empty statistics for {len(self.network_stats)} networks")
    
    def _save_network_stats(self):
        """Save network statistics to JSON file"""
        stats_data = {}
        
        for network_id, stats in self.network_stats.items():
            # Convert NetworkStats object to dictionary
            stats_dict = stats.__dict__.copy()
            
            # Convert datetime to string
            stats_dict["last_updated"] = stats_dict["last_updated"].isoformat()
            
            stats_data[network_id] = stats_dict
        
        with open(self.networks_file, "w") as f:
            json.dump(stats_data, f, indent=2)
            logger.info(f"Saved statistics for {len(stats_data)} networks")
    
    def _load_best_model(self):
        """Load the best network selector model"""
        self.network_selector_model_id = self.model_trainer.get_best_model("network")
        
        if self.network_selector_model_id:
            logger.info(f"Loaded best network selector model: {self.network_selector_model_id}")
        else:
            logger.warning("No network selector model found")
    
    def update_network_stats(self, force_update: bool = False):
        """
        Update network statistics for all enabled networks
        
        Args:
            force_update: Whether to force update even if recently updated
        """
        for network in self.network_config["networks"]:
            network_id = network["id"]
            
            # Skip disabled networks
            if not network.get("enabled", True):
                continue
            
            # Skip networks that were recently updated (within the last hour)
            if not force_update and network_id in self.network_stats:
                last_updated = self.network_stats[network_id].last_updated
                if datetime.now() - last_updated < timedelta(hours=1):
                    logger.info(f"Skipping update for {network_id} (updated {last_updated.isoformat()})")
                    continue
            
            try:
                # Get RPC URL from environment variable if needed
                rpc_url = network["rpc_url"]
                if rpc_url.startswith("${") and rpc_url.endswith("}"):
                    env_var = rpc_url[2:-1]
                    rpc_url = os.getenv(env_var, "")
                
                if not rpc_url:
                    logger.warning(f"No RPC URL for {network_id}, skipping update")
                    continue
                
                # Initialize Web3 connection
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                # Check connection
                if not w3.is_connected():
                    logger.warning(f"Failed to connect to {network_id} at {rpc_url}")
                    continue
                
                # Get current gas price
                gas_price = w3.eth.gas_price / 1e9  # Convert to Gwei
                
                # Get latest block
                latest_block = w3.eth.get_block("latest")
                
                # Get block time (average of last 10 blocks)
                block_times = []
                current_block = latest_block
                previous_block = None
                
                for i in range(10):
                    if previous_block:
                        block_time = current_block.timestamp - previous_block.timestamp
                        block_times.append(block_time)
                    
                    previous_block = current_block
                    current_block = w3.eth.get_block(current_block.number - 1)
                
                avg_block_time = sum(block_times) / len(block_times) if block_times else 0
                
                # Calculate congestion level (based on gas price relative to historical average)
                # This is a simplified approach - in production, use more sophisticated metrics
                congestion_level = min(1.0, gas_price / 50.0)  # Normalize to [0, 1]
                
                # Get liquidity score (in production, fetch from DEX APIs or subgraphs)
                # For now, use a placeholder value
                liquidity_score = np.random.uniform(0.5, 1.0)
                
                # Get historical success rate (in production, calculate from actual trade history)
                # For now, use a placeholder value
                historical_success_rate = np.random.uniform(0.7, 0.95)
                
                # Get current arbitrage opportunities (in production, scan for actual opportunities)
                # For now, use a placeholder value
                current_arbitrage_opportunities = np.random.randint(0, 10)
                
                # Update network stats
                self.network_stats[network_id] = NetworkStats(
                    network_id=network_id,
                    name=network["name"],
                    gas_price=float(gas_price),
                    block_time=float(avg_block_time),
                    congestion_level=float(congestion_level),
                    liquidity_score=float(liquidity_score),
                    historical_success_rate=float(historical_success_rate),
                    current_arbitrage_opportunities=int(current_arbitrage_opportunities),
                    last_updated=datetime.now()
                )
                
                logger.info(f"Updated statistics for {network_id}")
            
            except Exception as e:
                logger.error(f"Error updating statistics for {network_id}: {str(e)}")
        
        # Save updated statistics
        self._save_network_stats()
    
    def train_network_selector(self, historical_data_path: Optional[str] = None):
        """
        Train a model to select the best network for arbitrage
        
        Args:
            historical_data_path: Path to historical trade data (optional)
        """
        # In production, use actual historical trade data
        # For now, generate synthetic data for demonstration
        
        if historical_data_path and os.path.exists(historical_data_path):
            # Load historical data
            historical_df = pd.read_csv(historical_data_path)
            logger.info(f"Loaded {len(historical_df)} historical trades from {historical_data_path}")
        else:
            # Generate synthetic data
            logger.info("Generating synthetic training data")
            
            # Get network IDs
            network_ids = [network["id"] for network in self.network_config["networks"] 
                         if network.get("enabled", True)]
            
            # Generate 1000 synthetic trades
            num_samples = 1000
            
            # Features
            gas_prices = np.random.uniform(5, 200, num_samples)  # Gas prices in Gwei
            block_times = np.random.uniform(1, 15, num_samples)  # Block times in seconds
            congestion_levels = np.random.uniform(0, 1, num_samples)  # Congestion levels [0, 1]
            liquidity_scores = np.random.uniform(0, 1, num_samples)  # Liquidity scores [0, 1]
            trade_amounts = np.random.uniform(1000, 100000, num_samples)  # Trade amounts in USD
            
            # Time features
            hours = np.random.randint(0, 24, num_samples)
            days_of_week = np.random.randint(0, 7, num_samples)
            
            # Calculate hour and day of week cyclical features
            hour_sin = np.sin(2 * np.pi * hours / 24)
            hour_cos = np.cos(2 * np.pi * hours / 24)
            day_of_week_sin = np.sin(2 * np.pi * days_of_week / 7)
            day_of_week_cos = np.cos(2 * np.pi * days_of_week / 7)
            
            # Target (best network)
            # For synthetic data, we'll use a simple rule:
            # - Low gas price and high liquidity -> Ethereum
            # - Fast block time and medium gas -> Arbitrum
            # - Low gas price and fast block time -> Polygon
            # - Medium gas and high liquidity -> Optimism
            # - Otherwise -> Base
            
            best_networks = []
            for i in range(num_samples):
                if gas_prices[i] < 50 and liquidity_scores[i] > 0.8:
                    best_networks.append("ethereum")
                elif block_times[i] < 5 and 50 <= gas_prices[i] < 100:
                    best_networks.append("arbitrum")
                elif gas_prices[i] < 30 and block_times[i] < 3:
                    best_networks.append("polygon")
                elif 30 <= gas_prices[i] < 80 and liquidity_scores[i] > 0.7:
                    best_networks.append("optimism")
                else:
                    best_networks.append("base")
            
            # Create DataFrame
            historical_df = pd.DataFrame({
                "gas_price": gas_prices,
                "block_time": block_times,
                "congestion_level": congestion_levels,
                "liquidity_score": liquidity_scores,
                "trade_amount": trade_amounts,
                "hour": hours,
                "day_of_week": days_of_week,
                "hour_sin": hour_sin,
                "hour_cos": hour_cos,
                "day_of_week_sin": day_of_week_sin,
                "day_of_week_cos": day_of_week_cos,
                "best_network": best_networks
            })
            
            # Save synthetic data
            synthetic_data_path = os.path.join(self.data_dir, "synthetic_network_trades.csv")
            historical_df.to_csv(synthetic_data_path, index=False)
            logger.info(f"Saved {len(historical_df)} synthetic trades to {synthetic_data_path}")
        
        # Prepare features and target
        X = historical_df[[
            "gas_price", "block_time", "congestion_level", "liquidity_score", 
            "trade_amount", "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos"
        ]].values
        
        # Convert network names to numeric labels
        network_mapping = {network: i for i, network in enumerate(historical_df["best_network"].unique())}
        y = historical_df["best_network"].map(network_mapping).values
        
        # Save network mapping for later use
        with open(os.path.join(self.models_dir, "network_mapping.json"), "w") as f:
            json.dump(network_mapping, f, indent=2)
        
        # Normalize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Save scaler for later use
        joblib.dump(scaler, os.path.join(self.models_dir, "network_selector_scaler.pkl"))
        
        # Split into training and testing sets
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Create FeatureSet objects
        from feature_extractor import FeatureSet
        
        feature_names = [
            "gas_price", "block_time", "congestion_level", "liquidity_score", 
            "trade_amount", "hour_sin", "hour_cos", "day_of_week_sin", "day_of_week_cos"
        ]
        
        training_data = FeatureSet(
            X=X_train,
            y=y_train,
            feature_names=feature_names,
            target_name="network",
            scaler=scaler
        )
        
        testing_data = FeatureSet(
            X=X_test,
            y=y_test,
            feature_names=feature_names,
            target_name="network",
            scaler=scaler
        )
        
        # Train network selector model
        result = self.model_trainer.train_network_selector(training_data)
        
        # Evaluate model
        model_id = result["model_id"]
        evaluation = self.model_trainer.evaluate_model(model_id, testing_data)
        
        # Update best model
        self.network_selector_model_id = model_id
        
        logger.info(f"Trained network selector model with ID: {model_id}")
        logger.info(f"Evaluation metrics: {evaluation['metrics']}")
        
        return {
            "model_id": model_id,
            "metrics": evaluation["metrics"],
            "feature_importance": result["feature_importance"],
            "feature_names": feature_names
        }
    
    def select_best_network(self, trade_data: Dict) -> str:
        """
        Select the best network for a given trade
        
        Args:
            trade_data: Dictionary with trade data
            
        Returns:
            ID of the best network for the trade
        """
        # If no model is available, use heuristic approach
        if not self.network_selector_model_id:
            return self._select_network_heuristic(trade_data)
        
        try:
            # Load network mapping
            mapping_path = os.path.join(self.models_dir, "network_mapping.json")
            if not os.path.exists(mapping_path):
                logger.error("Network mapping not found")
                return self._select_network_heuristic(trade_data)
            
            with open(mapping_path, "r") as f:
                network_mapping = json.load(f)
            
            # Reverse mapping (from numeric to network ID)
            reverse_mapping = {v: k for k, v in network_mapping.items()}
            
            # Load scaler
            scaler_path = os.path.join(self.models_dir, "network_selector_scaler.pkl")
            if not os.path.exists(scaler_path):
                logger.error("Network selector scaler not found")
                return self._select_network_heuristic(trade_data)
            
            scaler = joblib.load(scaler_path)
            
            # Prepare features
            features = np.array([[
                trade_data.get("gas_price", 50),
                trade_data.get("block_time", 5),
                trade_data.get("congestion_level", 0.5),
                trade_data.get("liquidity_score", 0.5),
                trade_data.get("trade_amount", 10000),
                trade_data.get("hour_sin", 0),
                trade_data.get("hour_cos", 0),
                trade_data.get("day_of_week_sin", 0),
                trade_data.get("day_of_week_cos", 0)
            ]])
            
            # Scale features
            features_scaled = scaler.transform(features)
            
            # Make prediction
            prediction = self.model_trainer.predict(self.network_selector_model_id, features_scaled)
            
            # Convert prediction to network ID
            if isinstance(prediction, np.ndarray) and len(prediction) > 0:
                predicted_label = int(np.round(prediction[0]))
                best_network = reverse_mapping.get(predicted_label, self.network_config["default_network"])
                
                logger.info(f"Model predicted network: {best_network}")
                return best_network
            else:
                logger.warning("Invalid prediction from model")
                return self._select_network_heuristic(trade_data)
        
        except Exception as e:
            logger.error(f"Error selecting network with model: {str(e)}")
            return self._select_network_heuristic(trade_data)
    
    def _select_network_heuristic(self, trade_data: Dict) -> str:
        """
        Select the best network using a heuristic approach
        
        Args:
            trade_data: Dictionary with trade data
            
        Returns:
            ID of the best network for the trade
        """
        # Update network stats if needed
        for network_id, stats in self.network_stats.items():
            if datetime.now() - stats.last_updated > timedelta(hours=1):
                logger.info(f"Network stats for {network_id} are outdated, updating...")
                self.update_network_stats()
                break
        
        # Get weights from config
        gas_weight = self.network_config.get("gas_price_weight", 0.3)
        liquidity_weight = self.network_config.get("liquidity_weight", 0.4)
        success_weight = self.network_config.get("historical_success_weight", 0.3)
        
        # Calculate score for each network
        network_scores = {}
        
        for network in self.network_config["networks"]:
            network_id = network["id"]
            
            # Skip disabled networks
            if not network.get("enabled", True):
                continue
            
            # Get network stats
            if network_id not in self.network_stats:
                continue
            
            stats = self.network_stats[network_id]
            
            # Normalize gas price (lower is better)
            max_gas = max(stat.gas_price for stat in self.network_stats.values())
            normalized_gas = 1 - (stats.gas_price / max_gas if max_gas > 0 else 0)
            
            # Calculate score
            score = (
                gas_weight * normalized_gas +
                liquidity_weight * stats.liquidity_score +
                success_weight * stats.historical_success_rate
            )
            
            # Adjust score based on current arbitrage opportunities
            if stats.current_arbitrage_opportunities > 0:
                score *= (1 + 0.1 * min(stats.current_arbitrage_opportunities, 10))
            
            network_scores[network_id] = score
        
        if not network_scores:
            logger.warning("No networks available for selection")
            return self.network_config["default_network"]
        
        # Select network with highest score
        best_network = max(network_scores.items(), key=lambda x: x[1])[0]
        
        logger.info(f"Selected network using heuristic: {best_network} (score: {network_scores[best_network]:.4f})")
        return best_network
    
    def get_network_stats_summary(self) -> Dict:
        """
        Get a summary of network statistics
        
        Returns:
            Dictionary with network statistics summary
        """
        summary = {}
        
        for network_id, stats in self.network_stats.items():
            summary[network_id] = {
                "name": stats.name,
                "gas_price": stats.gas_price,
                "block_time": stats.block_time,
                "congestion_level": stats.congestion_level,
                "liquidity_score": stats.liquidity_score,
                "historical_success_rate": stats.historical_success_rate,
                "current_arbitrage_opportunities": stats.current_arbitrage_opportunities,
                "last_updated": stats.last_updated.isoformat()
            }
        
        return summary
    
    def visualize_network_comparison(self, save_path: Optional[str] = None):
        """
        Visualize network comparison
        
        Args:
            save_path: Path to save the visualization
        """
        if not self.network_stats:
            logger.warning("No network stats available for visualization")
            return
        
        # Prepare data
        networks = []
        gas_prices = []
        block_times = []
        congestion_levels = []
        liquidity_scores = []
        success_rates = []
        
        for network_id, stats in self.network_stats.items():
            networks.append(stats.name)
            gas_prices.append(stats.gas_price)
            block_times.append(stats.block_time)
            congestion_levels.append(stats.congestion_level)
            liquidity_scores.append(stats.liquidity_score)
            success_rates.append(stats.historical_success_rate)
        
        # Create figure
        fig, axs = plt.subplots(2, 2, figsize=(14, 10))
        
        # Gas prices
        axs[0, 0].bar(networks, gas_prices)
        axs[0, 0].set_title("Gas Prices (Gwei)")
        axs[0, 0].set_ylabel("Gwei")
        axs[0, 0].tick_params(axis="x", rotation=45)
        
        # Block times
        axs[0, 1].bar(networks, block_times)
        axs[0, 1].set_title("Block Times (seconds)")
        axs[0, 1].set_ylabel("Seconds")
        axs[0, 1].tick_params(axis="x", rotation=45)
        
        # Congestion and liquidity
        axs[1, 0].bar(networks, congestion_levels, label="Congestion Level")
        axs[1, 0].bar(networks, liquidity_scores, bottom=congestion_levels, label="Liquidity Score")
        axs[1, 0].set_title("Congestion and Liquidity")
        axs[1, 0].set_ylabel("Score")
        axs[1, 0].tick_params(axis="x", rotation=45)
        axs[1, 0].legend()
        
        # Success rates
        axs[1, 1].bar(networks, success_rates)
        axs[1, 1].set_title("Historical Success Rates")
        axs[1, 1].set_ylabel("Rate")
        axs[1, 1].tick_params(axis="x", rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Network comparison visualization saved to {save_path}")
        else:
            plt.show()

# Example usage
if __name__ == "__main__":
    network_adaptation = NetworkAdaptation()
    
    # Update network statistics
    network_adaptation.update_network_stats()
    
    # Train network selector model
    network_adaptation.train_network_selector()
    
    # Example trade data
    trade_data = {
        "token_in": "WETH",
        "token_out": "USDC",
        "amount_in": 1.0,
        "gas_price": 30.0,
        "trade_amount": 2000.0,
        "hour_sin": np.sin(2 * np.pi * 14 / 24),  # 2 PM
        "hour_cos": np.cos(2 * np.pi * 14 / 24),
        "day_of_week_sin": np.sin(2 * np.pi * 2 / 7),  # Wednesday
        "day_of_week_cos": np.cos(2 * np.pi * 2 / 7)
    }
    
    # Select best network for trade
    best_network = network_adaptation.select_best_network(trade_data)
    print(f"Best network for trade: {best_network}")
    
    # Get network stats summary
    stats_summary = network_adaptation.get_network_stats_summary()
    print(f"Network stats summary: {json.dumps(stats_summary, indent=2)}")
    
    # Visualize network comparison
    network_adaptation.visualize_network_comparison("network_comparison.png") 