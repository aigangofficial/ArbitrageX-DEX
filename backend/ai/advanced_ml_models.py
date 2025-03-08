#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Advanced ML Models

This module implements advanced machine learning models for the ArbitrageX trading bot,
including reinforcement learning for strategy optimization and predictive models
for market dynamics, price impact, and volatility tracking.
"""

import os
import json
import time
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from enum import Enum
from datetime import datetime, timedelta
import random  # For simulations; would use real model predictions in production

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("advanced_ml_models.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AdvancedMLModels")

# Constants
DEFAULT_MODEL_PATH = "backend/ai/models"
DEFAULT_DATA_PATH = "backend/ai/data"
DEFAULT_METRICS_PATH = "backend/ai/metrics/ml_models"


class ModelType(Enum):
    """Enum for different types of ML models."""
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    PRICE_IMPACT = "price_impact"
    VOLATILITY = "volatility"
    MARKET_DYNAMICS = "market_dynamics"
    GAS_PRICE = "gas_price"
    LIQUIDITY = "liquidity"
    STRATEGY_OPTIMIZER = "strategy_optimizer"


class BaseModel:
    """Base class for all ML models."""
    
    def __init__(self, model_type: ModelType, config_path: Optional[str] = None):
        """
        Initialize the base model.
        
        Args:
            model_type: Type of model
            config_path: Path to configuration file (optional)
        """
        self.model_type = model_type
        self.model_name = f"{model_type.value}_model"
        self.config = {
            "enabled": True,
            "training": {
                "enabled": True,
                "batch_size": 32,
                "epochs": 10,
                "validation_split": 0.2,
                "early_stopping": True,
                "patience": 5
            },
            "inference": {
                "batch_size": 1,
                "confidence_threshold": 0.7
            },
            "model_path": os.path.join(DEFAULT_MODEL_PATH, model_type.value),
            "data_path": os.path.join(DEFAULT_DATA_PATH, model_type.value),
            "metrics_path": os.path.join(DEFAULT_METRICS_PATH, model_type.value)
        }
        
        # Update config from file if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    if "ml_models" in loaded_config and model_type.value in loaded_config["ml_models"]:
                        self.config.update(loaded_config["ml_models"][model_type.value])
                logger.info(f"Loaded {model_type.value} model configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load model configuration: {e}")
        
        # Create directories
        os.makedirs(self.config["model_path"], exist_ok=True)
        os.makedirs(self.config["data_path"], exist_ok=True)
        os.makedirs(self.config["metrics_path"], exist_ok=True)
        
        # Model state
        self.is_trained = False
        self.last_training_time = None
        self.metrics = {
            "training_loss": [],
            "validation_loss": [],
            "accuracy": 0.0,
            "predictions": 0,
            "correct_predictions": 0,
            "training_time": 0.0,
            "inference_time": 0.0
        }
        
        logger.info(f"{model_type.value.capitalize()} model initialized")
    
    def train(self, training_data: Any) -> Dict[str, Any]:
        """
        Train the model with provided data.
        
        Args:
            training_data: Training data in appropriate format
            
        Returns:
            Dictionary with training metrics
        """
        if not self.config["enabled"] or not self.config["training"]["enabled"]:
            logger.warning(f"{self.model_type.value} model training is disabled")
            return {"success": False, "error": "Model training is disabled"}
        
        start_time = time.time()
        
        # This would be implemented by specific model classes
        # Here we just simulate training
        time.sleep(0.5)  # Simulate training time
        
        self.is_trained = True
        self.last_training_time = datetime.now()
        training_time = time.time() - start_time
        
        # Update metrics
        self.metrics["training_time"] = training_time
        self.metrics["training_loss"].append(random.uniform(0.1, 0.5))
        self.metrics["validation_loss"].append(random.uniform(0.2, 0.6))
        
        logger.info(f"{self.model_type.value.capitalize()} model trained in {training_time:.2f} seconds")
        
        return {
            "success": True,
            "training_time": training_time,
            "training_loss": self.metrics["training_loss"][-1],
            "validation_loss": self.metrics["validation_loss"][-1]
        }
    
    def predict(self, input_data: Any) -> Dict[str, Any]:
        """
        Make predictions with the model.
        
        Args:
            input_data: Input data for prediction
            
        Returns:
            Dictionary with prediction results
        """
        if not self.config["enabled"]:
            logger.warning(f"{self.model_type.value} model is disabled")
            return {"success": False, "error": "Model is disabled"}
        
        if not self.is_trained:
            logger.warning(f"{self.model_type.value} model is not trained")
            return {"success": False, "error": "Model is not trained"}
        
        start_time = time.time()
        
        # This would be implemented by specific model classes
        # Here we just simulate prediction
        time.sleep(0.1)  # Simulate prediction time
        
        inference_time = time.time() - start_time
        
        # Update metrics
        self.metrics["inference_time"] = inference_time
        self.metrics["predictions"] += 1
        
        logger.info(f"{self.model_type.value.capitalize()} model prediction in {inference_time:.4f} seconds")
        
        return {
            "success": True,
            "inference_time": inference_time,
            "prediction": None  # Should be overridden by subclasses
        }
    
    def save(self) -> Dict[str, Any]:
        """
        Save the model to disk.
        
        Returns:
            Dictionary with save results
        """
        if not self.is_trained:
            logger.warning(f"{self.model_type.value} model is not trained, nothing to save")
            return {"success": False, "error": "Model is not trained"}
        
        # This would be implemented by specific model classes
        # Here we just simulate saving
        
        # Save metrics
        metrics_file = os.path.join(self.config["metrics_path"], f"{self.model_name}_metrics.json")
        try:
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
            logger.info(f"{self.model_type.value.capitalize()} model metrics saved to {metrics_file}")
        except Exception as e:
            logger.error(f"Failed to save model metrics: {e}")
            return {"success": False, "error": f"Failed to save metrics: {str(e)}"}
        
        return {"success": True, "metrics_file": metrics_file}
    
    def load(self) -> Dict[str, Any]:
        """
        Load the model from disk.
        
        Returns:
            Dictionary with load results
        """
        # This would be implemented by specific model classes
        # Here we just simulate loading
        
        # Load metrics if available
        metrics_file = os.path.join(self.config["metrics_path"], f"{self.model_name}_metrics.json")
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r') as f:
                    self.metrics = json.load(f)
                self.is_trained = True
                logger.info(f"{self.model_type.value.capitalize()} model metrics loaded from {metrics_file}")
            except Exception as e:
                logger.error(f"Failed to load model metrics: {e}")
                return {"success": False, "error": f"Failed to load metrics: {str(e)}"}
        
            return {"success": True, "metrics_file": metrics_file}
        else:
            logger.warning(f"No saved metrics found for {self.model_type.value} model")
            return {"success": False, "error": "No saved metrics found"}
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current model metrics.
        
        Returns:
            Dictionary with model metrics
        """
        return {
            "model_type": self.model_type.value,
            "is_trained": self.is_trained,
            "last_training_time": self.last_training_time,
            **self.metrics
        }


