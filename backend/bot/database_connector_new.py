"""
Database Connector Module for ArbitrageX

This module handles database connections and operations for the ArbitrageX bot.
It provides a unified interface for storing and retrieving data from MongoDB.
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("database_connector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DatabaseConnector")

class DatabaseConnector:
    """
    Handles database connections and operations for the ArbitrageX bot.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the database connector.
        
        Args:
            config: Bot configuration dictionary
        """
        logger.info("Initializing Database Connector")
        self.config = config
        
        # Default MongoDB connection settings
        self.mongodb_uri = config.get("mongodb_uri", "mongodb://localhost:27017")
        self.database_name = config.get("database_name", "arbitragex")
        
        # Initialize MongoDB client
        self.client = None
        self.db = None
        
        # Connect to MongoDB
        self._connect_to_mongodb()
        
        logger.info("Database Connector initialized")
    
    def _connect_to_mongodb(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Connect to MongoDB with a timeout
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            
            # Verify connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[self.database_name]
            
            logger.info(f"Connected to MongoDB: {self.mongodb_uri}, database: {self.database_name}")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.client = None
            self.db = None
            return False
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB server selection timeout: {e}")
            self.client = None
            self.db = None
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            self.client = None
            self.db = None
            return False
    
    def is_connected(self) -> bool:
        """
        Check if connected to MongoDB.
        
        Returns:
            True if connected, False otherwise
        """
        if not self.client:
            return False
            
        try:
            # Verify connection
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def save_market_data(self, market_data: Dict) -> bool:
        """
        Save market data to MongoDB.
        
        Args:
            market_data: Market data to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot save market data: Not connected to MongoDB")
            return False
        
        try:
            # Ensure required fields are present
            required_fields = ['tokenA', 'tokenB', 'exchange', 'price', 'liquidity', 'blockNumber']
            for field in required_fields:
                if field not in market_data:
                    logger.error(f"Cannot save market data: Missing required field '{field}'")
                    return False
            
            # Add timestamp if not present
            if 'timestamp' not in market_data:
                market_data['timestamp'] = datetime.now()
            
            # Insert into marketdatas collection
            result = self.db.marketdatas.insert_one(market_data)
            
            logger.info(f"Saved market data to MongoDB: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving market data to MongoDB: {e}")
            return False
    
    def save_arbitrage_opportunity(self, opportunity: Dict) -> bool:
        """
        Save arbitrage opportunity to MongoDB.
        
        Args:
            opportunity: Arbitrage opportunity to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot save arbitrage opportunity: Not connected to MongoDB")
            return False
        
        try:
            # Ensure required fields are present
            required_fields = ['tokenA', 'tokenB', 'route', 'expectedProfit']
            for field in required_fields:
                if field not in opportunity:
                    logger.error(f"Cannot save arbitrage opportunity: Missing required field '{field}'")
                    return False
            
            # Add timestamp if not present
            if 'timestamp' not in opportunity:
                opportunity['timestamp'] = datetime.now()
            
            # Add createdAt and updatedAt fields
            opportunity['createdAt'] = datetime.now()
            opportunity['updatedAt'] = datetime.now()
            
            # Insert into arbitrageopportunities collection
            result = self.db.arbitrageopportunities.insert_one(opportunity)
            
            logger.info(f"Saved arbitrage opportunity to MongoDB: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving arbitrage opportunity to MongoDB: {e}")
            return False
    
    def save_trade(self, trade: Dict) -> bool:
        """
        Save trade to MongoDB.
        
        Args:
            trade: Trade to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot save trade: Not connected to MongoDB")
            return False
        
        try:
            # Ensure required fields are present
            required_fields = ['tokenA', 'tokenB', 'amount', 'profit', 'success']
            for field in required_fields:
                if field not in trade:
                    logger.error(f"Cannot save trade: Missing required field '{field}'")
                    return False
            
            # Add timestamp if not present
            if 'timestamp' not in trade:
                trade['timestamp'] = datetime.now()
            
            # Add createdAt and updatedAt fields
            trade['createdAt'] = datetime.now()
            trade['updatedAt'] = datetime.now()
            
            # Insert into trades collection
            result = self.db.trades.insert_one(trade)
            
            # If it's an arbitrage trade, also save to arbitragetrades collection
            if trade.get('type') == 'arbitrage':
                self.db.arbitragetrades.insert_one(trade)
            
            logger.info(f"Saved trade to MongoDB: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving trade to MongoDB: {e}")
            return False
    
    def get_recent_market_data(self, limit: int = 10) -> List[Dict]:
        """
        Get recent market data from MongoDB.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of market data records
        """
        if not self.is_connected():
            logger.error("Cannot get market data: Not connected to MongoDB")
            return []
        
        try:
            # Query marketdatas collection
            cursor = self.db.marketdatas.find().sort('timestamp', pymongo.DESCENDING).limit(limit)
            
            # Convert cursor to list
            market_data = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for item in market_data:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
            
            logger.info(f"Retrieved {len(market_data)} market data records from MongoDB")
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market data from MongoDB: {e}")
            return []
    
    def get_recent_arbitrage_opportunities(self, limit: int = 10) -> List[Dict]:
        """
        Get recent arbitrage opportunities from MongoDB.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of arbitrage opportunities
        """
        if not self.is_connected():
            logger.error("Cannot get arbitrage opportunities: Not connected to MongoDB")
            return []
        
        try:
            # Query arbitrageopportunities collection
            cursor = self.db.arbitrageopportunities.find().sort('timestamp', pymongo.DESCENDING).limit(limit)
            
            # Convert cursor to list
            opportunities = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for item in opportunities:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
            
            logger.info(f"Retrieved {len(opportunities)} arbitrage opportunities from MongoDB")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error getting arbitrage opportunities from MongoDB: {e}")
            return []
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """
        Get recent trades from MongoDB.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of trade records
        """
        if not self.is_connected():
            logger.error("Cannot get trades: Not connected to MongoDB")
            return []
        
        try:
            # Query trades collection
            cursor = self.db.trades.find().sort('timestamp', pymongo.DESCENDING).limit(limit)
            
            # Convert cursor to list
            trades = list(cursor)
            
            # Convert ObjectId to string for JSON serialization
            for item in trades:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
            
            logger.info(f"Retrieved {len(trades)} trades from MongoDB")
            return trades
            
        except Exception as e:
            logger.error(f"Error getting trades from MongoDB: {e}")
            return []
    
    def get_opportunities_from_db(self, network: Optional[str] = None, limit: int = 100, 
                                 min_profit: Optional[float] = None, 
                                 token_pair: Optional[tuple] = None) -> List[Dict]:
        """
        Retrieve arbitrage opportunities from the database.
        
        Args:
            network: Optional network to filter by
            limit: Maximum number of opportunities to return
            min_profit: Minimum profit threshold
            token_pair: Optional token pair to filter by (tokenA, tokenB)
            
        Returns:
            List of arbitrage opportunities from the database
        """
        if not self.is_connected():
            logger.error("Cannot retrieve opportunities: Not connected to MongoDB")
            return []
            
        try:
            # Build query
            query = {}
            
            if network:
                query["network"] = network
                
            if min_profit:
                query["expectedProfit"] = {"$gte": min_profit}
                
            if token_pair:
                token_a, token_b = token_pair
                query["tokenA"] = token_a
                query["tokenB"] = token_b
                
            # Get opportunities from database
            opportunities = list(self.db.arbitrageopportunities.find(
                query, 
                sort=[("timestamp", -1)],
                limit=limit
            ))
            
            # Convert MongoDB ObjectId to string for JSON serialization
            for opp in opportunities:
                if "_id" in opp:
                    opp["_id"] = str(opp["_id"])
                    
            logger.info(f"Retrieved {len(opportunities)} opportunities from database")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error retrieving opportunities from database: {e}")
            return []
            
    def update_opportunity_status(self, opportunity_id: str, status: str, 
                                 execution_result: Optional[Dict] = None) -> bool:
        """
        Update the status of an arbitrage opportunity in the database.
        
        Args:
            opportunity_id: ID of the opportunity to update
            status: New status (e.g., "pending", "executing", "completed", "failed")
            execution_result: Optional execution result data
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self.is_connected():
            logger.error("Cannot update opportunity: Not connected to MongoDB")
            return False
            
        try:
            # Build update document
            update_doc = {
                "status": status,
                "updatedAt": datetime.now()
            }
            
            if execution_result:
                update_doc["executionResult"] = execution_result
                
            # Update opportunity in database
            result = self.db.arbitrageopportunities.update_one(
                {"_id": opportunity_id},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated opportunity {opportunity_id} status to {status}")
                return True
            else:
                logger.warning(f"Opportunity {opportunity_id} not found or not updated")
                return False
                
        except Exception as e:
            logger.error(f"Error updating opportunity status: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection") 