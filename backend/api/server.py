#!/usr/bin/env python3
"""
ArbitrageX API Server

This module serves as the main entry point for the ArbitrageX API,
providing endpoints for arbitrage opportunities, bot control, and monitoring.
"""

import os
import logging
from datetime import datetime
import json
import threading
import signal
from typing import Dict, List, Optional

# Web framework imports
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pymongo
from pymongo import MongoClient
import redis
from dotenv import load_dotenv

# Monitoring imports
try:
    import sentry_sdk
    from prometheus_client import Counter, Histogram, generate_latest
    MONITORING_ENABLED = True
except ImportError:
    MONITORING_ENABLED = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("APIServer")

# Initialize Sentry for error tracking (if configured)
SENTRY_DSN = os.getenv("SENTRY_DSN")
if MONITORING_ENABLED and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )
    logger.info("Sentry initialized for error tracking")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize metrics if monitoring is enabled
if MONITORING_ENABLED:
    REQUESTS = Counter('arbitragex_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
    REQUEST_LATENCY = Histogram('arbitragex_request_latency_seconds', 'Request latency in seconds', ['method', 'endpoint'])

# Bot status (for compatibility with existing Python server)
bot_status = {
    "isRunning": False,
    "startTime": None,
    "stats": {
        "opportunities": 0,
        "trades": 0,
        "profit": 0
    }
}

# Database connections
mongo_client = None
db = None
redis_client = None

def init_database_connections():
    """Initialize database connections."""
    global mongo_client, db, redis_client
    
    try:
        # MongoDB connection
        MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client["arbitragex"]
        logger.info(f"Connected to MongoDB at {MONGO_URI}")
        
        # Redis connection (for caching and pub/sub)
        REDIS_URI = os.getenv("REDIS_URI", "redis://localhost:6379/0")
        redis_client = redis.from_url(REDIS_URI)
        redis_client.ping()  # Test connection
        logger.info(f"Connected to Redis at {REDIS_URI}")
        
        return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False

# Import bot modules
bot_core = None
network_scanner = None

def init_bot_components():
    """Initialize bot components."""
    global bot_core, network_scanner
    
    try:
        # Import bot modules conditionally to handle missing modules gracefully
        try:
            from backend.bot.bot_core import BotCore
            from backend.bot.network_scanner import NetworkScanner
            
            # Initialize bot components with configuration
            config_path = os.getenv("BOT_CONFIG_PATH", "backend/bot/bot_settings.json")
            with open(config_path, 'r') as f:
                bot_config = json.load(f)
            
            bot_core = BotCore(config_path)
            network_scanner = NetworkScanner(bot_config)
            logger.info("Bot components initialized")
            
            return True
        except ImportError as e:
            logger.warning(f"Bot modules not available: {e}. Running in API-only mode.")
            return False
    except Exception as e:
        logger.error(f"Error initializing bot components: {e}")
        return False

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "mongodb": "connected" if mongo_client is not None else "disconnected",
            "redis": "connected" if redis_client is not None else "disconnected",
            "bot_core": "initialized" if bot_core is not None else "not_initialized",
            "network_scanner": "initialized" if network_scanner is not None else "not_initialized"
        }
    })