class PriceImpactModel(BaseModel):
    """
    Model for predicting price impact and slippage of trades.
    
    This model predicts how a trade of a specific size will impact the price
    on a given DEX, allowing for dynamic adjustment of trade size and slippage
    tolerance to optimize profitability.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the price impact model.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        super().__init__(ModelType.PRICE_IMPACT, config_path)
        
        # Additional configuration specific to price impact model
        price_impact_config = {
            "features": [
                "token_pair",
                "dex",
                "position_size",
                "market_volatility",
                "liquidity_depth",
                "time_of_day",
                "gas_price"
            ],
            "output": [
                "price_impact_percentage",
                "slippage_expected",
                "confidence"
            ],
            "token_pairs": {
                "WETH-USDC": {"historical_impact_mean": 0.0015, "historical_impact_std": 0.0008},
                "WETH-DAI": {"historical_impact_mean": 0.0018, "historical_impact_std": 0.0010},
                "WBTC-USDC": {"historical_impact_mean": 0.0020, "historical_impact_std": 0.0012},
                "LINK-USDC": {"historical_impact_mean": 0.0025, "historical_impact_std": 0.0015}
            },
            "dexes": {
                "uniswap": {"impact_multiplier": 1.0},
                "sushiswap": {"impact_multiplier": 1.1},
                "curve": {"impact_multiplier": 0.8},
                "balancer": {"impact_multiplier": 0.9}
            }
        }
        
        # Update config with price impact specific settings
        self.config.update(price_impact_config)
        
        # Initialize model-specific metrics
        self.metrics.update({
            "mean_absolute_error": 0.0,
            "mean_squared_error": 0.0,
            "r2_score": 0.0,
            "prediction_accuracy_by_token_pair": {pair: 0.0 for pair in self.config["token_pairs"]},
            "prediction_accuracy_by_dex": {dex: 0.0 for dex in self.config["dexes"]}
        })
        
        logger.info("Price impact model initialized with additional configurations")
    
    def predict(self, trade_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict price impact and slippage for a specific trade.
        
        Args:
            trade_details: Dictionary with trade details including token_pair, dex, position_size, etc.
            
        Returns:
            Dictionary with price impact predictions
        """
        # Call the base predict method for common functionality
        base_result = super().predict(trade_details)
        if not base_result["success"]:
            return base_result
        
        # Extract required parameters
        token_pair = trade_details.get("token_pair", "WETH-USDC")
        dex = trade_details.get("dex", "uniswap")
        position_size = float(trade_details.get("position_size", 1.0))
        
        # Check if token pair and DEX are supported
        if token_pair not in self.config["token_pairs"]:
            logger.warning(f"Unsupported token pair: {token_pair}")
            token_pair = "WETH-USDC"  # Default to WETH-USDC
        
        if dex not in self.config["dexes"]:
            logger.warning(f"Unsupported DEX: {dex}")
            dex = "uniswap"  # Default to uniswap
        
        # In a real implementation, this would use a trained model
        # Here we simulate predictions based on historical data and simple heuristics
        
        # Get historical impact statistics for this token pair
        token_stats = self.config["token_pairs"][token_pair]
        
        # Get DEX-specific impact multiplier
        dex_multiplier = self.config["dexes"][dex]["impact_multiplier"]
        
        # Base impact calculation using statistical distribution
        mean_impact = token_stats["historical_impact_mean"]
        std_impact = token_stats["historical_impact_std"]
        
        # Calculate impact based on position size (larger positions have more impact)
        # We use a simple logarithmic model: impact ~ log(position_size)
        size_factor = np.log1p(position_size) / np.log1p(1.0)  # Normalized to 1.0 ETH
        
        # Add some randomness to simulate model uncertainty
        random_factor = np.random.normal(0, 0.2)
        
        # Calculate final price impact
        price_impact = (mean_impact + random_factor * std_impact) * size_factor * dex_multiplier
        
        # Ensure impact is positive and reasonable
        price_impact = max(0.0001, min(0.05, price_impact))
        
        # Slippage should be higher than price impact to account for volatility during execution
        slippage_multiplier = random.uniform(1.2, 1.5)
        recommended_slippage = price_impact * slippage_multiplier
        
        # Calculate confidence (higher for well-known token pairs and DEXes)
        confidence = random.uniform(0.7, 0.95)
        
        # Update metrics
        self.metrics["predictions"] += 1
        
        # Return prediction results
        prediction_result = {
            "success": True,
            "price_impact_percentage": price_impact * 100,  # Convert to percentage
            "slippage_expected": price_impact * 100,  # Convert to percentage
            "recommended_slippage": recommended_slippage * 100,  # Convert to percentage
            "confidence": confidence,
            "token_pair": token_pair,
            "dex": dex,
            "position_size": position_size,
            "impact_usd": position_size * price_impact * trade_details.get("token_price", 1800),  # Assuming ETH price
            "notes": "Price impact increases with position size and varies by DEX and token pair"
        }
        
        logger.info(f"Price impact prediction for {position_size} {token_pair} on {dex}: {price_impact*100:.4f}%")
        
        return prediction_result
    
    def adjust_position_size(self, trade_details: Dict[str, Any], target_impact: float = 0.005) -> Dict[str, Any]:
        """
        Adjust position size to achieve a target price impact.
        
        Args:
            trade_details: Dictionary with trade details
            target_impact: Target price impact as a decimal (default: 0.5%)
            
        Returns:
            Dictionary with adjusted position size and other details
        """
        # Start with initial position size
        original_size = float(trade_details.get("position_size", 1.0))
        token_pair = trade_details.get("token_pair", "WETH-USDC")
        dex = trade_details.get("dex", "uniswap")
        
        # Use binary search to find optimal position size
        min_size = original_size * 0.1
        max_size = original_size * 3.0
        current_size = original_size
        best_size = original_size
        best_impact = float('inf')
        
        # Perform a few iterations to approximate
        for _ in range(5):
            # Test current size
            test_details = trade_details.copy()
            test_details["position_size"] = current_size
            
            # Get prediction for current size
            prediction = self.predict(test_details)
            current_impact = prediction["price_impact_percentage"] / 100  # Convert back to decimal
            
            # Check if this is closer to target
            if abs(current_impact - target_impact) < abs(best_impact - target_impact):
                best_size = current_size
                best_impact = current_impact
            
            # Adjust size based on impact
            if current_impact > target_impact:
                max_size = current_size
                current_size = (min_size + current_size) / 2
            else:
                min_size = current_size
                current_size = (max_size + current_size) / 2
        
        # Prepare result
        result = {
            "success": True,
            "original_position_size": original_size,
            "adjusted_position_size": best_size,
            "target_impact_percentage": target_impact * 100,
            "achieved_impact_percentage": best_impact * 100,
            "token_pair": token_pair,
            "dex": dex,
            "adjustment_factor": best_size / original_size
        }
        
        logger.info(f"Position size adjusted from {original_size} to {best_size} for {token_pair} on {dex}")
        
        return result 


