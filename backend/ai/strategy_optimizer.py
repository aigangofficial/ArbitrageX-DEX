import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Dict, Tuple, Union, Optional
import joblib
import os
import asyncio
from datetime import datetime
from web3 import Web3, AsyncWeb3
from web3.providers.async_rpc import AsyncHTTPProvider
import json
from collections import defaultdict
import logging
from pymongo import MongoClient
from web3_connector import Web3Connector

logger = logging.getLogger(__name__)

class LSTMModel(nn.Module):
    def __init__(self, input_size: int = 6, hidden_size: int = 64, num_layers: int = 2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2
        )

        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        # x shape: (batch_size, sequence_length, input_size)
        lstm_out, _ = self.lstm(x)
        # Use only the last output for prediction
        last_out = lstm_out[:, -1, :]
        return self.fc(last_out)

class StrategyOptimizer:
    def __init__(self, web3_provider: Optional[str] = None):
        """Initialize strategy optimizer with Web3 and MongoDB connections."""
        self.web3 = None  # Will be initialized in create()
        self.db = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017')).arbitragex

        # Initialize models
        self.model = self._load_or_create_models()
        self.scaler = StandardScaler()

        # Store provider for later initialization
        self.web3_provider = web3_provider

        # Trading parameters
        self.min_confidence = 0.9
        self.min_profit_threshold = 0.002  # 0.2% minimum profit
        self.max_slippage = 0.01  # 1% maximum slippage

    @classmethod
    async def create(cls, web3_provider: Optional[str] = None):
        """Factory method to create and initialize StrategyOptimizer."""
        instance = cls(web3_provider)
        instance.web3 = await Web3Connector.create(web3_provider)
        return instance

    def _load_or_create_models(self) -> LSTMModel:
        """Load existing model or create new one."""
        model_path = 'models/lstm_model.pth'
        if os.path.exists(model_path):
            model = LSTMModel()
            model.load_state_dict(torch.load(model_path))
            logger.info("Loaded existing model")
        else:
            model = LSTMModel()
            logger.info("Created new model")
        return model

    async def execute_simulated_trade(self, pair: str):
        """Execute simulated arbitrage trade with AI prediction and enhanced monitoring."""
        try:
            # Get real-time market data with cross-validation
            price_data = await self.web3.get_real_time_price(pair)
            if not price_data:
                logger.warning(f"Could not get validated price data for {pair}")
                return None

            # Get current network state
            network_info = self.web3.get_network_info()
            current_block = network_info['block']
            current_gas_price = network_info['gas_price']

            # Prepare features for prediction
            features = self._prepare_features(price_data)

            # Make prediction with confidence check
            with torch.no_grad():
                prediction = self.model(features)
                confidence = prediction.item()

            # Get gas price and optimize based on network conditions
            base_gas_cost = await self.web3.estimate_gas_cost()
            optimized_gas = self._optimize_gas_price(base_gas_cost, confidence)

            # Get liquidity data from both DEXs
            quickswap_liquidity = await self.web3.get_pool_liquidity(
                self.web3.contracts['QUICKSWAP_FACTORY'].address,
                *pair.split('/')
            )
            sushiswap_liquidity = await self.web3.get_pool_liquidity(
                self.web3.contracts['SUSHISWAP_FACTORY'].address,
                *pair.split('/')
            )

            # Calculate potential profit considering gas and liquidity
            potential_profit = self._calculate_potential_profit(price_data)
            net_profit = potential_profit - optimized_gas

            # Calculate dynamic slippage based on liquidity
            max_slippage = self._calculate_max_slippage(min(
                sum(quickswap_liquidity),
                sum(sushiswap_liquidity)
            ))
            estimated_slippage = self._estimate_slippage(price_data)

            # Enhanced trade log with detailed metrics
            trade_log = {
                'pair': pair,
                'timestamp': datetime.now(),
                'block_number': current_block,
                'price': price_data['price'],
                'confidence': confidence,
                'potential_profit': potential_profit,
                'net_profit': net_profit,
                'gas_cost': optimized_gas,
                'base_gas_cost': base_gas_cost,
                'slippage': estimated_slippage,
                'max_slippage': max_slippage,
                'volatility': price_data['volatility'],
                'sources': price_data.get('sources', []),
                'quickswap_liquidity': quickswap_liquidity,
                'sushiswap_liquidity': sushiswap_liquidity,
                'network_gas_price': current_gas_price,
                'predicted_price': price_data['price'] * (1 + prediction.item()),
                'actual_price': price_data['price'],
                'market_impact': self._calculate_market_impact(
                    potential_profit,
                    min(sum(quickswap_liquidity), sum(sushiswap_liquidity))
                )
            }

            # Execute trade if conditions are met
            if (confidence >= self.min_confidence and
                net_profit >= self.min_profit_threshold and
                estimated_slippage <= max_slippage and
                trade_log['market_impact'] < 0.01):  # Less than 1% market impact

                trade_log['executed'] = True
                trade_log['execution_time'] = datetime.now()
                logger.info(f"Executing simulated trade for {pair}")

                # Store trade in database with execution details
                await self.db.trades.insert_one({
                    **trade_log,
                    'execution_block': current_block,
                    'execution_gas_price': current_gas_price,
                    'execution_timestamp': datetime.now()
                })

                # Emit detailed trade signal
                await self._emit_trade_signal(trade_log)

                # Schedule model retraining if needed
                await self._check_and_retrain_model()

            else:
                trade_log['executed'] = False
                trade_log['reason'] = self._get_rejection_reason(
                    confidence,
                    net_profit,
                    estimated_slippage,
                    max_slippage,
                    trade_log['market_impact']
                )

            return trade_log

        except Exception as e:
            logger.error(f"Error executing simulated trade: {str(e)}")
            raise

    def _prepare_features(self, price_data: Dict) -> torch.Tensor:
        """Prepare features for model prediction."""
        features = np.array([
            price_data['price'],
            price_data['volatility'],
            price_data['liquidity'],
            self._get_market_sentiment(price_data),
            self._get_time_features(),
            self._get_gas_price_impact()
        ]).reshape(1, 1, -1)  # Reshape for LSTM: (batch, sequence, features)

        return torch.FloatTensor(self.scaler.transform(features))

    def _calculate_potential_profit(self, price_data: Dict) -> float:
        """Calculate potential profit considering price impact."""
        base_profit = abs(price_data['price'] - self._get_sushiswap_price())
        impact = self._calculate_price_impact(price_data['liquidity'])
        return base_profit * (1 - impact)

    def _calculate_slippage(self, liquidity: float) -> float:
        """Dynamic slippage calculation based on liquidity."""
        return min(0.01, 0.5 / (liquidity ** 0.5))  # Cap at 1%

    def _get_rejection_reason(self, confidence: float, profit: float, slippage: float, max_slippage: float, market_impact: float) -> str:
        """Get detailed reason for trade rejection."""
        if confidence < self.min_confidence:
            return f"Insufficient confidence: {confidence:.4f} < {self.min_confidence}"
        if profit < self.min_profit_threshold:
            return f"Insufficient profit: {profit:.6f} < {self.min_profit_threshold}"
        if slippage > max_slippage:
            return f"Excessive slippage: {slippage:.4f} > {max_slippage:.4f}"
        if market_impact >= 0.01:
            return f"High market impact: {market_impact:.4f} >= 0.01"
        return "Unknown"

    async def _emit_trade_signal(self, trade_log: Dict):
        """Emit trade signal to subscribers with full market data."""
        try:
            signal = {
                'type': 'trade_signal',
                'data': {
                    'pair': trade_log['pair'],
                    'action': 'BUY' if trade_log['net_profit'] > 0 else 'SELL',
                    'price': trade_log['price'],
                    'confidence': trade_log['confidence'],
                    'expected_profit': trade_log['net_profit'],
                    'gas_price': trade_log['gas_cost'],
                    'slippage': trade_log['slippage'],
                    'timestamp': datetime.now().isoformat(),
                    'market_data': {
                        'volatility': trade_log['volatility'],
                        'sources': trade_log['sources']
                    }
                }
            }

            # Broadcast signal through WebSocket
            if hasattr(self, 'ws_service'):
                await self.ws_service.broadcast_message(signal)

            logger.info(f"Emitted trade signal: {json.dumps(signal, indent=2)}")

        except Exception as e:
            logger.error(f"Error emitting trade signal: {str(e)}")

    async def _check_and_retrain_model(self):
        """Check if model retraining is needed and perform if necessary."""
        try:
            last_train_time = getattr(self, '_last_train_time', None)
            current_time = datetime.now()

            # Retrain every 24 hours or if not trained yet
            if not last_train_time or (current_time - last_train_time).hours >= 24:
                logger.info("Starting model retraining...")

                # Get recent trades for training
                recent_trades = await self.db.trades.find(
                    {'executed': True}
                ).sort('timestamp', -1).limit(1000).to_list(1000)

                if len(recent_trades) < 100:
                    logger.warning("Insufficient data for retraining")
                    return

                # Prepare training data
                X, y = self._prepare_training_data(recent_trades)

                # Update scaler with new data
                self.scaler.fit(X)
                X_scaled = self.scaler.transform(X)

                # Retrain model
                self.model.train()
                optimizer = torch.optim.Adam(self.model.parameters())
                criterion = nn.BCELoss()

                # Training loop
                for epoch in range(10):
                    optimizer.zero_grad()
                    output = self.model(torch.FloatTensor(X_scaled))
                    loss = criterion(output, torch.FloatTensor(y))
                    loss.backward()
                    optimizer.step()

                # Save updated model
                self._save_model()
                self._last_train_time = current_time
                logger.info("Model retraining completed successfully")

        except Exception as e:
            logger.error(f"Error in model retraining: {str(e)}")

    def _prepare_training_data(self, trades: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from trade history."""
        X = []
        y = []

        for trade in trades:
            features = [
                trade['price'],
                trade['volatility'],
                trade['slippage'],
                trade['gas_cost'],
                self._get_market_sentiment(trade),
                self._get_time_features()
            ]
            X.append(features)
            # Success is when actual profit exceeds gas cost
            y.append(1.0 if trade.get('actual_profit', 0) > trade['gas_cost'] else 0.0)

        return np.array(X), np.array(y)

    def _save_model(self):
        """Save model and scaler to disk."""
        os.makedirs('models', exist_ok=True)
        torch.save(self.model.state_dict(), 'models/lstm_model.pth')
        joblib.dump(self.scaler, 'models/feature_scaler.pkl')
        logger.info("Saved model and scaler to disk")

    def _optimize_gas_price(self, base_gas: float, confidence: float) -> float:
        """Optimize gas price based on confidence and market conditions."""
        # Start with base gas price
        optimal_gas = base_gas

        # Adjust based on confidence
        if confidence > 0.95:  # Very high confidence
            optimal_gas *= 1.2  # Willing to pay 20% more for high confidence trades
        elif confidence < 0.9:  # Lower confidence
            optimal_gas *= 0.9  # Reduce gas price to maintain profitability

        # Ensure within network limits
        return self.web3.validate_gas_price(optimal_gas)

    def _calculate_max_slippage(self, liquidity: float) -> float:
        """Calculate maximum acceptable slippage based on liquidity."""
        # Base slippage of 0.5%
        base_slippage = 0.005

        # Adjust based on liquidity
        if liquidity > 1_000_000:  # High liquidity
            return base_slippage * 0.8
        elif liquidity < 100_000:  # Low liquidity
            return base_slippage * 1.5

        return base_slippage

    def _estimate_slippage(self, price_data: Dict) -> float:
        """Estimate actual slippage based on market conditions."""
        volatility_factor = price_data['volatility'] * 2
        liquidity_factor = 1 / (price_data['liquidity'] ** 0.5)
        return min(0.01, volatility_factor + liquidity_factor)  # Cap at 1%

    def _get_market_sentiment(self, price_data: Dict) -> float:
        """Calculate market sentiment score."""
        volatility_weight = 0.3
        liquidity_weight = 0.3
        momentum_weight = 0.4

        volatility_score = 1 - min(price_data['volatility'] / 0.1, 1)  # Normalize to [0,1]
        liquidity_score = min(price_data['liquidity'] / 1e6, 1)  # Normalize to [0,1]
        momentum_score = self._calculate_momentum(price_data)

        return (volatility_score * volatility_weight +
                liquidity_score * liquidity_weight +
                momentum_score * momentum_weight)

    def _calculate_momentum(self, price_data: Dict) -> float:
        """Calculate price momentum indicator."""
        if not self.web3.price_history[price_data['pair']]:
            return 0.5

        prices = [p['price'] for p in self.web3.price_history[price_data['pair']][-20:]]
        if len(prices) < 2:
            return 0.5

        momentum = (prices[-1] - prices[0]) / prices[0]
        return (np.tanh(momentum) + 1) / 2  # Normalize to [0,1]

    def _get_time_features(self) -> float:
        """Get time-based features."""
        now = datetime.now()
        hour = now.hour / 24.0  # Normalize to [0,1]
        return hour

    def _get_gas_price_impact(self) -> float:
        """Calculate gas price impact on profitability."""
        current_gas = self.web3.w3.eth.gas_price
        baseline_gas = 50 * 10**9  # 50 Gwei
        return min(baseline_gas / current_gas, 1)  # Normalize to [0,1]

    def _calculate_market_impact(self, trade_size: float, pool_liquidity: float) -> float:
        """Calculate expected market impact of trade."""
        if pool_liquidity == 0:
            return float('inf')
        return trade_size / pool_liquidity

    def save_models(self):
        """Save models to disk."""
        os.makedirs('models', exist_ok=True)
        torch.save(self.model.state_dict(), 'models/lstm_model.pth')
        logger.info("Saved models to disk")

if __name__ == "__main__":
    # Example usage
    optimizer = StrategyOptimizer(web3_provider="http://localhost:8545")

    async def main():
        # Test with sample data
        market_data = {
            'price_difference': 0.02,
            'volume_24h': 5000000,
            'liquidity_pool_size': 1000000,
            'gas_price': 50,
            'network_congestion': 0.7,
            'historical_success_rate': 0.85,
            'avg_profit': 0.003,
            'avg_loss': -0.001
        }

        # Test optimization
        params = await optimizer.optimize_trade_parameters(market_data)
        print("Optimized Parameters:", json.dumps(params, indent=2))

        # Test price fetching
        prices = await optimizer.fetch_real_time_prices(['ETH/USDC', 'ETH/USDT'])
        print("Real-time Prices:", json.dumps(prices, indent=2))

        # Test market state updates
        optimizer.update_market_state({
            'liquidity_depth': {'ETH/USDC': 1000000},
            'prices': {'ETH/USDC': 1800.0},
            'gas_price': 50
        })

        # Get and print market state
        state = optimizer.get_market_state()
        print("Market State:", json.dumps(state, indent=2))

        # Get and print model info
        info = optimizer.get_model_info()
        print("Model Info:", json.dumps(info, indent=2))

    asyncio.run(main())
