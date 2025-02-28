import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout, BatchNormalization, Input, Concatenate
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import xgboost as xgb
import lightgbm as lgb
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
import json
import os
import time
from datetime import datetime
import matplotlib.pyplot as plt
import pickle
import joblib
from feature_extractor import FeatureSet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ModelTrainer:
    """Trains and evaluates machine learning models for arbitrage execution"""
    
    def __init__(self, models_dir: str = "backend/ai/models"):
        self.models_dir = models_dir
        
        # Create models directory if it doesn't exist
        os.makedirs(models_dir, exist_ok=True)
        
        # Initialize model registry
        self.model_registry = {}
        
        # Load existing models if available
        self._load_models()
    
    def _load_models(self):
        """Load existing models from disk"""
        # Check for model registry file
        registry_path = os.path.join(self.models_dir, "model_registry.json")
        if os.path.exists(registry_path):
            with open(registry_path, "r") as f:
                self.model_registry = json.load(f)
                logger.info(f"Loaded model registry with {len(self.model_registry)} models")
    
    def _save_model_registry(self):
        """Save model registry to disk"""
        registry_path = os.path.join(self.models_dir, "model_registry.json")
        with open(registry_path, "w") as f:
            json.dump(self.model_registry, f, indent=2)
        logger.info(f"Saved model registry with {len(self.model_registry)} models")
    
    def train_profit_predictor(self, training_data: FeatureSet, model_type: str = "xgboost") -> Dict:
        """
        Train a model to predict arbitrage profit
        
        Args:
            training_data: FeatureSet containing training data
            model_type: Type of model to train (xgboost, lightgbm, random_forest, neural_network)
            
        Returns:
            Dictionary with training results
        """
        X_train, y_train = training_data.X, training_data.y
        feature_names = training_data.feature_names
        
        # Generate a unique model ID
        model_id = f"profit_predictor_{model_type}_{int(time.time())}"
        model_path = os.path.join(self.models_dir, f"{model_id}.pkl")
        
        # Train model based on type
        if model_type == "xgboost":
            model = xgb.XGBRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                min_child_weight=1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="reg:squarederror",
                random_state=42
            )
            model.fit(X_train, y_train)
            
            # Save model
            joblib.dump(model, model_path)
            
            # Get feature importance
            feature_importance = model.feature_importances_
            
        elif model_type == "lightgbm":
            model = lgb.LGBMRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=6,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="regression",
                random_state=42
            )
            model.fit(X_train, y_train)
            
            # Save model
            joblib.dump(model, model_path)
            
            # Get feature importance
            feature_importance = model.feature_importances_
            
        elif model_type == "random_forest":
            model = RandomForestRegressor(
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            model.fit(X_train, y_train)
            
            # Save model
            joblib.dump(model, model_path)
            
            # Get feature importance
            feature_importance = model.feature_importances_
            
        elif model_type == "neural_network":
            # Define model architecture
            input_dim = X_train.shape[1]
            
            model = Sequential([
                Dense(128, activation="relu", input_shape=(input_dim,)),
                BatchNormalization(),
                Dropout(0.3),
                Dense(64, activation="relu"),
                BatchNormalization(),
                Dropout(0.2),
                Dense(32, activation="relu"),
                Dense(1)  # Output layer for regression
            ])
            
            # Compile model
            model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss="mse",
                metrics=["mae"]
            )
            
            # Define callbacks
            callbacks = [
                EarlyStopping(patience=20, restore_best_weights=True),
                ReduceLROnPlateau(factor=0.5, patience=5, min_lr=0.00001)
            ]
            
            # Train model
            history = model.fit(
                X_train, y_train,
                epochs=200,
                batch_size=32,
                validation_split=0.2,
                callbacks=callbacks,
                verbose=1
            )
            
            # Save model
            model_path = os.path.join(self.models_dir, f"{model_id}.h5")
            model.save(model_path)
            
            # Get feature importance (for neural networks, we'll use permutation importance)
            # This is a simplified version - in production, use permutation importance
            feature_importance = np.zeros(len(feature_names))
            
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Register model
        self.model_registry[model_id] = {
            "model_type": model_type,
            "target": "profit",
            "feature_names": feature_names,
            "model_path": model_path,
            "created_at": datetime.now().isoformat(),
            "metrics": {}  # Will be populated during evaluation
        }
        
        # Save model registry
        self._save_model_registry()
        
        logger.info(f"Trained {model_type} profit predictor model with ID: {model_id}")
        
        return {
            "model_id": model_id,
            "model_type": model_type,
            "feature_importance": feature_importance.tolist(),
            "feature_names": feature_names
        }
    
    def train_gas_optimizer(self, training_data: FeatureSet) -> Dict:
        """
        Train a model to optimize gas prices for arbitrage transactions
        
        Args:
            training_data: FeatureSet containing training data
            
        Returns:
            Dictionary with training results
        """
        X_train, y_train = training_data.X, training_data.y
        feature_names = training_data.feature_names
        
        # Generate a unique model ID
        model_id = f"gas_optimizer_{int(time.time())}"
        model_path = os.path.join(self.models_dir, f"{model_id}.pkl")
        
        # Train XGBoost model for gas optimization
        model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            objective="reg:squarederror",
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Save model
        joblib.dump(model, model_path)
        
        # Get feature importance
        feature_importance = model.feature_importances_
        
        # Register model
        self.model_registry[model_id] = {
            "model_type": "xgboost",
            "target": "gas_price",
            "feature_names": feature_names,
            "model_path": model_path,
            "created_at": datetime.now().isoformat(),
            "metrics": {}  # Will be populated during evaluation
        }
        
        # Save model registry
        self._save_model_registry()
        
        logger.info(f"Trained gas optimizer model with ID: {model_id}")
        
        return {
            "model_id": model_id,
            "model_type": "xgboost",
            "feature_importance": feature_importance.tolist(),
            "feature_names": feature_names
        }
    
    def train_network_selector(self, training_data: FeatureSet) -> Dict:
        """
        Train a model to select the best network for arbitrage
        
        Args:
            training_data: FeatureSet containing training data
            
        Returns:
            Dictionary with training results
        """
        X_train, y_train = training_data.X, training_data.y
        feature_names = training_data.feature_names
        
        # Generate a unique model ID
        model_id = f"network_selector_{int(time.time())}"
        model_path = os.path.join(self.models_dir, f"{model_id}.pkl")
        
        # Train LightGBM model for network selection
        model = lgb.LGBMClassifier(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            num_leaves=31,
            objective="multiclass",
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Save model
        joblib.dump(model, model_path)
        
        # Get feature importance
        feature_importance = model.feature_importances_
        
        # Register model
        self.model_registry[model_id] = {
            "model_type": "lightgbm",
            "target": "network",
            "feature_names": feature_names,
            "model_path": model_path,
            "created_at": datetime.now().isoformat(),
            "metrics": {}  # Will be populated during evaluation
        }
        
        # Save model registry
        self._save_model_registry()
        
        logger.info(f"Trained network selector model with ID: {model_id}")
        
        return {
            "model_id": model_id,
            "model_type": "lightgbm",
            "feature_importance": feature_importance.tolist(),
            "feature_names": feature_names
        }
    
    def train_time_optimizer(self, training_data: FeatureSet) -> Dict:
        """
        Train a model to optimize execution timing for arbitrage
        
        Args:
            training_data: FeatureSet containing training data
            
        Returns:
            Dictionary with training results
        """
        X_train, y_train = training_data.X, training_data.y
        feature_names = training_data.feature_names
        
        # Generate a unique model ID
        model_id = f"time_optimizer_{int(time.time())}"
        model_path = os.path.join(self.models_dir, f"{model_id}.h5")
        
        # Define model architecture
        input_dim = X_train.shape[1]
        
        model = Sequential([
            Dense(64, activation="relu", input_shape=(input_dim,)),
            BatchNormalization(),
            Dropout(0.2),
            Dense(32, activation="relu"),
            BatchNormalization(),
            Dense(16, activation="relu"),
            Dense(1, activation="sigmoid")  # Output layer for binary classification (execute now or wait)
        ])
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss="binary_crossentropy",
            metrics=["accuracy"]
        )
        
        # Define callbacks
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5, min_lr=0.00001)
        ]
        
        # Train model
        history = model.fit(
            X_train, y_train,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=1
        )
        
        # Save model
        model.save(model_path)
        
        # Register model
        self.model_registry[model_id] = {
            "model_type": "neural_network",
            "target": "execution_timing",
            "feature_names": feature_names,
            "model_path": model_path,
            "created_at": datetime.now().isoformat(),
            "metrics": {
                "final_accuracy": float(history.history["accuracy"][-1]),
                "final_val_accuracy": float(history.history["val_accuracy"][-1])
            }
        }
        
        # Save model registry
        self._save_model_registry()
        
        logger.info(f"Trained time optimizer model with ID: {model_id}")
        
        return {
            "model_id": model_id,
            "model_type": "neural_network",
            "history": {
                "accuracy": [float(x) for x in history.history["accuracy"]],
                "val_accuracy": [float(x) for x in history.history["val_accuracy"]],
                "loss": [float(x) for x in history.history["loss"]],
                "val_loss": [float(x) for x in history.history["val_loss"]]
            }
        }
    
    def evaluate_model(self, model_id: str, test_data: FeatureSet) -> Dict:
        """
        Evaluate a trained model on test data
        
        Args:
            model_id: ID of the model to evaluate
            test_data: FeatureSet containing test data
            
        Returns:
            Dictionary with evaluation metrics
        """
        if model_id not in self.model_registry:
            logger.error(f"Model ID {model_id} not found in registry")
            return {"error": f"Model ID {model_id} not found"}
        
        model_info = self.model_registry[model_id]
        model_path = model_info["model_path"]
        model_type = model_info["model_type"]
        target = model_info["target"]
        
        X_test, y_test = test_data.X, test_data.y
        
        # Load model based on type
        if model_type in ["xgboost", "lightgbm", "random_forest"]:
            model = joblib.load(model_path)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            if target in ["profit", "gas_price"]:
                # Regression metrics
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                metrics = {
                    "mse": float(mse),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "r2": float(r2)
                }
            else:
                # Classification metrics
                from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
                
                accuracy = accuracy_score(y_test, np.round(y_pred))
                precision = precision_score(y_test, np.round(y_pred), average="weighted")
                recall = recall_score(y_test, np.round(y_pred), average="weighted")
                f1 = f1_score(y_test, np.round(y_pred), average="weighted")
                
                metrics = {
                    "accuracy": float(accuracy),
                    "precision": float(precision),
                    "recall": float(recall),
                    "f1": float(f1)
                }
        
        elif model_type == "neural_network":
            model = load_model(model_path)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            if target in ["profit", "gas_price"]:
                # Regression metrics
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                metrics = {
                    "mse": float(mse),
                    "rmse": float(rmse),
                    "mae": float(mae),
                    "r2": float(r2)
                }
            else:
                # Classification metrics
                from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
                
                accuracy = accuracy_score(y_test, np.round(y_pred))
                precision = precision_score(y_test, np.round(y_pred), average="weighted")
                recall = recall_score(y_test, np.round(y_pred), average="weighted")
                f1 = f1_score(y_test, np.round(y_pred), average="weighted")
                
                metrics = {
                    "accuracy": float(accuracy),
                    "precision": float(precision),
                    "recall": float(recall),
                    "f1": float(f1)
                }
        
        else:
            logger.error(f"Unsupported model type: {model_type}")
            return {"error": f"Unsupported model type: {model_type}"}
        
        # Update model registry with metrics
        self.model_registry[model_id]["metrics"] = metrics
        self._save_model_registry()
        
        logger.info(f"Evaluated model {model_id} with metrics: {metrics}")
        
        return {
            "model_id": model_id,
            "metrics": metrics
        }
    
    def predict(self, model_id: str, features: np.ndarray) -> np.ndarray:
        """
        Make predictions using a trained model
        
        Args:
            model_id: ID of the model to use
            features: Feature matrix for prediction
            
        Returns:
            Numpy array with predictions
        """
        if model_id not in self.model_registry:
            logger.error(f"Model ID {model_id} not found in registry")
            return np.array([])
        
        model_info = self.model_registry[model_id]
        model_path = model_info["model_path"]
        model_type = model_info["model_type"]
        
        # Load model based on type
        if model_type in ["xgboost", "lightgbm", "random_forest"]:
            model = joblib.load(model_path)
        elif model_type == "neural_network":
            model = load_model(model_path)
        else:
            logger.error(f"Unsupported model type: {model_type}")
            return np.array([])
        
        # Make predictions
        predictions = model.predict(features)
        
        return predictions
    
    def get_best_model(self, target: str) -> str:
        """
        Get the ID of the best model for a specific target
        
        Args:
            target: Target variable (profit, gas_price, network, execution_timing)
            
        Returns:
            Model ID of the best model
        """
        # Filter models by target
        target_models = {
            model_id: info for model_id, info in self.model_registry.items()
            if info["target"] == target and "metrics" in info and info["metrics"]
        }
        
        if not target_models:
            logger.warning(f"No models found for target: {target}")
            return None
        
        # Select best model based on metrics
        if target in ["profit", "gas_price"]:
            # For regression, use R² score
            best_model_id = max(
                target_models.items(),
                key=lambda x: x[1]["metrics"].get("r2", -float("inf"))
            )[0]
        else:
            # For classification, use F1 score
            best_model_id = max(
                target_models.items(),
                key=lambda x: x[1]["metrics"].get("f1", -float("inf"))
            )[0]
        
        logger.info(f"Selected best model for {target}: {best_model_id}")
        
        return best_model_id
    
    def visualize_training_history(self, history: Dict, save_path: Optional[str] = None):
        """
        Visualize training history for neural network models
        
        Args:
            history: Dictionary with training history
            save_path: Path to save the visualization
        """
        plt.figure(figsize=(12, 5))
        
        # Plot loss
        plt.subplot(1, 2, 1)
        plt.plot(history["loss"], label="Training Loss")
        plt.plot(history["val_loss"], label="Validation Loss")
        plt.title("Loss")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.legend()
        
        # Plot accuracy
        plt.subplot(1, 2, 2)
        plt.plot(history["accuracy"], label="Training Accuracy")
        plt.plot(history["val_accuracy"], label="Validation Accuracy")
        plt.title("Accuracy")
        plt.xlabel("Epoch")
        plt.ylabel("Accuracy")
        plt.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Training history visualization saved to {save_path}")
        else:
            plt.show()
    
    def visualize_predictions(self, y_true: np.ndarray, y_pred: np.ndarray, 
                            title: str = "Predictions vs Actual",
                            save_path: Optional[str] = None):
        """
        Visualize model predictions against actual values
        
        Args:
            y_true: True values
            y_pred: Predicted values
            title: Plot title
            save_path: Path to save the visualization
        """
        plt.figure(figsize=(10, 6))
        
        # Scatter plot of predictions vs actual
        plt.scatter(y_true, y_pred, alpha=0.5)
        
        # Add perfect prediction line
        min_val = min(np.min(y_true), np.min(y_pred))
        max_val = max(np.max(y_true), np.max(y_pred))
        plt.plot([min_val, max_val], [min_val, max_val], 'r--')
        
        plt.title(title)
        plt.xlabel("Actual Values")
        plt.ylabel("Predicted Values")
        plt.grid(True, linestyle='--', alpha=0.7)
        
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Predictions visualization saved to {save_path}")
        else:
            plt.show()

# Example usage
if __name__ == "__main__":
    # This would be used with actual data in production
    trainer = ModelTrainer()
    
    # Example of loading a model and making predictions
    model_id = trainer.get_best_model("profit")
    if model_id:
        # Example features (would come from feature_extractor in production)
        example_features = np.random.rand(1, 10)
        
        # Make prediction
        prediction = trainer.predict(model_id, example_features)
        print(f"Predicted profit: {prediction[0]}")
    else:
        print("No profit prediction model found. Train a model first.") 