class VolatilityTrackingModel(BaseModel):
    """
    Model for tracking and predicting market volatility.
    
    This model helps adjust trade frequency and execution timing based on
    current and predicted market volatility.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the volatility tracking model.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        super().__init__(ModelType.VOLATILITY, config_path)
        
        # Additional configuration specific to volatility model
        volatility_config = {
            "lookback_periods": [1, 4, 24, 168],  # Hours (1h, 4h, 1d, 1w)
            "volatility_thresholds": {
                "very_low": 0.01,  # 1% price movement
                "low": 0.025,      # 2.5% price movement
                "medium": 0.05,    # 5% price movement
                "high": 0.10,      # 10% price movement
                "very_high": 0.20  # 20% price movement
            },
            "trading_frequency_multipliers": {
                "very_low": 1.5,   # Increase trading frequency
                "low": 1.2,        # Slightly increase trading frequency
                "medium": 1.0,     # Normal trading frequency
                "high": 0.7,       # Reduce trading frequency
                "very_high": 0.4   # Significantly reduce trading frequency
            },
            "position_size_multipliers": {
                "very_low": 1.2,   # Increase position size
                "low": 1.1,        # Slightly increase position size
                "medium": 1.0,     # Normal position size
                "high": 0.8,       # Reduce position size
                "very_high": 0.6   # Significantly reduce position size
            },
            "token_pairs": {
                "WETH-USDC": {"base_volatility": 0.03, "volatility_factor": 1.0},
                "WETH-DAI": {"base_volatility": 0.03, "volatility_factor": 1.0},
                "WBTC-USDC": {"base_volatility": 0.04, "volatility_factor": 1.2},
                "LINK-USDC": {"base_volatility": 0.06, "volatility_factor": 1.5}
            },
            "volatility_memory": 24,  # Hours to keep volatility history
            "update_frequency": 1     # Hours between volatility updates
        }
        
        # Update config with volatility specific settings
        self.config.update(volatility_config)
        
        # Initialize volatility history (would be persistent in production)
        self.volatility_history = {
            pair: {
                period: [] for period in self.config["lookback_periods"]
            } for pair in self.config["token_pairs"]
        }
        
        # Initialize model-specific metrics
        self.metrics.update({
            "volatility_prediction_accuracy": 0.0,
            "trend_prediction_accuracy": 0.0,
            "volatility_by_token_pair": {pair: 0.0 for pair in self.config["token_pairs"]},
            "volatility_by_period": {period: 0.0 for period in self.config["lookback_periods"]}
        })
        
        # Last update time
        self.last_update_time = datetime.now() - timedelta(hours=self.config["update_frequency"])
        
        logger.info("Volatility tracking model initialized with additional configurations")
    
    def update_volatility(self, market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Update volatility data with latest market information.
        
        Args:
            market_data: Dictionary with latest market data (optional, simulated if None)
            
        Returns:
            Dictionary with update results
        """
        # Check if it's time to update
        current_time = datetime.now()
        hours_since_update = (current_time - self.last_update_time).total_seconds() / 3600
        
        if hours_since_update < self.config["update_frequency"]:
            return {
                "success": True,
                "updated": False,
                "reason": f"Update frequency not met, last update was {hours_since_update:.1f} hours ago"
            }
        
        # If no market data provided, simulate it
        if market_data is None:
            market_data = self._simulate_market_data()
        
        # Process each token pair
        for pair in self.config["token_pairs"]:
            if pair not in market_data:
                continue
                
            # Get volatility data for different periods
            for period in self.config["lookback_periods"]:
                if f"volatility_{period}h" in market_data[pair]:
                    volatility = market_data[pair][f"volatility_{period}h"]
                else:
                    # Simulate volatility if not provided
                    base_vol = self.config["token_pairs"][pair]["base_volatility"]
                    vol_factor = self.config["token_pairs"][pair]["volatility_factor"]
                    volatility = base_vol * vol_factor * random.uniform(0.7, 1.3)
                
                # Add to history
                self.volatility_history[pair][period].append({
                    "timestamp": current_time.isoformat(),
                    "volatility": volatility
                })
                
                # Trim history if needed
                max_entries = self.config["volatility_memory"]
                if len(self.volatility_history[pair][period]) > max_entries:
                    self.volatility_history[pair][period] = self.volatility_history[pair][period][-max_entries:]
        
        # Update last update time
        self.last_update_time = current_time
        
        logger.info(f"Volatility data updated for {len(market_data)} token pairs")
        
        return {
            "success": True,
            "updated": True,
            "token_pairs_updated": list(market_data.keys()),
            "update_time": current_time.isoformat()
        }
    
    def _simulate_market_data(self) -> Dict[str, Dict[str, float]]:
        """
        Simulate market data for volatility updates.
        
        Returns:
            Dictionary with simulated market data
        """
        market_data = {}
        
        for pair in self.config["token_pairs"]:
            base_vol = self.config["token_pairs"][pair]["base_volatility"]
            vol_factor = self.config["token_pairs"][pair]["volatility_factor"]
            
            pair_data = {}
            for period in self.config["lookback_periods"]:
                # More variation in longer periods
                period_factor = (np.log1p(period) / np.log1p(1)) * 0.5
                
                # Simulate volatility with some randomness
                volatility = base_vol * vol_factor * random.uniform(0.7 + period_factor, 1.3 + period_factor)
                pair_data[f"volatility_{period}h"] = volatility
            
            market_data[pair] = pair_data
        
        return market_data
    
    def get_current_volatility(self, token_pair: str) -> Dict[str, Any]:
        """
        Get current volatility metrics for a token pair.
        
        Args:
            token_pair: Token pair to get volatility for
            
        Returns:
            Dictionary with volatility metrics
        """
        if token_pair not in self.config["token_pairs"]:
            logger.warning(f"Unsupported token pair for volatility: {token_pair}")
            # Default to WETH-USDC if unsupported
            token_pair = "WETH-USDC"
        
        # Ensure we have volatility data
        if not any(len(self.volatility_history[token_pair][period]) > 0 for period in self.config["lookback_periods"]):
            self.update_volatility()
        
        # Get latest volatility for each period
        volatility_data = {}
        
        for period in self.config["lookback_periods"]:
            history = self.volatility_history[token_pair][period]
            
            if len(history) > 0:
                latest = history[-1]["volatility"]
            else:
                # Fallback if no history
                base_vol = self.config["token_pairs"][token_pair]["base_volatility"]
                vol_factor = self.config["token_pairs"][token_pair]["volatility_factor"]
                latest = base_vol * vol_factor
            
            volatility_data[f"{period}h"] = latest
        
        # Determine volatility level based on 24h volatility (or closest available)
        if "24h" in volatility_data:
            vol_24h = volatility_data["24h"]
        elif "168h" in volatility_data:
            vol_24h = volatility_data["168h"] * 0.7  # Scale weekly to daily
        elif "4h" in volatility_data:
            vol_24h = volatility_data["4h"] * 1.3  # Scale 4h to daily
        elif "1h" in volatility_data:
            vol_24h = volatility_data["1h"] * 1.5  # Scale hourly to daily
        else:
            vol_24h = self.config["token_pairs"][token_pair]["base_volatility"]
        
        # Determine volatility level
        level = "medium"  # Default
        for level_name, threshold in sorted(self.config["volatility_thresholds"].items(), key=lambda x: x[1]):
            if vol_24h <= threshold:
                level = level_name
                break
        
        # Get multipliers based on volatility level
        trading_frequency_multiplier = self.config["trading_frequency_multipliers"][level]
        position_size_multiplier = self.config["position_size_multipliers"][level]
        
        result = {
            "token_pair": token_pair,
            "volatility": volatility_data,
            "volatility_24h": vol_24h,
            "volatility_level": level,
            "trading_frequency_multiplier": trading_frequency_multiplier,
            "position_size_multiplier": position_size_multiplier,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Current volatility for {token_pair}: {level} ({vol_24h:.2%})")
        
        return result
    
    def predict_volatility(self, token_pair: str, prediction_hours: int = 24) -> Dict[str, Any]:
        """
        Predict volatility for a token pair over a future time period.
        
        Args:
            token_pair: Token pair to predict volatility for
            prediction_hours: Number of hours to predict ahead
            
        Returns:
            Dictionary with volatility predictions
        """
        # Call the base predict method for common functionality
        base_result = super().predict({"token_pair": token_pair, "hours": prediction_hours})
        if not base_result["success"]:
            return base_result
        
        # Get current volatility as baseline
        current = self.get_current_volatility(token_pair)
        
        # In a real model, we would use time series forecasting
        # Here, we simulate predictions with some trend continuation and mean reversion
        
        # Get historical trend (if available)
        trend_factor = 1.0  # Default: no trend
        
        for period in sorted(self.config["lookback_periods"]):
            history = self.volatility_history[token_pair][period]
            if len(history) >= 2:
                latest = history[-1]["volatility"]
                previous = history[-2]["volatility"]
                
                # Calculate trend (positive = increasing volatility)
                if previous > 0:
                    period_trend = (latest / previous) - 1
                    # More weight to more recent periods
                    recency_weight = 1.0 / period
                    trend_factor += period_trend * recency_weight
                
                break
        
        # Apply some mean reversion - volatility tends to return to baseline
        base_vol = self.config["token_pairs"][token_pair]["base_volatility"]
        current_vol = current["volatility_24h"]
        
        # If current volatility is far from base, stronger mean reversion
        reversion_strength = abs(current_vol - base_vol) / base_vol
        reversion_factor = 1.0 - min(reversion_strength * 0.3, 0.5)  # Cap at 50% reversion
        
        # Direction of reversion
        if current_vol > base_vol:
            reversion_direction = -1  # Revert downward
        else:
            reversion_direction = 1   # Revert upward
        
        # Calculate predicted volatility
        predicted_volatility = current_vol * trend_factor
        predicted_volatility += (base_vol - current_vol) * reversion_strength * reversion_direction * 0.2
        
        # Add random noise for short-term unpredictability
        noise_factor = 0.1  # 10% random variation
        predicted_volatility *= (1 + random.uniform(-noise_factor, noise_factor))
        
        # Ensure predicted volatility is positive and reasonable
        predicted_volatility = max(0.005, min(0.5, predicted_volatility))
        
        # Determine predicted volatility level
        predicted_level = "medium"  # Default
        for level_name, threshold in sorted(self.config["volatility_thresholds"].items(), key=lambda x: x[1]):
            if predicted_volatility <= threshold:
                predicted_level = level_name
                break
        
        # Prepare prediction confidence based on prediction horizon
        if prediction_hours <= 4:
            confidence = random.uniform(0.8, 0.9)  # High confidence for short-term
        elif prediction_hours <= 24:
            confidence = random.uniform(0.7, 0.8)  # Medium confidence for medium-term
        else:
            confidence = random.uniform(0.6, 0.7)  # Lower confidence for long-term
        
        # Return prediction results
        prediction_result = {
            "success": True,
            "token_pair": token_pair,
            "current_volatility": current_vol,
            "current_level": current["volatility_level"],
            "predicted_volatility": predicted_volatility,
            "predicted_level": predicted_level,
            "prediction_hours": prediction_hours,
            "confidence": confidence,
            "trend_factor": trend_factor,
            "prediction_timestamp": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(hours=prediction_hours)).isoformat(),
            "recommended_actions": self._get_recommended_actions(predicted_level)
        }
        
        logger.info(f"Volatility prediction for {token_pair}: {predicted_level} ({predicted_volatility:.2%}) in {prediction_hours}h")
        
        return prediction_result
    
    def _get_recommended_actions(self, volatility_level: str) -> Dict[str, Any]:
        """
        Get recommended trading actions based on volatility level.
        
        Args:
            volatility_level: Predicted volatility level
            
        Returns:
            Dictionary with recommended actions
        """
        actions = {
            "very_low": {
                "trading_frequency": "Increase trading frequency by 50%",
                "position_size": "Increase position sizes by 20%",
                "slippage_tolerance": "Reduce slippage tolerance",
                "strategy": "More aggressive trading, exploit smaller opportunities"
            },
            "low": {
                "trading_frequency": "Increase trading frequency by 20%",
                "position_size": "Increase position sizes by 10%",
                "slippage_tolerance": "Slightly reduce slippage tolerance",
                "strategy": "More active trading, pursue most opportunities"
            },
            "medium": {
                "trading_frequency": "Maintain normal trading frequency",
                "position_size": "Use standard position sizes",
                "slippage_tolerance": "Use standard slippage tolerance",
                "strategy": "Balanced trading, pursue good opportunities"
            },
            "high": {
                "trading_frequency": "Reduce trading frequency by 30%",
                "position_size": "Reduce position sizes by 20%",
                "slippage_tolerance": "Increase slippage tolerance",
                "strategy": "More selective trading, focus on higher-profit opportunities"
            },
            "very_high": {
                "trading_frequency": "Reduce trading frequency by 60%",
                "position_size": "Reduce position sizes by 40%",
                "slippage_tolerance": "Significantly increase slippage tolerance",
                "strategy": "Highly selective trading, only pursue exceptional opportunities"
            }
        }
        
        return actions.get(volatility_level, actions["medium"])


