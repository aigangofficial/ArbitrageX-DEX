"""
Competitor Tracker Module for ArbitrageX

This module is responsible for tracking and analyzing competitor arbitrage bots,
identifying their patterns, and developing counter-strategies including decoy
transactions to mislead them.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple, Set, Any
from web3 import Web3
from eth_typing import HexStr
import numpy as np
import random
from datetime import datetime, timedelta
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("competitor_tracker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CompetitorTracker")

class CompetitorPattern:
    """
    Represents a pattern of behavior for a competitor arbitrage bot.
    Tracks gas usage, token pairs, timing, and success metrics.
    """
    
    def __init__(self):
        self.gas_patterns: List[int] = []
        self.token_pairs: Dict[str, int] = {}
        self.timing_patterns: List[float] = []
        self.success_rate: float = 0.0
        self.last_seen: datetime = datetime.now()
        self.total_transactions: int = 0
        self.profitable_transactions: int = 0
        self.gas_price_history: List[int] = []
        self.gas_limit_history: List[int] = []
        self.transaction_hashes: List[str] = []
        self.estimated_profit: float = 0.0
        self.preferred_dexes: Dict[str, int] = {}
        self.active_hours: Dict[int, int] = {i: 0 for i in range(24)}
        self.active_days: Dict[int, int] = {i: 0 for i in range(7)}
        self.first_seen: datetime = datetime.now()
        
    def update_active_time(self, timestamp: datetime):
        """Update active time patterns"""
        self.active_hours[timestamp.hour] += 1
        self.active_days[timestamp.weekday()] += 1
        
    def get_peak_hours(self) -> List[int]:
        """Get the peak hours of activity"""
        if not any(self.active_hours.values()):
            return []
        
        avg = sum(self.active_hours.values()) / len(self.active_hours)
        return [hour for hour, count in self.active_hours.items() 
                if count > avg * 1.5]
                
    def get_preferred_tokens(self, limit: int = 5) -> List[str]:
        """Get the most frequently traded token pairs"""
        sorted_pairs = sorted(self.token_pairs.items(), 
                             key=lambda x: x[1], reverse=True)
        return [pair[0] for pair in sorted_pairs[:limit]]
        
    def get_avg_gas_price(self) -> float:
        """Get average gas price used by this competitor"""
        if not self.gas_price_history:
            return 0
        return sum(self.gas_price_history) / len(self.gas_price_history)
        
    def get_activity_score(self) -> float:
        """Calculate activity score based on recency and frequency"""
        time_since_last = (datetime.now() - self.last_seen).total_seconds()
        time_factor = max(0, 1 - (time_since_last / (24 * 3600)))
        
        # Frequency factor based on transactions per day
        days_active = max(1, (datetime.now() - self.first_seen).days)
        freq_factor = min(1, self.total_transactions / (days_active * 10))
        
        return (time_factor * 0.7) + (freq_factor * 0.3)

class CompetitorTracker:
    """
    Tracks and analyzes competitor arbitrage bots, identifying their patterns,
    and developing counter-strategies.
    """
    
    def __init__(self, config: Dict = None, config_path: str = "config/competitor_analysis.json"):
        """
        Initialize the competitor tracker.
        
        Args:
            config: Optional configuration dictionary
            config_path: Path to the competitor analysis configuration file
        """
        logger.info("Initializing Competitor Tracker")
        
        # Load configuration
        self.config = config if config else self._load_config(config_path)
        
        # Initialize competitor tracking
        self.competitors: Dict[str, CompetitorPattern] = {}
        self.known_addresses: Dict[str, str] = self.config.get("known_competitors", {})
        self.mempool_history: deque = deque(maxlen=1000)
        self.decoy_transactions: List[Dict] = []
        self.last_analysis: datetime = datetime.now()
        
        # Initialize counters
        self.total_transactions_analyzed = 0
        self.total_competitors_detected = 0
        self.total_decoys_generated = 0
        
        # Initialize web3 connections
        self.web3_connections = self._init_web3_connections()
        
        # Load historical data if available
        self._load_historical_data()
        
        logger.info(f"Competitor Tracker initialized with {len(self.known_addresses)} known competitors")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load competitor analysis configuration from file"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded competitor analysis config from {config_path}")
                return config
            else:
                logger.warning(f"Config file not found at {config_path}, using default values")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration values"""
        return {
            "known_competitors": {
                "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": {
                    "name": "Uniswap Router",
                    "type": "DEX Router"
                },
                "0xdef1c0ded9bec7f1a1670819833240f027b25eff": {
                    "name": "0x Exchange Proxy",
                    "type": "DEX Aggregator"
                },
                "0x881d40237659c251811cec9c364ef91dc08d300c": {
                    "name": "Known MEV Bot",
                    "type": "Arbitrage Bot"
                }
            },
            "competitorTracking": {
                "minGasPrice": 20,  # Gwei
                "patternExpiryDays": 7,
                "minTransactionsForPattern": 5,
                "maxCompetitorsToTrack": 100
            },
            "decoyStrategies": {
                "enabled": True,
                "minDecoys": 1,
                "maxDecoys": 3,
                "maxDelaySeconds": 2.0,
                "targetPairs": [
                    "ETH/USDC",
                    "ETH/USDT",
                    "WBTC/ETH",
                    "ETH/DAI"
                ]
            },
            "networks": ["ethereum", "arbitrum", "polygon"]
        }
    
    def _init_web3_connections(self) -> Dict[str, Web3]:
        """Initialize Web3 connections for each network"""
        connections = {}
        
        # Network RPC endpoints - in production, these would be loaded from secure config
        network_rpcs = {
            "ethereum": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
            "arbitrum": "https://arb1.arbitrum.io/rpc",
            "polygon": "https://polygon-rpc.com",
            # Add more networks as needed
        }
        
        # Initialize connections
        for network in self.config.get("networks", ["ethereum"]):
            try:
                if network in network_rpcs:
                    # For now, just store the RPC URL
                    connections[network] = network_rpcs[network]
                    logger.info(f"Stored RPC URL for {network}")
                else:
                    logger.warning(f"No RPC endpoint configured for {network}")
            except Exception as e:
                logger.error(f"Error setting up connection for {network}: {e}")
        
        return connections
    
    def _load_historical_data(self):
        """Load historical competitor data if available"""
        try:
            data_path = "backend/bot/data/competitor_history.json"
            if os.path.exists(data_path):
                with open(data_path, 'r') as f:
                    data = json.load(f)
                
                # Process historical data
                for competitor_id, competitor_data in data.get("competitors", {}).items():
                    pattern = CompetitorPattern()
                    
                    # Set basic attributes
                    pattern.total_transactions = competitor_data.get("total_transactions", 0)
                    pattern.profitable_transactions = competitor_data.get("profitable_transactions", 0)
                    pattern.success_rate = competitor_data.get("success_rate", 0.0)
                    
                    # Convert timestamp strings to datetime objects
                    last_seen_str = competitor_data.get("last_seen")
                    first_seen_str = competitor_data.get("first_seen")
                    
                    if last_seen_str:
                        pattern.last_seen = datetime.fromisoformat(last_seen_str)
                    if first_seen_str:
                        pattern.first_seen = datetime.fromisoformat(first_seen_str)
                    
                    # Load other data
                    pattern.gas_patterns = competitor_data.get("gas_patterns", [])
                    pattern.token_pairs = competitor_data.get("token_pairs", {})
                    pattern.timing_patterns = competitor_data.get("timing_patterns", [])
                    pattern.active_hours = competitor_data.get("active_hours", {i: 0 for i in range(24)})
                    pattern.active_days = competitor_data.get("active_days", {i: 0 for i in range(7)})
                    
                    # Add to competitors dictionary
                    self.competitors[competitor_id] = pattern
                
                logger.info(f"Loaded {len(self.competitors)} competitor profiles from historical data")
                
        except Exception as e:
            logger.error(f"Error loading historical competitor data: {e}")
            # Continue with empty competitors dictionary
    
    def analyze_mempool_transaction(self, tx: Dict) -> Optional[str]:
        """
        Analyze a transaction to identify if it belongs to a competitor.
        
        Args:
            tx: Transaction data dictionary
            
        Returns:
            Competitor ID if identified, None otherwise
        """
        self.total_transactions_analyzed += 1
        
        # Add to mempool history
        self.mempool_history.append({
            "tx": tx,
            "timestamp": datetime.now()
        })
        
        # Check if from address is a known competitor
        from_address = tx.get("from", "").lower()
        if from_address in self.known_addresses:
            competitor_id = from_address
            
            # Create pattern if not exists
            if competitor_id not in self.competitors:
                self.competitors[competitor_id] = CompetitorPattern()
            
            self._update_competitor_stats(competitor_id, tx)
            return competitor_id
        
        # Extract transaction patterns
        patterns = self._extract_patterns(tx)
        
        # Check against known competitor patterns
        for known_id, known_pattern in self.competitors.items():
            if self._match_patterns(patterns, known_pattern):
                competitor_id = known_id
                self._update_competitor_stats(known_id, tx)
                return competitor_id
        
        # If new pattern detected, create new competitor profile
        if self._is_likely_bot(patterns):
            competitor_id = self._create_new_competitor(patterns, tx)
            self.total_competitors_detected += 1
            return competitor_id
        
        return None
    
    def _extract_patterns(self, tx: Dict) -> Dict:
        """
        Extract behavioral patterns from a transaction.
        
        Args:
            tx: Transaction data dictionary
            
        Returns:
            Dictionary of extracted patterns
        """
        # Extract basic transaction data
        gas_price = int(tx.get("gasPrice", 0))
        gas_limit = int(tx.get("gas", 0))
        input_data = tx.get("input", "")
        value = int(tx.get("value", 0))
        
        # Extract token pair (simplified - in real implementation would decode input data)
        token_pair = self._extract_token_pair(input_data)
        
        # Extract method signature (first 10 characters of input data)
        method_sig = input_data[:10] if len(input_data) >= 10 else ""
        
        return {
            "from_address": tx.get("from", "").lower(),
            "to_address": tx.get("to", "").lower(),
            "gas_price": gas_price,
            "gas_limit": gas_limit,
            "input_length": len(input_data),
            "method_signature": method_sig,
            "token_pair": token_pair,
            "timestamp": datetime.now(),
            "value": value,
            "nonce": tx.get("nonce", 0)
        }
    
    def _match_patterns(self, patterns: Dict, known_pattern: CompetitorPattern) -> bool:
        """
        Check if transaction patterns match known competitor patterns.
        
        Args:
            patterns: Extracted transaction patterns
            known_pattern: Known competitor pattern to match against
            
        Returns:
            True if patterns match, False otherwise
        """
        # Need at least some history to match against
        if not known_pattern.gas_patterns or len(known_pattern.gas_patterns) < 3:
            return False
        
        # Match criteria counters
        matches = 0
        total_criteria = 4
        
        # 1. Gas price matching (within 10% of recent gas prices)
        gas_match = any(abs(g - patterns["gas_price"]) / max(g, 1) < 0.1 
                        for g in known_pattern.gas_patterns[-10:])
        if gas_match:
            matches += 1
        
        # 2. Token pair matching
        token_match = patterns["token_pair"] in known_pattern.token_pairs
        if token_match:
            matches += 1
        
        # 3. Timing pattern matching (within 1 minute of known timing patterns)
        current_seconds = patterns["timestamp"].hour * 3600 + patterns["timestamp"].minute * 60 + patterns["timestamp"].second
        timing_match = any(abs(t - current_seconds) < 60 for t in known_pattern.timing_patterns)
        if timing_match:
            matches += 1
        
        # 4. Method signature matching
        method_match = patterns["method_signature"] in [tx[:10] for tx in known_pattern.transaction_hashes if len(tx) >= 10]
        if method_match:
            matches += 1
        
        # Require at least 3 out of 4 criteria to match
        return matches >= 3
    
    def _is_likely_bot(self, patterns: Dict) -> bool:
        """
        Determine if transaction patterns suggest bot behavior.
        
        Args:
            patterns: Extracted transaction patterns
            
        Returns:
            True if likely a bot, False otherwise
        """
        # Check for bot-like characteristics
        
        # 1. High gas price (above minimum threshold)
        high_gas = patterns["gas_price"] > self.config.get("competitorTracking", {}).get("minGasPrice", 20) * 1e9
        
        # 2. Complex contract interaction (input data length)
        complex_input = patterns["input_length"] > 100
        
        # 3. Known arbitrage token pair
        known_pair = self._is_arbitrage_pair(patterns["token_pair"])
        
        # 4. To address is a known DEX or router
        to_address = patterns["to_address"]
        known_dex = to_address in [
            "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",  # Uniswap V2 Router
            "0xe592427a0aece92de3edee1f18e0157c05861564",  # Uniswap V3 Router
            "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f",  # SushiSwap Router
            "0x1111111254fb6c44bac0bed2854e76f90643097d",  # 1inch Router
            "0xdef1c0ded9bec7f1a1670819833240f027b25eff"   # 0x Exchange Proxy
        ]
        
        # Need at least 3 of the 4 criteria to consider it a bot
        bot_score = sum([high_gas, complex_input, known_pair, known_dex])
        return bot_score >= 3
    
    def generate_decoys(self, real_tx: Dict) -> List[Dict]:
        """
        Generate decoy transactions to mislead competitors.
        
        Args:
            real_tx: Real transaction to create decoys for
            
        Returns:
            List of transactions (real + decoys)
        """
        decoys = []
        
        # Check if decoy strategies are enabled
        if not self.config.get("decoyStrategies", {}).get("enabled", False):
            return [real_tx]
        
        # Determine number of decoys to generate
        min_decoys = self.config.get("decoyStrategies", {}).get("minDecoys", 1)
        max_decoys = self.config.get("decoyStrategies", {}).get("maxDecoys", 3)
        num_decoys = random.randint(min_decoys, max_decoys)
        
        # Generate decoys
        for _ in range(num_decoys):
            decoy = self._create_decoy_transaction(real_tx)
            decoys.append(decoy)
            self.total_decoys_generated += 1
        
        # Randomize order of real and decoy transactions
        all_tx = [real_tx] + decoys
        random.shuffle(all_tx)
        
        # Add to decoy transactions list
        self.decoy_transactions.extend(decoys)
        
        logger.info(f"Generated {num_decoys} decoy transactions")
        return all_tx
    
    def _create_decoy_transaction(self, real_tx: Dict) -> Dict:
        """
        Create a single decoy transaction.
        
        Args:
            real_tx: Real transaction to base decoy on
            
        Returns:
            Decoy transaction
        """
        decoy = real_tx.copy()
        
        # Modify gas price within reasonable range
        gas_multiplier = random.uniform(0.9, 1.1)
        decoy["gasPrice"] = int(real_tx["gasPrice"] * gas_multiplier)
        
        # Modify token amounts slightly
        if "value" in decoy:
            value_multiplier = random.uniform(0.8, 1.2)
            decoy["value"] = int(real_tx["value"] * value_multiplier)
        
        # Add random delay
        max_delay = self.config.get("decoyStrategies", {}).get("maxDelaySeconds", 2.0)
        delay = random.uniform(0, max_delay)
        decoy["submitAfter"] = delay
        
        # Mark as decoy for internal tracking
        decoy["_isDecoy"] = True
        decoy["_decoyId"] = f"decoy_{int(time.time())}_{random.randint(1000, 9999)}"
        
        return decoy
    
    def update_competitor_database(self):
        """Update and maintain competitor database"""
        current_time = datetime.now()
        
        # Get expiry threshold
        expiry_days = self.config.get("competitorTracking", {}).get("patternExpiryDays", 7)
        expired_threshold = current_time - timedelta(days=expiry_days)
        
        # Remove expired patterns
        expired_competitors = [
            cid for cid, pattern in self.competitors.items()
            if pattern.last_seen < expired_threshold
        ]
        
        for cid in expired_competitors:
            logger.info(f"Removing expired competitor profile: {cid}")
            del self.competitors[cid]
        
        # Update success rates
        for pattern in self.competitors.values():
            if pattern.total_transactions > 0:
                pattern.success_rate = pattern.profitable_transactions / pattern.total_transactions
        
        # Limit number of competitors to track
        max_competitors = self.config.get("competitorTracking", {}).get("maxCompetitorsToTrack", 100)
        if len(self.competitors) > max_competitors:
            # Sort by activity score and keep only the most active
            sorted_competitors = sorted(
                self.competitors.items(),
                key=lambda x: x[1].get_activity_score(),
                reverse=True
            )
            
            # Keep only the top competitors
            self.competitors = {
                cid: pattern for cid, pattern in sorted_competitors[:max_competitors]
            }
        
        # Save competitor database
        self._save_competitor_data()
        
        logger.info(f"Updated competitor database. Tracking {len(self.competitors)} competitors")
    
    def _save_competitor_data(self):
        """Save competitor data to file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs("backend/bot/data", exist_ok=True)
            
            # Prepare data for serialization
            data = {
                "competitors": {},
                "meta": {
                    "total_transactions_analyzed": self.total_transactions_analyzed,
                    "total_competitors_detected": self.total_competitors_detected,
                    "total_decoys_generated": self.total_decoys_generated,
                    "last_update": datetime.now().isoformat()
                }
            }
            
            # Convert competitor patterns to serializable format
            for competitor_id, pattern in self.competitors.items():
                data["competitors"][competitor_id] = {
                    "total_transactions": pattern.total_transactions,
                    "profitable_transactions": pattern.profitable_transactions,
                    "success_rate": pattern.success_rate,
                    "last_seen": pattern.last_seen.isoformat(),
                    "first_seen": pattern.first_seen.isoformat(),
                    "gas_patterns": pattern.gas_patterns[-50:],  # Save last 50 for space
                    "token_pairs": pattern.token_pairs,
                    "timing_patterns": pattern.timing_patterns[-50:],  # Save last 50 for space
                    "active_hours": {str(k): v for k, v in pattern.active_hours.items()},
                    "active_days": {str(k): v for k, v in pattern.active_days.items()},
                    "estimated_profit": pattern.estimated_profit,
                    "preferred_dexes": pattern.preferred_dexes
                }
            
            # Save to file
            with open("backend/bot/data/competitor_history.json", 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Saved competitor data to file")
            
        except Exception as e:
            logger.error(f"Error saving competitor data: {e}")
    
    def get_competitor_stats(self) -> Dict:
        """
        Get statistics about tracked competitors.
        
        Returns:
            Dictionary with competitor statistics
        """
        # Update database first
        self.update_competitor_database()
        
        # Count active competitors (seen in last hour)
        active_threshold = datetime.now() - timedelta(hours=1)
        active_competitors = sum(
            1 for p in self.competitors.values()
            if p.last_seen > active_threshold
        )
        
        # Get top competitors by activity score
        top_competitors = sorted(
            self.competitors.items(),
            key=lambda x: x[1].get_activity_score(),
            reverse=True
        )[:10]  # Top 10
        
        return {
            "total_competitors": len(self.competitors),
            "active_competitors": active_competitors,
            "total_transactions_analyzed": self.total_transactions_analyzed,
            "total_decoys_generated": self.total_decoys_generated,
            "top_competitors": [
                {
                    "id": cid,
                    "success_rate": f"{pattern.success_rate:.2%}",
                    "total_tx": pattern.total_transactions,
                    "last_seen": pattern.last_seen.isoformat(),
                    "activity_score": f"{pattern.get_activity_score():.2f}",
                    "preferred_tokens": pattern.get_preferred_tokens(3),
                    "peak_hours": pattern.get_peak_hours()
                }
                for cid, pattern in top_competitors
            ]
        }
    
    def _extract_token_pair(self, input_data: str) -> str:
        """
        Extract token pair from transaction input data.
        
        Args:
            input_data: Transaction input data
            
        Returns:
            Token pair string
        """
        # In a real implementation, this would decode the input data
        # to extract actual token addresses
        
        # For now, return a simplified representation based on input data hash
        if not input_data or len(input_data) < 10:
            return "unknown/unknown"
        
        # Use method signature to guess token pair
        method_sig = input_data[:10]
        
        # Common method signatures for swaps
        swap_sigs = {
            "0x38ed1739": "ETH/USDC",  # swapExactTokensForTokens
            "0x7ff36ab5": "ETH/USDT",  # swapExactETHForTokens
            "0x18cbafe5": "WBTC/ETH",  # swapExactTokensForETH
            "0x8803dbee": "ETH/DAI",   # swapTokensForExactTokens
            "0x4a25d94a": "USDC/USDT", # swapTokensForExactETH
            "0x5c11d795": "DAI/USDC",  # swapExactTokensForTokensSupportingFeeOnTransferTokens
            "0xfb3bdb41": "ETH/WBTC",  # swapExactETHForTokensSupportingFeeOnTransferTokens
            "0x791ac947": "USDT/DAI"   # swapExactTokensForETHSupportingFeeOnTransferTokens
        }
        
        return swap_sigs.get(method_sig, "unknown/unknown")
    
    def predict_competitor_actions(self, market_conditions: Dict) -> List[Dict]:
        """
        Predict likely actions of competitors under specific market conditions.
        
        Args:
            market_conditions: Dictionary with current market conditions
            
        Returns:
            List of predicted competitor actions
        """
        predictions = []
        
        # Get current hour
        current_hour = datetime.now().hour
        
        # For each competitor, predict if they're likely to be active
        for competitor_id, pattern in self.competitors.items():
            # Skip if not enough data
            if pattern.total_transactions < 10:
                continue
            
            # Check if current hour is a peak hour for this competitor
            peak_hours = pattern.get_peak_hours()
            is_peak_hour = current_hour in peak_hours
            
            # Check if current market conditions match preferred tokens
            preferred_tokens = pattern.get_preferred_tokens(5)
            token_match = any(token in market_conditions.get("active_pairs", []) 
                             for token in preferred_tokens)
            
            # Calculate activity probability
            activity_prob = 0.2  # Base probability
            
            if is_peak_hour:
                activity_prob += 0.4
            
            if token_match:
                activity_prob += 0.3
            
            # Add recency factor
            time_since_last = (datetime.now() - pattern.last_seen).total_seconds()
            if time_since_last < 3600:  # Within last hour
                activity_prob += 0.1
            
            predictions.append({
                "competitor_id": competitor_id,
                "activity_probability": min(activity_prob, 1.0),
                "preferred_tokens": preferred_tokens[:3],
                "peak_hours": peak_hours,
                "estimated_gas_price": pattern.get_avg_gas_price()
            })
        
        # Sort by activity probability
        predictions.sort(key=lambda x: x["activity_probability"], reverse=True)
        
        return predictions
    
    def get_optimal_counter_strategy(self, competitor_id: str) -> Dict:
        """
        Get optimal counter-strategy for a specific competitor.
        
        Args:
            competitor_id: Competitor ID
            
        Returns:
            Dictionary with counter-strategy details
        """
        if competitor_id not in self.competitors:
            return {"error": "Competitor not found"}
        
        pattern = self.competitors[competitor_id]
        
        # Determine gas price strategy
        avg_gas = pattern.get_avg_gas_price()
        gas_strategy = {
            "type": "outbid",
            "gas_price": int(avg_gas * 1.1),  # 10% higher
            "description": "Outbid competitor with slightly higher gas price"
        }
        
        # Determine timing strategy
        peak_hours = pattern.get_peak_hours()
        current_hour = datetime.now().hour
        
        if current_hour in peak_hours:
            timing_strategy = {
                "type": "immediate",
                "description": "Competitor is likely active now, execute immediately"
            }
        else:
            timing_strategy = {
                "type": "delayed",
                "description": "Competitor is less active now, can use lower gas price"
            }
        
        # Determine decoy strategy
        decoy_strategy = {
            "type": "multiple_decoys",
            "count": random.randint(2, 5),
            "description": "Use multiple decoys to confuse competitor"
        }
        
        return {
            "competitor_id": competitor_id,
            "gas_strategy": gas_strategy,
            "timing_strategy": timing_strategy,
            "decoy_strategy": decoy_strategy,
            "preferred_tokens": pattern.get_preferred_tokens(3),
            "success_rate": pattern.success_rate,
            "activity_score": pattern.get_activity_score()
        }

# Example usage
if __name__ == "__main__":
    tracker = CompetitorTracker()
    
    # Example transaction
    example_tx = {
        "hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "from": "0x881d40237659c251811cec9c364ef91dc08d300c",
        "to": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",  # Uniswap V2 Router
        "gasPrice": 50000000000,  # 50 Gwei
        "gas": 250000,
        "value": 1000000000000000000,  # 1 ETH
        "input": "0x38ed1739000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        "nonce": 123
    }
    
    # Analyze transaction
    competitor_id = tracker.analyze_mempool_transaction(example_tx)
    print(f"Detected competitor: {competitor_id}")
    
    # Generate decoys
    decoys = tracker.generate_decoys(example_tx)
    print(f"Generated {len(decoys) - 1} decoy transactions")
    
    # Get competitor stats
    stats = tracker.get_competitor_stats()
    print(f"Competitor stats: {json.dumps(stats, indent=2)}")
    
    # Get counter strategy
    if competitor_id:
        strategy = tracker.get_optimal_counter_strategy(competitor_id)
        print(f"Counter strategy: {json.dumps(strategy, indent=2)}")