# Metrics endpoint for Prometheus
@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint."""
    if MONITORING_ENABLED:
        return Response(generate_latest(), mimetype="text/plain")
    else:
        return jsonify({"error": "Monitoring not enabled"}), 501

# Legacy endpoints (for compatibility with existing Python server)
@app.route('/api/v1/bot-control/status', methods=['GET'])
def get_bot_status_legacy():
    """Get the current status of the bot (legacy endpoint)."""
    logger.info("Legacy status endpoint called")
    return jsonify({
        "success": True,
        "data": {
            "isRunning": bot_status["isRunning"]
        }
    })

@app.route('/api/v1/bot-control/start', methods=['POST'])
def start_bot_legacy():
    """Start the bot (legacy endpoint)."""
    logger.info("Legacy start endpoint called")
    
    # Update status
    bot_status["isRunning"] = True
    
    # Try to use the new bot_core if available
    if bot_core:
        try:
            bot_core.start()
        except Exception as e:
            logger.error(f"Error starting bot core: {e}")
    
    return jsonify({
        "success": True,
        "message": "Bot started successfully"
    })

@app.route('/api/v1/bot-control/stop', methods=['POST'])
def stop_bot_legacy():
    """Stop the bot (legacy endpoint)."""
    logger.info("Legacy stop endpoint called")
    
    # Update status
    bot_status["isRunning"] = False
    
    # Try to use the new bot_core if available
    if bot_core:
        try:
            bot_core.stop()
        except Exception as e:
            logger.error(f"Error stopping bot core: {e}")
    
    return jsonify({
        "success": True,
        "message": "Bot stopped successfully"
    })

@app.route('/api/v1/market-data/recent', methods=['GET'])
def get_recent_market_data_legacy():
    """Get recent market data (legacy endpoint)."""
    logger.info("Legacy recent market data endpoint called")
    
    # Try to get data from database if available
    if db:
        try:
            market_data = list(db.marketdatas.find().sort('timestamp', -1).limit(10))
            # Convert ObjectId to string for JSON serialization
            for item in market_data:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
            
            return jsonify({
                "success": True,
                "data": market_data
            })
        except Exception as e:
            logger.error(f"Error getting market data from database: {e}")
    
    # Fall back to mock data
    return jsonify({
        "success": True,
        "data": [
            {
                "tokenA": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "tokenB": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "exchange": "SUSHISWAP",
                "price": 12502.653847629745,
                "liquidity": 7.483705267106336e+23,
                "timestamp": "2025-03-02T07:07:01.000Z",
                "blockNumber": 21957581,
                "txHash": "0x19555ae01eff30a6",
                "priceImpact": 0.01,
                "spread": 5785.689057030242,
                "createdAt": "2025-03-02T07:07:02.000Z",
                "updatedAt": "2025-03-02T07:07:02.000Z"
            }
        ]
    })

@app.route('/api/v1/arbitrage/opportunities', methods=['GET'])
def get_arbitrage_opportunities_legacy():
    """Get arbitrage opportunities (legacy endpoint)."""
    logger.info("Legacy arbitrage opportunities endpoint called")
    
    # Try to get data from database if available
    if db:
        try:
            opportunities = list(db.arbitrageopportunities.find().sort('timestamp', -1).limit(10))
            # Convert ObjectId to string for JSON serialization
            for item in opportunities:
                if '_id' in item:
                    item['_id'] = str(item['_id'])
            
            return jsonify({
                "success": True,
                "data": opportunities
            })
        except Exception as e:
            logger.error(f"Error getting opportunities from database: {e}")
    
    # Fall back to mock data
    return jsonify({
        "success": True,
        "data": [
            {
                "id": "opp-1",
                "tokenA": "USDC",
                "tokenB": "DAI",
                "dexA": "Uniswap",
                "dexB": "Sushiswap",
                "profitUSD": 12.5,
                "timestamp": "2025-03-07T11:30:00.000Z"
            }
        ]
    })

@app.route('/api/v1/settings', methods=['GET'])
def get_settings_legacy():
    """Get bot settings (legacy endpoint)."""
    logger.info("Legacy settings endpoint called")
    
    # Try to get settings from bot_core if available
    if bot_core and hasattr(bot_core, 'config'):
        try:
            return jsonify({
                "success": True,
                "data": bot_core.config
            })
        except Exception as e:
            logger.error(f"Error getting settings from bot core: {e}")
    
    # Fall back to mock settings
    return jsonify({
        "success": True,
        "data": {
            "scanInterval": 5,
            "minProfitThreshold": 0.01,
            "maxSlippage": 1.0,
            "gasStrategy": "dynamic"
        }
    })

@app.route('/api/v1/settings', methods=['POST'])
def update_settings_legacy():
    """Update bot settings (legacy endpoint)."""
    logger.info("Legacy update settings endpoint called")
    
    # Try to update settings in bot_core if available
    if bot_core and hasattr(bot_core, 'config'):
        try:
            new_settings = request.json
            # Update config
            for key, value in new_settings.items():
                bot_core.config[key] = value
            
            # Save config to file
            config_path = os.getenv("BOT_CONFIG_PATH", "backend/bot/bot_settings.json")
            with open(config_path, 'w') as f:
                json.dump(bot_core.config, f, indent=4)
            
            return jsonify({
                "success": True,
                "message": "Settings updated successfully"
            })
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
    
    # Fall back to mock response
    return jsonify({
        "success": True,
        "message": "Settings updated successfully"
    })

# New API endpoints
@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    """Get arbitrage opportunities with optional filtering."""
    try:
        # Get query parameters
        network = request.args.get('network')
        limit = int(request.args.get('limit', 100))
        min_profit = float(request.args.get('min_profit', 0))
        
        if not network_scanner or not db:
            return jsonify({"error": "Service not available"}), 503
        
        # Get opportunities from database
        opportunities = network_scanner.get_opportunities_from_db(
            network=network,
            limit=limit,
            min_profit=min_profit
        )
        
        return jsonify({
            "count": len(opportunities),
            "opportunities": opportunities
        })
    except Exception as e:
        logger.error(f"Error getting opportunities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/opportunities/latest', methods=['GET'])
def get_latest_opportunities():
    """Get the latest arbitrage opportunities."""
    try:
        if not network_scanner:
            return jsonify({"error": "Network scanner not available"}), 503
        
        # Scan for new opportunities
        opportunities = network_scanner.scan()
        
        return jsonify({
            "count": len(opportunities),
            "opportunities": opportunities
        })
    except Exception as e:
        logger.error(f"Error scanning for opportunities: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Get the current status of the arbitrage bot."""
    try:
        if not bot_core:
            return jsonify({"error": "Bot core not available"}), 503
        
        status = bot_core.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the arbitrage bot."""
    try:
        if not bot_core:
            return jsonify({"error": "Bot core not available"}), 503
        
        bot_core.start()
        bot_status["isRunning"] = True  # Update legacy status
        return jsonify({"status": "started", "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the arbitrage bot."""
    try:
        if not bot_core:
            return jsonify({"error": "Bot core not available"}), 503
        
        bot_core.stop()
        bot_status["isRunning"] = False  # Update legacy status
        return jsonify({"status": "stopped", "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot/pause', methods=['POST'])
def pause_bot():
    """Pause the arbitrage bot."""
    try:
        if not bot_core:
            return jsonify({"error": "Bot core not available"}), 503
        
        bot_core.pause()
        return jsonify({"status": "paused", "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Error pausing bot: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/bot/resume', methods=['POST'])
def resume_bot():
    """Resume the arbitrage bot."""
    try:
        if not bot_core:
            return jsonify({"error": "Bot core not available"}), 503
        
        bot_core.resume()
        return jsonify({"status": "resumed", "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Error resuming bot: {e}")
        return jsonify({"error": str(e)}), 500

# AI endpoints
@app.route('/api/ai/optimize', methods=['POST'])
def optimize_strategy():
    """Optimize trading strategy using AI."""
    try:
        # Import AI modules
        from backend.ai.strategy_optimizer import StrategyOptimizer
        
        data = request.json
        network = data.get('network', 'ethereum')
        
        optimizer = StrategyOptimizer()
        result = optimizer.optimize(network=network)
        
        return jsonify(result)
    except ImportError:
        logger.error("AI modules not available")
        return jsonify({"error": "AI optimization not available"}), 503
    except Exception as e:
        logger.error(f"Error optimizing strategy: {e}")
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# Request logging middleware
@app.before_request
def before_request():
    """Log request and start timer for latency tracking."""
    request.start_time = datetime.now()

@app.after_request
def after_request(response):
    """Log response and record metrics."""
    latency = (datetime.now() - request.start_time).total_seconds()
    
    # Log request details
    logger.info(f"{request.method} {request.path} - {response.status_code} - {latency:.4f}s")
    
    # Record metrics if monitoring is enabled
    if MONITORING_ENABLED:
        endpoint = request.path
        REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(latency)
    
    return response

def graceful_shutdown(signal_received, frame):
    """Handle graceful shutdown."""
    logger.info(f"Signal {signal_received} received, shutting down gracefully")
    
    # Close database connections
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")
    
    if redis_client:
        redis_client.close()
        logger.info("Redis connection closed")
    
    # Exit
    logger.info("Server shutdown complete")
    exit(0)

def main():
    """Main entry point for the API server."""
    # Initialize database connections
    init_database_connections()
    
    # Initialize bot components (but continue even if they fail)
    init_bot_components()
    
    # Get port from environment or use default
    port = int(os.getenv("API_PORT", 3002))  # Changed from 3001 to 3002
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    # Start the server
    logger.info(f"Starting ArbitrageX API server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)

if __name__ == "__main__":
    main() 