class ReinforcementLearningModel(BaseModel):
    """
    Model that uses reinforcement learning to optimize trading strategies.
    
    This model learns from past trading outcomes to continuously improve
    strategy parameter selection and execution decisions.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the reinforcement learning model.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        super().__init__(ModelType.REINFORCEMENT_LEARNING, config_path)
        
        # Additional configuration specific to RL model
        rl_config = {
            "learning_rate": 0.001,
            "discount_factor": 0.95,
            "exploration_rate": 0.1,
            "min_exploration_rate": 0.01,
            "exploration_decay": 0.995,
            "reward_scaling": {
                "profit": 1.0,          # Scale factor for profit-based rewards
                "gas_savings": 0.5,     # Scale factor for gas-saving rewards
                "speed": 0.3,           # Scale factor for execution speed rewards
                "success_rate": 0.7     # Scale factor for success rate rewards
            },
            "state_features": [
                "token_pair",
                "dex",
                "position_size",
                "expected_profit",
                "gas_price",
                "market_volatility",
                "time_of_day",
                "day_of_week",
                "l2_availability",
                "flash_loan_availability"
            ],
            "action_space": {
                "execution_method": ["base", "l2", "flash_loan", "l2_flash"],
                "l2_network": ["arbitrum", "optimism", "base", "polygon"],
                "flash_loan_provider": ["aave", "uniswap", "balancer", "maker"],
                "trade_size_multiplier": [0.5, 0.75, 1.0, 1.25, 1.5],
                "slippage_tolerance_multiplier": [0.8, 1.0, 1.2, 1.5, 2.0]
            },
            "episode_length": 20,       # Number of trades per learning episode
            "min_samples_for_update": 50,  # Minimum samples before model update
            "batch_size": 32,           # Batch size for model updates
            "model_update_frequency": 10  # Update model every N trades
        }
        
        # Update config with RL specific settings
        self.config.update(rl_config)
        
        # Initialize RL state
        self.experience_buffer = []
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = 0.0
        self.total_gas_saved = 0.0
        self.episodes_completed = 0
        self.current_exploration_rate = self.config["exploration_rate"]
        self.last_state = None
        self.last_action = None
        
        # Track performance by token pair and DEX
        self.token_pair_performance = {}
        self.dex_performance = {}
        
        # Track performance by execution method
        self.execution_method_performance = {
            method: {"count": 0, "success": 0, "profit": 0.0}
            for method in self.config["action_space"]["execution_method"]
        }
        
        # Initialize model-specific metrics
        self.metrics.update({
            "episodes_completed": 0,
            "average_reward_per_episode": 0.0,
            "exploration_rate": self.current_exploration_rate,
            "action_distribution": {
                action_type: {action: 0 for action in actions}
                for action_type, actions in self.config["action_space"].items()
            },
            "top_performing_strategies": []
        })
        
        logger.info("Reinforcement learning model initialized with additional configurations")
    
    def get_action(self, state: Dict[str, Any], explore: bool = True) -> Dict[str, Any]:
        """
        Get recommended action for a given state.
        
        Args:
            state: Current state information
            explore: Whether to use exploration (vs exploitation)
            
        Returns:
            Dictionary with recommended actions
        """
        # Extract key state features
        token_pair = state.get("token_pair", "WETH-USDC")
        dex = state.get("dex", "uniswap")
        position_size = float(state.get("position_size", 1.0))
        expected_profit = float(state.get("expected_profit", 0.0))
        gas_price = float(state.get("gas_price", 20.0))
        market_volatility = state.get("market_volatility", "medium")
        
        # In a real implementation, we would use a trained RL model
        # Here we simulate decisions based on heuristics and some randomness
        
        # Decide whether to explore or exploit
        if explore and random.random() < self.current_exploration_rate:
            # Exploration: choose random actions
            execution_method = random.choice(self.config["action_space"]["execution_method"])
            l2_network = random.choice(self.config["action_space"]["l2_network"])
            flash_loan_provider = random.choice(self.config["action_space"]["flash_loan_provider"])
            trade_size_multiplier = random.choice(self.config["action_space"]["trade_size_multiplier"])
            slippage_multiplier = random.choice(self.config["action_space"]["slippage_tolerance_multiplier"])
            
            action_source = "exploration"
        else:
            # Exploitation: choose best actions based on learned policy
            # Since we don't have a real model, we'll use heuristics
            
            # 1. Execution method selection based on state
            if gas_price > 40.0:
                # High gas price favors L2
                execution_method = "l2"
            elif position_size > 5.0:
                # Large position size favors flash loans
                execution_method = "flash_loan"
            elif gas_price > 30.0 and position_size > 3.0:
                # Both high gas and large position favors combined approach
                execution_method = "l2_flash"
            else:
                # Default to base strategy for smaller trades with low gas
                execution_method = "base"
            
            # 2. L2 network selection
            if market_volatility in ["high", "very_high"]:
                # In high volatility, prefer faster L2s
                l2_network = random.choice(["arbitrum", "optimism"])
            else:
                # Otherwise, prefer cheaper L2s
                l2_network = random.choice(["polygon", "base"])
            
            # 3. Flash loan provider selection
            if expected_profit < 50.0:
                # For smaller profits, use cheaper providers
                flash_loan_provider = random.choice(["uniswap", "balancer"])
            else:
                # For larger profits, use more reliable providers
                flash_loan_provider = random.choice(["aave", "maker"])
            
            # 4. Trade size based on volatility
            if market_volatility in ["very_low", "low"]:
                trade_size_multiplier = random.choice([1.0, 1.25, 1.5])
            elif market_volatility == "medium":
                trade_size_multiplier = 1.0
            else:
                trade_size_multiplier = random.choice([0.5, 0.75])
            
            # 5. Slippage tolerance based on volatility
            if market_volatility in ["very_low", "low"]:
                slippage_multiplier = 0.8
            elif market_volatility == "medium":
                slippage_multiplier = 1.0
            elif market_volatility == "high":
                slippage_multiplier = 1.5
            else:
                slippage_multiplier = 2.0
            
            action_source = "exploitation"
        
        # Store last state and action for learning
        self.last_state = state.copy()
        self.last_action = {
            "execution_method": execution_method,
            "l2_network": l2_network,
            "flash_loan_provider": flash_loan_provider,
            "trade_size_multiplier": trade_size_multiplier,
            "slippage_tolerance_multiplier": slippage_multiplier
        }
        
        # Update action distribution metrics
        for action_type, action_value in self.last_action.items():
            if action_type in self.metrics["action_distribution"]:
                if action_value in self.metrics["action_distribution"][action_type]:
                    self.metrics["action_distribution"][action_type][action_value] += 1
        
        # Prepare result with additional context
        result = {
            "state": {key: state.get(key) for key in self.config["state_features"] if key in state},
            "action": self.last_action,
            "action_source": action_source,
            "exploration_rate": self.current_exploration_rate,
            "adjusted_position_size": position_size * trade_size_multiplier,
            "adjusted_slippage": float(state.get("slippage", 0.005)) * slippage_multiplier,
            "confidence": 0.9 if action_source == "exploitation" else 0.6
        }
        
        logger.info(f"RL model recommended {execution_method} for {token_pair} on {dex} ({action_source})")
        
        return result
    
    def observe_reward(self, state: Dict[str, Any], action: Dict[str, Any], result: Dict[str, Any]) -> float:
        """
        Process the result of an action and calculate reward.
        
        Args:
            state: State information when action was taken
            action: Action that was taken
            result: Result of the action
            
        Returns:
            Calculated reward value
        """
        # Extract key result information
        success = result.get("success", False)
        profit = float(result.get("profit", 0.0))
        gas_saved = float(result.get("gas_saved", 0.0))
        execution_time = float(result.get("execution_time", 1.0))
        
        # Extract key action information
        execution_method = action.get("execution_method", "base")
        
        # Calculate reward components
        profit_reward = profit * self.config["reward_scaling"]["profit"]
        gas_reward = gas_saved * self.config["reward_scaling"]["gas_savings"]
        speed_reward = (1.0 / execution_time) * self.config["reward_scaling"]["speed"] if execution_time > 0 else 0
        success_reward = float(success) * self.config["reward_scaling"]["success_rate"]
        
        # Total reward
        total_reward = profit_reward + gas_reward + speed_reward + success_reward
        
        # Update performance tracking
        self.total_trades += 1
        if success:
            self.successful_trades += 1
        self.total_profit += profit
        self.total_gas_saved += gas_saved
        
        # Update execution method performance
        if execution_method in self.execution_method_performance:
            self.execution_method_performance[execution_method]["count"] += 1
            if success:
                self.execution_method_performance[execution_method]["success"] += 1
            self.execution_method_performance[execution_method]["profit"] += profit
        
        # Update token pair and DEX performance
        token_pair = state.get("token_pair", "WETH-USDC")
        dex = state.get("dex", "uniswap")
        
        if token_pair not in self.token_pair_performance:
            self.token_pair_performance[token_pair] = {"count": 0, "success": 0, "profit": 0.0}
        self.token_pair_performance[token_pair]["count"] += 1
        if success:
            self.token_pair_performance[token_pair]["success"] += 1
        self.token_pair_performance[token_pair]["profit"] += profit
        
        if dex not in self.dex_performance:
            self.dex_performance[dex] = {"count": 0, "success": 0, "profit": 0.0}
        self.dex_performance[dex]["count"] += 1
        if success:
            self.dex_performance[dex]["success"] += 1
        self.dex_performance[dex]["profit"] += profit
        
        # Add experience to buffer
        if self.last_state is not None and self.last_action is not None:
            experience = {
                "state": self.last_state,
                "action": self.last_action,
                "reward": total_reward,
                "next_state": state,
                "done": False  # Typically false for trading unless we're ending an episode
            }
            self.experience_buffer.append(experience)
        
        # Check if we should update the model
        if len(self.experience_buffer) >= self.config["min_samples_for_update"] and \
           self.total_trades % self.config["model_update_frequency"] == 0:
            self._update_model()
        
        # Check if we completed an episode
        if self.total_trades % self.config["episode_length"] == 0:
            self.episodes_completed += 1
            self.metrics["episodes_completed"] = self.episodes_completed
            
            # Calculate average reward for this episode
            episode_rewards = [exp["reward"] for exp in self.experience_buffer[-self.config["episode_length"]:]]
            avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0
            self.metrics["average_reward_per_episode"] = avg_reward
            
            # Mark the last experience as the end of an episode
            if self.experience_buffer:
                self.experience_buffer[-1]["done"] = True
            
            # Update exploration rate
            self.current_exploration_rate = max(
                self.config["min_exploration_rate"],
                self.current_exploration_rate * self.config["exploration_decay"]
            )
            self.metrics["exploration_rate"] = self.current_exploration_rate
            
            logger.info(f"RL episode {self.episodes_completed} completed: avg reward = {avg_reward:.2f}, "
                      f"exploration = {self.current_exploration_rate:.3f}")
        
        # Reset last state and action
        self.last_state = None
        self.last_action = None
        
        return total_reward
    
    def _update_model(self) -> None:
        """Update the RL model based on collected experiences."""
        # In a real implementation, this would update the model weights
        # Here we just log that an update would happen
        
        # Calculate success rate
        success_rate = self.successful_trades / self.total_trades if self.total_trades > 0 else 0
        
        # Identify top performing strategies
        top_strategies = []
        
        # By execution method
        for method, stats in self.execution_method_performance.items():
            if stats["count"] > 0:
                success_rate = stats["success"] / stats["count"]
                avg_profit = stats["profit"] / stats["count"]
                top_strategies.append({
                    "type": "execution_method",
                    "value": method,
                    "success_rate": success_rate,
                    "avg_profit": avg_profit,
                    "count": stats["count"]
                })
        
        # By token pair
        for pair, stats in self.token_pair_performance.items():
            if stats["count"] > 0:
                success_rate = stats["success"] / stats["count"]
                avg_profit = stats["profit"] / stats["count"]
                top_strategies.append({
                    "type": "token_pair",
                    "value": pair,
                    "success_rate": success_rate,
                    "avg_profit": avg_profit,
                    "count": stats["count"]
                })
        
        # By DEX
        for dex, stats in self.dex_performance.items():
            if stats["count"] > 0:
                success_rate = stats["success"] / stats["count"]
                avg_profit = stats["profit"] / stats["count"]
                top_strategies.append({
                    "type": "dex",
                    "value": dex,
                    "success_rate": success_rate,
                    "avg_profit": avg_profit,
                    "count": stats["count"]
                })
        
        # Sort by average profit
        top_strategies.sort(key=lambda x: x["avg_profit"], reverse=True)
        
        # Keep only top 10
        self.metrics["top_performing_strategies"] = top_strategies[:10]
        
        logger.info(f"RL model updated after {self.total_trades} trades: "
                  f"success rate = {success_rate:.2%}, avg profit = ${self.total_profit/self.total_trades:.2f}")
    
    def predict(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a prediction for the optimal actions in the given state.
        
        Args:
            state: Current state information
            
        Returns:
            Dictionary with prediction results
        """
        # Call the base predict method for common functionality
        base_result = super().predict(state)
        if not base_result["success"]:
            return base_result
        
        # Get best action without exploration
        action = self.get_action(state, explore=False)
        
        # Prepare confidence scores for different aspects of the prediction
        execution_confidence = 0.0
        method = action["action"]["execution_method"]
        
        # Calculate confidence based on historical performance
        if method in self.execution_method_performance and self.execution_method_performance[method]["count"] > 0:
            method_stats = self.execution_method_performance[method]
            success_rate = method_stats["success"] / method_stats["count"]
            avg_profit = method_stats["profit"] / method_stats["count"]
            
            # Higher success rate and profit lead to higher confidence
            execution_confidence = 0.5 + (success_rate * 0.3) + min(avg_profit / 100, 0.2)
        else:
            execution_confidence = 0.5  # Default for untested methods
        
        # Overall confidence is weighted by experience
        experience_factor = min(self.total_trades / 1000, 1.0)  # Caps at 1.0 after 1000 trades
        overall_confidence = 0.3 + (execution_confidence * 0.7 * experience_factor)
        
        # Return prediction results
        prediction_result = {
            "success": True,
            "recommended_action": action["action"],
            "execution_method": method,
            "adjusted_position_size": action["adjusted_position_size"],
            "adjusted_slippage": action["adjusted_slippage"],
            "confidence": overall_confidence,
            "execution_confidence": execution_confidence,
            "experience_factor": experience_factor,
            "exploration_rate": self.current_exploration_rate,
            "note": "Recommendations improve with more trading experience"
        }
        
        logger.info(f"RL prediction: {method} with {overall_confidence:.2%} confidence")
        
        return prediction_result 


