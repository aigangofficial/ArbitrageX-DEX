"""
Feature Extractor for ArbitrageX AI

This module extracts features from historical arbitrage data to prepare datasets
for machine learning model training. It processes raw trade data and transforms
it into feature vectors that can be used for predictive modeling.

Features extracted include:
- Market volatility indicators
- Gas price trends
- Token liquidity metrics
- Time-based patterns
- Network congestion metrics
- Historical profitability

The extracted features are used by model_training.py to train ML models for
arbitrage opportunity prediction and optimization.
"""

import os
import json
import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/feature_extractor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FeatureExtractor")

class FeatureSet:
    """
    Container class for feature datasets used in model training.
    Provides a standardized interface for accessing feature data.
    """
    
    def __init__(self, features_df: pd.DataFrame, target_df: pd.DataFrame, metadata: Dict = None):
        """
        Initialize a feature set with features and target variables.
        
        Args:
            features_df: DataFrame containing extracted features
            target_df: DataFrame containing target variables
            metadata: Optional metadata about the feature set
        """
        self.features = features_df
        self.targets = target_df
        self.metadata = metadata or {}
        
        # Store column information
        self.feature_columns = list(features_df.columns)
        self.target_columns = list(target_df.columns)
        
        # Track transformations
        self.is_scaled = False
        self.scaler = None
        
    def get_train_test_split(self, test_size: float = 0.2, random_state: int = 42) -> Tuple:
        """
        Split the dataset into training and testing sets.
        
        Args:
            test_size: Proportion of the dataset to include in the test split
            random_state: Random seed for reproducibility
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        if self.features.empty or self.targets.empty:
            logger.error("Cannot split empty feature set")
            return None, None, None, None
            
        X_train, X_test, y_train, y_test = train_test_split(
            self.features, self.targets, test_size=test_size, random_state=random_state
        )
        
        return X_train, X_test, y_train, y_test
    
    def scale_features(self, method: str = "standard") -> None:
        """
        Scale features using the specified method.
        
        Args:
            method: Scaling method ('standard' or 'minmax')
        """
        if self.features.empty:
            logger.error("Cannot scale empty feature set")
            return
            
        if method == "standard":
            self.scaler = StandardScaler()
        elif method == "minmax":
            self.scaler = MinMaxScaler()
        else:
            logger.warning(f"Unknown scaling method: {method}, using StandardScaler")
            self.scaler = StandardScaler()
            
        # Fit and transform
        scaled_features = pd.DataFrame(
            self.scaler.fit_transform(self.features),
            columns=self.features.columns,
            index=self.features.index
        )
        
        self.features = scaled_features
        self.is_scaled = True
        
    def save(self, features_path: str, targets_path: str) -> None:
        """
        Save features and targets to CSV files.
        
        Args:
            features_path: Path to save features CSV
            targets_path: Path to save targets CSV
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(features_path), exist_ok=True)
        os.makedirs(os.path.dirname(targets_path), exist_ok=True)
        
        # Save to CSV
        self.features.to_csv(features_path)
        self.targets.to_csv(targets_path)
        
        # Save scaler if available
        if self.scaler is not None:
            scaler_path = os.path.join(os.path.dirname(features_path), "scaler.pkl")
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
                
        logger.info(f"Saved feature set to {features_path} and {targets_path}")
        
    @classmethod
    def load(cls, features_path: str, targets_path: str) -> 'FeatureSet':
        """
        Load a feature set from CSV files.
        
        Args:
            features_path: Path to features CSV
            targets_path: Path to targets CSV
            
        Returns:
            FeatureSet object
        """
        if not os.path.exists(features_path) or not os.path.exists(targets_path):
            logger.error(f"Feature files not found: {features_path} or {targets_path}")
            return None
            
        features_df = pd.read_csv(features_path, index_col=0)
        targets_df = pd.read_csv(targets_path, index_col=0)
        
        feature_set = cls(features_df, targets_df)
        
        # Load scaler if available
        scaler_path = os.path.join(os.path.dirname(features_path), "scaler.pkl")
        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                feature_set.scaler = pickle.load(f)
                feature_set.is_scaled = True
                
        logger.info(f"Loaded feature set from {features_path} and {targets_path}")
        return feature_set

