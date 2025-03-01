#!/usr/bin/env python3
"""
ArbitrageX MEV Protection

This module provides protection against MEV (Miner Extractable Value) attacks by using
Flashbots or private transactions to avoid front-running by MEV bots.
"""

import os
import sys
import json
import time
import logging
import requests
import random
from typing import Dict, Any, Optional, List, Tuple
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MEVProtection")

class MEVProtection:
    """
    Provides protection against MEV attacks using Flashbots or private transactions.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the MEV protection.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.web3 = None
        self.flashbots_enabled = self.config.get("flashbots_enabled", True)
        self.private_tx_enabled = self.config.get("private_tx_enabled", True)
        self.pending_tx_analysis_enabled = self.config.get("pending_tx_analysis_enabled", True)
        
        # Initialize Web3 connection
        self._initialize_web3()
        
        # Track MEV attack attempts for analysis
        self.mev_attack_attempts = []
        
        logger.info(f"MEV Protection initialized (flashbots={self.flashbots_enabled}, "
                   f"private_tx={self.private_tx_enabled}, "
                   f"pending_analysis={self.pending_tx_analysis_enabled})")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "flashbots_enabled": True,
            "private_tx_enabled": True,
            "pending_tx_analysis_enabled": True,
            "flashbots_relay_url": "https://relay.flashbots.net",
            "flashbots_auth_key": os.environ.get("FLASHBOTS_AUTH_KEY", ""),
            "private_tx_providers": {
                "ethereum": "https://api.blocknative.com/v1",
                "arbitrum": "https://arbitrum-api.blocknative.com/v1",
                "polygon": "https://polygon-api.blocknative.com/v1"
            },
            "private_tx_api_keys": {
                "blocknative": os.environ.get("BLOCKNATIVE_API_KEY", "")
            },
            "gas_price_multipliers": {
                "normal": 1.0,
                "fast": 1.2,
                "urgent": 1.5
            },
            "max_gas_price_gwei": {
                "ethereum": 300,
                "arbitrum": 1.0,
                "polygon": 500
            },
            "mev_risk_thresholds": {
                "low": {
                    "competing_txs": 1,
                    "gas_multiplier": 1.1
                },
                "medium": {
                    "competing_txs": 3,
                    "gas_multiplier": 1.3
                },
                "high": {
                    "competing_txs": 5,
                    "gas_multiplier": 1.5
                }
            },
            "rpc_urls": {
                "ethereum": os.environ.get("ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/your-api-key"),
                "arbitrum": os.environ.get("ARBITRUM_RPC_URL", "https://arb-mainnet.g.alchemy.com/v2/your-api-key"),
                "polygon": os.environ.get("POLYGON_RPC_URL", "https://polygon-mainnet.g.alchemy.com/v2/your-api-key")
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                    # Merge user config with default config
                    for key, value in user_config.items():
                        if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
                logger.info(f"Loaded MEV protection configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        return default_config
    
    def _initialize_web3(self) -> None:
        """
        Initialize Web3 connection.
        """
        try:
            # Use Ethereum mainnet by default
            rpc_url = self.config["rpc_urls"]["ethereum"]
            self.web3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if self.web3.is_connected():
                logger.info(f"Connected to Ethereum node: {rpc_url}")
            else:
                logger.error(f"Failed to connect to Ethereum node: {rpc_url}")
        except Exception as e:
            logger.error(f"Error initializing Web3: {e}")
    
    def create_flashbots_bundle(self, signed_transaction: str, block_number: int) -> Dict[str, Any]:
        """
        Create a Flashbots bundle for the transaction.
        
        Args:
            signed_transaction: Signed transaction data
            block_number: Target block number for the bundle
            
        Returns:
            Flashbots bundle
        """
        logger.info(f"Creating Flashbots bundle for block {block_number}")
        
        try:
            # Convert signed transaction to the format expected by Flashbots
            tx_params = {
                "signed_transaction": signed_transaction
            }
            
            # Create bundle with just this transaction
            bundle = {
                "txs": [tx_params],
                "block_number": block_number,
                "min_timestamp": 0,  # No minimum timestamp
                "max_timestamp": 0,  # No maximum timestamp
                "revertingTxHashes": []  # No reverting transactions
            }
            
            return bundle
        except Exception as e:
            logger.error(f"Error creating Flashbots bundle: {e}")
            return {"error": str(e)}
    
    def analyze_pending_transactions(self, network: str, token_pair: str) -> Dict[str, Any]:
        """
        Analyze pending transactions to detect potential MEV risks.
        
        Args:
            network: Network to analyze
            token_pair: Token pair to analyze
            
        Returns:
            Dictionary with MEV risk analysis
        """
        if not self.pending_tx_analysis_enabled:
            logger.info("Pending transaction analysis is disabled")
            return {"mev_risk": "unknown", "reason": "Pending transaction analysis is disabled"}
        
        logger.info(f"Analyzing pending transactions for {token_pair} on {network}")
        
        try:
            # In a real implementation, this would connect to a mempool API
            # or use a local node to get pending transactions
            # For now, we'll simulate the analysis
            
            # Simulate different risk levels based on network and token pair
            if network == "ethereum":
                # Ethereum has higher MEV activity
                if token_pair in ["WETH-USDC", "WETH-DAI", "WBTC-WETH"]:
                    # High-volume pairs have higher MEV risk
                    risk_level = "high"
                    competing_txs = 5
                else:
                    risk_level = "medium"
                    competing_txs = 2
            elif network == "arbitrum":
                # Arbitrum has moderate MEV activity
                if token_pair in ["WETH-USDC", "WETH-DAI"]:
                    risk_level = "medium"
                    competing_txs = 3
                else:
                    risk_level = "low"
                    competing_txs = 1
            else:
                # Other networks have lower MEV activity
                risk_level = "low"
                competing_txs = 0
            
            # Simulate gas prices of competing transactions
            competing_gas_prices = []
            if competing_txs > 0:
                base_gas_price = self.get_current_gas_price(network)
                for i in range(competing_txs):
                    # Competitors often bid 5-20% higher
                    competing_gas_prices.append(base_gas_price * (1.05 + (i * 0.05)))
            
            return {
                "mev_risk": risk_level,
                "competing_transactions": competing_txs,
                "competing_gas_prices": competing_gas_prices,
                "recommended_action": "flashbots" if risk_level == "high" else "private_tx" if risk_level == "medium" else "normal"
            }
        except Exception as e:
            logger.error(f"Error analyzing pending transactions: {e}")
            return {"mev_risk": "unknown", "reason": f"Error: {str(e)}"}
    
    def get_current_gas_price(self, network: str) -> float:
        """
        Get current gas price for the specified network.
        
        Args:
            network: Network to get gas price for
            
        Returns:
            Current gas price in Gwei
        """
        try:
            if network == "ethereum":
                # Use Web3 to get current gas price
                if self.web3 and self.web3.is_connected():
                    gas_price_wei = self.web3.eth.gas_price
                    gas_price_gwei = gas_price_wei / 1e9
                    return gas_price_gwei
            
            # For other networks or if Web3 is not available, use default values
            default_gas_prices = {
                "ethereum": 50.0,  # 50 Gwei
                "arbitrum": 0.1,   # 0.1 Gwei
                "polygon": 100.0   # 100 Gwei
            }
            
            return default_gas_prices.get(network, 50.0)
        except Exception as e:
            logger.error(f"Error getting gas price: {e}")
            return 50.0  # Default to 50 Gwei
    
    def get_eip1559_fee_data(self, network: str) -> Dict[str, Any]:
        """
        Get EIP-1559 fee data (base fee, priority fee) for the specified network.
        
        Args:
            network: Network to get fee data for
            
        Returns:
            Dictionary with base fee and priority fee
        """
        try:
            if network == "ethereum" and self.web3 and self.web3.is_connected():
                # Get latest block to extract base fee
                latest_block = self.web3.eth.get_block('latest')
                base_fee_wei = latest_block.get('baseFeePerGas', 0)
                base_fee_gwei = base_fee_wei / 1e9
                
                # Get max priority fee (tip)
                max_priority_fee_wei = self.web3.eth.max_priority_fee
                max_priority_fee_gwei = max_priority_fee_wei / 1e9
                
                return {
                    "base_fee_gwei": base_fee_gwei,
                    "max_priority_fee_gwei": max_priority_fee_gwei,
                    "supports_eip1559": True
                }
            
            # For networks that don't support EIP-1559 or if Web3 is not available
            return {
                "base_fee_gwei": 0,
                "max_priority_fee_gwei": 0,
                "supports_eip1559": False
            }
        except Exception as e:
            logger.error(f"Error getting EIP-1559 fee data: {e}")
            return {
                "base_fee_gwei": 0,
                "max_priority_fee_gwei": 0,
                "supports_eip1559": False,
                "error": str(e)
            }
    
    def estimate_network_congestion(self, network: str) -> str:
        """
        Estimate network congestion level based on recent gas prices and pending transactions.
        
        Args:
            network: Network to estimate congestion for
            
        Returns:
            Congestion level: "low", "medium", or "high"
        """
        try:
            if network == "ethereum" and self.web3 and self.web3.is_connected():
                # Get current gas price
                current_gas_price = self.get_current_gas_price(network)
                
                # Get EIP-1559 fee data
                fee_data = self.get_eip1559_fee_data(network)
                base_fee = fee_data.get("base_fee_gwei", 0)
                
                # Estimate congestion based on gas price and base fee
                if base_fee > 100:  # Very high base fee
                    return "high"
                elif base_fee > 50:  # Moderate base fee
                    return "medium"
                else:
                    return "low"
            
            # For other networks, use simpler heuristics
            if network == "arbitrum":
                return "low"  # Arbitrum typically has low congestion
            elif network == "polygon":
                # Polygon can have varying congestion
                current_gas_price = self.get_current_gas_price(network)
                if current_gas_price > 200:
                    return "high"
                elif current_gas_price > 100:
                    return "medium"
                else:
                    return "low"
            
            # Default to medium congestion if unknown
            return "medium"
        except Exception as e:
            logger.error(f"Error estimating network congestion: {e}")
            return "medium"  # Default to medium congestion
    
    def calculate_optimal_gas_price(self, network: str, token_pair: str, expected_profit: float) -> Dict[str, Any]:
        """
        Calculate optimal gas price to outbid MEV bots while maintaining profitability.
        
        Args:
            network: Network to calculate gas price for
            token_pair: Token pair to calculate gas price for
            expected_profit: Expected profit from the trade in USD
            
        Returns:
            Dictionary with optimal gas price and related information
        """
        logger.info(f"Calculating optimal gas price for {token_pair} on {network}")
        
        try:
            # Get current gas price
            current_gas_price = self.get_current_gas_price(network)
            
            # Get EIP-1559 fee data
            fee_data = self.get_eip1559_fee_data(network)
            supports_eip1559 = fee_data.get("supports_eip1559", False)
            base_fee_gwei = fee_data.get("base_fee_gwei", 0)
            max_priority_fee_gwei = fee_data.get("max_priority_fee_gwei", 0)
            
            # Estimate network congestion
            congestion = self.estimate_network_congestion(network)
            
            # Analyze pending transactions to detect MEV risks
            mev_analysis = self.analyze_pending_transactions(network, token_pair)
            mev_risk = mev_analysis.get("mev_risk", "unknown")
            
            # Get gas price multiplier based on MEV risk and congestion
            if mev_risk == "high" or congestion == "high":
                multiplier = self.config["gas_price_multipliers"]["urgent"]
            elif mev_risk == "medium" or congestion == "medium":
                multiplier = self.config["gas_price_multipliers"]["fast"]
            else:
                multiplier = self.config["gas_price_multipliers"]["normal"]
            
            # Calculate optimal gas price based on whether EIP-1559 is supported
            if supports_eip1559:
                # For EIP-1559, we adjust the priority fee (tip)
                priority_fee_multiplier = multiplier
                optimal_priority_fee_gwei = max_priority_fee_gwei * priority_fee_multiplier
                
                # Calculate max fee per gas (base fee + priority fee with buffer)
                base_fee_buffer = 1.2  # 20% buffer for base fee fluctuations
                max_fee_per_gas_gwei = (base_fee_gwei * base_fee_buffer) + optimal_priority_fee_gwei
                
                # Use max fee per gas as the optimal gas price
                optimal_gas_price = max_fee_per_gas_gwei
            else:
                # For legacy transactions, adjust the gas price directly
                optimal_gas_price = current_gas_price * multiplier
            
            # Ensure gas price doesn't exceed maximum
            max_gas_price = self.config["max_gas_price_gwei"].get(network, 300)
            if optimal_gas_price > max_gas_price:
                optimal_gas_price = max_gas_price
                logger.warning(f"Gas price capped at maximum: {max_gas_price} Gwei")
            
            # Estimate gas cost
            gas_limit = 500000  # Example gas limit for a complex arbitrage transaction
            gas_cost_eth = (optimal_gas_price * 1e-9) * gas_limit
            
            # Convert gas cost to USD (simplified)
            eth_price_usd = 3000  # Example ETH price in USD
            if network == "polygon":
                eth_price_usd = 1  # Use MATIC price instead
            elif network == "arbitrum":
                # Arbitrum uses ETH but has lower gas costs
                pass
            
            gas_cost_usd = gas_cost_eth * eth_price_usd
            
            # Check if trade is still profitable with this gas price
            is_profitable = expected_profit > gas_cost_usd
            profit_margin = expected_profit - gas_cost_usd
            
            # Prepare result
            result = {
                "current_gas_price_gwei": current_gas_price,
                "optimal_gas_price_gwei": optimal_gas_price,
                "gas_limit": gas_limit,
                "gas_cost_eth": gas_cost_eth,
                "gas_cost_usd": gas_cost_usd,
                "is_profitable": is_profitable,
                "profit_margin_usd": profit_margin,
                "mev_risk": mev_risk,
                "network_congestion": congestion,
                "recommended_submission_method": mev_analysis.get("recommended_action", "normal")
            }
            
            # Add EIP-1559 specific data if supported
            if supports_eip1559:
                result.update({
                    "supports_eip1559": True,
                    "base_fee_gwei": base_fee_gwei,
                    "optimal_priority_fee_gwei": optimal_priority_fee_gwei,
                    "max_fee_per_gas_gwei": max_fee_per_gas_gwei
                })
            
            return result
        except Exception as e:
            logger.error(f"Error calculating optimal gas price: {e}")
            return {
                "error": str(e),
                "current_gas_price_gwei": self.get_current_gas_price(network),
                "is_profitable": False
            }
    
    def submit_via_flashbots(self, network: str, signed_transaction: str) -> Dict[str, Any]:
        """
        Submit a transaction via Flashbots to avoid front-running.
        
        Args:
            network: Network to submit transaction on
            signed_transaction: Signed transaction data
            
        Returns:
            Dictionary with submission result
        """
        if not self.flashbots_enabled:
            logger.warning("Flashbots submission is disabled")
            return {"success": False, "reason": "Flashbots submission is disabled"}
        
        if network != "ethereum":
            logger.warning(f"Flashbots is only available on Ethereum, not {network}")
            return {"success": False, "reason": f"Flashbots is not available on {network}"}
        
        logger.info("Submitting transaction via Flashbots")
        
        try:
            # Get current block number
            current_block = self.web3.eth.block_number if self.web3 else 0
            target_block = current_block + 1
            
            # Create Flashbots bundle
            bundle = self.create_flashbots_bundle(signed_transaction, target_block)
            
            # In a real implementation, this would use the Flashbots API
            # to submit the transaction bundle
            flashbots_relay_url = self.config["flashbots_relay_url"]
            flashbots_auth_key = self.config["flashbots_auth_key"]
            
            # Log the bundle submission attempt
            logger.info(f"Submitting bundle to Flashbots relay: {flashbots_relay_url} for block {target_block}")
            
            # Simulate successful submission
            bundle_hash = "0x" + "".join([f"{i}" for i in range(64)])
            
            # Log successful submission
            logger.info(f"Bundle submitted successfully: {bundle_hash}")
            
            return {
                "success": True,
                "bundle_hash": bundle_hash,
                "target_block": target_block,
                "submission_time": time.time(),
                "bundle": bundle
            }
        except Exception as e:
            logger.error(f"Error submitting via Flashbots: {e}")
            return {"success": False, "reason": str(e)}
    
    def submit_private_transaction(self, network: str, signed_transaction: str) -> Dict[str, Any]:
        """
        Submit a transaction via a private transaction service to avoid front-running.
        
        Args:
            network: Network to submit transaction on
            signed_transaction: Signed transaction data
            
        Returns:
            Dictionary with submission result
        """
        if not self.private_tx_enabled:
            logger.warning("Private transaction submission is disabled")
            return {"success": False, "reason": "Private transaction submission is disabled"}
        
        logger.info(f"Submitting private transaction on {network}")
        
        try:
            # In a real implementation, this would use a private transaction service
            # like Blocknative's Mempool API to submit the transaction
            # For now, we'll simulate the submission
            
            # Simulate successful submission
            return {
                "success": True,
                "transaction_hash": "0x" + "".join([f"{i}" for i in range(64)]),
                "submission_time": time.time()
            }
        except Exception as e:
            logger.error(f"Error submitting private transaction: {e}")
            return {"success": False, "reason": str(e)}
    
    def log_mev_attack_attempt(self, network: str, token_pair: str, attack_type: str, details: Dict[str, Any]) -> None:
        """
        Log an MEV attack attempt for later analysis.
        
        Args:
            network: Network where the attack was detected
            token_pair: Token pair targeted by the attack
            attack_type: Type of attack (e.g., "front-running", "sandwich", "back-running")
            details: Additional details about the attack
        """
        timestamp = time.time()
        
        attack_record = {
            "timestamp": timestamp,
            "network": network,
            "token_pair": token_pair,
            "attack_type": attack_type,
            "details": details
        }
        
        self.mev_attack_attempts.append(attack_record)
        
        # Log the attack attempt
        logger.warning(f"MEV attack attempt detected: {attack_type} on {token_pair} ({network})")
        
        # In a production environment, we would also store this in a database
        # for long-term analysis and strategy improvement
        try:
            # Example: Write to a local JSON file
            log_file = "mev_attack_log.json"
            
            # Read existing logs if file exists
            existing_logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r") as f:
                        existing_logs = json.load(f)
                except Exception as e:
                    logger.error(f"Error reading MEV attack log file: {e}")
            
            # Append new log
            existing_logs.append(attack_record)
            
            # Write updated logs
            with open(log_file, "w") as f:
                json.dump(existing_logs, f, indent=2)
        except Exception as e:
            logger.error(f"Error logging MEV attack attempt: {e}")
    
    def detect_front_running(self, network: str, token_pair: str, transaction_hash: str) -> Dict[str, Any]:
        """
        Detect if a transaction was front-run by MEV bots.
        
        Args:
            network: Network to check
            token_pair: Token pair to check
            transaction_hash: Hash of the transaction to check
            
        Returns:
            Dictionary with front-running detection results
        """
        logger.info(f"Detecting front-running for transaction {transaction_hash} on {network}")
        
        try:
            # In a real implementation, this would analyze the transaction and surrounding blocks
            # to detect if it was front-run by MEV bots
            # For now, we'll simulate the detection
            
            # Simulate different detection results based on network and token pair
            if network == "ethereum":
                # Ethereum has higher MEV activity
                if token_pair in ["WETH-USDC", "WETH-DAI", "WBTC-WETH"]:
                    # High-volume pairs have higher front-running risk
                    was_front_run = random.random() < 0.3  # 30% chance of front-running
                else:
                    was_front_run = random.random() < 0.1  # 10% chance of front-running
            elif network == "arbitrum":
                # Arbitrum has moderate MEV activity
                was_front_run = random.random() < 0.05  # 5% chance of front-running
            else:
                # Other networks have lower MEV activity
                was_front_run = random.random() < 0.02  # 2% chance of front-running
            
            # If front-running was detected, log it
            if was_front_run:
                front_runner_tx = "0x" + "".join([f"{i}" for i in range(64)])
                profit_loss_usd = random.uniform(5, 50)
                
                attack_details = {
                    "front_runner_tx": front_runner_tx,
                    "profit_loss_usd": profit_loss_usd,
                    "original_tx": transaction_hash
                }
                
                self.log_mev_attack_attempt(network, token_pair, "front-running", attack_details)
                
                return {
                    "was_front_run": True,
                    "front_runner_tx": front_runner_tx,
                    "profit_loss_usd": profit_loss_usd,
                    "recommendation": "Use Flashbots or increase gas price"
                }
            else:
                return {
                    "was_front_run": False
                }
        except Exception as e:
            logger.error(f"Error detecting front-running: {e}")
            return {"error": str(e)}
    
    def analyze_mev_attack_patterns(self) -> Dict[str, Any]:
        """
        Analyze MEV attack patterns to improve protection strategies.
        
        Returns:
            Dictionary with analysis results
        """
        if not self.mev_attack_attempts:
            return {"message": "No MEV attack attempts recorded yet"}
        
        try:
            # Count attacks by network
            networks = {}
            for attack in self.mev_attack_attempts:
                network = attack["network"]
                if network not in networks:
                    networks[network] = 0
                networks[network] += 1
            
            # Count attacks by token pair
            token_pairs = {}
            for attack in self.mev_attack_attempts:
                token_pair = attack["token_pair"]
                if token_pair not in token_pairs:
                    token_pairs[token_pair] = 0
                token_pairs[token_pair] += 1
            
            # Count attacks by type
            attack_types = {}
            for attack in self.mev_attack_attempts:
                attack_type = attack["attack_type"]
                if attack_type not in attack_types:
                    attack_types[attack_type] = 0
                attack_types[attack_type] += 1
            
            # Calculate average profit loss
            total_profit_loss = 0
            profit_loss_count = 0
            for attack in self.mev_attack_attempts:
                if "details" in attack and "profit_loss_usd" in attack["details"]:
                    total_profit_loss += attack["details"]["profit_loss_usd"]
                    profit_loss_count += 1
            
            avg_profit_loss = total_profit_loss / profit_loss_count if profit_loss_count > 0 else 0
            
            # Identify most vulnerable networks and token pairs
            most_vulnerable_network = max(networks.items(), key=lambda x: x[1])[0] if networks else "none"
            most_vulnerable_token_pair = max(token_pairs.items(), key=lambda x: x[1])[0] if token_pairs else "none"
            
            return {
                "total_attacks": len(self.mev_attack_attempts),
                "attacks_by_network": networks,
                "attacks_by_token_pair": token_pairs,
                "attacks_by_type": attack_types,
                "avg_profit_loss_usd": avg_profit_loss,
                "most_vulnerable_network": most_vulnerable_network,
                "most_vulnerable_token_pair": most_vulnerable_token_pair,
                "recommendation": "Use Flashbots for transactions on " + most_vulnerable_network + " involving " + most_vulnerable_token_pair
            }
        except Exception as e:
            logger.error(f"Error analyzing MEV attack patterns: {e}")
            return {"error": str(e)}
    
    def protect_transaction(self, network: str, token_pair: str, expected_profit: float, 
                           signed_transaction: str) -> Dict[str, Any]:
        """
        Protect a transaction from MEV attacks by using the appropriate submission method.
        
        Args:
            network: Network to submit transaction on
            token_pair: Token pair being traded
            expected_profit: Expected profit from the trade in USD
            signed_transaction: Signed transaction data
            
        Returns:
            Dictionary with protection result
        """
        logger.info(f"Protecting transaction for {token_pair} on {network}")
        
        try:
            # Calculate optimal gas price
            gas_price_info = self.calculate_optimal_gas_price(network, token_pair, expected_profit)
            
            # Check if trade is still profitable with optimal gas price
            if not gas_price_info.get("is_profitable", False):
                # Log this as a potential MEV vulnerability (trade not profitable due to gas costs)
                attack_details = {
                    "expected_profit": expected_profit,
                    "gas_cost_usd": gas_price_info.get("gas_cost_usd", 0),
                    "reason": "Gas costs exceed expected profit"
                }
                self.log_mev_attack_attempt(network, token_pair, "gas-outbidding", attack_details)
                
                return {
                    "success": False,
                    "reason": f"Trade not profitable with optimal gas price. "
                             f"Expected profit: ${expected_profit}, "
                             f"Gas cost: ${gas_price_info.get('gas_cost_usd', 0)}",
                    "gas_price_info": gas_price_info
                }
            
            # Determine submission method based on MEV risk
            submission_method = gas_price_info.get("recommended_submission_method", "normal")
            
            # Submit transaction using appropriate method
            if submission_method == "flashbots" and network == "ethereum":
                result = self.submit_via_flashbots(network, signed_transaction)
                result["submission_method"] = "flashbots"
            elif submission_method == "private_tx":
                result = self.submit_private_transaction(network, signed_transaction)
                result["submission_method"] = "private_tx"
            else:
                # For normal submission, we would just return the optimal gas price
                # In a real implementation, the caller would use this to submit the transaction
                result = {
                    "success": True,
                    "submission_method": "normal",
                    "optimal_gas_price_gwei": gas_price_info.get("optimal_gas_price_gwei", 0)
                }
            
            # Add gas price info to result
            result["gas_price_info"] = gas_price_info
            
            # If submission was successful, monitor for front-running
            if result.get("success", False):
                # In a real implementation, we would return a transaction hash
                # and then monitor it for front-running
                tx_hash = result.get("transaction_hash", result.get("bundle_hash", "0x0"))
                
                # Add monitoring info to result
                result["monitoring"] = {
                    "tx_hash": tx_hash,
                    "monitoring_enabled": True,
                    "check_front_running_url": f"/api/check-front-running?tx={tx_hash}&network={network}"
                }
            
            return result
        except Exception as e:
            logger.error(f"Error protecting transaction: {e}")
            return {"success": False, "reason": str(e)}

# Example usage
if __name__ == "__main__":
    # Create MEV protection
    mev_protection = MEVProtection()
    
    # Example transaction
    network = "ethereum"
    token_pair = "WETH-USDC"
    expected_profit = 50.0  # USD
    signed_transaction = "0x..."  # Example signed transaction
    
    # Protect transaction
    result = mev_protection.protect_transaction(network, token_pair, expected_profit, signed_transaction)
    
    # Print result
    print(json.dumps(result, indent=2)) 