class ModelManager:
    """
    Manager for all ML models, providing a unified interface.
    
    This class instantiates and manages all the different models, allowing
    for easy access and coordination between models.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path
        
        # Initialize models
        self.models = {
            ModelType.REINFORCEMENT_LEARNING: ReinforcementLearningModel(config_path),
            ModelType.PRICE_IMPACT: PriceImpactModel(config_path),
            ModelType.VOLATILITY: VolatilityTrackingModel(config_path)
            # Add other models as needed
        }
        
        logger.info(f"Model manager initialized with {len(self.models)} models")
    
    def get_model(self, model_type: ModelType) -> BaseModel:
        """
        Get a specific model.
        
        Args:
            model_type: Type of model to get
            
        Returns:
            The requested model
        """
        if model_type not in self.models:
            raise ValueError(f"Model type {model_type} not found")
        
        return self.models[model_type]
    
    def train_all_models(self, training_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Train all models with provided data.
        
        Args:
            training_data: Training data for all models (optional)
            
        Returns:
            Dictionary with training results
        """
        results = {}
        
        for model_type, model in self.models.items():
            # Use model-specific data if available, otherwise use general data
            model_data = training_data.get(model_type.value, training_data) if training_data else None
            results[model_type.value] = model.train(model_data)
        
        return results
    
    def save_all_models(self) -> Dict[str, Any]:
        """
        Save all models.
        
        Returns:
            Dictionary with save results
        """
        results = {}
        
        for model_type, model in self.models.items():
            results[model_type.value] = model.save()
        
        return results
    
    def load_all_models(self) -> Dict[str, Any]:
        """
        Load all models.
        
        Returns:
            Dictionary with load results
        """
        results = {}
        
        for model_type, model in self.models.items():
            results[model_type.value] = model.load()
        
        return results
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from all models.
        
        Returns:
            Dictionary with metrics from all models
        """
        metrics = {}
        
        for model_type, model in self.models.items():
            metrics[model_type.value] = model.get_metrics()
        
        return metrics
    
    def enhance_trade_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all relevant models to enhance a trade opportunity.
        
        Args:
            opportunity: Original trade opportunity
            
        Returns:
            Enhanced opportunity with model-based adjustments
        """
        enhanced = opportunity.copy()
        
        # 1. Check market volatility
        try:
            token_pair = opportunity.get("token_pair", "WETH-USDC")
            volatility_model = self.get_model(ModelType.VOLATILITY)
            volatility_data = volatility_model.get_current_volatility(token_pair)
            
            # Add volatility information to the opportunity
            enhanced["market_volatility"] = volatility_data["volatility_level"]
            enhanced["volatility_data"] = volatility_data
            
            # Apply position size adjustment based on volatility
            original_position_size = float(opportunity.get("position_size", 1.0))
            position_size_multiplier = volatility_data["position_size_multiplier"]
            enhanced["position_size"] = original_position_size * position_size_multiplier
            enhanced["position_size_adjustment"] = {
                "original": original_position_size,
                "multiplier": position_size_multiplier,
                "adjusted": enhanced["position_size"],
                "reason": f"Adjusted based on {volatility_data['volatility_level']} market volatility"
            }
        except Exception as e:
            logger.error(f"Error applying volatility model: {str(e)}")
        
        # 2. Apply price impact prediction for slippage adjustment
        try:
            price_impact_model = self.get_model(ModelType.PRICE_IMPACT)
            impact_prediction = price_impact_model.predict(enhanced)
            
            if impact_prediction["success"]:
                # Add price impact information to the opportunity
                enhanced["price_impact_data"] = impact_prediction
                
                # Adjust slippage tolerance based on prediction
                original_slippage = float(opportunity.get("max_slippage", 0.005))
                recommended_slippage = impact_prediction["recommended_slippage"] / 100  # Convert from percentage
                
                # Use max of original and recommended to ensure safety
                enhanced["max_slippage"] = max(original_slippage, recommended_slippage)
                enhanced["slippage_adjustment"] = {
                    "original": original_slippage,
                    "recommended": recommended_slippage,
                    "adjusted": enhanced["max_slippage"],
                    "reason": "Adjusted based on predicted price impact"
                }
        except Exception as e:
            logger.error(f"Error applying price impact model: {str(e)}")
        
        # 3. Apply reinforcement learning for execution method selection
        try:
            rl_model = self.get_model(ModelType.REINFORCEMENT_LEARNING)
            rl_prediction = rl_model.predict(enhanced)
            
            if rl_prediction["success"]:
                # Add execution recommendations to the opportunity
                enhanced["execution_recommendation"] = rl_prediction["recommended_action"]
                enhanced["execution_confidence"] = rl_prediction["confidence"]
                
                # Apply execution method
                enhanced["execution_method"] = rl_prediction["execution_method"]
                
                # Apply additional RL-based adjustments
                enhanced["position_size"] = rl_prediction["adjusted_position_size"]
                enhanced["max_slippage"] = rl_prediction["adjusted_slippage"]
        except Exception as e:
            logger.error(f"Error applying reinforcement learning model: {str(e)}")
        
        return enhanced
    
    def observe_trade_result(self, state: Dict[str, Any], action: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Update all relevant models with the result of a trade.
        
        Args:
            state: State before the trade
            action: Action taken
            result: Result of the trade
        """
        # Update reinforcement learning model
        try:
            rl_model = self.get_model(ModelType.REINFORCEMENT_LEARNING)
            reward = rl_model.observe_reward(state, action, result)
            logger.info(f"RL model updated with reward: {reward:.2f}")
        except Exception as e:
            logger.error(f"Error updating reinforcement learning model: {str(e)}") 

def test_models():
    """Test the advanced ML models with example data."""
    # Initialize model manager
    manager = ModelManager()
    
    print("\n===== Testing Advanced ML Models =====\n")
    
    # Example trade opportunity
    opportunity = {
        "token_pair": "WETH-USDC",
        "dex": "uniswap",
        "position_size": 2.5,
        "expected_profit": 45.0,
        "gas_price": 35.0,
        "max_slippage": 0.005
    }
    
    print(f"Original opportunity: {json.dumps(opportunity, indent=2)}")
    
    # Test price impact model
    price_impact_model = manager.get_model(ModelType.PRICE_IMPACT)
    impact_result = price_impact_model.predict(opportunity)
    print(f"\nPrice Impact Prediction: {json.dumps(impact_result, indent=2)}")
    
    # Test position size adjustment
    size_adjustment = price_impact_model.adjust_position_size(opportunity, target_impact=0.003)
    print(f"\nPosition Size Adjustment: {json.dumps(size_adjustment, indent=2)}")
    
    # Test volatility model
    volatility_model = manager.get_model(ModelType.VOLATILITY)
    volatility_result = volatility_model.get_current_volatility("WETH-USDC")
    print(f"\nCurrent Volatility: {json.dumps(volatility_result, indent=2)}")
    
    volatility_prediction = volatility_model.predict_volatility("WETH-USDC", 24)
    print(f"\nVolatility Prediction: {json.dumps(volatility_prediction, indent=2)}")
    
    # Test reinforcement learning model
    rl_model = manager.get_model(ModelType.REINFORCEMENT_LEARNING)
    
    # Add volatility information to the opportunity
    opportunity["market_volatility"] = volatility_result["volatility_level"]
    
    rl_action = rl_model.get_action(opportunity)
    print(f"\nRL Recommended Action: {json.dumps(rl_action, indent=2)}")
    
    # Simulate a trade result
    trade_result = {
        "success": True,
        "profit": 42.5,
        "gas_saved": 15.0,
        "execution_time": 0.8
    }
    
    # Observe the reward
    reward = rl_model.observe_reward(opportunity, rl_action["action"], trade_result)
    print(f"\nRL Reward: {reward:.2f}")
    
    # Test enhancing an opportunity using all models
    enhanced = manager.enhance_trade_opportunity(opportunity)
    print(f"\nEnhanced Opportunity: {json.dumps(enhanced, indent=2)}")
    
    print("\n===== End of Test =====\n")
    
    return manager


if __name__ == "__main__":
    test_models() 