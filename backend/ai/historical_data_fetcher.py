import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional, Union, Any
from web3 import Web3
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("historical_data_fetcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HistoricalDataFetcher")

class HistoricalDataFetcher:
    """
    Fetches and processes historical data from various sources for AI model training.
    Supports multiple DEXs, networks, and time periods.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the historical data fetcher.
        
        Args:
            data_dir: Directory to store fetched data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Default API endpoints and settings
        self.settings = {
            "ethereum": {
                "api_url": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
                "rpc_url": os.getenv("ETHEREUM_RPC_URL", ""),
                "dexes": ["uniswap", "sushiswap", "curve"]
            },
            "arbitrum": {
                "api_url": "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-minimal",
                "rpc_url": os.getenv("ARBITRUM_RPC_URL", ""),
                "dexes": ["uniswap", "sushiswap", "curve"]
            },
            "polygon": {
                "api_url": "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon",
                "rpc_url": os.getenv("POLYGON_RPC_URL", ""),
                "dexes": ["uniswap", "quickswap", "sushiswap"]
            },
            "optimism": {
                "api_url": "https://api.thegraph.com/subgraphs/name/ianlapham/optimism-post-regenesis",
                "rpc_url": os.getenv("OPTIMISM_RPC_URL", ""),
                "dexes": ["uniswap", "velodrome"]
            }
        }
        
        # Initialize web3 connections
        self.web3_connections = {}
        for network, config in self.settings.items():
            if config["rpc_url"]:
                try:
                    self.web3_connections[network] = Web3(Web3.HTTPProvider(config["rpc_url"]))
                    logger.info(f"Connected to {network} network")
                except Exception as e:
                    logger.error(f"Failed to connect to {network} network: {e}")
    
    def fetch_dex_swaps(self, 
                       network: str, 
                       dex: str, 
                       token_pair: Optional[str] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       limit: int = 1000) -> pd.DataFrame:
        """
        Fetch historical swap data from a specific DEX on a specific network.
        
        Args:
            network: Network to fetch data from (ethereum, arbitrum, etc.)
            dex: DEX to fetch data from (uniswap, sushiswap, etc.)
            token_pair: Optional token pair to filter by (e.g., "ETH-USDC")
            start_time: Start time for data fetching
            end_time: End time for data fetching
            limit: Maximum number of swaps to fetch
            
        Returns:
            DataFrame containing historical swap data
        """
        if network not in self.settings:
            logger.error(f"Network {network} not supported")
            return pd.DataFrame()
        
        if dex not in self.settings[network]["dexes"]:
            logger.error(f"DEX {dex} not supported on {network}")
            return pd.DataFrame()
        
        # Set default time range if not provided
        if start_time is None:
            start_time = datetime.now() - timedelta(days=30)
        if end_time is None:
            end_time = datetime.now()
        
        # Convert times to Unix timestamps
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        
        logger.info(f"Fetching {dex} swaps on {network} from {start_time} to {end_time}")
        
        # Construct GraphQL query based on DEX and network
        query = self._get_graphql_query(dex, network, token_pair, start_timestamp, end_timestamp, limit)
        
        try:
            response = requests.post(
                self.settings[network]["api_url"],
                json={"query": query}
            )
            
            if response.status_code != 200:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return pd.DataFrame()
            
            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL query returned errors: {data['errors']}")
                return pd.DataFrame()
            
            # Process the response based on DEX
            swaps = self._process_dex_response(dex, data)
            
            if not swaps:
                logger.warning(f"No swaps found for {dex} on {network}")
                return pd.DataFrame()
            
            df = pd.DataFrame(swaps)
            
            # Save to CSV
            output_file = self.data_dir / f"{network}_{dex}_swaps_{start_timestamp}_{end_timestamp}.csv"
            df.to_csv(output_file, index=False)
            logger.info(f"Saved {len(df)} swaps to {output_file}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {dex} swaps on {network}: {e}")
            return pd.DataFrame()
    
    def _get_graphql_query(self, 
                          dex: str, 
                          network: str, 
                          token_pair: Optional[str], 
                          start_timestamp: int, 
                          end_timestamp: int, 
                          limit: int) -> str:
        """Generate the appropriate GraphQL query for the specified DEX"""
        if dex == "uniswap":
            return """
            {
                swaps(first: %d, orderBy: timestamp, orderDirection: desc, 
                      where: {timestamp_gte: %d, timestamp_lte: %d}) {
                    id
                    timestamp
                    pool {
                        token0 {
                            symbol
                        }
                        token1 {
                            symbol
                        }
                        feeTier
                    }
                    amount0
                    amount1
                    amountUSD
                    sqrtPriceX96
                    tick
                }
            }
            """ % (limit, start_timestamp, end_timestamp)
        elif dex == "sushiswap":
            return """
            {
                swaps(first: %d, orderBy: timestamp, orderDirection: desc, 
                      where: {timestamp_gte: %d, timestamp_lte: %d}) {
                    id
                    timestamp
                    pair {
                        token0 {
                            symbol
                        }
                        token1 {
                            symbol
                        }
                    }
                    amount0In
                    amount1In
                    amount0Out
                    amount1Out
                    amountUSD
                }
            }
            """ % (limit, start_timestamp, end_timestamp)
        else:
            # Default query structure
            return """
            {
                swaps(first: %d, orderBy: timestamp, orderDirection: desc, 
                      where: {timestamp_gte: %d, timestamp_lte: %d}) {
                    id
                    timestamp
                    pair {
                        token0 {
                            symbol
                        }
                        token1 {
                            symbol
                        }
                    }
                    amount0In
                    amount1In
                    amount0Out
                    amount1Out
                }
            }
            """ % (limit, start_timestamp, end_timestamp)
    
    def _process_dex_response(self, dex: str, response_data: Dict) -> List[Dict]:
        """Process the API response based on the DEX format"""
        if dex == "uniswap":
            swaps = response_data.get("data", {}).get("swaps", [])
            return [
                {
                    "id": swap["id"],
                    "timestamp": int(swap["timestamp"]),
                    "datetime": datetime.fromtimestamp(int(swap["timestamp"])),
                    "token0": swap["pool"]["token0"]["symbol"],
                    "token1": swap["pool"]["token1"]["symbol"],
                    "amount0": float(swap["amount0"]),
                    "amount1": float(swap["amount1"]),
                    "amountUSD": float(swap["amountUSD"]),
                    "price": abs(float(swap["amount1"]) / float(swap["amount0"])) if float(swap["amount0"]) != 0 else 0,
                    "fee_tier": swap["pool"]["feeTier"],
                    "dex": dex
                }
                for swap in swaps
            ]
        elif dex == "sushiswap":
            swaps = response_data.get("data", {}).get("swaps", [])
            return [
                {
                    "id": swap["id"],
                    "timestamp": int(swap["timestamp"]),
                    "datetime": datetime.fromtimestamp(int(swap["timestamp"])),
                    "token0": swap["pair"]["token0"]["symbol"],
                    "token1": swap["pair"]["token1"]["symbol"],
                    "amount0": float(swap["amount0In"]) - float(swap["amount0Out"]),
                    "amount1": float(swap["amount1In"]) - float(swap["amount1Out"]),
                    "amountUSD": float(swap["amountUSD"]),
                    "price": abs((float(swap["amount1In"]) - float(swap["amount1Out"])) / 
                               (float(swap["amount0In"]) - float(swap["amount0Out"]))) 
                               if (float(swap["amount0In"]) - float(swap["amount0Out"])) != 0 else 0,
                    "dex": dex
                }
                for swap in swaps
            ]
        else:
            # Default processing
            swaps = response_data.get("data", {}).get("swaps", [])
            return [
                {
                    "id": swap["id"],
                    "timestamp": int(swap["timestamp"]),
                    "datetime": datetime.fromtimestamp(int(swap["timestamp"])),
                    "token0": swap["pair"]["token0"]["symbol"],
                    "token1": swap["pair"]["token1"]["symbol"],
                    "amount0": float(swap["amount0In"]) - float(swap["amount0Out"]),
                    "amount1": float(swap["amount1In"]) - float(swap["amount1Out"]),
                    "dex": dex
                }
                for swap in swaps
            ]
    
    def fetch_gas_prices(self, 
                        network: str, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        interval: str = "hour") -> pd.DataFrame:
        """
        Fetch historical gas prices for a specific network.
        
        Args:
            network: Network to fetch gas prices for
            start_time: Start time for data fetching
            end_time: End time for data fetching
            interval: Time interval for data points (hour, day)
            
        Returns:
            DataFrame containing historical gas prices
        """
        if network not in self.web3_connections:
            logger.error(f"No web3 connection for network {network}")
            return pd.DataFrame()
        
        # Set default time range if not provided
        if start_time is None:
            start_time = datetime.now() - timedelta(days=7)
        if end_time is None:
            end_time = datetime.now()
        
        logger.info(f"Fetching gas prices on {network} from {start_time} to {end_time}")
        
        # Determine time step based on interval
        if interval == "hour":
            time_step = timedelta(hours=1)
        elif interval == "day":
            time_step = timedelta(days=1)
        else:
            time_step = timedelta(hours=1)
        
        # Fetch gas prices at each time step
        gas_prices = []
        current_time = start_time
        
        while current_time <= end_time:
            try:
                # For historical data, we would need an archive node or external API
                # This is a simplified example using current gas price
                web3 = self.web3_connections[network]
                gas_price = web3.eth.gas_price
                
                gas_prices.append({
                    "timestamp": int(current_time.timestamp()),
                    "datetime": current_time,
                    "gas_price_wei": gas_price,
                    "gas_price_gwei": gas_price / 1e9,
                    "network": network
                })
                
                logger.debug(f"Fetched gas price for {current_time}: {gas_price / 1e9} gwei")
                
            except Exception as e:
                logger.error(f"Error fetching gas price for {current_time}: {e}")
            
            current_time += time_step
        
        if not gas_prices:
            logger.warning(f"No gas prices fetched for {network}")
            return pd.DataFrame()
        
        df = pd.DataFrame(gas_prices)
        
        # Save to CSV
        output_file = self.data_dir / f"{network}_gas_prices_{int(start_time.timestamp())}_{int(end_time.timestamp())}.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"Saved {len(df)} gas price records to {output_file}")
        
        return df
    
    def fetch_arbitrage_opportunities(self, 
                                    networks: List[str] = None, 
                                    dexes: List[str] = None,
                                    token_pairs: List[str] = None,
                                    start_time: Optional[datetime] = None,
                                    end_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        Identify historical arbitrage opportunities across multiple DEXs and networks.
        
        Args:
            networks: List of networks to analyze
            dexes: List of DEXs to analyze
            token_pairs: List of token pairs to analyze
            start_time: Start time for data fetching
            end_time: End time for data fetching
            
        Returns:
            DataFrame containing historical arbitrage opportunities
        """
        if networks is None:
            networks = list(self.settings.keys())
        
        if dexes is None:
            dexes = []
            for network in networks:
                dexes.extend(self.settings[network]["dexes"])
            dexes = list(set(dexes))  # Remove duplicates
        
        # Set default time range if not provided
        if start_time is None:
            start_time = datetime.now() - timedelta(days=30)
        if end_time is None:
            end_time = datetime.now()
        
        logger.info(f"Analyzing arbitrage opportunities across {networks} networks and {dexes} DEXs")
        
        # Fetch swap data for each network and DEX
        all_swaps = []
        
        for network in networks:
            for dex in self.settings[network]["dexes"]:
                if dex in dexes:
                    swaps_df = self.fetch_dex_swaps(
                        network=network,
                        dex=dex,
                        token_pair=None,  # Fetch all token pairs
                        start_time=start_time,
                        end_time=end_time
                    )
                    
                    if not swaps_df.empty:
                        swaps_df["network"] = network
                        all_swaps.append(swaps_df)
        
        if not all_swaps:
            logger.warning("No swap data fetched")
            return pd.DataFrame()
        
        # Combine all swap data
        combined_df = pd.concat(all_swaps, ignore_index=True)
        
        # Group by timestamp (rounded to nearest minute) and token pair
        combined_df["minute"] = combined_df["timestamp"].apply(lambda x: x - (x % 60))
        
        # Identify arbitrage opportunities
        arbitrage_opportunities = []
        
        for (minute, token0, token1), group in combined_df.groupby(["minute", "token0", "token1"]):
            if len(group) < 2:
                continue
            
            # Find min and max prices within the group
            min_price_row = group.loc[group["price"].idxmin()]
            max_price_row = group.loc[group["price"].idxmax()]
            
            # Skip if min and max are from the same DEX and network
            if (min_price_row["dex"] == max_price_row["dex"] and 
                min_price_row["network"] == max_price_row["network"]):
                continue
            
            # Calculate potential profit percentage
            price_diff_pct = (max_price_row["price"] - min_price_row["price"]) / min_price_row["price"] * 100
            
            # Only consider significant opportunities
            if price_diff_pct > 0.5:  # More than 0.5% difference
                arbitrage_opportunities.append({
                    "timestamp": minute,
                    "datetime": datetime.fromtimestamp(minute),
                    "token0": token0,
                    "token1": token1,
                    "buy_dex": min_price_row["dex"],
                    "buy_network": min_price_row["network"],
                    "buy_price": min_price_row["price"],
                    "sell_dex": max_price_row["dex"],
                    "sell_network": max_price_row["network"],
                    "sell_price": max_price_row["price"],
                    "price_diff_pct": price_diff_pct,
                    "potential_profit_usd": price_diff_pct * min_price_row["amountUSD"] / 100 if "amountUSD" in min_price_row else None
                })
        
        if not arbitrage_opportunities:
            logger.warning("No arbitrage opportunities identified")
            return pd.DataFrame()
        
        arb_df = pd.DataFrame(arbitrage_opportunities)
        
        # Save to CSV
        output_file = self.data_dir / f"arbitrage_opportunities_{int(start_time.timestamp())}_{int(end_time.timestamp())}.csv"
        arb_df.to_csv(output_file, index=False)
        logger.info(f"Saved {len(arb_df)} arbitrage opportunities to {output_file}")
        
        return arb_df
    
    def combine_datasets(self, 
                        arb_opportunities_df: pd.DataFrame, 
                        gas_prices_df: pd.DataFrame) -> pd.DataFrame:
        """
        Combine arbitrage opportunities with gas prices to create a comprehensive dataset.
        
        Args:
            arb_opportunities_df: DataFrame of arbitrage opportunities
            gas_prices_df: DataFrame of gas prices
            
        Returns:
            Combined DataFrame with arbitrage opportunities and corresponding gas prices
        """
        if arb_opportunities_df.empty or gas_prices_df.empty:
            logger.warning("Cannot combine empty datasets")
            return pd.DataFrame()
        
        # Ensure timestamp columns are of the same type
        arb_opportunities_df["timestamp"] = arb_opportunities_df["timestamp"].astype(int)
        gas_prices_df["timestamp"] = gas_prices_df["timestamp"].astype(int)
        
        # Find the closest gas price timestamp for each arbitrage opportunity
        def find_closest_gas_price(row):
            network = row["buy_network"]  # Use the buy network for gas price
            network_gas = gas_prices_df[gas_prices_df["network"] == network]
            
            if network_gas.empty:
                return None
            
            # Find closest timestamp
            closest_idx = (network_gas["timestamp"] - row["timestamp"]).abs().idxmin()
            return network_gas.loc[closest_idx, "gas_price_gwei"]
        
        arb_opportunities_df["gas_price_gwei"] = arb_opportunities_df.apply(find_closest_gas_price, axis=1)
        
        # Calculate estimated gas cost and net profit
        arb_opportunities_df["estimated_gas_cost_usd"] = arb_opportunities_df.apply(
            lambda row: row["gas_price_gwei"] * 200000 / 1e9 * 2000 if pd.notnull(row["gas_price_gwei"]) else None, 
            axis=1  # Assuming 200k gas per transaction and $2000 ETH price
        )
        
        arb_opportunities_df["net_profit_usd"] = arb_opportunities_df.apply(
            lambda row: row["potential_profit_usd"] - row["estimated_gas_cost_usd"] 
                       if pd.notnull(row["potential_profit_usd"]) and pd.notnull(row["estimated_gas_cost_usd"]) 
                       else None,
            axis=1
        )
        
        arb_opportunities_df["profitable"] = arb_opportunities_df["net_profit_usd"] > 0
        
        # Save combined dataset
        output_file = self.data_dir / f"combined_arbitrage_dataset_{int(datetime.now().timestamp())}.csv"
        arb_opportunities_df.to_csv(output_file, index=False)
        logger.info(f"Saved combined dataset with {len(arb_opportunities_df)} records to {output_file}")
        
        return arb_opportunities_df

# Example usage
if __name__ == "__main__":
    fetcher = HistoricalDataFetcher()
    
    # Fetch historical swap data
    swaps_df = fetcher.fetch_dex_swaps(
        network="ethereum",
        dex="uniswap",
        start_time=datetime.now() - timedelta(days=7),
        end_time=datetime.now()
    )
    
    # Fetch gas prices
    gas_df = fetcher.fetch_gas_prices(
        network="ethereum",
        start_time=datetime.now() - timedelta(days=7),
        end_time=datetime.now()
    )
    
    # Identify arbitrage opportunities
    arb_df = fetcher.fetch_arbitrage_opportunities(
        networks=["ethereum", "arbitrum"],
        dexes=["uniswap", "sushiswap"],
        start_time=datetime.now() - timedelta(days=7),
        end_time=datetime.now()
    )
    
    # Combine datasets
    if not arb_df.empty and not gas_df.empty:
        combined_df = fetcher.combine_datasets(arb_df, gas_df)
        print(f"Found {combined_df['profitable'].sum()} profitable arbitrage opportunities out of {len(combined_df)}") 