"""
Web3 Connector for ArbitrageX

This module provides Web3 connectivity to interact with the Hardhat fork
for the Strategy Optimizer and other AI modules.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from web3 import Web3
from web3.middleware import geth_poa_middleware
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web3_connector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Web3Connector")

class Web3Connector:
    """
    Provides Web3 connectivity to interact with the Hardhat fork.
    """
    
    def __init__(self, fork_config_path: Optional[str] = None):
        """
        Initialize the Web3 connector with the given fork configuration.
        
        Args:
            fork_config_path: Path to the fork configuration file
        """
        self.web3 = None
        self.contracts = {}
        self.fork_config = self._load_fork_config(fork_config_path)
        self._initialize_web3()
        self._load_contract_addresses()
        self._initialize_contracts()
        logger.info("Web3Connector initialized with real mainnet fork data")
    
    def _load_fork_config(self, config_path: Optional[str] = None) -> Dict:
        """
        Load fork configuration from a JSON file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "mode": "mainnet_fork",
            "fork_url": "http://localhost:8546",
            "fork_block_number": "latest",
            "networks": ["ethereum"],
            "tokens": {
                "ethereum": ["WETH", "USDC", "DAI", "USDT", "WBTC", "LINK"]
            },
            "dexes": {
                "ethereum": ["uniswap_v3", "sushiswap", "curve", "balancer"]
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
                    logger.info(f"Fork configuration loaded from {config_path}")
            except Exception as e:
                logger.error(f"Error loading fork config: {e}")
        
        return default_config
    
    def _initialize_web3(self) -> None:
        """
        Initialize Web3 connection to the Hardhat fork.
        """
        try:
            fork_url = self.fork_config.get("fork_url", "http://localhost:8546")
            logger.info(f"Connecting to Hardhat fork at {fork_url}")
            
            self.web3 = Web3(Web3.HTTPProvider(fork_url))
            
            # Add middleware for POA chains if needed
            self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check connection using a more reliable method
            try:
                if hasattr(self.web3, 'is_connected') and callable(self.web3.is_connected):
                    connected = self.web3.is_connected()
                else:
                    # Fallback: Try to get the block number as a connection test
                    self.web3.eth.block_number
                    connected = True
                
                if connected:
                    block_number = self.web3.eth.block_number
                    logger.info(f"Connected to Hardhat fork at block {block_number}")
                else:
                    logger.error(f"Failed to connect to Hardhat fork at {fork_url}")
            except Exception as conn_error:
                logger.error(f"Connection test failed: {conn_error}")
                # Continue anyway as the web3 instance might still be usable
                logger.warning("Proceeding with Web3 initialization despite connection test failure")
        except Exception as e:
            logger.error(f"Error initializing Web3: {e}")
            raise e  # Re-raise to ensure we don't proceed with a failed connection
    
    def _load_contract_addresses(self) -> None:
        """
        Load deployed contract addresses from the backend config.
        """
        try:
            # Path to the contract addresses file
            addresses_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config",
                "contractAddresses.json"
            )
            
            if os.path.exists(addresses_file):
                with open(addresses_file, 'r') as f:
                    self.contract_addresses = json.load(f)
                logger.info(f"Loaded contract addresses from {addresses_file}")
            else:
                logger.warning(f"Contract addresses file not found at {addresses_file}")
                self.contract_addresses = {}
        except Exception as e:
            logger.error(f"Error loading contract addresses: {e}")
            self.contract_addresses = {}
    
    def _initialize_contracts(self) -> None:
        """
        Initialize contract instances using the loaded addresses.
        """
        try:
            # Load ABIs for the contracts
            abi_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "artifacts",
                "contracts"
            )
            
            # Initialize ArbitrageExecutor contract
            if 'arbitrageExecutor' in self.contract_addresses:
                arbitrage_executor_address = self.contract_addresses['arbitrageExecutor']
                arbitrage_executor_abi_path = os.path.join(
                    abi_dir, 
                    "ArbitrageExecutor.sol", 
                    "ArbitrageExecutor.json"
                )
                
                if os.path.exists(arbitrage_executor_abi_path):
                    with open(arbitrage_executor_abi_path, 'r') as f:
                        arbitrage_executor_data = json.load(f)
                        arbitrage_executor_abi = arbitrage_executor_data.get('abi')
                        
                    self.contracts['arbitrageExecutor'] = self.web3.eth.contract(
                        address=arbitrage_executor_address,
                        abi=arbitrage_executor_abi
                    )
                    logger.info(f"Initialized ArbitrageExecutor contract at {arbitrage_executor_address}")
            
            # Initialize FlashLoanService contract
            if 'flashLoanService' in self.contract_addresses:
                flash_loan_service_address = self.contract_addresses['flashLoanService']
                flash_loan_service_abi_path = os.path.join(
                    abi_dir, 
                    "FlashLoanService.sol", 
                    "FlashLoanService.json"
                )
                
                if os.path.exists(flash_loan_service_abi_path):
                    with open(flash_loan_service_abi_path, 'r') as f:
                        flash_loan_service_data = json.load(f)
                        flash_loan_service_abi = flash_loan_service_data.get('abi')
                        
                    self.contracts['flashLoanService'] = self.web3.eth.contract(
                        address=flash_loan_service_address,
                        abi=flash_loan_service_abi
                    )
                    logger.info(f"Initialized FlashLoanService contract at {flash_loan_service_address}")
        except Exception as e:
            logger.error(f"Error initializing contracts: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if Web3 is connected to the Hardhat fork.
        
        Returns:
            True if connected, False otherwise
        """
        if self.web3 is None:
            return False
            
        try:
            if hasattr(self.web3, 'is_connected') and callable(self.web3.is_connected):
                return self.web3.is_connected()
            else:
                # Fallback: Try to get the block number as a connection test
                self.web3.eth.block_number
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_token_balance(self, token_address: str, wallet_address: str) -> int:
        """
        Get the balance of a token for a wallet.
        
        Args:
            token_address: Address of the token
            wallet_address: Address of the wallet
            
        Returns:
            Token balance in wei
        """
        if not self.is_connected():
            logger.error("Web3 not connected")
            return 0
        
        try:
            # ERC20 ABI for balanceOf
            abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }
            ]
            
            token_contract = self.web3.eth.contract(address=token_address, abi=abi)
            balance = token_contract.functions.balanceOf(wallet_address).call()
            return balance
        except Exception as e:
            logger.error(f"Error getting token balance: {e}")
            return 0
    
    def get_eth_balance(self, wallet_address: str) -> int:
        """
        Get the ETH balance of a wallet.
        
        Args:
            wallet_address: Address of the wallet
            
        Returns:
            ETH balance in wei
        """
        if not self.is_connected():
            logger.error("Web3 not connected")
            return 0
        
        try:
            balance = self.web3.eth.get_balance(wallet_address)
            return balance
        except Exception as e:
            logger.error(f"Error getting ETH balance: {e}")
            return 0
    
    def get_uniswap_pool_info(self, token0: str, token1: str) -> Dict:
        """
        Get information about a Uniswap V3 pool.
        
        Args:
            token0: Address of the first token
            token1: Address of the second token
            
        Returns:
            Dictionary with pool information
        """
        if not self.is_connected():
            logger.error("Web3 not connected")
            return {}
        
        try:
            # Get the Uniswap V3 Factory address
            uniswap_v3_factory = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
            
            # ABI for the getPool function
            factory_abi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "tokenA", "type": "address"},
                        {"internalType": "address", "name": "tokenB", "type": "address"},
                        {"internalType": "uint24", "name": "fee", "type": "uint24"}
                    ],
                    "name": "getPool",
                    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # ABI for the pool contract
            pool_abi = [
                {
                    "inputs": [],
                    "name": "liquidity",
                    "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "slot0",
                    "outputs": [
                        {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
                        {"internalType": "int24", "name": "tick", "type": "int24"},
                        {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
                        {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
                        {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
                        {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
                        {"internalType": "bool", "name": "unlocked", "type": "bool"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # Create factory contract instance
            factory_contract = self.web3.eth.contract(address=uniswap_v3_factory, abi=factory_abi)
            
            # Get pool address for the token pair with 0.3% fee
            pool_address = factory_contract.functions.getPool(token0, token1, 3000).call()
            
            if pool_address == "0x0000000000000000000000000000000000000000":
                logger.warning(f"No Uniswap V3 pool found for {token0}/{token1}")
                return {}
            
            # Create pool contract instance
            pool_contract = self.web3.eth.contract(address=pool_address, abi=pool_abi)
            
            # Get liquidity and slot0 data
            liquidity = pool_contract.functions.liquidity().call()
            slot0 = pool_contract.functions.slot0().call()
            
            return {
                "address": pool_address,
                "liquidity": liquidity,
                "sqrtPriceX96": slot0[0],
                "tick": slot0[1]
            }
        except Exception as e:
            logger.error(f"Error getting Uniswap pool info: {e}")
            return {}
    
    def get_aave_flash_loan_availability(self, token_address: str) -> int:
        """
        Get the available amount for flash loans from Aave.
        
        Args:
            token_address: Address of the token
            
        Returns:
            Available amount in wei
        """
        if not self.is_connected():
            logger.error("Web3 not connected")
            return 0
        
        try:
            # Aave V3 Pool address
            aave_pool_address = self.contract_addresses.get('aavePool', "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9")
            
            # ABI for getReserveData function
            aave_pool_abi = [
                {
                    "inputs": [{"internalType": "address", "name": "asset", "type": "address"}],
                    "name": "getReserveData",
                    "outputs": [
                        {"internalType": "uint256", "name": "configuration", "type": "uint256"},
                        {"internalType": "uint128", "name": "liquidityIndex", "type": "uint128"},
                        {"internalType": "uint128", "name": "variableBorrowIndex", "type": "uint128"},
                        {"internalType": "uint128", "name": "currentLiquidityRate", "type": "uint128"},
                        {"internalType": "uint128", "name": "currentVariableBorrowRate", "type": "uint128"},
                        {"internalType": "uint128", "name": "currentStableBorrowRate", "type": "uint128"},
                        {"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"},
                        {"internalType": "address", "name": "aTokenAddress", "type": "address"},
                        {"internalType": "address", "name": "stableDebtTokenAddress", "type": "address"},
                        {"internalType": "address", "name": "variableDebtTokenAddress", "type": "address"},
                        {"internalType": "address", "name": "interestRateStrategyAddress", "type": "address"},
                        {"internalType": "uint8", "name": "id", "type": "uint8"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # Create Aave Pool contract instance
            aave_pool_contract = self.web3.eth.contract(address=aave_pool_address, abi=aave_pool_abi)
            
            # Get reserve data
            reserve_data = aave_pool_contract.functions.getReserveData(token_address).call()
            
            # Get aToken address
            atoken_address = reserve_data[7]
            
            # Get aToken balance (available liquidity)
            atoken_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"
                }
            ]
            
            atoken_contract = self.web3.eth.contract(address=atoken_address, abi=atoken_abi)
            available_liquidity = atoken_contract.functions.totalSupply().call()
            
            return available_liquidity
        except Exception as e:
            logger.error(f"Error getting Aave flash loan availability: {e}")
            return 0
    
    def execute_arbitrage(self, opportunity: Dict) -> Dict:
        """
        Execute an arbitrage opportunity on the Hardhat fork.
        
        Args:
            opportunity: Dictionary with opportunity details
            
        Returns:
            Dictionary with execution results
        """
        if not self.is_connected():
            logger.error("Web3 not connected")
            return {"success": False, "error": "Web3 not connected"}
        
        try:
            # Get the ArbitrageExecutor contract
            if 'arbitrageExecutor' not in self.contracts:
                return {"success": False, "error": "ArbitrageExecutor contract not initialized"}
            
            arbitrage_executor = self.contracts['arbitrageExecutor']
            
            # Get the first account to use as the sender
            sender = self.web3.eth.accounts[0]
            
            # Extract opportunity details
            source_token = opportunity.get('token_in')
            target_token = opportunity.get('token_out')
            amount = opportunity.get('amount')
            source_dex = opportunity.get('source_dex', 'uniswap_v3')
            target_dex = opportunity.get('target_dex', 'sushiswap')
            
            # Convert amount to Wei if it's in ETH
            if isinstance(amount, (int, float)):
                amount = self.web3.to_wei(amount, 'ether')
            
            # Estimate gas for the transaction
            gas_estimate = arbitrage_executor.functions.executeArbitrage(
                source_token,
                target_token,
                amount,
                source_dex,
                target_dex
            ).estimate_gas({'from': sender})
            
            # Execute the transaction
            tx_hash = arbitrage_executor.functions.executeArbitrage(
                source_token,
                target_token,
                amount,
                source_dex,
                target_dex
            ).transact({'from': sender, 'gas': gas_estimate})
            
            # Wait for the transaction to be mined
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Check if the transaction was successful
            if tx_receipt['status'] == 1:
                return {
                    "success": True,
                    "tx_hash": tx_hash.hex(),
                    "gas_used": tx_receipt['gasUsed'],
                    "block_number": tx_receipt['blockNumber']
                }
            else:
                return {
                    "success": False,
                    "tx_hash": tx_hash.hex(),
                    "error": "Transaction failed"
                }
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            return {"success": False, "error": str(e)} 