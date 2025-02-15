import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategy_optimizer import StrategyOptimizer
from risk_analyzer import AdaptiveRiskManager
import logging
import json
from web3 import AsyncWeb3
from web3.providers.async_rpc import AsyncHTTPProvider
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import websockets
import signal
from typing import Dict, Set, Optional
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('testnet_trades.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self, port: int = int(os.getenv('WS_PORT', 3002))):
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        self.heartbeat_interval = int(os.getenv('WS_HEARTBEAT_INTERVAL', 30))
        logger.info(f"Initializing WebSocket server on port {port}")

    async def start(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(self.handler, "0.0.0.0", self.port)
        logger.info(f"WebSocket server started on port {self.port}")
        asyncio.create_task(self.heartbeat())

    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle new WebSocket connections."""
        self.clients.add(websocket)
        try:
            await websocket.send(json.dumps({
                'type': 'connection_established',
                'timestamp': datetime.now().isoformat()
            }))
            async for message in websocket:
                # Handle incoming messages if needed
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return

        message_str = json.dumps(message)
        disconnected = set()

        for client in self.clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)

        # Remove disconnected clients
        self.clients -= disconnected

    async def heartbeat(self):
        """Send periodic heartbeat to keep connections alive."""
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            if self.clients:
                await self.broadcast({
                    'type': 'heartbeat',
                    'timestamp': datetime.now().isoformat(),
                    'connected_clients': len(self.clients)
                })

class TestnetTradeMonitor:
    def __init__(self, ws_server: Optional[WebSocketServer] = None):
        """Initialize testnet trade monitor with WebSocket support."""
        self.db = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017')).arbitragex
        self.risk_manager = AdaptiveRiskManager()
        self.ws_server = ws_server
        self.performance_metrics = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit': 0,
            'avg_slippage': 0,
            'avg_gas_cost': 0,
            'price_accuracy': 0,
            'last_trade_timestamp': None,
            'consecutive_failures': 0
        }
        self.alert_threshold = int(os.getenv('ALERT_ON_CONSECUTIVE_FAILURES', 3))

    async def log_trade(self, trade_data: dict):
        """Log trade data and update performance metrics with enhanced monitoring."""
        try:
            # Add risk metrics
            trade_data['risk_metrics'] = await self.risk_manager.analyze_market_risk(
                pd.Series([t['price'] for t in trade_data.get('price_history', [])]),
                pd.Series([t.get('volume', 0) for t in trade_data.get('price_history', [])])
            )

            # Store trade in database with full context
            await self.db.testnet_trades.insert_one({
                **trade_data,
                'timestamp': datetime.now(),
                'network_state': trade_data.get('network_state', {}),
                'market_conditions': trade_data.get('market_conditions', {}),
                'execution_metrics': {
                    'response_time': trade_data.get('execution_time', 0),
                    'validation_time': trade_data.get('validation_time', 0),
                    'gas_optimization': trade_data.get('gas_optimization', {})
                }
            })

            # Update performance metrics
            self._update_performance_metrics(trade_data)

            # Broadcast trade update via WebSocket
            if self.ws_server:
                await self.ws_server.broadcast({
                    'type': 'trade_update',
                    'data': {
                        'pair': trade_data['pair'],
                        'price': trade_data.get('price', 0),
                        'profit': trade_data.get('net_profit', 0),
                        'executed': trade_data.get('executed', False),
                        'timestamp': datetime.now().isoformat()
                    }
                })

            # Check for warning conditions
            await self._check_warning_conditions()

        except Exception as e:
            logger.error(f"Error logging trade: {str(e)}")
            if self.ws_server:
                await self.ws_server.broadcast({
                    'type': 'error',
                    'message': f"Trade logging error: {str(e)}",
                    'timestamp': datetime.now().isoformat()
                })

    def _update_performance_metrics(self, trade_data: Dict):
        """Update performance metrics with new trade data."""
        self.performance_metrics['total_trades'] += 1
        self.performance_metrics['last_trade_timestamp'] = datetime.now()

        if trade_data.get('executed', False):
            self.performance_metrics['successful_trades'] += 1
            self.performance_metrics['total_profit'] += trade_data.get('net_profit', 0)
            self.performance_metrics['consecutive_failures'] = 0
        else:
            self.performance_metrics['failed_trades'] += 1
            self.performance_metrics['consecutive_failures'] += 1

        # Update moving averages
        self._update_moving_averages(trade_data)

    async def _check_warning_conditions(self):
        """Check for warning conditions and send alerts if necessary."""
        warnings = []

        # Check consecutive failures
        if self.performance_metrics['consecutive_failures'] >= self.alert_threshold:
            warnings.append({
                'type': 'high_failure_rate',
                'message': f"High consecutive failure rate detected: {self.performance_metrics['consecutive_failures']} trades"
            })

        # Check success rate
        if self.performance_metrics['total_trades'] > 10:
            success_rate = (self.performance_metrics['successful_trades'] /
                          self.performance_metrics['total_trades'])
            if success_rate < 0.3:
                warnings.append({
                    'type': 'low_success_rate',
                    'message': f"Low success rate detected: {success_rate:.2%}"
                })

        # Send warnings via WebSocket
        if warnings and self.ws_server:
            for warning in warnings:
                await self.ws_server.broadcast({
                    'type': 'warning',
                    'data': warning,
                    'timestamp': datetime.now().isoformat()
                })
                logger.warning(f"Trading Warning: {warning['message']}")

    def _update_moving_averages(self, trade_data: Dict):
        """Update moving averages for performance metrics."""
        n = self.performance_metrics['total_trades']

        # Update average slippage
        self.performance_metrics['avg_slippage'] = (
            (self.performance_metrics['avg_slippage'] * (n - 1) +
             trade_data.get('slippage', 0)) / n
        )

        # Update average gas cost
        self.performance_metrics['avg_gas_cost'] = (
            (self.performance_metrics['avg_gas_cost'] * (n - 1) +
             trade_data.get('gas_cost', 0)) / n
        )

        # Update price accuracy
        if 'predicted_price' in trade_data and 'actual_price' in trade_data:
            accuracy = 1 - abs(trade_data['predicted_price'] - trade_data['actual_price']) / trade_data['actual_price']
            self.performance_metrics['price_accuracy'] = (
                (self.performance_metrics['price_accuracy'] * (n - 1) + accuracy) / n
            )

async def test_real_time_price_fetching(optimizer: StrategyOptimizer, monitor: TestnetTradeMonitor):
    """Test real-time price fetching functionality with enhanced monitoring."""
    logger.info("Starting real-time price fetching test...")

    # Test with main token pairs on Amoy testnet
    token_pairs = ['WMATIC/USDC', 'WMATIC/USDT', 'USDC/USDT']
    test_results = []
    failed_pairs = []

    try:
        for pair in token_pairs:
            logger.info(f"\nTesting pair: {pair}")
            try:
                # Get real-time price data with validation
                price_data = await optimizer.web3.get_real_time_price(pair)
                if not price_data:
                    logger.warning(f"Could not get validated price data for {pair}")
                    failed_pairs.append(pair)
                    continue

                logger.info(f"Successfully fetched price data for {pair}:")
                logger.info(json.dumps(price_data, indent=2))

                # Execute simulated trade with full monitoring
                trade_start = datetime.now()
                trade_result = await optimizer.execute_simulated_trade(pair)
                execution_time = (datetime.now() - trade_start).total_seconds()

                if trade_result:
                    # Add execution metrics
                    trade_result['execution_time'] = execution_time
                    trade_result['market_conditions'] = {
                        'volatility': price_data['volatility'],
                        'liquidity': price_data['liquidity'],
                        'timestamp': price_data['timestamp']
                    }

                    # Log trade with enhanced monitoring
                    await monitor.log_trade(trade_result)

                    # Store test result
                    test_results.append({
                        'pair': pair,
                        'execution_time': execution_time,
                        'success': trade_result.get('executed', False),
                        'profit': trade_result.get('net_profit', 0),
                        'timestamp': datetime.now().isoformat()
                    })

            except Exception as e:
                logger.error(f"Error processing {pair}: {str(e)}")
                failed_pairs.append(pair)
                continue

        if failed_pairs:
            logger.warning(f"\nFailed pairs: {', '.join(failed_pairs)}")

        return test_results

    except Exception as e:
        logger.error(f"Error in price fetching test: {str(e)}")
        return []

async def run_continuous_test(duration_seconds: int = 3600):
    """Run continuous testing with WebSocket support."""
    logger.info(f"Starting continuous test for {duration_seconds} seconds...")

    # Initialize WebSocket server
    ws_server = WebSocketServer()
    await ws_server.start()

    # Initialize components
    optimizer = await StrategyOptimizer.create(web3_provider=os.getenv('RPC_URL'))
    monitor = TestnetTradeMonitor(ws_server)

    start_time = datetime.now()
    test_results = []
    iteration = 0

    try:
        while (datetime.now() - start_time).seconds < duration_seconds:
            iteration += 1
            logger.info(f"\nStarting test iteration {iteration}")

            # Test price fetching and trade execution
            iteration_results = await test_real_time_price_fetching(optimizer, monitor)
            test_results.extend(iteration_results)

            # Get and broadcast performance metrics
            performance = monitor.performance_metrics
            if ws_server:
                await ws_server.broadcast({
                    'type': 'performance_update',
                    'data': performance,
                    'timestamp': datetime.now().isoformat()
                })

            # Adaptive sleep based on market conditions
            sleep_time = _calculate_adaptive_sleep(performance)
            logger.info(f"Waiting {sleep_time} seconds before next iteration...")
            await asyncio.sleep(sleep_time)

    except Exception as e:
        logger.error(f"Error in continuous test: {str(e)}")
    finally:
        # Generate final report
        final_report = _generate_final_report(test_results, monitor.performance_metrics)
        logger.info("\nTest completed. Final report:")
        logger.info(json.dumps(final_report, indent=2))

        # Broadcast test completion
        if ws_server:
            await ws_server.broadcast({
                'type': 'test_completed',
                'data': final_report,
                'timestamp': datetime.now().isoformat()
            })

def _calculate_adaptive_sleep(performance: dict) -> float:
    """Calculate adaptive sleep time based on performance metrics."""
    base_sleep = float(os.getenv('MONITOR_INTERVAL_SECONDS', 5))

    # Adjust based on success rate
    success_rate = (performance['successful_trades'] / performance['total_trades']
                   if performance['total_trades'] > 0 else 0.5)

    if success_rate < 0.3:
        base_sleep *= 2  # Slow down if success rate is low
    elif success_rate > 0.7:
        base_sleep *= 0.5  # Speed up if success rate is high

    # Adjust based on price accuracy
    if performance['price_accuracy'] < 0.7:
        base_sleep *= 1.5  # Slow down if price predictions are less accurate

    return min(max(base_sleep, 2), 30)  # Keep between 2 and 30 seconds

def _generate_final_report(test_results: list, metrics: dict) -> dict:
    """Generate comprehensive final report."""
    return {
        'summary': {
            'total_trades': metrics['total_trades'],
            'successful_trades': metrics['successful_trades'],
            'failed_trades': metrics['failed_trades'],
            'success_rate': (metrics['successful_trades'] / metrics['total_trades']
                           if metrics['total_trades'] > 0 else 0),
            'total_profit': metrics['total_profit'],
            'avg_slippage': metrics['avg_slippage'],
            'avg_gas_cost': metrics['avg_gas_cost'],
            'price_accuracy': metrics['price_accuracy']
        },
        'test_duration': {
            'start_time': min(r['timestamp'] for r in test_results) if test_results else None,
            'end_time': max(r['timestamp'] for r in test_results) if test_results else None
        },
        'performance_metrics': metrics,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    asyncio.run(run_continuous_test(duration_seconds=3600))  # Run for 1 hour
