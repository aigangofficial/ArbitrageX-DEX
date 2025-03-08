"""
ArbitrageX Model Management Module

This module combines functionality from:
- model_training.py: AI model training implementation
- force_model_update.py: Force AI model updates
- get_model_performance.py: Get AI model performance metrics
"""

import os
import json
import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import tensorflow as tf
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("model_management.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("model_management")

# Load configuration
def load_config(config_path: str) -> Dict:
    """Load configuration from a JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        return {}

class ModelTrainer:
    """Handles AI model training and updates."""
    
    def __init__(self, config_path: str = "config/model_training_config.json"):
        self.config = load_config(config_path)
        self.model_dir = self.config.get("model_dir", "models")
        self.data_dir = self.config.get("data_dir", "data")
        self.batch_size = self.config.get("batch_size", 32)
        self.epochs = self.config.get("epochs", 50)
        self.validation_split = self.config.get("validation_split", 0.2)
        self.learning_rate = self.config.get("learning_rate", 0.001)
        
        # Create directories if they don't exist
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        logger.info(f"Model trainer initialized with {self.epochs} epochs, {self.batch_size} batch size")
    
    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load training data from files.
        
        Returns:
            Tuple of (features, labels)
        """
        try:
            features_path = os.path.join(self.data_dir, "training_features.npy")
            labels_path = os.path.join(self.data_dir, "training_labels.npy")
            
            if os.path.exists(features_path) and os.path.exists(labels_path):
                features = np.load(features_path)
                labels = np.load(labels_path)
                logger.info(f"Loaded training data: {features.shape} features, {labels.shape} labels")
                return features, labels
            else:
                logger.warning("Training data files not found")
                return np.array([]), np.array([])
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            return np.array([]), np.array([])
    
    def create_model(self, input_shape: Tuple[int, ...]) -> tf.keras.Model:
        """
        Create a new model architecture.
        
        Args:
            input_shape: Shape of input features
            
        Returns:
            TensorFlow Keras model
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=input_shape),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info(f"Created model with input shape {input_shape}")
        return model
    
    def train_model(self, features: np.ndarray, labels: np.ndarray, model_name: str = "trade_model") -> tf.keras.Model:
        """
        Train a new model on the provided data.
        
        Args:
            features: Training features
            labels: Training labels
            model_name: Name for the saved model
            
        Returns:
            Trained TensorFlow Keras model
        """
        if len(features) == 0 or len(labels) == 0:
            logger.error("Cannot train model: No training data provided")
            return None
        
        # Create model
        model = self.create_model((features.shape[1],))
        
        # Train model
        logger.info(f"Starting model training with {len(features)} samples")
        history = model.fit(
            features, labels,
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_split=self.validation_split,
            verbose=1
        )
        
        # Save model
        model_path = os.path.join(self.model_dir, f"{model_name}.h5")
        model.save(model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Save training history
        history_path = os.path.join(self.model_dir, f"{model_name}_history.json")
        with open(history_path, 'w') as f:
            history_dict = {
                "accuracy": [float(x) for x in history.history['accuracy']],
                "val_accuracy": [float(x) for x in history.history['val_accuracy']],
                "loss": [float(x) for x in history.history['loss']],
                "val_loss": [float(x) for x in history.history['val_loss']]
            }
            json.dump(history_dict, f)
        
        return model
    
    def update_model(self, new_features: np.ndarray, new_labels: np.ndarray, model_name: str = "trade_model") -> tf.keras.Model:
        """
        Update an existing model with new data.
        
        Args:
            new_features: New training features
            new_labels: New training labels
            model_name: Name of the model to update
            
        Returns:
            Updated TensorFlow Keras model
        """
        model_path = os.path.join(self.model_dir, f"{model_name}.h5")
        
        if os.path.exists(model_path):
            try:
                # Load existing model
                model = tf.keras.models.load_model(model_path)
                logger.info(f"Loaded existing model from {model_path}")
                
                # Update with new data
                logger.info(f"Updating model with {len(new_features)} new samples")
                history = model.fit(
                    new_features, new_labels,
                    batch_size=self.batch_size,
                    epochs=self.epochs // 2,  # Fewer epochs for updates
                    validation_split=self.validation_split,
                    verbose=1
                )
                
                # Save updated model
                model.save(model_path)
                logger.info(f"Updated model saved to {model_path}")
                
                return model
            except Exception as e:
                logger.error(f"Error updating model: {e}")
                return self.train_model(new_features, new_labels, model_name)
        else:
            logger.warning(f"Model {model_name} not found, training new model")
            return self.train_model(new_features, new_labels, model_name)
    
    def force_update(self, model_name: str = "trade_model") -> bool:
        """
        Force an update of the model using all available data.
        
        Args:
            model_name: Name of the model to update
            
        Returns:
            Boolean indicating success
        """
        try:
            # Load all available data
            features, labels = self.load_training_data()
            
            if len(features) == 0 or len(labels) == 0:
                logger.error("Cannot force update: No training data available")
                return False
            
            # Train a completely new model
            logger.info(f"Forcing complete model update with {len(features)} samples")
            self.train_model(features, labels, model_name)
            
            # Record the update
            update_record = {
                "timestamp": datetime.now().isoformat(),
                "samples": len(features),
                "forced": True
            }
            
            record_path = os.path.join(self.model_dir, f"{model_name}_updates.json")
            updates = []
            
            if os.path.exists(record_path):
                with open(record_path, 'r') as f:
                    updates = json.load(f)
            
            updates.append(update_record)
            
            with open(record_path, 'w') as f:
                json.dump(updates, f)
            
            logger.info("Force update completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error during force update: {e}")
            return False

class ModelPerformanceAnalyzer:
    """Analyzes and reports on model performance."""
    
    def __init__(self, config_path: str = "config/model_performance_config.json"):
        self.config = load_config(config_path)
        self.model_dir = self.config.get("model_dir", "models")
        self.data_dir = self.config.get("data_dir", "data")
        self.performance_window = self.config.get("performance_window_days", 30)
        logger.info(f"Model performance analyzer initialized with {self.performance_window} day window")
    
    def load_test_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load test data for performance evaluation.
        
        Returns:
            Tuple of (features, labels)
        """
        try:
            features_path = os.path.join(self.data_dir, "test_features.npy")
            labels_path = os.path.join(self.data_dir, "test_labels.npy")
            
            if os.path.exists(features_path) and os.path.exists(labels_path):
                features = np.load(features_path)
                labels = np.load(labels_path)
                logger.info(f"Loaded test data: {features.shape} features, {labels.shape} labels")
                return features, labels
            else:
                logger.warning("Test data files not found")
                return np.array([]), np.array([])
        except Exception as e:
            logger.error(f"Error loading test data: {e}")
            return np.array([]), np.array([])
    
    def evaluate_model(self, model_name: str = "trade_model") -> Dict:
        """
        Evaluate model performance on test data.
        
        Args:
            model_name: Name of the model to evaluate
            
        Returns:
            Dictionary with performance metrics
        """
        model_path = os.path.join(self.model_dir, f"{model_name}.h5")
        
        if not os.path.exists(model_path):
            logger.error(f"Model {model_name} not found at {model_path}")
            return {"error": "Model not found"}
        
        try:
            # Load model
            model = tf.keras.models.load_model(model_path)
            
            # Load test data
            features, labels = self.load_test_data()
            
            if len(features) == 0 or len(labels) == 0:
                logger.error("Cannot evaluate model: No test data available")
                return {"error": "No test data available"}
            
            # Evaluate model
            logger.info(f"Evaluating model on {len(features)} test samples")
            loss, accuracy = model.evaluate(features, labels, verbose=0)
            
            # Make predictions
            predictions = model.predict(features)
            
            # Calculate additional metrics
            true_positives = np.sum((predictions.flatten() >= 0.5) & (labels == 1))
            false_positives = np.sum((predictions.flatten() >= 0.5) & (labels == 0))
            true_negatives = np.sum((predictions.flatten() < 0.5) & (labels == 0))
            false_negatives = np.sum((predictions.flatten() < 0.5) & (labels == 1))
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            # Get model info
            model_info = {
                "last_modified": datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat(),
                "size_mb": os.path.getsize(model_path) / (1024 * 1024)
            }
            
            # Compile results
            results = {
                "model_name": model_name,
                "accuracy": float(accuracy),
                "loss": float(loss),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1_score),
                "true_positives": int(true_positives),
                "false_positives": int(false_positives),
                "true_negatives": int(true_negatives),
                "false_negatives": int(false_negatives),
                "evaluation_time": datetime.now().isoformat(),
                "model_info": model_info
            }
            
            # Save evaluation results
            results_path = os.path.join(self.model_dir, f"{model_name}_evaluation.json")
            with open(results_path, 'w') as f:
                json.dump(results, f)
            
            logger.info(f"Model evaluation completed with accuracy: {accuracy:.4f}")
            return results
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return {"error": str(e)}
    
    def get_performance_history(self, model_name: str = "trade_model") -> Dict:
        """
        Get historical performance metrics for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with historical performance data
        """
        history_path = os.path.join(self.model_dir, f"{model_name}_history.json")
        
        if not os.path.exists(history_path):
            logger.warning(f"No training history found for model {model_name}")
            return {"error": "No training history found"}
        
        try:
            with open(history_path, 'r') as f:
                history = json.load(f)
            
            # Get recent evaluations
            evaluations = []
            eval_path = os.path.join(self.model_dir, f"{model_name}_evaluation.json")
            
            if os.path.exists(eval_path):
                with open(eval_path, 'r') as f:
                    evaluations = [json.load(f)]
            
            # Compile results
            results = {
                "model_name": model_name,
                "training_history": history,
                "recent_evaluations": evaluations,
                "retrieval_time": datetime.now().isoformat()
            }
            
            logger.info(f"Retrieved performance history for model {model_name}")
            return results
        except Exception as e:
            logger.error(f"Error retrieving performance history: {e}")
            return {"error": str(e)}

def main():
    """Main function for testing the model management module."""
    logger.info("Testing Model Management Module")
    
    # Initialize components
    trainer = ModelTrainer()
    analyzer = ModelPerformanceAnalyzer()
    
    # Generate some sample data for testing
    num_samples = 1000
    num_features = 10
    
    features = np.random.random((num_samples, num_features))
    labels = (np.random.random(num_samples) > 0.5).astype(np.int32)
    
    # Save sample data
    os.makedirs("data", exist_ok=True)
    np.save("data/training_features.npy", features[:800])
    np.save("data/training_labels.npy", labels[:800])
    np.save("data/test_features.npy", features[800:])
    np.save("data/test_labels.npy", labels[800:])
    
    # Train model
    model = trainer.train_model(features[:800], labels[:800], "test_model")
    
    # Evaluate model
    performance = analyzer.evaluate_model("test_model")
    logger.info(f"Model performance: {performance}")
    
    # Force update
    success = trainer.force_update("test_model")
    logger.info(f"Force update success: {success}")
    
    # Get performance history
    history = analyzer.get_performance_history("test_model")
    logger.info(f"Performance history retrieved")

if __name__ == "__main__":
    main() 