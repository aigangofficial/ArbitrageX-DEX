"""
Network Scanner Module for ArbitrageX

This module is responsible for scanning blockchain networks to identify
potential arbitrage opportunities across different DEXes and liquidity pools.
"""

import logging
import json
import time
import uuid
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import asyncio
import random
from web3 import Web3
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("network_scanner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("NetworkScanner")

class NetworkScanner:
    """
    Scanner for identifying arbitrage opportunities across blockchain networks.
    Monitors DEXes, AMMs, and lending protocols for price discrepancies.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the network scanner.
        
        Args:
            config: Bot configuration dictionary
        """
        logger.info("Initializing Network Scanner")
        self.config = config
        self.networks = config.get("networks", ["ethereum"])
        self.default_network = config.get("default_network", "ethereum")
        
        # Initialize web3 connections for each network
        self.web3_connections = self._init_web3_connections()
        
        # Load DEX configurations
        self.dex_configs = self._load_dex_configs()
        
        # Token price cache to reduce API calls
        self.price_cache = {}
        self.price_cache_expiry = 60  # seconds
        self.last_cache_cleanup = time.time()
        
        # Track last scan time for each network
        self.last_scan_times = {network: 0 for network in self.networks}
        
        # Opportunity ID counter
        self.opportunity_counter = 0
        
        logger.info(f"Network Scanner initialized for networks: {', '.join(self.networks)}")
    
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
            for network in self.networks:
                connections[network] = None
                logger.info(f"Using mock connection for {network}")
            return connections
        
        # Initialize real connections
        for network in self.networks:
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
    
    def _load_dex_configs(self) -> Dict:
        """Load DEX configurations from file"""
        try:
            dex_config_path = "backend/bot/dex_configs.json"
            with open(dex_config_path, 'r') as f:
                dex_configs = json.load(f)
            logger.info(f"Loaded DEX configurations from {dex_config_path}")
            return dex_configs
        except Exception as e:
            logger.warning(f"Error loading DEX configs: {e}")
            # Return default/mock DEX configurations
            return {
                "ethereum": {
                    "uniswap_v2": {
                        "router_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
                        "factory_address": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
                    },
                    "uniswap_v3": {
                        "router_address": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                        "factory_address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
                    },
                    "sushiswap": {
                        "router_address": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
                        "factory_address": "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
                    }
                },
                "arbitrum": {
                    "uniswap_v3": {
                        "router_address": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                        "factory_address": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
                    },
                    "sushiswap": {
                        "router_address": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
                        "factory_address": "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
                    }
                },
                # Add more networks as needed
            }
    
    def scan_networks(self) -> List[Dict]:
        """
        Scan all configured networks for arbitrage opportunities.
        
        Returns:
            List of potential arbitrage opportunities
        """
        all_opportunities = []
        
        for network in self.networks:
            # Check if we should scan this network based on scan interval
            current_time = time.time()
            network_scan_interval = self.config.get("network_scan_intervals", {}).get(network, self.config.get("scan_interval", 5))
            
            if current_time - self.last_scan_times.get(network, 0) < network_scan_interval:
                continue
            
            # Update last scan time
            self.last_scan_times[network] = current_time
            
            try:
                logger.info(f"Scanning {network} for arbitrage opportunities")
                opportunities = self._scan_network(network)
                
                if opportunities:
                    logger.info(f"Found {len(opportunities)} potential opportunities on {network}")
                    all_opportunities.extend(opportunities)
                else:
                    logger.debug(f"No opportunities found on {network}")
                    
            except Exception as e:
                logger.error(f"Error scanning {network}: {e}")
        
        # Clean up price cache periodically
        if time.time() - self.last_cache_cleanup > 300:  # Every 5 minutes
            self._cleanup_price_cache()
            self.last_cache_cleanup = time.time()
        
        return all_opportunities
    
    def _scan_network(self, network: str) -> List[Dict]:
        """
        Scan a specific network for arbitrage opportunities.
        
        Args:
            network: Network name to scan
            
        Returns:
            List of potential arbitrage opportunities on the network
        """
        opportunities = []
        
        # In a real implementation, this would:
        # 1. Query on-chain data for token prices across different DEXes
        # 2. Compare prices to identify arbitrage opportunities
        # 3. Calculate potential profit after gas and fees
        # 4. Return viable opportunities
        
        # For demonstration, we'll generate mock opportunities
        if self.config.get("use_mock_data", True):
            mock_count = random.randint(0, 3)  # Random number of opportunities
            for _ in range(mock_count):
                opportunity = self._generate_mock_opportunity(network)
                opportunities.append(opportunity)
            
            return opportunities
        
        # Real implementation would include:
        # 1. Get DEX configurations for this network
        network_dexes = self.dex_configs.get(network, {})
        if not network_dexes:
            logger.warning(f"No DEX configurations found for {network}")
            return []
        
        # 2. Get token pairs to monitor
        token_pairs = self._get_token_pairs(network)
        
        # 3. Check each token pair across different DEXes
        for token_pair in token_pairs:
            token_a, token_b = token_pair
            
            # Get prices from different DEXes
            dex_prices = self._get_prices_across_dexes(network, token_a, token_b, network_dexes)
            
            # Find arbitrage opportunities
            arb_opportunities = self._find_arbitrage_in_prices(network, token_a, token_b, dex_prices)
            opportunities.extend(arb_opportunities)
        
        return opportunities
    
    def _get_token_pairs(self, network: str) -> List[tuple]:
        """Get token pairs to monitor for the specified network"""
        # In production, this would load from a configuration file or database
        # For now, return some common pairs
        common_pairs = [
            ("ETH", "USDC"),
            ("ETH", "USDT"),
            ("WBTC", "ETH"),
            ("ETH", "DAI"),
            ("LINK", "ETH"),
            ("UNI", "ETH"),
            ("AAVE", "ETH"),
            ("COMP", "ETH"),
            ("SNX", "ETH"),
            ("YFI", "ETH")
        ]
        
        # Filter or add network-specific pairs
        if network == "polygon":
            common_pairs.extend([("MATIC", "USDC"), ("MATIC", "ETH")])
        elif network == "arbitrum":
            common_pairs.extend([("ARB", "ETH"), ("ARB", "USDC")])
        elif network == "bsc":
            common_pairs = [
                ("BNB", "BUSD"),
                ("BNB", "USDT"),
                ("CAKE", "BNB"),
                ("ETH", "BNB"),
                ("BTCB", "BNB")
            ]
        
        return common_pairs
    
    def _get_prices_across_dexes(self, network: str, token_a: str, token_b: str, network_dexes: Dict) -> Dict:
        """Get prices for a token pair across different DEXes"""
        # In a real implementation, this would query on-chain data
        # For demonstration, generate mock prices
        dex_prices = {}
        
        for dex_name, dex_config in network_dexes.items():
            # Base price with some randomness
            base_price = self._get_base_price(token_a, token_b)
            if base_price is None:
                continue
                
            # Add some variation between DEXes (up to 2%)
            variation = random.uniform(-0.02, 0.02)
            price = base_price * (1 + variation)
            
            dex_prices[dex_name] = {
                "price": price,
                "liquidity": random.uniform(10000, 1000000),  # Mock liquidity
                "router_address": dex_config.get("router_address")
            }
        
        return dex_prices
    
    def _get_base_price(self, token_a: str, token_b: str) -> Optional[float]:
        """Get base price for a token pair from cache or API"""
        pair_key = f"{token_a}_{token_b}"
        
        # Check cache first
        if pair_key in self.price_cache:
            cache_entry = self.price_cache[pair_key]
            if time.time() - cache_entry["timestamp"] < self.price_cache_expiry:
                return cache_entry["price"]
        
        # In production, this would call a price API
        # For demonstration, use mock prices
        mock_prices = {
            "ETH_USDC": 3500.0,
            "ETH_USDT": 3500.0,
            "WBTC_ETH": 15.0,  # 1 BTC = 15 ETH
            "ETH_DAI": 3500.0,
            "LINK_ETH": 0.01,  # 1 LINK = 0.01 ETH
            "UNI_ETH": 0.005,
            "AAVE_ETH": 0.05,
            "COMP_ETH": 0.03,
            "SNX_ETH": 0.002,
            "YFI_ETH": 0.3,
            "MATIC_USDC": 1.5,
            "MATIC_ETH": 0.0004,
            "ARB_ETH": 0.001,
            "ARB_USDC": 3.5,
            "BNB_BUSD": 300.0,
            "BNB_USDT": 300.0,
            "CAKE_BNB": 0.01,
            "ETH_BNB": 0.08,
            "BTCB_BNB": 3.8
        }
        
        # Try both directions
        price = mock_prices.get(pair_key)
        if price is None:
            reverse_key = f"{token_b}_{token_a}"
            reverse_price = mock_prices.get(reverse_key)
            if reverse_price is not None:
                price = 1 / reverse_price
        
        # Update cache
        if price is not None:
            self.price_cache[pair_key] = {
                "price": price,
                "timestamp": time.time()
            }
        
        return price
    
    def _find_arbitrage_in_prices(self, network: str, token_a: str, token_b: str, dex_prices: Dict) -> List[Dict]:
        """Find arbitrage opportunities in the prices across DEXes"""
        opportunities = []
        
        # Need at least 2 DEXes to compare
        if len(dex_prices) < 2:
            return []
        
        # Find the best buy and sell prices
        best_buy_dex = min(dex_prices.items(), key=lambda x: x[1]["price"])
        best_sell_dex = max(dex_prices.items(), key=lambda x: x[1]["price"])
        
        buy_price = best_buy_dex[1]["price"]
        sell_price = best_sell_dex[1]["price"]
        buy_dex = best_buy_dex[0]
        sell_dex = best_sell_dex[0]
        
        # Calculate price difference percentage
        price_diff_pct = ((sell_price - buy_price) / buy_price) * 100
        
        # Check if the difference is significant enough (e.g., > 0.5%)
        min_profit_threshold_pct = self.config.get("min_profit_threshold_pct", 0.5)
        
        if price_diff_pct > min_profit_threshold_pct and buy_dex != sell_dex:
            # Calculate potential profit
            trade_amount = min(
                best_buy_dex[1]["liquidity"] * 0.1,  # Use at most 10% of available liquidity
                best_sell_dex[1]["liquidity"] * 0.1,
                self.config.get("risk_management", {}).get("max_trade_size", 10.0)  # Max trade size in ETH
            )
            
            # Estimate gas cost (in ETH)
            estimated_gas_cost = self._estimate_gas_cost(network)
            
            # Calculate potential profit
            potential_profit = (trade_amount / buy_price) * (sell_price - buy_price) - estimated_gas_cost
            
            # Only include if profitable after gas
            if potential_profit > 0:
                opportunity_id = f"ARB-{network}-{self.opportunity_counter}"
                self.opportunity_counter += 1
                
                opportunity = {
                    "id": opportunity_id,
                    "network": network,
                    "token_a": token_a,
                    "token_b": token_b,
                    "buy_dex": buy_dex,
                    "sell_dex": sell_dex,
                    "buy_price": buy_price,
                    "sell_price": sell_price,
                    "price_diff_pct": price_diff_pct,
                    "trade_amount": trade_amount,
                    "estimated_gas_cost": estimated_gas_cost,
                    "potential_profit": potential_profit,
                    "buy_router": dex_prices[buy_dex]["router_address"],
                    "sell_router": dex_prices[sell_dex]["router_address"],
                    "timestamp": datetime.now().isoformat(),
                    "confidence": random.uniform(0.7, 0.95)  # Mock confidence score
                }
                
                opportunities.append(opportunity)
                logger.info(f"Found arbitrage opportunity: {token_a}/{token_b} on {network}, "
                           f"buy on {buy_dex}, sell on {sell_dex}, "
                           f"potential profit: {potential_profit:.6f} ETH")
        
        return opportunities
    
    def _estimate_gas_cost(self, network: str) -> float:
        """Estimate gas cost for an arbitrage transaction on the specified network"""
        # In production, this would query the network for current gas prices
        # and estimate based on historical transaction data
        
        # For demonstration, use mock values
        network_gas_costs = {
            "ethereum": random.uniform(0.005, 0.02),  # Higher gas on Ethereum
            "arbitrum": random.uniform(0.0005, 0.002),
            "polygon": random.uniform(0.0001, 0.0005),
            "optimism": random.uniform(0.0003, 0.001),
            "bsc": random.uniform(0.0001, 0.0003)
        }
        
        return network_gas_costs.get(network, 0.01)  # Default to 0.01 ETH
    
    def _generate_mock_opportunity(self, network: str) -> Dict:
        """Generate a mock arbitrage opportunity for testing"""
        # Token pairs to choose from
        token_pairs = [
            ("ETH", "USDC"),
            ("ETH", "USDT"),
            ("WBTC", "ETH"),
            ("ETH", "DAI"),
            ("LINK", "ETH"),
            ("UNI", "ETH")
        ]
        
        # DEXes to choose from
        dexes = {
            "ethereum": ["uniswap_v2", "uniswap_v3", "sushiswap", "curve"],
            "arbitrum": ["uniswap_v3", "sushiswap", "balancer"],
            "polygon": ["quickswap", "sushiswap", "uniswap_v3"],
            "optimism": ["uniswap_v3", "velodrome", "curve"],
            "bsc": ["pancakeswap", "biswap", "apeswap"]
        }
        
        network_dexes = dexes.get(network, ["dex1", "dex2", "dex3"])
        
        # Select random token pair and DEXes
        token_a, token_b = random.choice(token_pairs)
        buy_dex, sell_dex = random.sample(network_dexes, 2)
        
        # Generate random prices with a spread
        base_price = random.uniform(0.001, 5000)
        price_diff_pct = random.uniform(0.5, 3.0)
        buy_price = base_price
        sell_price = buy_price * (1 + price_diff_pct/100)
        
        # Calculate trade details
        trade_amount = random.uniform(0.1, 5.0)  # ETH
        estimated_gas_cost = self._estimate_gas_cost(network)
        potential_profit = (trade_amount / buy_price) * (sell_price - buy_price) - estimated_gas_cost
        
        # Generate unique ID
        opportunity_id = f"ARB-{network}-{self.opportunity_counter}"
        self.opportunity_counter += 1
        
        # Create opportunity object
        opportunity = {
            "id": opportunity_id,
            "network": network,
            "token_a": token_a,
            "token_b": token_b,
            "buy_dex": buy_dex,
            "sell_dex": sell_dex,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "price_diff_pct": price_diff_pct,
            "trade_amount": trade_amount,
            "estimated_gas_cost": estimated_gas_cost,
            "potential_profit": potential_profit,
            "buy_router": f"0x{random.randint(0, 0xffffffff):08x}",  # Mock address
            "sell_router": f"0x{random.randint(0, 0xffffffff):08x}",  # Mock address
            "timestamp": datetime.now().isoformat(),
            "confidence": random.uniform(0.7, 0.95)  # Mock confidence score
        }
        
        return opportunity
    
    def _cleanup_price_cache(self):
        """Clean up expired entries in the price cache"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.price_cache.items():
            if current_time - entry["timestamp"] > self.price_cache_expiry:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.price_cache[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired entries from price cache")

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        "networks": ["ethereum", "arbitrum", "polygon"],
        "default_network": "ethereum",
        "scan_interval": 5,
        "use_mock_data": True,
        "min_profit_threshold_pct": 0.5
    }
    
    scanner = NetworkScanner(config)
    
    # Scan for opportunities
    opportunities = scanner.scan_networks()
    
    # Print results
    for opp in opportunities:
        print(f"Opportunity: {opp['token_a']}/{opp['token_b']} on {opp['network']}")
        print(f"  Buy on {opp['buy_dex']} at {opp['buy_price']}")
        print(f"  Sell on {opp['sell_dex']} at {opp['sell_price']}")
        print(f"  Potential profit: {opp['potential_profit']:.6f} ETH")
        print()