class FeatureExtractor:
    """
    Extracts and processes features from historical arbitrage data for ML model training.
    """
    
    def __init__(self, config_path: str = "backend/ai/config/feature_extraction.json"):
        """
        Initialize the feature extractor with configuration settings.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.raw_data = None
        self.features_df = None
        self.target_df = None
        self.scaler = None
        
        # Initialize data paths
        self.data_dir = self.config.get("data_directory", "backend/ai/data")
        self.raw_data_path = os.path.join(self.data_dir, "trade_history", "trade_history.json")
        self.features_path = os.path.join(self.data_dir, "features", "extracted_features.csv")
        self.target_path = os.path.join(self.data_dir, "features", "target_variables.csv")
        
        # Ensure directories exist
        os.makedirs(os.path.join(self.data_dir, "features"), exist_ok=True)
        
        logger.info(f"FeatureExtractor initialized with config from {config_path}")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary containing configuration settings
        """
        default_config = {
            "data_directory": "backend/ai/data",
            "feature_window_size": 24,  # Hours of historical data to use for feature extraction
            "target_window_size": 6,    # Hours ahead to predict
            "min_data_points": 100,     # Minimum number of data points required
            "scaling_method": "standard",  # 'standard' or 'minmax'
            "features_to_extract": [
                "market_volatility",
                "gas_price_trends",
                "token_liquidity",
                "time_patterns",
                "network_congestion",
                "historical_profitability"
            ],
            "target_variables": [
                "profit",
                "success_rate"
            ]
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {config_path}")
                # Merge with default config to ensure all keys exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            else:
                logger.warning(f"Config file {config_path} not found, using default configuration")
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return default_config
    
    def load_raw_data(self) -> pd.DataFrame:
        """
        Load raw trade data from JSON file.
        
        Returns:
            DataFrame containing raw trade data
        """
        try:
            if os.path.exists(self.raw_data_path):
                with open(self.raw_data_path, 'r') as f:
                    data = json.load(f)
                
                # Extract trade history from the loaded data
                if "trade_history" in data and isinstance(data["trade_history"], list):
                    trades = data["trade_history"]
                    logger.info(f"Loaded {len(trades)} trades from {self.raw_data_path}")
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(trades)
                    
                    # Convert timestamp to datetime
                    if "timestamp" in df.columns:
                        df["datetime"] = pd.to_datetime(df["timestamp"], unit='s')
                        df.set_index("datetime", inplace=True)
                        df.sort_index(inplace=True)
                    
                    self.raw_data = df
                    return df
                else:
                    logger.warning("No trade history found in the data file")
                    return pd.DataFrame()
            else:
                logger.warning(f"Raw data file {self.raw_data_path} not found")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading raw data: {str(e)}")
            return pd.DataFrame()
    
    def extract_features(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Extract features from raw trade data.
        
        Returns:
            Tuple of (features_df, target_df)
        """
        if self.raw_data is None or self.raw_data.empty:
            self.load_raw_data()
            
        if self.raw_data is None or self.raw_data.empty:
            logger.error("No raw data available for feature extraction")
            return pd.DataFrame(), pd.DataFrame()
        
        logger.info("Starting feature extraction process")
        
        # Check if we have enough data points
        if len(self.raw_data) < self.config.get("min_data_points", 100):
            logger.warning(f"Insufficient data points: {len(self.raw_data)} < {self.config.get('min_data_points', 100)}")
            return pd.DataFrame(), pd.DataFrame()
        
        # Initialize feature dataframes
        features = []
        targets = []
        
        # Get feature window size in hours
        window_size = self.config.get("feature_window_size", 24)
        target_window = self.config.get("target_window_size", 6)
        
        # Resample data to hourly intervals if needed
        hourly_data = self.raw_data.resample('1H').agg({
            'profit': 'mean',
            'success': 'mean',  # This gives success rate
            'gas_price': 'mean',
            'gas_used': 'mean',
            'amount': 'mean',
            'timestamp': 'count'  # This gives trade count per hour
        }).fillna(0)
        
        hourly_data.rename(columns={'timestamp': 'trade_count'}, inplace=True)
        
        # Extract features for each time window
        for i in range(window_size, len(hourly_data) - target_window):
            # Get window data
            window_data = hourly_data.iloc[i-window_size:i]
            target_data = hourly_data.iloc[i:i+target_window]
            
            # Extract features from this window
            window_features = {}
            
            # 1. Market volatility indicators
            if "market_volatility" in self.config.get("features_to_extract", []):
                window_features["profit_std"] = window_data["profit"].std()
                window_features["profit_range"] = window_data["profit"].max() - window_data["profit"].min()
                window_features["profit_trend"] = self._calculate_trend(window_data["profit"])
            
            # 2. Gas price trends
            if "gas_price_trends" in self.config.get("features_to_extract", []):
                window_features["gas_price_mean"] = window_data["gas_price"].mean()
                window_features["gas_price_std"] = window_data["gas_price"].std()
                window_features["gas_price_trend"] = self._calculate_trend(window_data["gas_price"])
            
            # 3. Time-based patterns
            if "time_patterns" in self.config.get("features_to_extract", []):
                current_hour = window_data.index[-1].hour
                current_day = window_data.index[-1].dayofweek
                window_features["hour_of_day"] = current_hour
                window_features["day_of_week"] = current_day
                
                # One-hot encode hour of day (simplified to 4 periods)
                for period in range(4):
                    period_start = period * 6
                    period_end = (period + 1) * 6 - 1
                    window_features[f"hour_period_{period}"] = 1 if period_start <= current_hour <= period_end else 0
                
                # One-hot encode day of week (weekday vs weekend)
                window_features["is_weekend"] = 1 if current_day >= 5 else 0
            
            # 4. Historical profitability
            if "historical_profitability" in self.config.get("features_to_extract", []):
                window_features["avg_profit_1h"] = window_data["profit"].iloc[-1]
                window_features["avg_profit_6h"] = window_data["profit"].iloc[-6:].mean()
                window_features["avg_profit_24h"] = window_data["profit"].mean()
                window_features["success_rate_24h"] = window_data["success"].mean()
            
            # 5. Network congestion metrics
            if "network_congestion" in self.config.get("features_to_extract", []):
                window_features["avg_gas_used"] = window_data["gas_used"].mean()
                window_features["gas_used_trend"] = self._calculate_trend(window_data["gas_used"])
                window_features["trade_frequency"] = window_data["trade_count"].mean()
            
            # Add timestamp for reference
            window_features["timestamp"] = window_data.index[-1].timestamp()
            
            # Extract target variables
            target_vars = {}
            for target in self.config.get("target_variables", ["profit", "success_rate"]):
                if target == "profit":
                    target_vars["future_profit"] = target_data["profit"].mean()
                elif target == "success_rate":
                    target_vars["future_success_rate"] = target_data["success"].mean()
            
            target_vars["timestamp"] = window_data.index[-1].timestamp()
            
            features.append(window_features)
            targets.append(target_vars)
        
        # Convert to DataFrames
        features_df = pd.DataFrame(features)
        target_df = pd.DataFrame(targets)
        
        # Set timestamp as index
        if "timestamp" in features_df.columns:
            features_df["datetime"] = pd.to_datetime(features_df["timestamp"], unit='s')
            features_df.set_index("datetime", inplace=True)
            features_df.drop("timestamp", axis=1, inplace=True)
        
        if "timestamp" in target_df.columns:
            target_df["datetime"] = pd.to_datetime(target_df["timestamp"], unit='s')
            target_df.set_index("datetime", inplace=True)
            target_df.drop("timestamp", axis=1, inplace=True)
        
        # Scale features
        features_df = self._scale_features(features_df)
        
        self.features_df = features_df
        self.target_df = target_df
        
        logger.info(f"Extracted {len(features_df)} feature vectors with {features_df.shape[1]} features each")
        
        return features_df, target_df
    
    def _calculate_trend(self, series: pd.Series) -> float:
        """
        Calculate the trend of a time series using linear regression.
        
        Args:
            series: Time series data
            
        Returns:
            Slope of the linear regression line
        """
        if len(series) < 2:
            return 0
        
        x = np.arange(len(series))
        y = series.values
        
        # Calculate slope using least squares
        x_mean = x.mean()
        y_mean = y.mean()
        
        numerator = ((x - x_mean) * (y - y_mean)).sum()
        denominator = ((x - x_mean) ** 2).sum()
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        return slope
    
    def _scale_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Scale features using the specified scaling method.
        
        Args:
            features_df: DataFrame containing features
            
        Returns:
            DataFrame with scaled features
        """
        # Select columns to scale (exclude categorical features)
        categorical_cols = [col for col in features_df.columns if col.startswith("hour_period_") or col == "is_weekend"]
        numeric_cols = [col for col in features_df.columns if col not in categorical_cols]
        
        if not numeric_cols:
            return features_df
        
        # Initialize scaler based on configuration
        scaling_method = self.config.get("scaling_method", "standard")
        if scaling_method == "standard":
            self.scaler = StandardScaler()
        elif scaling_method == "minmax":
            self.scaler = MinMaxScaler()
        else:
            logger.warning(f"Unknown scaling method: {scaling_method}, using StandardScaler")
            self.scaler = StandardScaler()
        
        # Scale numeric features
        scaled_features = self.scaler.fit_transform(features_df[numeric_cols])
        
        # Create new DataFrame with scaled features
        scaled_df = pd.DataFrame(scaled_features, columns=numeric_cols, index=features_df.index)
        
        # Add back categorical features
        for col in categorical_cols:
            scaled_df[col] = features_df[col]
        
        return scaled_df
    
    def save_features(self) -> Tuple[str, str]:
        """
        Save extracted features and target variables to CSV files.
        
        Returns:
            Tuple of (features_path, target_path)
        """
        if self.features_df is None or self.target_df is None:
            logger.warning("No features or targets to save")
            return "", ""
        
        try:
            # Save features
            self.features_df.to_csv(self.features_path)
            logger.info(f"Saved features to {self.features_path}")
            
            # Save targets
            self.target_df.to_csv(self.target_path)
            logger.info(f"Saved target variables to {self.target_path}")
            
            return self.features_path, self.target_path
        except Exception as e:
            logger.error(f"Error saving features: {str(e)}")
            return "", ""
    
    def visualize_features(self, save_path: Optional[str] = None):
        """
        Visualize extracted features.
        
        Args:
            save_path: Path to save the visualization, if None, display only
        """
        if self.features_df is None or self.features_df.empty:
            logger.warning("No features available for visualization")
            return
        
        # Select a subset of features to visualize
        numeric_features = [col for col in self.features_df.columns 
                           if not col.startswith("hour_period_") and col != "is_weekend"]
        
        if len(numeric_features) > 6:
            selected_features = numeric_features[:6]
        else:
            selected_features = numeric_features
        
        # Create figure with subplots
        fig, axes = plt.subplots(len(selected_features), 1, figsize=(12, 3*len(selected_features)))
        fig.suptitle("Feature Trends Over Time", fontsize=16)
        
        # Plot each feature
        for i, feature in enumerate(selected_features):
            ax = axes[i] if len(selected_features) > 1 else axes
            self.features_df[feature].plot(ax=ax)
            ax.set_title(f"{feature}")
            ax.set_xlabel("")
            ax.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved feature visualization to {save_path}")
        else:
            plt.show()
    
    def visualize_feature_correlations(self, save_path: Optional[str] = None):
        """
        Visualize correlations between features and target variables.
        
        Args:
            save_path: Path to save the visualization, if None, display only
        """
        if self.features_df is None or self.target_df is None:
            logger.warning("No features or targets available for correlation visualization")
            return
        
        # Merge features and targets
        merged_df = pd.concat([self.features_df, self.target_df], axis=1)
        
        # Select numeric columns only
        numeric_cols = merged_df.select_dtypes(include=[np.number]).columns
        
        # Calculate correlation matrix
        corr_matrix = merged_df[numeric_cols].corr()
        
        # Create figure
        plt.figure(figsize=(12, 10))
        plt.title("Feature-Target Correlations", fontsize=16)
        
        # Plot correlation matrix as heatmap
        im = plt.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
        plt.colorbar(im, label='Correlation Coefficient')
        
        # Add labels
        plt.xticks(range(len(numeric_cols)), numeric_cols, rotation=90)
        plt.yticks(range(len(numeric_cols)), numeric_cols)
        
        # Add correlation values
        for i in range(len(numeric_cols)):
            for j in range(len(numeric_cols)):
                text = plt.text(j, i, f"{corr_matrix.iloc[i, j]:.2f}",
                               ha="center", va="center", color="black" if abs(corr_matrix.iloc[i, j]) < 0.5 else "white")
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Saved correlation visualization to {save_path}")
        else:
            plt.show()

# Example usage
if __name__ == "__main__":
    # Initialize feature extractor
    extractor = FeatureExtractor()
    
    # Load raw data
    raw_data = extractor.load_raw_data()
    
    if not raw_data.empty:
        # Extract features
        features_df, target_df = extractor.extract_features()
        
        if not features_df.empty and not target_df.empty:
            # Save features
            features_path, target_path = extractor.save_features()
            
            # Visualize features
            extractor.visualize_features("backend/ai/data/feature_trends.png")
            
            # Visualize correlations
            extractor.visualize_feature_correlations("backend/ai/data/feature_correlations.png")
            
            print(f"Feature extraction complete. Extracted {len(features_df)} feature vectors.")
            print(f"Features saved to {features_path}")
            print(f"Target variables saved to {target_path}")
        else:
            print("Feature extraction failed or produced empty results.")
    else:
        print("No raw data available for feature extraction.") 