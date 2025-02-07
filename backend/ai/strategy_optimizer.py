import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple
import joblib
import os

class StrategyOptimizer:
    def __init__(self, model_path: str = "models/strategy_model.joblib"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self._load_or_create_model()

    def _load_or_create_model(self):
        """Load existing model or create new one if not exists"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                print("Loaded existing model")
            else:
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                print("Created new model")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )

    def prepare_features(self, trade_data: List[Dict]) -> np.ndarray:
        """Convert trade data into feature matrix"""
        features = []
        for trade in trade_data:
            feature_vector = [
                trade['price_difference'],
                trade['volume_24h'],
                trade['liquidity_pool_size'],
                trade['gas_price'],
                trade['network_congestion'],
                trade['historical_success_rate']
            ]
            features.append(feature_vector)
        return np.array(features)

    def train(self, trade_data: List[Dict], outcomes: List[float]):
        """Train the model on historical trade data"""
        X = self.prepare_features(trade_data)
        X_scaled = self.scaler.fit_transform(X)
        y = np.array(outcomes)

        self.model.fit(X_scaled, y)
        joblib.dump(self.model, self.model_path)
        print("Model trained and saved")

    def predict_success_probability(self, trade_data: Dict) -> float:
        """Predict probability of successful arbitrage"""
        features = self.prepare_features([trade_data])
        features_scaled = self.scaler.transform(features)
        probability = self.model.predict(features_scaled)[0]
        return float(probability)

    def optimize_parameters(self, trade_data: Dict) -> Dict:
        """Optimize trading parameters for maximum profit"""
        base_prob = self.predict_success_probability(trade_data)
        optimized_params = {
            'min_profit_threshold': max(0.001, base_prob * 0.02),
            'max_gas_price': min(150, int(base_prob * 200)),
            'slippage_tolerance': max(0.001, min(0.01, base_prob * 0.015)),
            'confidence_score': base_prob
        }
        return optimized_params

if __name__ == "__main__":
    # Example usage
    optimizer = StrategyOptimizer()
    
    # Sample trade data
    sample_trade = {
        'price_difference': 0.02,
        'volume_24h': 1000000,
        'liquidity_pool_size': 500000,
        'gas_price': 50,
        'network_congestion': 0.7,
        'historical_success_rate': 0.85
    }
    
    # Get optimized parameters
    params = optimizer.optimize_parameters(sample_trade)
    print("Optimized parameters:", params) 