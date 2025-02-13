import asyncio
import logging
from datetime import datetime
from strategy_optimizer import StrategyOptimizer
from trade_analyzer import TradeAnalyzer
from risk_analyzer import AdaptiveRiskManager
from test_realtime import WebSocketServer, TestnetTradeMonitor
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('testnet_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TradingMonitor:
    def __init__(self):
        self.optimizer = StrategyOptimizer(web3_provider=os.getenv('RPC_URL'))
        self.analyzer = TradeAnalyzer()
        self.risk_manager = AdaptiveRiskManager()
        self.ws_server = WebSocketServer()
        self.trade_monitor = TestnetTradeMonitor(self.ws_server)

        # Performance thresholds
        self.min_success_rate = 0.7  # 70% success rate required
        self.max_slippage = 0.01     # 1% max slippage
        self.min_profit_threshold = 0.002  # 0.2% minimum profit

        # Monitoring state
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = 0
        self.average_slippage = 0
        self.average_gas_cost = 0

    async def start_monitoring(self, duration_seconds: int = 3600):
        """Start monitoring trade execution for the specified duration."""
        logger.info("Starting trade execution monitoring...")

        try:
            # Start WebSocket server
            await self.ws_server.start()
            start_time = datetime.now()

            while (datetime.now() - start_time).seconds < duration_seconds:
                # Monitor and analyze trades
                await self._monitor_trading_cycle()

                # Check performance metrics and adjust if needed
                await self._check_and_adjust_parameters()

                # Wait before next cycle
                await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Error in monitoring: {str(e)}")
        finally:
            await self._generate_final_report()

    async def _monitor_trading_cycle(self):
        """Monitor a single trading cycle."""
        try:
            # Get latest market data
            market_data = await self.optimizer.get_real_time_price('WMATIC/USDC')

            # Analyze market conditions
            risk_analysis = await self.risk_manager.analyze_market_risk(
                market_data.get('prices', []),
                market_data.get('volumes', [])
            )

            # Log market state
            await self.trade_monitor.log_trade({
                'timestamp': datetime.now().isoformat(),
                'market_data': market_data,
                'risk_analysis': risk_analysis
            })

            # Update performance metrics
            self._update_metrics(market_data)

        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")

    async def _check_and_adjust_parameters(self):
        """Check performance metrics and adjust parameters if needed."""
        if self.total_trades > 0:
            success_rate = self.successful_trades / self.total_trades

            # Adjust parameters based on performance
            if success_rate < self.min_success_rate:
                logger.warning(f"Low success rate ({success_rate:.2%}). Adjusting parameters...")
                await self._adjust_trading_parameters()

            # Check for anomalies
            if self.average_slippage > self.max_slippage:
                logger.warning(f"High slippage detected: {self.average_slippage:.2%}")
                await self._adjust_slippage_parameters()

    async def _adjust_trading_parameters(self):
        """Adjust trading parameters based on performance."""
        # Increase minimum profit threshold
        self.min_profit_threshold *= 1.1
        logger.info(f"Adjusted min profit threshold to: {self.min_profit_threshold:.4%}")

        # Update optimizer parameters
        await self.optimizer._check_and_retrain_model()

    async def _adjust_slippage_parameters(self):
        """Adjust parameters to handle high slippage."""
        # Decrease trade sizes
        self.optimizer.trade_size_multiplier *= 0.9
        logger.info(f"Reduced trade size multiplier to: {self.optimizer.trade_size_multiplier:.2f}")

    def _update_metrics(self, market_data: dict):
        """Update performance metrics with new market data."""
        self.total_trades += 1
        if market_data.get('profitable', False):
            self.successful_trades += 1
            self.total_profit += market_data.get('profit', 0)

        self.average_slippage = (
            (self.average_slippage * (self.total_trades - 1) +
             market_data.get('slippage', 0)) / self.total_trades
        )

        self.average_gas_cost = (
            (self.average_gas_cost * (self.total_trades - 1) +
             market_data.get('gas_cost', 0)) / self.total_trades
        )

    async def _generate_final_report(self):
        """Generate final monitoring report."""
        report = {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'success_rate': self.successful_trades / self.total_trades if self.total_trades > 0 else 0,
            'total_profit': self.total_profit,
            'average_slippage': self.average_slippage,
            'average_gas_cost': self.average_gas_cost,
            'final_parameters': {
                'min_profit_threshold': self.min_profit_threshold,
                'trade_size_multiplier': self.optimizer.trade_size_multiplier
            }
        }

        logger.info("\nFinal Monitoring Report:")
        logger.info(json.dumps(report, indent=2))

        # Save report to file
        with open('monitoring_report.json', 'w') as f:
            json.dump(report, f, indent=2)

async def main():
    monitor = TradingMonitor()
    await monitor.start_monitoring(duration_seconds=3600)  # Monitor for 1 hour

if __name__ == "__main__":
    asyncio.run(main())
