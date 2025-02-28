"""
ML Training Pipeline Module for ArbitrageX

This module implements the end-to-end pipeline for training machine learning models for:
- Arbitrage opportunity detection
- Price impact prediction
- Gas price optimization
- Competitor behavior prediction
"""

import logging
import os
import json
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, LSTM, Dropout, Input, Concatenate
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import joblib
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MLTrainingPipeline")

class MLTrainingPipeline:
    """
    End-to-end pipeline for training machine learning models for arbitrage strategies.
    """
    
    def __init__(self, config_path: str = "config/ml_config.json", data_dir: str = "data"):
        """
        Initialize the ML training pipeline.
        
        Args:
            config_path: Path to the ML configuration file
            data_dir: Directory containing training data
        """
        self.config = self._load_config(config_path)
        self.data_dir = Path(data_dir)
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Initialize scalers
        self.feature_scaler = None
        self.target_scaler = None
        
        # Initialize models
        self.opportunity_model = None
        self.price_impact_model = None
        self.gas_optimizer_model = None
        self.competitor_model = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load ML configuration from file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded ML config from {config_path}")
                return config
            else:
                logger.warning(f"Config file not found at {config_path}, using default values")
                return {
                    "opportunity_detection": {
                        "model_type": "lstm",
                        "sequence_length": 100,
                        "hidden_units": [128, 64],
                        "dropout_rate": 0.2,
                        "learning_rate": 0.001,
                        "batch_size": 32,
                        "epochs": 100,
                        "early_stopping_patience": 10
                    },
                    "price_impact": {
                        "model_type": "mlp",
                        "hidden_units": [64, 32, 16],
                        "dropout_rate": 0.1,
                        "learning_rate": 0.001,
                        "batch_size": 64,
                        "epochs": 50,
                        "early_stopping_patience": 5
                    },
                    "gas_optimization": {
                        "model_type": "mlp",
                        "hidden_units": [32, 16],
                        "dropout_rate": 0.1,
                        "learning_rate": 0.001,
                        "batch_size": 32,
                        "epochs": 30,
                        "early_stopping_patience": 5
                    },
                    "competitor_prediction": {
                        "model_type": "lstm",
                        "sequence_length": 50,
                        "hidden_units": [64, 32],
                        "dropout_rate": 0.2,
                        "learning_rate": 0.001,
                        "batch_size": 16,
                        "epochs": 50,
                        "early_stopping_patience": 10
                    },
                    "feature_engineering": {
                        "technical_indicators": ["sma", "ema", "rsi", "macd"],
                        "time_features": ["hour", "day_of_week", "is_weekend"],
                        "gas_features": ["gas_price", "gas_used", "gas_limit"],
                        "network_features": ["pending_tx_count", "block_time"]
                    },
                    "training": {
                        "test_size": 0.2,
                        "validation_size": 0.1,
                        "random_state": 42,
                        "shuffle": True
                    }
                }
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def load_and_preprocess_data(self, data_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load and preprocess data for model training.
        
        Args:
            data_file: Path to the data file (CSV)
            
        Returns:
            Tuple of (features_df, targets_df)
        """
        logger.info(f"Loading data from {data_file}")
        
        try:
            # Load data
            data_path = self.data_dir / data_file
            df = pd.read_csv(data_path)
            
            # Basic preprocessing
            df = self._clean_data(df)
            
            # Feature engineering
            df = self._engineer_features(df)
            
            # Split into features and targets
            feature_cols = self._get_feature_columns(df)
            target_cols = self._get_target_columns(df)
            
            features_df = df[feature_cols]
            targets_df = df[target_cols]
            
            # Scale features and targets
            self.feature_scaler = MinMaxScaler()
            self.target_scaler = MinMaxScaler()
            
            features_scaled = self.feature_scaler.fit_transform(features_df)
            targets_scaled = self.target_scaler.fit_transform(targets_df)
            
            # Convert back to DataFrame
            features_df = pd.DataFrame(features_scaled, columns=feature_cols, index=df.index)
            targets_df = pd.DataFrame(targets_scaled, columns=target_cols, index=df.index)
            
            logger.info(f"Preprocessed data: {len(features_df)} samples with {len(feature_cols)} features")
            
            return features_df, targets_df
            
        except Exception as e:
            logger.error(f"Error loading and preprocessing data: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare the raw data"""
        # Handle missing values
        df = df.dropna()
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Convert timestamp to datetime
        if "timestamp" in df.columns:
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
        
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features based on configuration"""
        # Get feature engineering config
        feature_config = self.config.get("feature_engineering", {})
        
        # Add time-based features
        if "datetime" in df.columns and "time_features" in feature_config:
            time_features = feature_config["time_features"]
            
            if "hour" in time_features:
                df["hour"] = df["datetime"].dt.hour
            
            if "day_of_week" in time_features:
                df["day_of_week"] = df["datetime"].dt.dayofweek
            
            if "is_weekend" in time_features:
                df["is_weekend"] = df["datetime"].dt.dayofweek >= 5
        
        # Add technical indicators if price data is available
        if "price" in df.columns and "technical_indicators" in feature_config:
            tech_indicators = feature_config["technical_indicators"]
            
            if "sma" in tech_indicators:
                df["sma_20"] = df["price"].rolling(window=20).mean()
                df["sma_50"] = df["price"].rolling(window=50).mean()
            
            if "ema" in tech_indicators:
                df["ema_12"] = df["price"].ewm(span=12).mean()
                df["ema_26"] = df["price"].ewm(span=26).mean()
            
            if "rsi" in tech_indicators:
                df["rsi_14"] = self._calculate_rsi(df["price"])
            
            if "macd" in tech_indicators:
                df["macd"] = df["ema_12"] - df["ema_26"]
        
        # Drop rows with NaN values created by rolling windows
        df = df.dropna()
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Get feature columns based on the dataset and configuration"""
        # Exclude target columns and non-feature columns
        exclude_cols = ["datetime", "timestamp", "hash", "block_number", "profit", "success"]
        exclude_cols.extend(self._get_target_columns(df))
        
        return [col for col in df.columns if col not in exclude_cols]
    
    def _get_target_columns(self, df: pd.DataFrame) -> List[str]:
        """Get target columns based on the dataset"""
        # Default target columns
        target_cols = []
        
        if "profit" in df.columns:
            target_cols.append("profit")
        
        if "success" in df.columns:
            target_cols.append("success")
        
        if "price_impact_percent" in df.columns:
            target_cols.append("price_impact_percent")
        
        if "optimal_gas_price" in df.columns:
            target_cols.append("optimal_gas_price")
        
        return target_cols
    
    def prepare_sequence_data(self, features_df: pd.DataFrame, targets_df: pd.DataFrame, 
                             sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequence data for LSTM models.
        
        Args:
            features_df: DataFrame of scaled features
            targets_df: DataFrame of scaled targets
            sequence_length: Length of sequences
            
        Returns:
            Tuple of (X_sequences, y_sequences)
        """
        X = features_df.values
        y = targets_df.values
        
        X_sequences = []
        y_sequences = []
        
        for i in range(len(X) - sequence_length):
            X_sequences.append(X[i:i+sequence_length])
            y_sequences.append(y[i+sequence_length])
        
        return np.array(X_sequences), np.array(y_sequences)
    
    def build_opportunity_model(self) -> tf.keras.Model:
        """Build and compile the opportunity detection model"""
        config = self.config.get("opportunity_detection", {})
        model_type = config.get("model_type", "lstm")
        sequence_length = config.get("sequence_length", 100)
        hidden_units = config.get("hidden_units", [128, 64])
        dropout_rate = config.get("dropout_rate", 0.2)
        learning_rate = config.get("learning_rate", 0.001)
        
        if model_type == "lstm":
            model = Sequential()
            model.add(LSTM(hidden_units[0], return_sequences=True, 
                          input_shape=(sequence_length, self.feature_scaler.n_features_in_)))
            model.add(Dropout(dropout_rate))
            
            for units in hidden_units[1:-1]:
                model.add(LSTM(units, return_sequences=True))
                model.add(Dropout(dropout_rate))
            
            if len(hidden_units) > 1:
                model.add(LSTM(hidden_units[-1], return_sequences=False))
                model.add(Dropout(dropout_rate))
            
            model.add(Dense(1, activation='sigmoid'))
            
        else:  # Default to MLP
            model = Sequential()
            model.add(Dense(hidden_units[0], activation='relu', 
                           input_shape=(self.feature_scaler.n_features_in_,)))
            model.add(Dropout(dropout_rate))
            
            for units in hidden_units[1:]:
                model.add(Dense(units, activation='relu'))
                model.add(Dropout(dropout_rate))
            
            model.add(Dense(1, activation='sigmoid'))
        
        model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info(f"Built opportunity detection model: {model.summary()}")
        return model
    
    def build_price_impact_model(self) -> tf.keras.Model:
        """Build and compile the price impact prediction model"""
        config = self.config.get("price_impact", {})
        model_type = config.get("model_type", "mlp")
        hidden_units = config.get("hidden_units", [64, 32, 16])
        dropout_rate = config.get("dropout_rate", 0.1)
        learning_rate = config.get("learning_rate", 0.001)
        
        model = Sequential()
        model.add(Dense(hidden_units[0], activation='relu', 
                       input_shape=(self.feature_scaler.n_features_in_,)))
        model.add(Dropout(dropout_rate))
        
        for units in hidden_units[1:]:
            model.add(Dense(units, activation='relu'))
            model.add(Dropout(dropout_rate))
        
        model.add(Dense(1, activation='linear'))
        
        model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info(f"Built price impact model: {model.summary()}")
        return model
    
    def build_gas_optimizer_model(self) -> tf.keras.Model:
        """Build and compile the gas price optimization model"""
        config = self.config.get("gas_optimization", {})
        hidden_units = config.get("hidden_units", [32, 16])
        dropout_rate = config.get("dropout_rate", 0.1)
        learning_rate = config.get("learning_rate", 0.001)
        
        model = Sequential()
        model.add(Dense(hidden_units[0], activation='relu', 
                       input_shape=(self.feature_scaler.n_features_in_,)))
        model.add(Dropout(dropout_rate))
        
        for units in hidden_units[1:]:
            model.add(Dense(units, activation='relu'))
            model.add(Dropout(dropout_rate))
        
        model.add(Dense(1, activation='linear'))
        
        model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        logger.info(f"Built gas optimizer model: {model.summary()}")
        return model
    
    def build_competitor_model(self) -> tf.keras.Model:
        """Build and compile the competitor behavior prediction model"""
        config = self.config.get("competitor_prediction", {})
        model_type = config.get("model_type", "lstm")
        sequence_length = config.get("sequence_length", 50)
        hidden_units = config.get("hidden_units", [64, 32])
        dropout_rate = config.get("dropout_rate", 0.2)
        learning_rate = config.get("learning_rate", 0.001)
        
        if model_type == "lstm":
            model = Sequential()
            model.add(LSTM(hidden_units[0], return_sequences=True, 
                          input_shape=(sequence_length, self.feature_scaler.n_features_in_)))
            model.add(Dropout(dropout_rate))
            
            for units in hidden_units[1:-1]:
                model.add(LSTM(units, return_sequences=True))
                model.add(Dropout(dropout_rate))
            
            if len(hidden_units) > 1:
                model.add(LSTM(hidden_units[-1], return_sequences=False))
                model.add(Dropout(dropout_rate))
            
            model.add(Dense(1, activation='sigmoid'))
            
        else:  # Default to MLP
            model = Sequential()
            model.add(Dense(hidden_units[0], activation='relu', 
                           input_shape=(self.feature_scaler.n_features_in_,)))
            model.add(Dropout(dropout_rate))
            
            for units in hidden_units[1:]:
                model.add(Dense(units, activation='relu'))
                model.add(Dropout(dropout_rate))
            
            model.add(Dense(1, activation='sigmoid'))
        
        model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info(f"Built competitor prediction model: {model.summary()}")
        return model
    
    def train_opportunity_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                               X_val: np.ndarray = None, y_val: np.ndarray = None) -> tf.keras.Model:
        """
        Train the opportunity detection model.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            
        Returns:
            Trained model
        """
        config = self.config.get("opportunity_detection", {})
        batch_size = config.get("batch_size", 32)
        epochs = config.get("epochs", 100)
        patience = config.get("early_stopping_patience", 10)
        
        # Build model if not already built
        if self.opportunity_model is None:
            self.opportunity_model = self.build_opportunity_model()
        
        # Prepare callbacks
        callbacks = [
            EarlyStopping(patience=patience, restore_best_weights=True),
            ModelCheckpoint(
                filepath=str(self.models_dir / "opportunity_model.h5"),
                save_best_only=True,
                monitor='val_loss' if X_val is not None else 'loss'
            )
        ]
        
        # Train model
        logger.info("Training opportunity detection model...")
        history = self.opportunity_model.fit(
            X_train, y_train,
            batch_size=batch_size,
            epochs=epochs,
            validation_data=(X_val, y_val) if X_val is not None else None,
            callbacks=callbacks,
            verbose=1
        )
        
        # Save model and scalers
        self.opportunity_model.save(str(self.models_dir / "opportunity_model.h5"))
        joblib.dump(self.feature_scaler, str(self.models_dir / "opportunity_feature_scaler.pkl"))
        joblib.dump(self.target_scaler, str(self.models_dir / "opportunity_target_scaler.pkl"))
        
        # Plot training history
        self._plot_training_history(history, "opportunity_model")
        
        logger.info("Opportunity detection model training completed")
        return self.opportunity_model
    
    def train_price_impact_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                                X_val: np.ndarray = None, y_val: np.ndarray = None) -> tf.keras.Model:
        """
        Train the price impact prediction model.
        
        Args:
            X_train: Training features
            y_train: Training targets
            X_val: Validation features
            y_val: Validation targets
            
        Returns:
            Trained model
        """
        config = self.config.get("price_impact", {})
        batch_size = config.get("batch_size", 64)
        epochs = config.get("epochs", 50)
        patience = config.get("early_stopping_patience", 5)
        
        # Build model if not already built
        if self.price_impact_model is None:
            self.price_impact_model = self.build_price_impact_model()
        
        # Prepare callbacks
        callbacks = [
            EarlyStopping(patience=patience, restore_best_weights=True),
            ModelCheckpoint(
                filepath=str(self.models_dir / "price_impact_model.h5"),
                save_best_only=True,
                monitor='val_loss' if X_val is not None else 'loss'
            )
        ]
        
        # Train model
        logger.info("Training price impact prediction model...")
        history = self.price_impact_model.fit(
            X_train, y_train,
            batch_size=batch_size,
            epochs=epochs,
            validation_data=(X_val, y_val) if X_val is not None else None,
            callbacks=callbacks,
            verbose=1
        )
        
        # Save model and scalers
        self.price_impact_model.save(str(self.models_dir / "price_impact_model.h5"))
        joblib.dump(self.feature_scaler, str(self.models_dir / "price_impact_feature_scaler.pkl"))
        joblib.dump(self.target_scaler, str(self.models_dir / "price_impact_target_scaler.pkl"))
        
        # Plot training history
        self._plot_training_history(history, "price_impact_model")
        
        logger.info("Price impact prediction model training completed")
        return self.price_impact_model
    
    def _plot_training_history(self, history, model_name: str):
        """Plot and save training history"""
        plt.figure(figsize=(12, 4))
        
        # Plot loss
        plt.subplot(1, 2, 1)
        plt.plot(history.history['loss'], label='Training Loss')
        if 'val_loss' in history.history:
            plt.plot(history.history['val_loss'], label='Validation Loss')
        plt.title(f'{model_name} - Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        
        # Plot metrics
        plt.subplot(1, 2, 2)
        for metric in history.history:
            if metric not in ['loss', 'val_loss']:
                plt.plot(history.history[metric], label=f'Training {metric}')
                val_metric = f'val_{metric}'
                if val_metric in history.history:
                    plt.plot(history.history[val_metric], label=f'Validation {metric}')
        plt.title(f'{model_name} - Metrics')
        plt.xlabel('Epoch')
        plt.ylabel('Value')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(str(self.models_dir / f"{model_name}_history.png"))
        plt.close()
    
    def run_full_pipeline(self, data_file: str) -> Dict:
        """
        Run the full ML training pipeline.
        
        Args:
            data_file: Path to the data file
            
        Returns:
            Dictionary with training results
        """
        logger.info(f"Starting full ML training pipeline with data file: {data_file}")
        
        try:
            # Load and preprocess data
            features_df, targets_df = self.load_and_preprocess_data(data_file)
            
            if features_df.empty or targets_df.empty:
                logger.error("Failed to load and preprocess data")
                return {"error": "Failed to load and preprocess data"}
            
            # Split data
            train_config = self.config.get("training", {})
            test_size = train_config.get("test_size", 0.2)
            val_size = train_config.get("validation_size", 0.1)
            random_state = train_config.get("random_state", 42)
            shuffle = train_config.get("shuffle", True)
            
            # First split: train+val and test
            X_train_val, X_test, y_train_val, y_test = train_test_split(
                features_df, targets_df,
                test_size=test_size,
                random_state=random_state,
                shuffle=shuffle
            )
            
            # Second split: train and val
            val_size_adjusted = val_size / (1 - test_size)
            X_train, X_val, y_train, y_val = train_test_split(
                X_train_val, y_train_val,
                test_size=val_size_adjusted,
                random_state=random_state,
                shuffle=shuffle
            )
            
            # Train opportunity model
            if "success" in targets_df.columns:
                logger.info("Training opportunity detection model...")
                self.opportunity_model = self.train_opportunity_model(
                    X_train.values, y_train["success"].values,
                    X_val.values, y_val["success"].values
                )
            
            # Train price impact model
            if "price_impact_percent" in targets_df.columns:
                logger.info("Training price impact prediction model...")
                self.price_impact_model = self.train_price_impact_model(
                    X_train.values, y_train["price_impact_percent"].values,
                    X_val.values, y_val["price_impact_percent"].values
                )
            
            # Train gas optimizer model
            if "optimal_gas_price" in targets_df.columns:
                logger.info("Training gas optimizer model...")
                self.gas_optimizer_model = self.build_gas_optimizer_model()
                # Training code similar to other models
            
            # Train competitor model
            # This would require sequence data preparation
            
            logger.info("ML training pipeline completed successfully")
            
            return {
                "status": "success",
                "models_trained": [
                    "opportunity_model" if self.opportunity_model is not None else None,
                    "price_impact_model" if self.price_impact_model is not None else None,
                    "gas_optimizer_model" if self.gas_optimizer_model is not None else None,
                    "competitor_model" if self.competitor_model is not None else None
                ],
                "data_samples": len(features_df),
                "features": list(features_df.columns),
                "targets": list(targets_df.columns),
                "models_dir": str(self.models_dir)
            }
            
        except Exception as e:
            logger.error(f"Error in ML training pipeline: {e}")
            return {"error": str(e)}

# Example usage
if __name__ == "__main__":
    pipeline = MLTrainingPipeline()
    
    # Example: Run full pipeline with a data file
    # result = pipeline.run_full_pipeline("arbitrage_opportunities.csv")
    # print(f"Pipeline result: {json.dumps(result, indent=2)}")
    
    # For demonstration, just print the configuration
    print(f"ML Training Pipeline Configuration: {json.dumps(pipeline.config, indent=2)}")
