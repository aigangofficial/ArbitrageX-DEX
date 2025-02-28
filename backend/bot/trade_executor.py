"""
Trade Executor Module for ArbitrageX

This module is responsible for executing arbitrage trades based on
identified opportunities. It handles transaction creation, signing,
and submission to the blockchain.
"""

import logging
import json
import time
import os
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import random
from web3 import Web3
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trade_executor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TradeExecutor")

class TradeExecutor:
    """
    Executes arbitrage trades based on identified opportunities.
    Handles transaction creation, signing, and submission.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the trade executor.
        
        Args:
            config: Bot configuration dictionary
        """
        logger.info("Initializing Trade Executor")
        self.config = config
        
        # Initialize web3 connections
        self.web3_connections = self._init_web3_connections()
        
        # Load contract ABIs
        self.contract_abis = self._load_contract_abis()
        
        # Initialize wallet
        self.wallet = self._init_wallet()
        
        # Trade history
        self.trade_history = deque(maxlen=100)  # Keep last 100 trades
        
        # Nonce tracking for each network
        self.nonces = {}
        
        # Track concurrent trades
        self.active_trades = 0
        self.max_concurrent_trades = config.get("execution", {}).get("max_concurrent_trades", 3)
        
        logger.info("Trade Executor initialized")
    
    def _init_web3_connections(self) -> Dict[str, Web3]:
        """Initialize Web3 connections for each network"""
        connections = {}
        
        # Network RPC endpoints - in production, these would be loaded from secure config
        network_rpcs = {
            "ethereum": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
            "arbitrum": "https://arb1.arbitrum.io/rpc",
            "polygon": "https://polygon-rpc.com",
            "optimism": "https://mainnet.optimism.io",
            "bsc": "https://bsc-dataseed.binance.org/",
            # Add more networks as needed
        }
        
        # For testing/development, use mock connections
        if self.config.get("use_mock_connections", True):
            networks = self.config.get("networks", ["ethereum"])
            for network in networks:
                connections[network] = None
                logger.info(f"Using mock connection for {network}")
            return connections
        
        # Initialize real connections
        networks = self.config.get("networks", ["ethereum"])
        for network in networks:
            try:
                if network in network_rpcs:
                    web3 = Web3(Web3.HTTPProvider(network_rpcs[network]))
                    if web3.is_connected():
                        connections[network] = web3
                        logger.info(f"Connected to {network}")
                    else:
                        logger.warning(f"Failed to connect to {network}")
                        connections[network] = None
                else:
                    logger.warning(f"No RPC endpoint configured for {network}")
                    connections[network] = None
            except Exception as e:
                logger.error(f"Error connecting to {network}: {e}")
                connections[network] = None
        
        return connections
    
    def _load_contract_abis(self) -> Dict:
        """Load contract ABIs from files"""
        abis = {}
        
        try:
            # Load router ABIs
            router_abi_path = "backend/bot/abis/router_abi.json"
            if os.path.exists(router_abi_path):
                with open(router_abi_path, 'r') as f:
                    abis["router"] = json.load(f)
                logger.info(f"Loaded router ABI from {router_abi_path}")
            
            # Load flash loan ABI
            flash_loan_abi_path = "backend/bot/abis/flash_loan_abi.json"
            if os.path.exists(flash_loan_abi_path):
                with open(flash_loan_abi_path, 'r') as f:
                    abis["flash_loan"] = json.load(f)
                logger.info(f"Loaded flash loan ABI from {flash_loan_abi_path}")
            
            # Load arbitrage executor ABI
            executor_abi_path = "backend/bot/abis/arbitrage_executor_abi.json"
            if os.path.exists(executor_abi_path):
                with open(executor_abi_path, 'r') as f:
                    abis["executor"] = json.load(f)
                logger.info(f"Loaded arbitrage executor ABI from {executor_abi_path}")
            
            return abis
            
        except Exception as e:
            logger.error(f"Error loading contract ABIs: {e}")
            # Return empty ABIs
            return {
                "router": [],
                "flash_loan": [],
                "executor": []
            }
    
    def _init_wallet(self) -> Dict:
        """Initialize wallet for transaction signing"""
        # In production, this would load private keys securely
        # For testing/development, use mock wallet
        
        if self.config.get("use_mock_wallet", True):
            wallet = {
                "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Example address
                "private_key": None  # No actual private key for mock
            }
            logger.info("Using mock wallet")
            return wallet
        
        # For real implementation, load wallet securely
        try:
            # This is just a placeholder - in production, use secure key management
            wallet_address = os.environ.get("WALLET_ADDRESS")
            private_key = os.environ.get("PRIVATE_KEY")
            
            if not wallet_address or not private_key:
                raise ValueError("Wallet address or private key not found in environment variables")
            
            wallet = {
                "address": wallet_address,
                "private_key": private_key
            }
            
            logger.info(f"Wallet initialized with address: {wallet_address[:6]}...{wallet_address[-4:]}")
            return wallet
            
        except Exception as e:
            logger.error(f"Error initializing wallet: {e}")
            # Return mock wallet as fallback
            return {
                "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "private_key": None
            }
    
    def execute_trade(self, opportunity: Dict) -> Dict:
        """
        Execute an arbitrage trade based on the identified opportunity.
        
        Args:
            opportunity: Dictionary containing arbitrage opportunity details
            
        Returns:
            Dictionary with trade execution results
        """
        # Check if we can execute more trades
        if self.active_trades >= self.max_concurrent_trades:
            logger.warning(f"Maximum concurrent trades ({self.max_concurrent_trades}) reached, skipping opportunity")
            return {
                "success": False,
                "error": "Maximum concurrent trades reached",
                "opportunity_id": opportunity.get("id")
            }
        
        # Increment active trades
        self.active_trades += 1
        
        try:
            # Log trade execution
            logger.info(f"Executing trade for opportunity {opportunity['id']}")
            logger.info(f"Network: {opportunity['network']}, "
                       f"Tokens: {opportunity['token_a']}/{opportunity['token_b']}, "
                       f"Buy on: {opportunity['buy_dex']}, Sell on: {opportunity['sell_dex']}")
            
            # For testing/development, use mock execution
            if self.config.get("use_mock_execution", True):
                result = self._execute_mock_trade(opportunity)
            else:
                result = self._execute_real_trade(opportunity)
            
            # Add to trade history
            self.trade_history.appendleft({
                "timestamp": datetime.now().isoformat(),
                "opportunity": opportunity,
                "result": result
            })
            
            # Log result
            if result["success"]:
                logger.info(f"Trade successful: {result['profit']} ETH profit")
            else:
                logger.warning(f"Trade failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {
                "success": False,
                "error": str(e),
                "opportunity_id": opportunity.get("id")
            }
        finally:
            # Decrement active trades
            self.active_trades -= 1
    
    def _execute_mock_trade(self, opportunity: Dict) -> Dict:
        """Execute a mock trade for testing/development"""
        # Simulate network latency
        execution_time = random.uniform(0.5, 2.0)
        time.sleep(execution_time)
        
        # Simulate success/failure (90% success rate)
        success = random.random() < 0.9
        
        if success:
            # Simulate some slippage (0-10%)
            slippage = random.uniform(0, 0.1)
            expected_profit = opportunity["potential_profit"]
            actual_profit = expected_profit * (1 - slippage)
            
            # Simulate gas cost variation (±20%)
            gas_variation = random.uniform(0.8, 1.2)
            gas_cost = opportunity["estimated_gas_cost"] * gas_variation
            
            return {
                "success": True,
                "opportunity_id": opportunity["id"],
                "transaction_hash": f"0x{random.randint(0, 0xffffffffffffffff):016x}",
                "expected_profit": expected_profit,
                "actual_profit": actual_profit,
                "profit": actual_profit,  # For consistency with real execution
                "gas_cost": gas_cost,
                "execution_time": execution_time,
                "slippage": slippage * 100,  # as percentage
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Simulate different failure reasons
            failure_reasons = [
                "Transaction reverted",
                "Slippage too high",
                "Insufficient liquidity",
                "Price changed",
                "Gas price too low",
                "Network congestion"
            ]
            error = random.choice(failure_reasons)
            
            # Simulate gas cost for failed transaction (usually lower)
            gas_cost = opportunity["estimated_gas_cost"] * random.uniform(0.1, 0.5)
            
            return {
                "success": False,
                "opportunity_id": opportunity["id"],
                "error": error,
                "gas_cost": gas_cost,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_real_trade(self, opportunity: Dict) -> Dict:
        """Execute a real trade on the blockchain"""
        network = opportunity["network"]
        web3 = self.web3_connections.get(network)
        
        if not web3:
            return {
                "success": False,
                "error": f"No Web3 connection for network {network}",
                "opportunity_id": opportunity["id"]
            }
        
        try:
            # Get wallet address
            wallet_address = self.wallet["address"]
            
            # Determine execution strategy
            use_flash_loan = self.config.get("execution", {}).get("use_flashloans", True)
            
            if use_flash_loan:
                # Execute with flash loan
                return self._execute_with_flash_loan(web3, opportunity, wallet_address)
            else:
                # Execute direct swap
                return self._execute_direct_swap(web3, opportunity, wallet_address)
                
        except Exception as e:
            logger.error(f"Error in real trade execution: {e}")
            return {
                "success": False,
                "error": str(e),
                "opportunity_id": opportunity["id"]
            }
    
    def _execute_with_flash_loan(self, web3: Web3, opportunity: Dict, wallet_address: str) -> Dict:
        """Execute arbitrage using a flash loan"""
        # In a real implementation, this would:
        # 1. Load the flash loan contract
        # 2. Prepare the transaction data
        # 3. Sign and send the transaction
        # 4. Wait for confirmation
        # 5. Parse the results
        
        # For now, return a mock result
        logger.warning("Flash loan execution not fully implemented, returning mock result")
        return self._execute_mock_trade(opportunity)
    
    def _execute_direct_swap(self, web3: Web3, opportunity: Dict, wallet_address: str) -> Dict:
        """Execute arbitrage using direct swaps"""
        # In a real implementation, this would:
        # 1. Load the router contracts
        # 2. Prepare the swap transactions
        # 3. Sign and send the transactions
        # 4. Wait for confirmations
        # 5. Parse the results
        
        # For now, return a mock result
        logger.warning("Direct swap execution not fully implemented, returning mock result")
        return self._execute_mock_trade(opportunity)
    
    def get_recent_trades(self, count: int = 10) -> List[Dict]:
        """
        Get recent trade history.
        
        Args:
            count: Number of recent trades to return
            
        Returns:
            List of recent trades
        """
        return [trade["result"] for trade in list(self.trade_history)[:count]]
    
    def get_trade_stats(self) -> Dict:
        """
        Get statistics about trade execution.
        
        Returns:
            Dictionary with trade statistics
        """
        if not self.trade_history:
            return {
                "total_trades": 0,
                "successful_trades": 0,
                "failed_trades": 0,
                "success_rate": 0,
                "total_profit": 0,
                "total_gas_spent": 0,
                "net_profit": 0,
                "average_execution_time": 0
            }
        
        # Calculate statistics
        total_trades = len(self.trade_history)
        successful_trades = sum(1 for trade in self.trade_history if trade["result"]["success"])
        failed_trades = total_trades - successful_trades
        success_rate = (successful_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_profit = sum(trade["result"].get("profit", 0) for trade in self.trade_history if trade["result"]["success"])
        total_gas_spent = sum(trade["result"].get("gas_cost", 0) for trade in self.trade_history)
        net_profit = total_profit - total_gas_spent
        
        execution_times = [trade["result"].get("execution_time", 0) for trade in self.trade_history]
        average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "failed_trades": failed_trades,
            "success_rate": success_rate,
            "total_profit": total_profit,
            "total_gas_spent": total_gas_spent,
            "net_profit": net_profit,
            "average_execution_time": average_execution_time
        }

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        "networks": ["ethereum", "arbitrum"],
        "execution": {
            "max_concurrent_trades": 3,
            "use_flashloans": True
        },
        "use_mock_execution": True
    }
    
    executor = TradeExecutor(config)
    
    # Example opportunity
    opportunity = {
        "id": "ARB-ethereum-123",
        "network": "ethereum",
        "token_a": "ETH",
        "token_b": "USDC",
        "buy_dex": "uniswap_v2",
        "sell_dex": "sushiswap",
        "buy_price": 3500.0,
        "sell_price": 3520.0,
        "price_diff_pct": 0.57,
        "trade_amount": 1.0,
        "estimated_gas_cost": 0.01,
        "potential_profit": 0.0057,
        "buy_router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "sell_router": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        "timestamp": datetime.now().isoformat()
    }
    
    # Execute trade
    result = executor.execute_trade(opportunity)
    
    # Print result
    print(f"Trade execution result: {'Success' if result['success'] else 'Failed'}")
    if result["success"]:
        print(f"Profit: {result['profit']} ETH")
        print(f"Gas cost: {result['gas_cost']} ETH")
        print(f"Net profit: {result['profit'] - result['gas_cost']} ETH")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Get trade stats
    stats = executor.get_trade_stats()
    print("\nTrade Statistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")
