from web3 import Web3, AsyncWeb3, AsyncHTTPProvider
from web3.middleware import geth_poa_middleware
from typing import Dict, Optional, Tuple, Callable, List
import logging
import os
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from websockets import connect
from web3.contract import Contract
from collections import defaultdict
import numpy as np
from datetime import datetime
import time
import json
import websockets
from asyncio import timeout

logger = logging.getLogger(__name__)

# Contract addresses for Polygon Amoy testnet (with proper EIP-55 checksums)
CONTRACT_ADDRESSES = {
    'WMATIC': Web3.to_checksum_address('0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270'),
    'USDC': Web3.to_checksum_address('0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'),
    'USDT': Web3.to_checksum_address('0xc2132D05D31c914a87C6611C10748AEb04B58e8F'),
    'QUICKSWAP_ROUTER': Web3.to_checksum_address('0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff'),
    'SUSHISWAP_ROUTER': Web3.to_checksum_address('0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'),
    'QUICKSWAP_FACTORY': Web3.to_checksum_address('0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32'),
    'SUSHISWAP_FACTORY': Web3.to_checksum_address('0xc35DADB65012eC5796536bD9864eD8773aBc74C4')
}

class Web3Connector:
    """Web3 connector for Amoy testnet with contract management and WebSocket support."""

    def __init__(self, rpc_url: Optional[str] = None, ws_url: Optional[str] = None):
        """Initialize basic attributes. Call connect() to establish connection."""
        # Initialize logger first
        self.logger = logging.getLogger(__name__)

        self.rpc_urls = [
            rpc_url or os.getenv('RPC_URL'),
            os.getenv('BACKUP_RPC_URL'),
            'https://rpc.ankr.com/polygon_amoy',
            'https://rpc-amoy.polygon.technology'
        ]
        self.ws_urls = [
            ws_url or os.getenv('WS_URL'),
            os.getenv('BACKUP_WS_URL')
        ]

        # Remove None values
        self.rpc_urls = [url for url in self.rpc_urls if url]
        self.ws_urls = [url for url in self.ws_urls if url]

        # Initialize state
        self.contracts = {}
        self.token_decimals = {}
        self.price_history = defaultdict(list)
        self.w3 = None

    @classmethod
    async def create(cls, rpc_url: Optional[str] = None, ws_url: Optional[str] = None):
        """Factory method to create and initialize a Web3Connector instance."""
        connector = cls(rpc_url, ws_url)
        await connector.connect()
        return connector

    async def connect(self):
        """Establish connection to the blockchain."""
        await self._initialize_web3()
        await self._initialize_contracts()

    async def _initialize_web3(self):
        """Initialize Web3 with failover support."""
        for rpc_url in self.rpc_urls:
            try:
                provider = AsyncHTTPProvider(rpc_url, request_kwargs={
                    'timeout': 30,
                    'headers': {
                        'User-Agent': 'arbitragex-v1'
                    }
                })
                self.w3 = AsyncWeb3(provider)

                # Test connection
                if await self.w3.is_connected():
                    self.logger.info(f"Connected to RPC: {rpc_url}")
                    return
            except Exception as e:
                self.logger.warning(f"Failed to connect to RPC {rpc_url}: {str(e)}")
                continue

        raise ConnectionError("Failed to connect to any RPC endpoint")

    async def _initialize_contracts(self):
        """Initialize contract instances with proper error handling."""
        try:
            # Initialize token contracts
            for token_name, address in CONTRACT_ADDRESSES.items():
                if 'ROUTER' in token_name:
                    self.contracts[token_name] = self.w3.eth.contract(
                        address=Web3.to_checksum_address(address),
                        abi=self._get_router_abi()
                    )
                elif 'FACTORY' in token_name:
                    self.contracts[token_name] = self.w3.eth.contract(
                        address=Web3.to_checksum_address(address),
                        abi=self._get_factory_abi()
                    )
                else:
                    self.contracts[token_name] = self.w3.eth.contract(
                        address=Web3.to_checksum_address(address),
                        abi=self._get_erc20_abi()
                    )

            self.logger.info("Contract initialization completed")
        except Exception as e:
            self.logger.error(f"Error initializing contracts: {str(e)}")
            raise

    def _get_erc20_abi(self) -> list:
        """Get complete ERC20 token ABI."""
        return [
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]

    def _get_router_abi(self) -> list:
        """Get complete QuickSwap/SushiSwap router ABI."""
        return [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsIn",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "factory",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]

    def _get_factory_abi(self) -> list:
        """Get complete DEX factory ABI."""
        return [
            {
                "constant": True,
                "inputs": [
                    {"internalType": "address", "name": "tokenA", "type": "address"},
                    {"internalType": "address", "name": "tokenB", "type": "address"}
                ],
                "name": "getPair",
                "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "name": "allPairs",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "allPairsLength",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "type": "function"
            }
        ]

    def _get_pair_abi(self) -> list:
        """Get complete DEX pair ABI."""
        return [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                    {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                    {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
                ],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token0",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token1",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "price0CumulativeLast",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "price1CumulativeLast",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "type": "function"
            }
        ]

    def _get_token_decimals(self, token_name: str) -> int:
        """Get token decimals with caching and fallback."""
        if token_name in self.token_decimals:
            return self.token_decimals[token_name]

        try:
            token_contract = self.contracts[token_name]
            decimals = token_contract.functions.decimals().call()
            self.token_decimals[token_name] = decimals
            logger.info(f"Got decimals for {token_name}: {decimals}")
            return decimals
        except Exception as e:
            logger.warning(f"Using default decimals (18) for {token_name}: {str(e)}")
            return 18  # Default to 18 decimals

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_token_price(self, router_address: str, token_in: str, token_out: str, amount_in: int) -> float:
        """Get token price with retries and failover."""
        try:
            router = self.contracts.get(router_address)
            if not router:
                router = self.w3.eth.contract(
                    address=Web3.to_checksum_address(router_address),
                    abi=self._get_router_abi()
                )
                self.contracts[router_address] = router

            path = [Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out)]
            amounts = await router.functions.getAmountsOut(amount_in, path).call()

            if not amounts or len(amounts) < 2:
                raise ValueError("Invalid amounts returned from router")

            return amounts[1]
        except Exception as e:
            self.logger.error(f"Error getting token price: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_pool_liquidity(self, factory_address: str, token_a: str, token_b: str) -> Tuple[int, int]:
        """Get pool liquidity with retries."""
        try:
            factory = self.w3.eth.contract(
                address=Web3.to_checksum_address(factory_address),
                abi=self._get_factory_abi()
            )

            pair_address = await factory.functions.getPair(
                Web3.to_checksum_address(token_a),
                Web3.to_checksum_address(token_b)
            ).call()

            if pair_address == '0x0000000000000000000000000000000000000000':
                return (0, 0)

            pair = self.w3.eth.contract(
                address=pair_address,
                abi=self._get_pair_abi()
            )

            reserves = await pair.functions.getReserves().call()
            token0 = await pair.functions.token0().call()

            if token0.lower() == token_a.lower():
                return (reserves[0], reserves[1])
            return (reserves[1], reserves[0])

        except Exception as e:
            self.logger.error(f"Error getting pool liquidity: {str(e)}")
            raise

    def validate_gas_price(self, gas_price: int) -> int:
        """Ensure gas price stays within Amoy testnet limits."""
        max_gwei = 50  # 50 Gwei cap for Amoy
        min_gwei = 1   # 1 Gwei minimum

        current_gwei = self.w3.from_wei(gas_price, 'gwei')
        if current_gwei > max_gwei:
            return self.w3.to_wei(max_gwei, 'gwei')
        if current_gwei < min_gwei:
            return self.w3.to_wei(min_gwei, 'gwei')
        return gas_price

    async def get_network_info(self) -> Dict:
        """Get current network information."""
        try:
            block = await self.w3.eth.block_number
            chain_id = await self.w3.eth.chain_id
            gas_price = await self.w3.eth.gas_price

            return {
                'block': block,
                'chain_id': chain_id,
                'gas_price': gas_price
            }
        except Exception as e:
            self.logger.error(f"Error getting network info: {str(e)}")
            raise

    def get_contract(self, name: str):
        """Get contract instance by name."""
        return self.contracts.get(name)

    async def price_stream(self, pair: str, callback: Callable):
        """Stream real-time price updates for a token pair with enhanced reconnection logic."""
        reconnect_delay = 1  # Initial reconnect delay in seconds
        max_reconnect_delay = 60  # Maximum reconnect delay

        while True:
            try:
                token_in, token_out = pair.split('/')
                router = self.contracts['QUICKSWAP_ROUTER']

                # Create event filter for Swap events
                event_filter = router.events.Swap.create_filter(fromBlock='latest')

                async with connect(self.ws_urls[0]) as ws:
                    # Set up heartbeat and connection monitoring
                    last_heartbeat = time.time()
                    last_price_update = time.time()
                    connection_healthy = True

                    # Reset reconnect delay on successful connection
                    reconnect_delay = 1

                    while connection_healthy:
                        try:
                            # Send heartbeat every 30 seconds
                            if time.time() - last_heartbeat > 30:
                                await ws.send(json.dumps({
                                    'type': 'ping',
                                    'timestamp': time.time()
                                }))
                                last_heartbeat = time.time()

                            # Check for price staleness (no updates in 2 minutes)
                            if time.time() - last_price_update > 120:
                                logger.warning(f"No price updates for {pair} in 2 minutes")
                                connection_healthy = False
                                break

                            # Check for new events
                            for event in event_filter.get_new_entries():
                                args = event['args']
                                price = args.amount1Out / args.amount0In if args.amount0In != 0 else 0

                                # Cross-validate price with other sources
                                validated_price = await self._validate_price(
                                    pair, price, [
                                        self._get_sushiswap_price,
                                        self._get_binance_price,
                                        self._get_coinbase_price
                                    ]
                                )

                                if validated_price:
                                    last_price_update = time.time()

                                    # Get block timestamp
                                    block = await self.w3.eth.get_block(event['blockNumber'])
                                    block_timestamp = block['timestamp']

                                    # Store validated price in history with full context
                                    price_entry = {
                                        'price': validated_price,
                                        'timestamp': block_timestamp,
                                        'block': event['blockNumber'],
                                        'sources': ['quickswap', 'sushiswap', 'binance', 'coinbase'],
                                        'gas_price': await self.w3.eth.gas_price,
                                        'validation_time': time.time() - last_price_update
                                    }

                                    self.price_history[pair].append(price_entry)

                                    # Trim history to last 1000 points
                                    if len(self.price_history[pair]) > 1000:
                                        self.price_history[pair] = self.price_history[pair][-1000:]

                                    # Call callback with validated price update
                                    await callback({
                                        'pair': pair,
                                        'data': price_entry,
                                        'market_state': {
                                            'volatility': self._calculate_volatility(pair),
                                            'liquidity': await self._get_pool_liquidity(pair),
                                            'network_state': await self._get_network_state()
                                        }
                                    })

                            await asyncio.sleep(0.1)

                        except websockets.ConnectionClosed:
                            logger.warning(f"WebSocket connection closed for {pair}")
                            connection_healthy = False
                            break
                        except Exception as e:
                            logger.error(f"Error in price stream loop for {pair}: {str(e)}")
                            if "Invalid JSON RPC response" in str(e):
                                connection_healthy = False
                                break
                            await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in price stream for {pair}: {str(e)}")

                # Implement exponential backoff for reconnection
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                continue

    async def _validate_price(self, pair: str, price: float, validators: List[Callable]) -> Optional[float]:
        """Validate price against multiple sources."""
        prices = [price]  # Include the original price
        weights = [1.0]   # Weight for the primary source

        for validator in validators:
            try:
                validated_price = await validator(pair)
                if validated_price > 0:
                    prices.append(validated_price)
                    weights.append(0.8)  # Lower weight for secondary sources
            except Exception as e:
                logger.warning(f"Price validation failed for {validator.__name__}: {str(e)}")

        if len(prices) < 2:
            logger.warning(f"Insufficient price sources for {pair}")
            return None

        # Calculate weighted average and check for outliers
        weighted_avg = np.average(prices, weights=weights)
        std_dev = np.std(prices)

        # Filter out prices that deviate more than 2 standard deviations
        valid_prices = [p for p in prices if abs(p - weighted_avg) <= 2 * std_dev]

        if len(valid_prices) < 2:
            logger.warning(f"Insufficient valid prices for {pair} after outlier removal")
            return None

        return np.mean(valid_prices)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_real_time_price(self, pair: str) -> Dict:
        """Get real-time price with enhanced error handling and validation."""
        try:
            token_a, token_b = pair.split('/')
            token_a_address = CONTRACT_ADDRESSES.get(token_a)
            token_b_address = CONTRACT_ADDRESSES.get(token_b)

            if not token_a_address or not token_b_address:
                raise ValueError(f"Invalid token pair: {pair}")

            # Verify contracts are deployed
            code_a = await self.w3.eth.get_code(Web3.to_checksum_address(token_a_address))
            code_b = await self.w3.eth.get_code(Web3.to_checksum_address(token_b_address))

            if len(code_a) <= 2:
                raise ValueError(f"Token {token_a} contract not deployed at {token_a_address}")
            if len(code_b) <= 2:
                raise ValueError(f"Token {token_b} contract not deployed at {token_b_address}")

            # Get prices from multiple sources with timeout and error handling
            prices = []

            try:
                quickswap_price = await self._get_price_async(
                    CONTRACT_ADDRESSES['QUICKSWAP_ROUTER'],
                    token_a_address,
                    token_b_address,
                    Web3.to_wei(1, 'ether')
                )
                if quickswap_price:
                    prices.append(quickswap_price)
            except Exception as e:
                self.logger.warning(f"QuickSwap price fetch failed: {str(e)}")

            try:
                sushiswap_price = await self._get_price_async(
                    CONTRACT_ADDRESSES['SUSHISWAP_ROUTER'],
                    token_a_address,
                    token_b_address,
                    Web3.to_wei(1, 'ether')
                )
                if sushiswap_price:
                    prices.append(sushiswap_price)
            except Exception as e:
                self.logger.warning(f"SushiSwap price fetch failed: {str(e)}")

            if not prices:
                raise ValueError("No valid prices returned from any source")

            avg_price = sum(prices) / len(prices)

            # Get additional market data
            try:
                liquidity = await self._get_pool_liquidity(pair)
            except Exception as e:
                self.logger.warning(f"Failed to get liquidity data: {str(e)}")
                liquidity = {"token_a": 0, "token_b": 0}

            return {
                'price': avg_price,
                'timestamp': datetime.now().isoformat(),
                'sources': len(prices),
                'volatility': self._calculate_volatility(pair),
                'liquidity': liquidity,
                'token_addresses': {
                    token_a: token_a_address,
                    token_b: token_b_address
                }
            }

        except Exception as e:
            self.logger.error(f"Error fetching real-time price for {pair}: {str(e)}")
            raise

    def _calculate_volatility(self, pair: str) -> float:
        """Calculate price volatility from historical data."""
        if not self.price_history[pair]:
            return 0.0

        prices = [p['price'] for p in self.price_history[pair][-100:]]  # Last 100 prices
        if len(prices) < 2:
            return 0.0

        returns = np.diff(np.log(prices))
        return np.std(returns) * np.sqrt(len(returns))

    async def _get_network_state(self) -> dict:
        """Get current network state including gas prices and congestion."""
        try:
            latest_block = await self.w3.eth.get_block('latest')
            pending_block = await self.w3.eth.get_block('pending')

            return {
                'block_number': latest_block['number'],
                'gas_price': await self.w3.eth.gas_price,
                'base_fee': latest_block.get('baseFeePerGas', 0),
                'network_congestion': pending_block['gasUsed'] / pending_block['gasLimit'],
                'timestamp': latest_block['timestamp']
            }
        except Exception as e:
            logger.error(f"Error getting network state: {str(e)}")
            return {}

    async def _get_pool_liquidity(self, pair: str) -> dict:
        """Get detailed pool liquidity information."""
        try:
            token_in, token_out = pair.split('/')

            # Get liquidity from both DEXs
            quickswap_liquidity = await self.get_pool_liquidity(
                self.contracts['QUICKSWAP_FACTORY'].address,
                self.contracts[token_in].address,
                self.contracts[token_out].address
            )

            sushiswap_liquidity = await self.get_pool_liquidity(
                self.contracts['SUSHISWAP_FACTORY'].address,
                self.contracts[token_in].address,
                self.contracts[token_out].address
            )

            return {
                'quickswap': {
                    'token_in': quickswap_liquidity[0],
                    'token_out': quickswap_liquidity[1],
                    'total': sum(quickswap_liquidity)
                },
                'sushiswap': {
                    'token_in': sushiswap_liquidity[0],
                    'token_out': sushiswap_liquidity[1],
                    'total': sum(sushiswap_liquidity)
                }
            }
        except Exception as e:
            logger.error(f"Error getting pool liquidity: {str(e)}")
            return {}

    async def _get_price_async(self, router_address: str, token_in: str, token_out: str, amount_in: int) -> float:
        """Get token price with retries and failover."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                router = self.contracts.get(router_address)
                if not router:
                    router = self.w3.eth.contract(
                        address=Web3.to_checksum_address(router_address),
                        abi=self._get_router_abi()
                    )
                    self.contracts[router_address] = router

                path = [Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out)]
                amounts = await router.functions.getAmountsOut(amount_in, path).call()

                if not amounts or len(amounts) < 2:
                    raise ValueError("Invalid amounts returned from router")

                return amounts[1]
            except Exception as e:
                self.logger.warning(f"Price fetch attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)  # Wait before retry
