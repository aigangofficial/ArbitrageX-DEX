#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Web Dashboard

This module provides a web interface for monitoring and controlling the
ArbitrageX trading bot, including real-time metrics, trading history,
system configuration, security management, and notifications.
"""

import os
import sys
import json
import logging
import datetime
from typing import Dict, Any, List, Optional, Union
from functools import wraps

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import (
    Flask, render_template, request, redirect, url_for, jsonify, 
    session, flash, Response, send_from_directory
)
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash

# Import ArbitrageX components
try:
    from notifications import get_notification_manager, notify
    from security.security_manager import SecurityManager
except ImportError:
    logging.warning("ArbitrageX modules not found. Running in standalone mode.")

# Add the import for MEV Protection Insights
from mev_protection_insights import MEVProtectionInsights

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/ai/logs/dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dashboard")

# Create Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Generate a secure secret key for the session
app.secret_key = os.urandom(24)

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Dashboard configuration
DASHBOARD_CONFIG_PATH = "backend/ai/config/dashboard.json"

# Default admin credentials (will be overridden by config file if it exists)
DEFAULT_ADMIN = {
    "username": "admin",
    "password_hash": generate_password_hash("arbitragex"),
    "email": "admin@example.com"
}

# Initialize MEV Protection Insights
mev_protection_insights = None
try:
    mev_protection_insights = MEVProtectionInsights()
    app.logger.info("MEV Protection Insights initialized successfully")
except Exception as e:
    app.logger.error(f"Error initializing MEV Protection Insights: {e}")

# Load or create dashboard config
def load_config() -> Dict[str, Any]:
    """Load dashboard configuration from file or create default config."""
    try:
        if os.path.exists(DASHBOARD_CONFIG_PATH):
            with open(DASHBOARD_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            # Ensure essential fields exist
            if "users" not in config:
                config["users"] = [DEFAULT_ADMIN]
            return config
        else:
            # Create default config
            config = {
                "port": 5000,
                "host": "127.0.0.1",
                "debug": False,
                "users": [DEFAULT_ADMIN],
                "session_lifetime": 3600,  # 1 hour
                "enable_api_auth": True,
                "api_keys": [],
                "notifications": {
                    "enable_browser_notifications": True,
                    "notify_on_trade": True,
                    "notify_on_error": True,
                    "notify_on_security_event": True
                },
                "appearance": {
                    "theme": "light",
                    "primary_color": "#3498db",
                    "refresh_interval": 5000  # ms
                }
            }
            # Save default config
            os.makedirs(os.path.dirname(DASHBOARD_CONFIG_PATH), exist_ok=True)
            with open(DASHBOARD_CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=2)
            return config
    except Exception as e:
        logger.error(f"Error loading dashboard config: {str(e)}")
        return {
            "port": 5000,
            "host": "127.0.0.1",
            "debug": False,
            "users": [DEFAULT_ADMIN],
            "session_lifetime": 3600
        }

# Load config
dashboard_config = load_config()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# API authentication decorator
def api_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip auth if disabled
        if not dashboard_config.get("enable_api_auth", True):
            return f(*args, **kwargs)
            
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key required"}), 401
            
        # Validate API key
        valid_keys = dashboard_config.get("api_keys", [])
        if api_key not in valid_keys:
            return jsonify({"error": "Invalid API key"}), 401
            
        return f(*args, **kwargs)
    return decorated_function

# Connect to ArbitrageX components
def get_security_manager() -> Optional[Any]:
    """Get the security manager instance if available."""
    try:
        return SecurityManager()
    except Exception as e:
        logger.error(f"Error initializing security manager: {str(e)}")
        return None

# Routes

@app.route('/')
@login_required
def index():
    """Dashboard home page."""
    return render_template('index.html', 
                           title="ArbitrageX Dashboard",
                           config=dashboard_config,
                           page="dashboard")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check credentials
        valid_login = False
        user_data = None
        
        for user in dashboard_config.get("users", []):
            if user["username"] == username and check_password_hash(user["password_hash"], password):
                valid_login = True
                user_data = user
                break
        
        if valid_login:
            session['user'] = username
            session['email'] = user_data.get("email", "")
            session['last_login'] = datetime.datetime.now().isoformat()
            
            # Notify of login
            try:
                notify(
                    title="Dashboard Login",
                    message=f"User {username} logged in to the dashboard",
                    category="SECURITY",
                    priority="MEDIUM"
                )
            except Exception as e:
                logger.error(f"Error sending login notification: {str(e)}")
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            error = "Invalid credentials. Please try again."
    
    return render_template('login.html', 
                           title="Login - ArbitrageX Dashboard",
                           error=error)

@app.route('/logout')
def logout():
    """User logout."""
    username = session.get('user', 'Unknown')
    session.clear()
    flash("You have been logged out", "info")
    
    # Notify of logout
    try:
        notify(
            title="Dashboard Logout",
            message=f"User {username} logged out from the dashboard",
            category="SECURITY",
            priority="LOW"
        )
    except Exception:
        pass
    
    return redirect(url_for('login'))

@app.route('/trades')
@login_required
def trades():
    """View trade history and performance."""
    return render_template('trades.html', 
                           title="Trades - ArbitrageX Dashboard",
                           config=dashboard_config,
                           page="trades")

@app.route('/strategies')
@login_required
def strategies():
    """View and configure trading strategies."""
    return render_template('strategies.html', 
                           title="Strategies - ArbitrageX Dashboard",
                           config=dashboard_config,
                           page="strategies")

@app.route('/backtesting')
@login_required
def backtesting():
    """Backtesting interface."""
    return render_template('backtesting.html', 
                           title="Backtesting - ArbitrageX Dashboard",
                           config=dashboard_config,
                           page="backtesting")

@app.route('/notifications')
@login_required
def notifications():
    """View and manage notifications."""
    return render_template('notifications.html', 
                           title="Notifications - ArbitrageX Dashboard",
                           config=dashboard_config,
                           page="notifications")

@app.route('/security')
@login_required
def security():
    """Security management interface."""
    return render_template('security.html', 
                           title="Security - ArbitrageX Dashboard",
                           config=dashboard_config,
                           page="security")

@app.route('/settings')
@login_required
def settings():
    """Dashboard and bot settings."""
    return render_template('settings.html', 
                           title="Settings - ArbitrageX Dashboard",
                           config=dashboard_config,
                           page="settings")

@app.route('/profile')
@login_required
def profile():
    """User profile management."""
    return render_template('profile.html', 
                           title="Profile - ArbitrageX Dashboard",
                           config=dashboard_config,
                           page="profile")

@app.route('/logs')
@login_required
def logs():
    """View system logs."""
    return render_template('logs.html', 
                           title="Logs - ArbitrageX Dashboard",
                           config=dashboard_config,
                           page="logs")

@app.route('/wallet')
@login_required
def wallet():
    """Render the wallet management page."""
    return render_template('wallet.html', page='wallet')

@app.route('/networks')
def networks():
    return render_template('networks.html')

@app.route('/ml_visualization')
def ml_visualization():
    return render_template('ml_visualization.html')

@app.route('/system_monitor')
@login_required
def system_monitor():
    """Render the system monitoring page."""
    return render_template('system_monitor.html', page='system_monitor')

@app.route('/power_control')
@login_required
def power_control():
    """Render the power control page."""
    return render_template('power_control.html', page='power_control')

@app.route('/analytics')
@login_required
def analytics():
    """Render the trading analytics page."""
    return render_template('analytics.html', page='analytics')

@app.route('/flash_loans')
@login_required
def flash_loans():
    """Render the flash loan tracking and analysis page."""
    return render_template('flash_loans.html', page='flash_loans')

@app.route('/mev_protection')
@login_required
def mev_protection():
    """Render the MEV Protection Insights page."""
    return render_template('mev_protection.html')

# API Routes

@app.route('/api/status')
@api_auth_required
def api_status():
    """Get the current status of the trading bot."""
    try:
        # In a real implementation, we would query the actual bot's status
        # For demo, we'll use session data
        
        # Initialize default status if not set
        if 'bot_status' not in session:
            session['bot_status'] = 'stopped'
            session['stopped_since'] = datetime.now().isoformat()
        
        status = session.get('bot_status', 'stopped')
        
        response = {
            'success': True,
            'status': status,
            'mode': session.get('current_network', 'forked'),
            'strategy': session.get('active_strategy', 'ml_enhanced')
        }
        
        # Add timestamp information based on status
        if status == 'running':
            response['running_since'] = session.get('running_since')
        elif status == 'paused':
            response['paused_since'] = session.get('paused_since')
        else:
            response['stopped_since'] = session.get('stopped_since')
        
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error getting bot status: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/trades')
@api_auth_required
def api_trades():
    """Get trade history."""
    # In a real implementation, this would retrieve actual trade data
    # For now, return mock data
    mock_trades = [
        {
            "id": "T1001",
            "timestamp": "2023-10-15T14:32:15",
            "strategy": "ml_enhanced",
            "entry_price": 1820.45,
            "exit_price": 1825.60,
            "amount": 0.5,
            "profit": 2.58,
            "gas_cost": 0.12,
            "net_profit": 2.46,
            "status": "completed",
            "execution_time": 8.5
        },
        {
            "id": "T1002",
            "timestamp": "2023-10-15T15:45:22",
            "strategy": "l2",
            "entry_price": 1826.30,
            "exit_price": 1830.15,
            "amount": 0.75,
            "profit": 2.89,
            "gas_cost": 0.05,
            "net_profit": 2.84,
            "status": "completed",
            "execution_time": 5.2
        },
        {
            "id": "T1003",
            "timestamp": "2023-10-15T16:12:07",
            "strategy": "flash",
            "entry_price": 1829.75,
            "exit_price": 1827.20,
            "amount": 1.0,
            "profit": -2.55,
            "gas_cost": 0.18,
            "net_profit": -2.73,
            "status": "completed",
            "execution_time": 7.8
        }
    ]
    
    return jsonify({
        "trades": mock_trades,
        "total_count": len(mock_trades),
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/metrics')
@api_auth_required
def api_metrics():
    """Get system metrics."""
    # In a real implementation, this would retrieve actual metrics
    # For now, return mock data
    mock_metrics = {
        "total_trades": 175,
        "successful_trades": 128,
        "failed_trades": 47,
        "success_rate": 73.14,
        "total_profit": 328.45,
        "total_gas_cost": 42.18,
        "net_profit": 286.27,
        "avg_profit_per_trade": 1.64,
        "largest_profit": 15.72,
        "largest_loss": 8.34,
        "avg_execution_time": 7.2,
        "active_since": "2023-10-01T00:00:00"
    }
    
    return jsonify({
        "metrics": mock_metrics,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/notifications')
@api_auth_required
def api_notifications():
    """Get notifications."""
    # Placeholder implementation
    try:
        limit = request.args.get('limit', 10, type=int)
        category = request.args.get('category', None)
        priority = request.args.get('priority', None)
        
        # Placeholder data
        notifications = []
        # Add implementation here
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wallet/connect', methods=['POST'])
@api_auth_required
def api_wallet_connect():
    """Handle wallet connection."""
    try:
        data = request.json
        address = data.get('address')
        chain_id = data.get('chainId')
        
        # In a real implementation, you would store the connection info
        # For now, just return success
        
        return jsonify({
            'success': True,
            'message': f'Wallet {address} connected successfully'
        })
    except Exception as e:
        logger.error(f"Error connecting wallet: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wallet/transactions', methods=['GET'])
@api_auth_required
def api_wallet_transactions():
    """Get wallet transaction history."""
    try:
        address = request.args.get('address')
        tx_type = request.args.get('type')  # deposit, withdrawal, all
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # In a real implementation, you would fetch transactions from database
        # For now, return placeholder data
        
        # Mock transaction data
        mock_transactions = [
            {
                'id': '1',
                'type': 'deposit',
                'amount': '1.5',
                'token': 'ETH',
                'timestamp': int((datetime.datetime.now() - datetime.timedelta(hours=1)).timestamp() * 1000),
                'hash': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
                'status': 'completed',
                'network': 'mainnet',
                'gas': '0.002134 ETH'
            },
            {
                'id': '2',
                'type': 'withdrawal',
                'amount': '500',
                'token': 'USDC',
                'timestamp': int((datetime.datetime.now() - datetime.timedelta(days=1)).timestamp() * 1000),
                'hash': '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
                'status': 'completed',
                'network': 'arbitrum',
                'gas': '0.000134 ETH'
            },
            {
                'id': '3',
                'type': 'deposit',
                'amount': '0.25',
                'token': 'WETH',
                'timestamp': int((datetime.datetime.now() - datetime.timedelta(days=2)).timestamp() * 1000),
                'hash': '0x7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123456',
                'status': 'completed',
                'network': 'optimism',
                'gas': '0.000089 ETH'
            }
        ]
        
        # Filter by type if specified
        if tx_type and tx_type != 'all':
            mock_transactions = [tx for tx in mock_transactions if tx['type'] == tx_type]
        
        # Calculate pagination
        total = len(mock_transactions)
        total_pages = (total + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, total)
        
        return jsonify({
            'success': True,
            'transactions': mock_transactions[start_idx:end_idx],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'totalPages': total_pages
            }
        })
    except Exception as e:
        logger.error(f"Error getting wallet transactions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wallet/deposit', methods=['POST'])
@api_auth_required
def api_wallet_deposit():
    """Handle wallet deposit."""
    try:
        data = request.json
        address = data.get('address')
        token = data.get('token')
        amount = data.get('amount')
        
        # In a real implementation, you would handle the deposit
        # For now, just return success
        
        # Generate mock transaction hash
        import hashlib
        import time
        mock_hash = '0x' + hashlib.sha256(f"{address}{token}{amount}{time.time()}".encode()).hexdigest()
        
        return jsonify({
            'success': True,
            'message': f'Deposit of {amount} {token} initiated',
            'transaction': {
                'hash': mock_hash,
                'type': 'deposit',
                'amount': amount,
                'token': token,
                'timestamp': int(time.time() * 1000),
                'status': 'pending'
            }
        })
    except Exception as e:
        logger.error(f"Error processing deposit: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/wallet/withdraw', methods=['POST'])
@api_auth_required
def api_wallet_withdraw():
    """Handle wallet withdrawal."""
    try:
        data = request.json
        address = data.get('address')
        token = data.get('token')
        amount = data.get('amount')
        
        # In a real implementation, you would handle the withdrawal
        # For now, just return success
        
        # Generate mock transaction hash
        import hashlib
        import time
        mock_hash = '0x' + hashlib.sha256(f"{address}{token}{amount}{time.time()}".encode()).hexdigest()
        
        return jsonify({
            'success': True,
            'message': f'Withdrawal of {amount} {token} initiated',
            'transaction': {
                'hash': mock_hash,
                'type': 'withdrawal',
                'amount': amount,
                'token': token,
                'timestamp': int(time.time() * 1000),
                'status': 'pending'
            }
        })
    except Exception as e:
        logger.error(f"Error processing withdrawal: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/start', methods=['POST'])
@api_auth_required
def api_start():
    """Start the trading bot with the specified strategy."""
    try:
        data = request.json or {}
        
        # Get the requested strategy, defaulting to the current one or ml_enhanced
        strategy = data.get('strategy', session.get('active_strategy', 'ml_enhanced'))
        
        # In a real application, this would start the actual bot
        # For demo purposes, we'll just update the status
        app.logger.info(f"Bot started with strategy: {strategy}")
        
        # Update the stored status and strategy
        session['bot_status'] = 'running'
        session['running_since'] = datetime.now().isoformat()
        session['active_strategy'] = strategy
        
        # Emit the status change event via WebSocket
        socketio.emit('system_status', {
            'status': 'running',
            'running_since': session.get('running_since'),
            'strategy': strategy
        })
        
        return jsonify({
            'success': True,
            'message': f"Bot started with {strategy} strategy"
        })
    except Exception as e:
        app.logger.error(f"Error starting bot: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/stop', methods=['POST'])
@api_auth_required
def api_stop():
    """Stop the trading bot."""
    try:
        # In a real application, this would stop the actual bot
        # For demo purposes, we'll just update the status
        app.logger.info("Bot stopped")
        
        # Update the stored status
        session['bot_status'] = 'stopped'
        session['stopped_since'] = datetime.now().isoformat()
        
        # Emit the status change event
        socketio.emit('system_status', {
            'status': 'stopped',
            'stopped_since': session.get('stopped_since')
        })
        
        return jsonify({
            'success': True,
            'message': "Bot stopped successfully"
        })
    except Exception as e:
        app.logger.error(f"Error stopping bot: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/networks/status')
@api_auth_required
def api_networks_status():
    """Get current network status (mainnet vs fork)."""
    try:
        # Read current network configuration
        network_config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'network_config.json')
        
        # Default values if file doesn't exist
        current_network = 'fork'
        fork_running = False
        
        # Try to read the config file
        if os.path.exists(network_config_file):
            with open(network_config_file, 'r') as f:
                network_config = json.load(f)
                current_network = network_config.get('current_network', 'fork')
                fork_running = network_config.get('fork_running', False)
        else:
            # Create default config if doesn't exist
            os.makedirs(os.path.dirname(network_config_file), exist_ok=True)
            network_config = {
                'current_network': 'fork',
                'fork_running': False,
                'fork_settings': {
                    'block_number': None
                }
            }
            with open(network_config_file, 'w') as f:
                json.dump(network_config, f, indent=4)
        
        # If we're supposed to be running a fork, check if it's actually running
        if current_network == 'fork':
            # Simple check to see if anything is running on the default Hardhat port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8545))
            fork_running = (result == 0)
            sock.close()
            
            # Update the config file with the actual status
            network_config['fork_running'] = fork_running
            with open(network_config_file, 'w') as f:
                json.dump(network_config, f, indent=4)
        
        return jsonify({
            'success': True,
            'current_network': current_network,
            'fork_running': fork_running
        })
    except Exception as e:
        logger.error(f"Error getting network status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/networks/switch', methods=['POST'])
@api_auth_required
def api_networks_switch():
    """Switch between mainnet and forked mainnet."""
    try:
        data = request.json or {}
        network = data.get('network', 'fork')
        
        if network not in ['mainnet', 'fork']:
            return jsonify({
                'success': False,
                'error': 'Invalid network. Must be either "mainnet" or "fork".'
            }), 400
        
        # Load the current network config
        network_config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'network_config.json')
        
        try:
            if os.path.exists(network_config_file):
                with open(network_config_file, 'r') as f:
                    network_config = json.load(f)
            else:
                network_config = {
                    'current_network': 'fork',
                    'fork_running': False,
                    'fork_settings': {
                        'block_number': None
                    }
                }
        except Exception as e:
            logger.error(f"Error loading network config: {str(e)}")
            network_config = {
                'current_network': 'fork',
                'fork_running': False,
                'fork_settings': {
                    'block_number': None
                }
            }
        
        network_config['current_network'] = network
        
        # Save the updated config
        with open(network_config_file, 'w') as f:
            json.dump(network_config, f, indent=4)
        
        # If switching to mainnet, stop any running fork
        if network == 'mainnet' and network_config.get('fork_running', False):
            try:
                import subprocess
                subprocess.run(['kill', '$(lsof -t -i:8545)'], shell=True, check=False)
                network_config['fork_running'] = False
                
                # Save again after stopping the fork
                with open(network_config_file, 'w') as f:
                    json.dump(network_config, f, indent=4)
            except Exception as e:
                logger.warning(f"Error stopping fork when switching to mainnet: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully switched to {network}.'
        })
    except Exception as e:
        logger.error(f"Error switching network: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/networks/fork/start', methods=['POST'])
@api_auth_required
def api_networks_fork_start():
    """Start a forked mainnet instance."""
    try:
        data = request.json or {}
        block_number = data.get('block_number')
        
        # Check if port 8545 is already in use
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8545))
        fork_already_running = (result == 0)
        sock.close()
        
        if fork_already_running:
            # Stop existing fork before starting a new one
            import subprocess
            subprocess.run(['kill', '$(lsof -t -i:8545)'], shell=True, check=False)
            # Wait for port to become available
            import time
            time.sleep(2)
        
        # Load config
        network_config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'network_config.json')
        
        try:
            if os.path.exists(network_config_file):
                with open(network_config_file, 'r') as f:
                    network_config = json.load(f)
            else:
                network_config = {
                    'current_network': 'fork',
                    'fork_running': False,
                    'fork_settings': {
                        'block_number': None
                    }
                }
        except Exception as e:
            logger.error(f"Error loading network config: {str(e)}")
            network_config = {
                'current_network': 'fork',
                'fork_running': False,
                'fork_settings': {
                    'block_number': None
                }
            }
        
        # Update block number if provided
        if block_number is not None:
            network_config['fork_settings']['block_number'] = block_number
        
        # Check if fork is already running
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8545))
        fork_already_running = (result == 0)
        sock.close()
        
        if fork_already_running:
            # Stop existing fork before starting a new one
            import subprocess
            subprocess.run(['kill', '$(lsof -t -i:8545)'], shell=True, check=False)
            # Wait for port to become available
            import time
            time.sleep(2)
        
        # Start the fork
        try:
            import subprocess
            import os
            
            # Determine the Hardhat project directory
            hardhat_dir = os.path.join(os.path.dirname(__file__), '..', 'hardhat')
            
            # Construct the command
            command = 'npx hardhat node'
            if block_number:
                command += f' --fork https://eth-mainnet.alchemyapi.io/v2/YOUR_ALCHEMY_KEY --fork-block-number {block_number}'
            else:
                command += ' --fork https://eth-mainnet.alchemyapi.io/v2/YOUR_ALCHEMY_KEY'
            
            # Start the process in the background
            process = subprocess.Popen(command, shell=True, cwd=hardhat_dir,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                      start_new_session=True)
            
            # Wait a moment for the process to start
            time.sleep(3)
            
            # Check if it's running
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8545))
            fork_running = (result == 0)
            sock.close()
            
            if not fork_running:
                # Get stderr from the process
                _, stderr = process.communicate(timeout=1)
                error_message = stderr.decode('utf-8') if stderr else "Unknown error starting Hardhat node"
                raise Exception(f"Failed to start Hardhat node: {error_message}")
            
            # Update network config
            network_config['current_network'] = 'fork'
            network_config['fork_running'] = True
            
            # Save the updated config
            with open(network_config_file, 'w') as f:
                json.dump(network_config, f, indent=4)
            
            return jsonify({
                'success': True,
                'message': 'Successfully started Hardhat fork'
            })
        except Exception as e:
            logger.error(f"Error starting Hardhat fork: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    except Exception as e:
        logger.error(f"Error in fork start API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/networks/fork/stop', methods=['POST'])
@api_auth_required
def api_networks_fork_stop():
    """Stop the Hardhat fork of mainnet."""
    try:
        # Get current network config
        network_config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'network_config.json')
        
        if os.path.exists(network_config_file):
            with open(network_config_file, 'r') as f:
                network_config = json.load(f)
        else:
            network_config = {
                'current_network': 'fork',
                'fork_running': False,
                'fork_settings': {
                    'block_number': None
                }
            }
        
        # Stop the fork
        try:
            import subprocess
            subprocess.run(['kill', '$(lsof -t -i:8545)'], shell=True, check=False)
            
            # Verify it's stopped
            import socket
            import time
            time.sleep(2)  # Give it a moment to stop
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8545))
            fork_stopped = (result != 0)
            sock.close()
            
            if not fork_stopped:
                raise Exception("Failed to stop Hardhat node")
            
            # Update network config
            network_config['fork_running'] = False
            
            # Save the updated config
            with open(network_config_file, 'w') as f:
                json.dump(network_config, f, indent=4)
            
            return jsonify({
                'success': True,
                'message': 'Successfully stopped Hardhat fork'
            })
        except Exception as e:
            logger.error(f"Error stopping Hardhat fork: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    except Exception as e:
        logger.error(f"Error in fork stop API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/networks/fork/settings', methods=['POST'])
@api_auth_required
def api_networks_fork_settings():
    """Update settings for the Hardhat fork."""
    try:
        data = request.json
        block_number = data.get('block_number')
        
        # Get current network config
        network_config_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'network_config.json')
        
        if os.path.exists(network_config_file):
            with open(network_config_file, 'r') as f:
                network_config = json.load(f)
        else:
            network_config = {
                'current_network': 'fork',
                'fork_running': False,
                'fork_settings': {
                    'block_number': None
                }
            }
        
        # Update settings
        if 'fork_settings' not in network_config:
            network_config['fork_settings'] = {}
        
        network_config['fork_settings']['block_number'] = block_number
        
        # Save the updated config
        with open(network_config_file, 'w') as f:
            json.dump(network_config, f, indent=4)
        
        return jsonify({
            'success': True,
            'message': 'Successfully updated fork settings',
            'fork_running': network_config.get('fork_running', False)
        })
    except Exception as e:
        logger.error(f"Error updating fork settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trades/logs')
@api_auth_required
def api_trades_logs():
    """Get trade logs, optionally filtered by network (mainnet/fork)."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        network = request.args.get('network')  # Optional filter
        
        # In a real implementation, you would query the database
        # For now, we'll return mock data
        
        # Generate mock trade logs
        import random
        import time
        
        mock_logs = []
        total_logs = 25  # Total number of mock logs
        
        strategies = ['MEV-Protected', 'Layer 2', 'Flash Loan', 'Combined', 'ML-Enhanced']
        trading_pairs = ['ETH/USDC', 'WBTC/ETH', 'LINK/ETH', 'UNI/ETH', 'AAVE/ETH']
        statuses = ['completed', 'failed', 'pending']
        
        for i in range(total_logs):
            # Alternate between mainnet and fork for demo
            is_mainnet = (i % 2 == 0)
            
            # Generate a random profit/loss
            profit = random.uniform(-0.05, 0.15)
            if is_mainnet:
                # Mainnet trades are typically larger
                amount = random.uniform(0.5, 2.0)
            else:
                # Fork trades can be more experimental
                amount = random.uniform(1.0, 5.0)
            
            # Calculate profit in currency units
            profit_amount = amount * profit
            
            # Generate timestamp (older as i increases)
            timestamp = int(time.time() * 1000) - (i * 3600000)  # Each log is 1 hour older
            
            mock_logs.append({
                'id': str(total_logs - i),
                'network': 'mainnet' if is_mainnet else 'fork',
                'strategy': random.choice(strategies),
                'trading_pair': random.choice(trading_pairs),
                'amount': f"{amount:.4f} ETH",
                'profit': f"{profit_amount:.6f} ETH ({profit*100:.2f}%)",
                'status': random.choice(statuses),
                'timestamp': timestamp
            })
        
        # Filter by network if specified
        if network:
            mock_logs = [log for log in mock_logs if log['network'] == network]
        
        # Calculate pagination
        total = len(mock_logs)
        total_pages = (total + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, total)
        
        return jsonify({
            'success': True,
            'logs': mock_logs[start_idx:end_idx],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'totalPages': total_pages
            }
        })
    except Exception as e:
        logger.error(f"Error getting trade logs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trades/details/<trade_id>')
@api_auth_required
def api_trades_details(trade_id):
    """Get detailed information about a specific trade."""
    try:
        # In a real implementation, you would query the database
        # For now, we'll return mock data based on the trade ID
        
        # Convert trade_id to an integer for mock data generation
        try:
            trade_num = int(trade_id)
        except ValueError:
            trade_num = hash(trade_id) % 100  # Fallback for non-numeric IDs
        
        # Determine if this is a mainnet or fork trade based on the ID
        is_mainnet = (trade_num % 2 == 0)
        
        # Generate mock trade details
        import random
        import time
        
        strategies = ['MEV-Protected', 'Layer 2', 'Flash Loan', 'Combined', 'ML-Enhanced']
        trading_pairs = ['ETH/USDC', 'WBTC/ETH', 'LINK/ETH', 'UNI/ETH', 'AAVE/ETH']
        statuses = ['completed', 'failed', 'pending']
        
        # Use the trade ID to seed the random generator for consistent results
        random.seed(trade_num)
        
        # Generate a random profit/loss
        profit = random.uniform(-0.05, 0.15)
        if is_mainnet:
            # Mainnet trades are typically larger
            amount = random.uniform(0.5, 2.0)
        else:
            # Fork trades can be more experimental
            amount = random.uniform(1.0, 5.0)
        
        # Calculate profit in currency units
        profit_amount = amount * profit
        
        # Generate timestamp
        timestamp = int(time.time() * 1000) - (trade_num * 3600000)  # Each log is 1 hour older
        
        status = random.choice(statuses)
        
        # Generate mock trade steps
        steps = []
        step_count = random.randint(3, 6)
        
        for i in range(step_count):
            step_status = status
            if status == 'failed' and i >= random.randint(0, step_count - 1):
                step_status = 'failed'
            elif status == 'pending' and i >= random.randint(0, step_count - 1):
                step_status = 'pending'
            
            steps.append({
                'description': get_mock_step_description(i, step_count),
                'status': step_status
            })
        
        # Generate mock transactions
        transactions = []
        tx_count = random.randint(1, 3)
        
        for i in range(tx_count):
            tx_status = status
            if status == 'failed' and i >= random.randint(0, tx_count - 1):
                tx_status = 'failed'
            elif status == 'pending' and i >= random.randint(0, tx_count - 1):
                tx_status = 'pending'
            
            gas_used = random.randint(50000, 250000)
            gas_price = random.randint(10, 100)
            
            transactions.append({
                'hash': f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
                'status': tx_status,
                'gas_used': f"{gas_used} gas units",
                'gas_price': f"{gas_price} gwei",
                'method': get_mock_tx_method(i),
                'block_number': random.randint(15000000, 16000000) if tx_status == 'completed' else None
            })
        
        # Construct the mock trade object
        mock_trade = {
            'id': trade_id,
            'network': 'mainnet' if is_mainnet else 'fork',
            'strategy': random.choice(strategies),
            'trading_pair': random.choice(trading_pairs),
            'amount': f"{amount:.4f} ETH",
            'profit': f"{profit_amount:.6f} ETH ({profit*100:.2f}%)",
            'status': status,
            'timestamp': timestamp,
            'gas_used': f"{random.randint(50000, 500000)} gas units",
            'steps': steps,
            'transactions': transactions
        }
        
        return jsonify({
            'success': True,
            'trade': mock_trade
        })
    except Exception as e:
        logger.error(f"Error getting trade details: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_mock_step_description(step_index, total_steps):
    """Generate a mock step description based on the step index."""
    steps = [
        "Checking price difference between exchanges",
        "Calculating potential profit after gas costs",
        "Simulating trade execution",
        "Borrowing funds via flash loan",
        "Executing trade on DEX 1",
        "Executing trade on DEX 2",
        "Repaying flash loan",
        "Verifying profit"
    ]
    
    if step_index < len(steps):
        return steps[step_index]
    else:
        return f"Step {step_index + 1}"

def get_mock_tx_method(tx_index):
    """Generate a mock transaction method based on the tx index."""
    methods = [
        "flashloan(address,uint256)",
        "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)",
        "transferFrom(address,address,uint256)",
        "approve(address,uint256)"
    ]
    
    if tx_index < len(methods):
        return methods[tx_index]
    else:
        return f"method{tx_index + 1}()"

@app.route('/api/flash-loans/overview')
@api_auth_required
def api_flash_loans_overview():
    """Get an overview of flash loan usage and costs."""
    try:
        # In a real implementation, this would query a database
        # For demo purposes, we'll return mock data
        
        # Mock flash loan overview data
        mock_overview = {
            'success': True,
            'total_amount': '15,432.50',
            'total_fees': '15.43',
            'avg_loan_size': '547.82',
            'success_rate': '94.2',
            'currency': 'ETH'
        }
        
        return jsonify(mock_overview)
    except Exception as e:
        logger.error(f"Error getting flash loan overview: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flash-loans')
@api_auth_required
def api_flash_loans_list():
    """Get a list of flash loans with pagination and filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        provider = request.args.get('provider', 'all')
        
        # In a real implementation, this would query a database
        # For demo purposes, we'll return mock data
        
        # Generate mock flash loan data
        import random
        import time
        
        mock_loans = []
        total_loans = 25  # Total number of mock loans
        
        providers = ['aave', 'uniswap', 'balancer', 'maker']
        tokens = ['ETH', 'USDC', 'DAI', 'WBTC', 'USDT']
        trade_results = ['success', 'failed']
        
        for i in range(total_loans):
            # Generate loan provider (filter if necessary)
            loan_provider = random.choice(providers)
            if provider != 'all' and loan_provider != provider:
                continue
                
            # Generate timestamp (older as i increases)
            timestamp = int(time.time() * 1000) - (i * 3600000)  # Each loan is 1 hour older
            
            # Generate fee rate based on provider
            fee_rate = 0.0
            if loan_provider == 'aave':
                fee_rate = 0.09
            elif loan_provider == 'uniswap':
                fee_rate = 0.05
            elif loan_provider == 'balancer':
                fee_rate = 0.04
            elif loan_provider == 'maker':
                fee_rate = 0.08
            
            # Add some minor variation to fee rates
            fee_rate += random.uniform(-0.01, 0.01)
            fee_rate = max(0, fee_rate)  # Ensure non-negative
            
            # Generate loan amount
            amount = random.uniform(10, 1000)
            if loan_provider == 'aave':
                amount = random.uniform(100, 1000)  # Aave typically has larger loans
            
            # Calculate fee paid
            fee_paid = (amount * fee_rate) / 100
            
            # Determine trade result
            trade_result = random.choice(trade_results)
            if trade_result == 'success':
                # Success rate is higher
                if random.random() < 0.8:
                    trade_result = 'success'
                else:
                    trade_result = 'failed'
            
            # Format values for display
            amount_formatted = f"{amount:.4f}"
            fee_rate_formatted = f"{fee_rate:.2f}"
            fee_paid_formatted = f"{fee_paid:.6f}"
            
            mock_loans.append({
                'id': str(total_loans - i),
                'provider': loan_provider,
                'token': random.choice(tokens),
                'amount': amount_formatted,
                'fee_rate': fee_rate_formatted,
                'fee_paid': fee_paid_formatted,
                'trade_result': trade_result,
                'timestamp': timestamp
            })
        
        # Calculate pagination
        start_idx = (page - 1) * limit
        end_idx = min(start_idx + limit, len(mock_loans))
        
        return jsonify({
            'success': True,
            'loans': mock_loans[start_idx:end_idx],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': len(mock_loans),
                'has_more': end_idx < len(mock_loans)
            }
        })
    except Exception as e:
        logger.error(f"Error getting flash loans: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flash-loans/<loan_id>')
@api_auth_required
def api_flash_loan_details(loan_id):
    """Get detailed information about a specific flash loan."""
    try:
        # In a real implementation, this would query a database
        # For demo purposes, we'll generate mock data based on the loan ID
        
        import random
        import time
        
        providers = ['aave', 'uniswap', 'balancer', 'maker']
        tokens = ['ETH', 'USDC', 'DAI', 'WBTC', 'USDT']
        strategies = ['MEV-Protected', 'Layer 2', 'Flash Loan', 'Combined', 'ML-Enhanced']
        trading_pairs = ['ETH/USDC', 'WBTC/ETH', 'LINK/ETH', 'UNI/ETH', 'AAVE/ETH']
        
        # Use loan_id to seed random for consistent results
        random.seed(int(loan_id))
        
        # Generate provider
        provider = random.choice(providers)
        
        # Generate fee rate based on provider
        fee_rate = 0.0
        if provider == 'aave':
            fee_rate = 0.09
        elif provider == 'uniswap':
            fee_rate = 0.05
        elif provider == 'balancer':
            fee_rate = 0.04
        elif provider == 'maker':
            fee_rate = 0.08
        
        # Add some minor variation to fee rates
        fee_rate += random.uniform(-0.01, 0.01)
        fee_rate = max(0, fee_rate)  # Ensure non-negative
        
        # Generate loan amount
        amount = random.uniform(10, 1000)
        if provider == 'aave':
            amount = random.uniform(100, 1000)  # Aave typically has larger loans
        
        # Calculate fee paid
        fee_paid = (amount * fee_rate) / 100
        
        # Determine trade result
        if random.random() < 0.8:
            trade_result = 'success'
        else:
            trade_result = 'failed'
        
        # Generate timestamp
        timestamp = int(time.time() * 1000) - (int(loan_id) * 3600000)
        
        # Format values for display
        amount_formatted = f"{amount:.4f}"
        fee_rate_formatted = f"{fee_rate:.2f}"
        fee_paid_formatted = f"{fee_paid:.6f}"
        
        # Generate gas used
        gas_used = f"{random.randint(50000, 250000)} gas units"
        
        # Generate transaction details
        tx_hash = "0x" + ''.join(random.choices('0123456789abcdef', k=64))
        block_number = random.randint(15000000, 16000000)
        gas_price = random.randint(10, 100)
        gas_cost = f"{(random.randint(50000, 250000) * gas_price / 1e9):.6f} ETH"
        
        # Generate trade details (if successful)
        trade = None
        if trade_result == 'success':
            profit_percent = random.uniform(-0.5, 3.0)
            profit_amount = amount * profit_percent / 100
            net_result = profit_amount - fee_paid
            
            trade = {
                'strategy': random.choice(strategies),
                'trading_pair': random.choice(trading_pairs),
                'profit': f"{profit_amount:.6f} ETH ({profit_percent:.2f}%)",
                'net_result': f"{net_result:.6f} ETH"
            }
        
        # Create mock loan object
        mock_loan = {
            'id': loan_id,
            'provider': provider,
            'token': random.choice(tokens),
            'amount': amount_formatted,
            'fee_rate': fee_rate_formatted,
            'fee_paid': fee_paid_formatted,
            'gas_used': gas_used,
            'trade_result': trade_result,
            'timestamp': timestamp,
            'transaction': {
                'hash': tx_hash,
                'block_number': block_number,
                'gas_cost': gas_cost
            },
            'trade': trade
        }
        
        return jsonify({
            'success': True,
            'loan': mock_loan
        })
    except Exception as e:
        logger.error(f"Error getting loan details: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flash-loans/failure-cost', methods=['POST'])
@api_auth_required
def api_flash_loan_failure_cost():
    """Calculate the cost of a failed flash loan transaction."""
    try:
        data = request.json
        provider = data.get('provider')
        token = data.get('token')
        amount = data.get('amount')
        
        if not provider or not token or not amount:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
        
        # In a real implementation, this would calculate based on current rates
        # For demo purposes, we'll return mock data
        
        # Calculate flash loan fee based on provider
        fee_rate = 0.0
        if provider == 'aave':
            fee_rate = 0.09
        elif provider == 'uniswap':
            fee_rate = 0.05
        elif provider == 'balancer':
            fee_rate = 0.04
        elif provider == 'maker':
            fee_rate = 0.08
        
        loan_fee = (amount * fee_rate) / 100
        
        # Estimate gas cost
        gas_units = 250000  # Average gas units for a flash loan transaction
        gas_price = 20  # Gwei
        gas_cost_eth = (gas_units * gas_price) / 1e9
        
        # Calculate total failure cost
        failure_cost = loan_fee
        if provider != 'uniswap':
            # Some protocols don't charge the fee if the transaction fails
            failure_cost = 0
        
        # Add gas cost converted to token amount (simplified)
        eth_price_map = {
            'ETH': 1.0,
            'WBTC': 0.06,  # 1 ETH ≈ 0.06 WBTC
            'USDC': 2000,  # 1 ETH ≈ 2000 USDC
            'USDT': 2000,  # 1 ETH ≈ 2000 USDT
            'DAI': 2000    # 1 ETH ≈ 2000 DAI
        }
        
        gas_cost_in_token = gas_cost_eth
        if token != 'ETH':
            gas_cost_in_token = gas_cost_eth * eth_price_map[token]
        
        failure_cost += gas_cost_in_token
        
        # USD conversion (simplified)
        usd_price_map = {
            'ETH': 2000,
            'WBTC': 35000,
            'USDC': 1,
            'USDT': 1,
            'DAI': 1
        }
        
        failure_cost_usd = failure_cost * usd_price_map[token]
        
        return jsonify({
            'success': True,
            'loan_fee': f"{loan_fee:.6f}",
            'gas_cost': f"{gas_cost_eth:.6f}",
            'failure_cost': f"{failure_cost:.6f}",
            'failure_cost_usd': f"{failure_cost_usd:.2f}"
        })
    except Exception as e:
        logger.error(f"Error calculating failure cost: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flash-loans/fee-analysis')
@api_auth_required
def api_flash_loan_fee_analysis():
    """Get historical fee analysis data for flash loan providers."""
    try:
        days = request.args.get('days', 30, type=int)
        
        # In a real implementation, this would query historical data
        # For demo purposes, we'll generate mock data
        
        import random
        import datetime
        
        # Generate fee trend data (line chart)
        providers = ['Aave', 'Uniswap', 'Balancer', 'Maker']
        fee_trends = {}
        
        for provider in providers:
            fee_trends[provider] = []
            
            # Set base fee rate based on provider
            base_fee_rate = 0.0
            if provider == 'Aave':
                base_fee_rate = 0.09
            elif provider == 'Uniswap':
                base_fee_rate = 0.05
            elif provider == 'Balancer':
                base_fee_rate = 0.04
            elif provider == 'Maker':
                base_fee_rate = 0.08
            
            # Generate daily fee rates with some variation
            for i in range(days):
                date = datetime.datetime.now() - datetime.timedelta(days=days-i-1)
                
                # Add some random variation to the fee rate
                variation = random.uniform(-0.01, 0.01)
                if i > 0 and i % 10 == 0:
                    # Occasional larger changes (e.g., protocol updates)
                    variation = random.uniform(-0.03, 0.03)
                
                fee_rate = max(0, base_fee_rate + variation)
                
                fee_trends[provider].append({
                    'date': date.strftime('%Y-%m-%d'),
                    'fee_rate': round(fee_rate, 4)
                })
        
        # Generate fee distribution data (donut chart)
        fee_distribution = [
            {'provider': 'Aave', 'total_fees': random.uniform(5, 15)},
            {'provider': 'Uniswap', 'total_fees': random.uniform(3, 8)},
            {'provider': 'Balancer', 'total_fees': random.uniform(1, 4)},
            {'provider': 'Maker', 'total_fees': random.uniform(2, 6)}
        ]
        
        # Round fee values to 4 decimal places
        for item in fee_distribution:
            item['total_fees'] = round(item['total_fees'], 4)
        
        # Generate provider comparison data (table)
        provider_comparison = [
            {
                'name': 'Aave',
                'current_fee_rate': '0.09',
                'fee_structure': 'Fixed percentage',
                'example_cost': '0.09000',
                'notes': 'Fee charged regardless of transaction success'
            },
            {
                'name': 'Uniswap',
                'current_fee_rate': '0.05',
                'fee_structure': 'Fixed percentage',
                'example_cost': '0.05000',
                'notes': 'Fee charged even if transaction fails'
            },
            {
                'name': 'Balancer',
                'current_fee_rate': '0.04',
                'fee_structure': 'Fixed percentage',
                'example_cost': '0.04000',
                'notes': 'Lowest fees among major providers'
            },
            {
                'name': 'Maker',
                'current_fee_rate': '0.08',
                'fee_structure': 'Fixed percentage',
                'example_cost': '0.08000',
                'notes': 'Fee only charged on successful transactions'
            }
        ]
        
        return jsonify({
            'success': True,
            'fee_trends': fee_trends,
            'fee_distribution': fee_distribution,
            'provider_comparison': provider_comparison
        })
    except Exception as e:
        logger.error(f"Error getting fee analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# System Monitoring API Endpoints
@app.route('/api/system/metrics')
@api_auth_required
def api_system_metrics():
    """Get current system metrics for CPU, memory, disk, and network."""
    try:
        import psutil
        import time
        import platform
        import socket
        
        # Get CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count()
        
        # Get memory metrics
        memory = psutil.virtual_memory()
        memory_used_gb = round(memory.used / (1024 ** 3), 2)
        memory_total_gb = round(memory.total / (1024 ** 3), 2)
        
        # Get disk metrics
        disk = psutil.disk_usage('/')
        disk_used_gb = round(disk.used / (1024 ** 3), 2)
        disk_total_gb = round(disk.total / (1024 ** 3), 2)
        
        # Simulate network latency (in a real environment, you would ping actual endpoints)
        # Here we're generating some random values for demonstration
        import random
        current_latency = random.uniform(20, 150)
        avg_latency = random.uniform(30, 80)
        max_latency = max(current_latency, 120)  # Ensure max is at least higher than current
        
        metrics = {
            'cpu': {
                'usage': round(cpu_percent, 1),
                'cores': cpu_count
            },
            'memory': {
                'percent': round(memory.percent, 1),
                'used': f"{memory_used_gb} GB",
                'total': f"{memory_total_gb} GB"
            },
            'disk': {
                'percent': round(disk.percent, 1),
                'used': f"{disk_used_gb} GB",
                'total': f"{disk_total_gb} GB"
            },
            'network': {
                'current_latency': round(current_latency, 1),
                'avg_latency': round(avg_latency, 1),
                'max_latency': round(max_latency, 1)
            }
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        app.logger.error(f"Error getting system metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system/historical')
@api_auth_required
def api_system_historical():
    """Get historical system metrics for charts."""
    try:
        # In a real environment, this would fetch data from a database
        # Here, we'll generate mock data for demonstration
        import random
        from datetime import datetime, timedelta
        
        # Generate timestamps for the last 24 hours, one point per hour
        end_time = datetime.now()
        timestamps = [(end_time - timedelta(hours=i)).isoformat() for i in range(24, 0, -1)]
        
        # Generate CPU and memory usage data
        cpu_memory_data = []
        for timestamp in timestamps:
            cpu_memory_data.append({
                'timestamp': timestamp,
                'cpu': round(random.uniform(10, 90), 1),
                'memory': round(random.uniform(30, 80), 1)
            })
        
        # Generate network latency data
        network_data = []
        for timestamp in timestamps:
            network_data.append({
                'timestamp': timestamp,
                'latency': round(random.uniform(20, 150), 1)
            })
        
        # Generate disk I/O data
        disk_io_data = []
        for timestamp in timestamps:
            disk_io_data.append({
                'timestamp': timestamp,
                'read': round(random.uniform(0.5, 10), 2),
                'write': round(random.uniform(0.5, 8), 2)
            })
        
        # Generate network traffic data
        network_traffic_data = []
        for timestamp in timestamps:
            network_traffic_data.append({
                'timestamp': timestamp,
                'sent': round(random.uniform(100, 800), 2),
                'received': round(random.uniform(150, 1200), 2)
            })
        
        return jsonify({
            'success': True,
            'historical': {
                'cpu_memory': cpu_memory_data,
                'network': network_data,
                'disk_io': disk_io_data,
                'network_traffic': network_traffic_data
            }
        })
    except Exception as e:
        app.logger.error(f"Error getting historical data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system/processes')
@api_auth_required
def api_system_processes():
    """Get information about running processes."""
    try:
        import psutil
        from datetime import datetime
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'create_time', 'num_threads']):
            try:
                # Get process info
                process_info = proc.info
                
                # Calculate CPU and memory usage
                try:
                    cpu_percent = proc.cpu_percent(interval=0.1)
                    memory_percent = proc.memory_percent()
                except:
                    cpu_percent = 0.0
                    memory_percent = 0.0
                
                # Format creation time
                try:
                    create_time = datetime.fromtimestamp(process_info['create_time']).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    create_time = 'N/A'
                
                # Add process to list
                processes.append({
                    'pid': process_info['pid'],
                    'name': process_info['name'],
                    'status': process_info['status'],
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'started': create_time,
                    'threads': process_info['num_threads']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort processes by CPU usage (descending)
        processes = sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)
        
        # Limit to top 20 processes
        processes = processes[:20]
        
        return jsonify({
            'success': True,
            'processes': processes
        })
    except Exception as e:
        app.logger.error(f"Error getting processes: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/system/info')
@api_auth_required
def api_system_info():
    """Get general system information."""
    try:
        import psutil
        import platform
        import socket
        from datetime import datetime
        
        # Get system boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        
        # Get CPU information
        cpu_info = platform.processor()
        
        # Get memory information
        memory = psutil.virtual_memory()
        memory_total = round(memory.total / (1024 ** 3), 2)
        
        # Get disk information
        disk = psutil.disk_usage('/')
        disk_total = round(disk.total / (1024 ** 3), 2)
        
        # Calculate uptime
        uptime_seconds = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
        uptime_days = int(uptime_seconds // (24 * 3600))
        uptime_hours = int((uptime_seconds % (24 * 3600)) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        uptime = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"
        
        # Get network interfaces
        net_if_addrs = psutil.net_if_addrs()
        network_interfaces = []
        for interface, addrs in net_if_addrs.items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    network_interfaces.append(f"{interface} ({addr.address})")
                    break
        
        # Use first available network interface
        network_interface = network_interfaces[0] if network_interfaces else "N/A"
        
        system_info = {
            'os': f"{platform.system()} {platform.release()}",
            'python': platform.python_version(),
            'cpu': cpu_info,
            'memory': f"{memory_total} GB",
            'disk': f"{disk_total} GB",
            'hostname': socket.gethostname(),
            'uptime': uptime,
            'version': "1.5.0",  # ArbitrageX version
            'last_reboot': boot_time,
            'network': network_interface
        }
        
        return jsonify({
            'success': True,
            'info': system_info
        })
    except Exception as e:
        app.logger.error(f"Error getting system info: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ML Visualization API Endpoints
@app.route('/api/ml/models', methods=['GET'])
def get_ml_models():
    """Get an overview of ML models used by the trading bot"""
    # In a real environment, this would fetch data from a database or ML service
    # Here, we simulate data for demonstration purposes
    models = {
        'success': True,
        'models': {
            'reinforcement_learning': {
                'name': 'Reinforcement Learning',
                'description': 'DQN-based model for optimizing trade execution',
                'status': 'Active',
                'accuracy': 87.5,
                'training_env': 'Forked Mainnet',
                'last_updated': '2023-05-15T10:22:45Z'
            },
            'price_impact_prediction': {
                'name': 'Price Impact Prediction',
                'description': 'LSTM network for predicting trade slippage',
                'status': 'Active',
                'accuracy': 92.3,
                'training_env': 'Forked Mainnet',
                'last_updated': '2023-05-14T16:14:32Z'
            },
            'volatility_tracking': {
                'name': 'Volatility Tracking',
                'description': 'Recurrent neural network for market volatility prediction',
                'status': 'Training',
                'accuracy': 78.9,
                'training_env': 'Forked Mainnet',
                'last_updated': '2023-05-15T14:05:18Z'
            }
        }
    }
    return jsonify(models)

@app.route('/api/ml/events', methods=['GET'])
def get_ml_events():
    """Get recent ML learning events"""
    # In a real environment, this would fetch data from a database or ML service
    events = {
        'success': True,
        'events': [
            {
                'timestamp': '2023-05-15T14:32:21Z',
                'model': 'Reinforcement Learning',
                'environment': 'Forked Mainnet',
                'event_type': 'Parameter Update',
                'description': 'Learning rate reduced to 0.0005 due to convergence detection',
                'impact': 'Medium'
            },
            {
                'timestamp': '2023-05-15T14:25:18Z',
                'model': 'Price Impact Prediction',
                'environment': 'Forked Mainnet',
                'event_type': 'Training Cycle',
                'description': 'Completed training cycle with 500 new samples, MSE decreased by 1.2%',
                'impact': 'Low'
            },
            {
                'timestamp': '2023-05-15T14:15:45Z',
                'model': 'Volatility Tracking',
                'environment': 'Forked Mainnet',
                'event_type': 'Architecture Change',
                'description': 'Added dropout layer (0.2) to prevent overfitting',
                'impact': 'High'
            },
            {
                'timestamp': '2023-05-15T14:10:33Z',
                'model': 'Reinforcement Learning',
                'environment': 'Mainnet',
                'event_type': 'Action Selection',
                'description': 'Used exploitation policy for high-value trade (2.5 ETH)',
                'impact': 'High'
            },
            {
                'timestamp': '2023-05-15T14:05:12Z',
                'model': 'Price Impact Prediction',
                'environment': 'Mainnet',
                'event_type': 'Prediction',
                'description': 'Predicted 0.15% slippage for UniswapV3 trade, actual was 0.18%',
                'impact': 'Medium'
            }
        ]
    }
    return jsonify(events)

@app.route('/api/ml/training', methods=['GET'])
def get_training_data():
    """Get ML training data for visualization"""
    model = request.args.get('model', 'all')
    
    # Generate dummy learning curve data
    learning_curve = {}
    
    if model == 'all' or model == 'reinforcement_learning':
        learning_curve['Reinforcement Learning'] = generate_learning_curve_data(100, 65, 89)
    
    if model == 'all' or model == 'price_impact_prediction':
        learning_curve['Price Impact Prediction'] = generate_learning_curve_data(100, 75, 95)
    
    if model == 'all' or model == 'volatility_tracking':
        learning_curve['Volatility Tracking'] = generate_learning_curve_data(100, 55, 80)
    
    # Generate training statistics
    stats = {
        'episodes': 2457,
        'successful_trades': 1892,
        'failed_trades': 565,
        'success_rate': '77.0%',
        'avg_reward': '0.042 ETH',
        'exploration_rate': '0.15'
    }
    
    return jsonify({
        'success': True,
        'learning_curve': learning_curve,
        'stats': stats
    })

@app.route('/api/ml/adjustments', methods=['GET'])
def get_ml_adjustments():
    """Get ML-based execution adjustments"""
    # In a real environment, this would fetch data from a database or ML service
    adjustments = {
        'success': True,
        'adjustments': [
            {
                'timestamp': '2023-05-15T14:32:15Z',
                'environment': 'Mainnet',
                'trade_id': 'TR-8743',
                'original_strategy': 'UniswapV3 > Curve',
                'ml_adjustment': 'Added SushiSwap as intermediate step',
                'reason': 'Detected better pricing with multi-hop route',
                'outcome': 'Success',
                'improvement': '+0.12%'
            },
            {
                'timestamp': '2023-05-15T14:25:42Z',
                'environment': 'Forked Mainnet',
                'trade_id': 'TR-8742',
                'original_strategy': 'Curve > Balancer',
                'ml_adjustment': 'Delayed execution by 2 blocks',
                'reason': 'Predicted improved gas fees',
                'outcome': 'Success',
                'improvement': '+0.08%'
            },
            {
                'timestamp': '2023-05-15T14:15:18Z',
                'environment': 'Mainnet',
                'trade_id': 'TR-8741',
                'original_strategy': 'Uniswap > DODO',
                'ml_adjustment': 'Split into two smaller trades',
                'reason': 'Reduced price impact prediction',
                'outcome': 'Success',
                'improvement': '+0.21%'
            },
            {
                'timestamp': '2023-05-15T14:05:33Z',
                'environment': 'Forked Mainnet',
                'trade_id': 'TR-8740',
                'original_strategy': 'Balancer > Uniswap',
                'ml_adjustment': 'Changed to Balancer > Curve > Uniswap',
                'reason': 'Found arbitrage opportunity in route',
                'outcome': 'Success',
                'improvement': '+0.35%'
            },
            {
                'timestamp': '2023-05-15T13:55:21Z',
                'environment': 'Mainnet',
                'trade_id': 'TR-8739',
                'original_strategy': 'DODO > Curve',
                'ml_adjustment': 'Aborted trade',
                'reason': 'Detected high risk of MEV sandwich attack',
                'outcome': 'Success',
                'improvement': 'Avoided -0.5%'
            }
        ]
    }
    return jsonify(adjustments)

def generate_learning_curve_data(episodes, start_accuracy, end_accuracy):
    """Generate dummy learning curve data for visualization"""
    data = []
    
    import random
    import math
    
    # Create a logarithmic improvement curve
    for i in range(1, episodes + 1):
        progress = i / episodes
        # Logarithmic accuracy improvement
        accuracy = start_accuracy + (end_accuracy - start_accuracy) * (math.log10(9 * progress + 1))
        
        # Add some noise
        accuracy += random.uniform(-2, 2)
        accuracy = min(100, max(0, accuracy))
        
        # Generate reward data
        base_reward = 0.02 + 0.05 * (accuracy / 100)
        reward = base_reward + random.uniform(-0.01, 0.01)
        reward = max(0, reward)
        
        data.append({
            'episode': i,
            'accuracy': round(accuracy, 1),
            'reward': round(reward, 4)
        })
    
    return data

# SocketIO events

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    if "user" in session:
        emit('authentication', {'status': 'success', 'user': session['user']})
    else:
        emit('authentication', {'status': 'error', 'message': 'Not authenticated'})

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle subscription to real-time updates."""
    if "user" not in session:
        emit('subscription', {'status': 'error', 'message': 'Not authenticated'})
        return
    
    topic = data.get('topic')
    if topic:
        # Join the requested topic room
        from flask_socketio import join_room
        join_room(topic)
        emit('subscription', {'status': 'success', 'topic': topic})
    else:
        emit('subscription', {'status': 'error', 'message': 'Topic not specified'})

@app.route('/api/pause', methods=['POST'])
@api_auth_required
def api_pause():
    """Pause the bot's execution without completely stopping it."""
    try:
        # In a real application, implement the logic to pause the bot
        # For demo purposes, we'll just record the status change
        app.logger.info("Bot paused")
        
        # Update the stored status
        session['bot_status'] = 'paused'
        session['paused_since'] = datetime.now().isoformat()
        
        # Emit the status change event
        socketio.emit('system_status', {
            'status': 'paused',
            'paused_since': session.get('paused_since')
        })
        
        return jsonify({
            'success': True,
            'message': 'Bot paused successfully'
        })
    except Exception as e:
        app.logger.error(f"Error pausing bot: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/resume', methods=['POST'])
@api_auth_required
def api_resume():
    """Resume the bot's execution after it has been paused."""
    try:
        # In a real application, implement the logic to resume the bot
        # For demo purposes, we'll just record the status change
        app.logger.info("Bot resumed")
        
        # Update the stored status
        session['bot_status'] = 'running'
        session['running_since'] = datetime.now().isoformat()
        
        # Emit the status change event
        socketio.emit('system_status', {
            'status': 'running',
            'running_since': session.get('running_since')
        })
        
        return jsonify({
            'success': True,
            'message': 'Bot resumed successfully'
        })
    except Exception as e:
        app.logger.error(f"Error resuming bot: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/power/history')
@api_auth_required
def api_power_history():
    """Get the bot's power status history."""
    try:
        # In a real application, this would fetch from a database
        # For demo purposes, we'll generate some mock history
        
        # Check if we have any stored history
        if 'power_history' not in session:
            # Generate some mock history if none exists
            now = datetime.now()
            session['power_history'] = [
                {
                    'status': 'started',
                    'message': 'Bot started',
                    'timestamp': (now - timedelta(hours=12)).isoformat()
                },
                {
                    'status': 'paused',
                    'message': 'Bot paused',
                    'timestamp': (now - timedelta(hours=10)).isoformat()
                },
                {
                    'status': 'resumed',
                    'message': 'Bot resumed',
                    'timestamp': (now - timedelta(hours=9)).isoformat()
                },
                {
                    'status': 'stopped',
                    'message': 'Bot stopped',
                    'timestamp': (now - timedelta(hours=6)).isoformat()
                },
                {
                    'status': 'started',
                    'message': 'Bot started',
                    'timestamp': (now - timedelta(hours=2)).isoformat()
                }
            ]
        
        return jsonify({
            'success': True,
            'history': session.get('power_history', [])
        })
    except Exception as e:
        app.logger.error(f"Error getting power history: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/power/record-status', methods=['POST'])
@api_auth_required
def api_record_status():
    """Record a new power status event."""
    try:
        data = request.json
        
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'message': 'Invalid data. Status is required.'
            }), 400
        
        # In a real application, this would save to a database
        # For demo purposes, we'll store in the session
        if 'power_history' not in session:
            session['power_history'] = []
        
        status_entry = {
            'status': data.get('status', '').lower(),
            'message': data.get('message', f"Bot {data.get('status', '')}"),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        
        session['power_history'] = [status_entry] + session.get('power_history', [])
        
        return jsonify({
            'success': True,
            'message': 'Status recorded successfully'
        })
    except Exception as e:
        app.logger.error(f"Error recording status: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/power/set-strategy', methods=['POST'])
@api_auth_required
def api_set_strategy():
    """Set the active trading strategy."""
    try:
        data = request.json
        
        if not data or 'strategy' not in data:
            return jsonify({
                'success': False,
                'message': 'Invalid data. Strategy is required.'
            }), 400
        
        strategy = data.get('strategy')
        
        # Validate strategy
        valid_strategies = ['ml_enhanced', 'combined', 'l2', 'flash', 'mev_protected']
        if strategy not in valid_strategies:
            return jsonify({
                'success': False,
                'message': f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}"
            }), 400
        
        # In a real application, this would update the bot's configuration
        # For demo purposes, we'll just store in the session
        session['active_strategy'] = strategy
        
        # Update the status message in WebSocket
        socketio.emit('strategy_update', {
            'strategy': strategy
        })
        
        return jsonify({
            'success': True,
            'message': f"Strategy set to {strategy}"
        })
    except Exception as e:
        app.logger.error(f"Error setting strategy: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/power/schedule', methods=['POST'])
@api_auth_required
def api_set_schedule():
    """Schedule the bot to start and stop at specific times."""
    try:
        data = request.json
        
        if not data or 'start_time' not in data or 'stop_time' not in data:
            return jsonify({
                'success': False,
                'message': 'Invalid data. Start time and stop time are required.'
            }), 400
        
        start_time = data.get('start_time')
        stop_time = data.get('stop_time')
        
        # In a real application, this would set up a scheduler
        # For demo purposes, we'll just store in the session
        session['scheduled_start'] = start_time
        session['scheduled_stop'] = stop_time
        
        return jsonify({
            'success': True,
            'message': f"Schedule set: Start at {start_time}, Stop at {stop_time}"
        })
    except Exception as e:
        app.logger.error(f"Error setting schedule: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/power/emergency-stop', methods=['POST'])
@api_auth_required
def api_emergency_stop():
    """Execute an emergency stop of the bot."""
    try:
        # In a real application, this would implement an immediate halt of all operations
        # For demo purposes, we'll just update the status
        app.logger.info("Emergency stop executed")
        
        # Update the stored status
        session['bot_status'] = 'stopped'
        session['stopped_since'] = datetime.now().isoformat()
        
        # Record in history
        if 'power_history' not in session:
            session['power_history'] = []
        
        status_entry = {
            'status': 'emergency',
            'message': 'Emergency stop executed',
            'timestamp': datetime.now().isoformat()
        }
        
        session['power_history'] = [status_entry] + session.get('power_history', [])
        
        # Emit the status change event
        socketio.emit('system_status', {
            'status': 'stopped',
            'stopped_since': session.get('stopped_since')
        })
        
        return jsonify({
            'success': True,
            'message': 'Emergency stop executed successfully'
        })
    except Exception as e:
        app.logger.error(f"Error executing emergency stop: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/power/cancel-trades', methods=['POST'])
@api_auth_required
def api_cancel_trades():
    """Cancel all active trades."""
    try:
        # In a real application, this would implement trade cancellation logic
        # For demo purposes, we'll just log the action
        app.logger.info("All trades cancelled")
        
        # Record in history
        if 'power_history' not in session:
            session['power_history'] = []
        
        status_entry = {
            'status': 'cancelled',
            'message': 'All trades cancelled',
            'timestamp': datetime.now().isoformat()
        }
        
        session['power_history'] = [status_entry] + session.get('power_history', [])
        
        # Emit a notification event
        socketio.emit('trades_cancelled', {
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'message': 'All trades cancelled successfully'
        })
    except Exception as e:
        app.logger.error(f"Error cancelling trades: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/power/restart-services', methods=['POST'])
@api_auth_required
def api_restart_services():
    """Restart the bot's services."""
    try:
        # In a real application, this would implement service restart logic
        # For demo purposes, we'll just log the action
        app.logger.info("Services restarting")
        
        # Record in history
        if 'power_history' not in session:
            session['power_history'] = []
        
        status_entry = {
            'status': 'restarting',
            'message': 'Services restarting',
            'timestamp': datetime.now().isoformat()
        }
        
        session['power_history'] = [status_entry] + session.get('power_history', [])
        
        # Emit a notification event
        socketio.emit('services_restarting', {
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({
            'success': True,
            'message': 'Services restarting'
        })
    except Exception as e:
        app.logger.error(f"Error restarting services: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/analytics/overview')
@api_auth_required
def api_analytics_overview():
    """Get overview metrics for the trading analytics dashboard."""
    try:
        # Get time period from query parameter
        period = request.args.get('period', 'day')
        
        # In a real application, this would query a database for actual trade data
        # For demo purposes, we'll generate mock data based on the period
        
        # Generate metrics based on time period
        if period == 'day':
            metrics = generate_daily_metrics()
            profit_data = generate_profit_data(24, 'hour')
            success_rate_data = generate_success_rate_data(24, 'hour')
            trade_count_data = generate_trade_count_data(24, 'hour')
            gas_data = generate_gas_data(24, 'hour')
            slippage_data = generate_slippage_data(24, 'hour')
            breakdown = generate_hourly_breakdown()
        elif period == 'week':
            metrics = generate_weekly_metrics()
            profit_data = generate_profit_data(7, 'day')
            success_rate_data = generate_success_rate_data(7, 'day')
            trade_count_data = generate_trade_count_data(7, 'day')
            gas_data = generate_gas_data(7, 'day')
            slippage_data = generate_slippage_data(7, 'day')
            breakdown = generate_daily_breakdown(7)
        elif period == 'month':
            metrics = generate_monthly_metrics()
            profit_data = generate_profit_data(30, 'day')
            success_rate_data = generate_success_rate_data(30, 'day')
            trade_count_data = generate_trade_count_data(30, 'day')
            gas_data = generate_gas_data(30, 'day')
            slippage_data = generate_slippage_data(30, 'day')
            breakdown = generate_daily_breakdown(30)
        elif period == 'year':
            metrics = generate_yearly_metrics()
            profit_data = generate_profit_data(12, 'month')
            success_rate_data = generate_success_rate_data(12, 'month')
            trade_count_data = generate_trade_count_data(12, 'month')
            gas_data = generate_gas_data(12, 'month')
            slippage_data = generate_slippage_data(12, 'month')
            breakdown = generate_monthly_breakdown()
        else:  # all time
            metrics = generate_all_time_metrics()
            profit_data = generate_profit_data(24, 'month')
            success_rate_data = generate_success_rate_data(24, 'month')
            trade_count_data = generate_trade_count_data(24, 'month')
            gas_data = generate_gas_data(24, 'month')
            slippage_data = generate_slippage_data(24, 'month')
            breakdown = generate_yearly_breakdown()
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'profit_data': profit_data,
            'success_rate_data': success_rate_data,
            'trade_count_data': trade_count_data,
            'gas_data': gas_data,
            'slippage_data': slippage_data,
            'breakdown': breakdown
        })
    except Exception as e:
        app.logger.error(f"Error getting analytics overview: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def generate_daily_metrics():
    """Generate metrics for daily view."""
    return {
        'profit_loss': '+0.1827 ETH',
        'profit_loss_change': 5.23,
        'win_loss_ratio': '3.42',
        'win_loss_ratio_change': 2.15,
        'success_rate': '77.3%',
        'success_rate_change': 1.78,
        'avg_gas_cost': '0.000428 ETH',
        'avg_gas_cost_change': -2.11
    }

def generate_weekly_metrics():
    """Generate metrics for weekly view."""
    return {
        'profit_loss': '+0.9542 ETH',
        'profit_loss_change': 8.67,
        'win_loss_ratio': '3.24',
        'win_loss_ratio_change': -1.21,
        'success_rate': '76.4%',
        'success_rate_change': -0.87,
        'avg_gas_cost': '0.000438 ETH',
        'avg_gas_cost_change': 1.43
    }

def generate_monthly_metrics():
    """Generate metrics for monthly view."""
    return {
        'profit_loss': '+4.2875 ETH',
        'profit_loss_change': 12.54,
        'win_loss_ratio': '3.18',
        'win_loss_ratio_change': 3.92,
        'success_rate': '76.1%',
        'success_rate_change': 2.36,
        'avg_gas_cost': '0.000452 ETH',
        'avg_gas_cost_change': 3.28
    }

def generate_yearly_metrics():
    """Generate metrics for yearly view."""
    return {
        'profit_loss': '+48.3621 ETH',
        'profit_loss_change': 23.78,
        'win_loss_ratio': '3.05',
        'win_loss_ratio_change': 7.42,
        'success_rate': '75.3%',
        'success_rate_change': 5.67,
        'avg_gas_cost': '0.000467 ETH',
        'avg_gas_cost_change': -8.54
    }

def generate_all_time_metrics():
    """Generate metrics for all time view."""
    return {
        'profit_loss': '+124.7389 ETH',
        'profit_loss_change': 0.0,
        'win_loss_ratio': '2.98',
        'win_loss_ratio_change': 0.0,
        'success_rate': '74.8%',
        'success_rate_change': 0.0,
        'avg_gas_cost': '0.000483 ETH',
        'avg_gas_cost_change': 0.0
    }

def generate_profit_data(num_points, interval):
    """Generate profit data points for the chart."""
    import random
    from datetime import datetime, timedelta
    
    data = []
    end_time = datetime.now()
    
    # Start with initial profit
    cumulative_profit = 0
    
    for i in range(num_points):
        if interval == 'hour':
            timestamp = end_time - timedelta(hours=num_points-i-1)
        elif interval == 'day':
            timestamp = end_time - timedelta(days=num_points-i-1)
        elif interval == 'month':
            timestamp = end_time - timedelta(days=30*(num_points-i-1))
            # Adjust to first day of month
            timestamp = timestamp.replace(day=1)
        
        # Generate a random profit/loss for this period
        if random.random() < 0.7:  # 70% chance of profit
            profit = random.uniform(0.01, 0.5)
        else:
            profit = random.uniform(-0.2, -0.01)
        
        # Add to cumulative profit
        cumulative_profit += profit
        
        data.append({
            'timestamp': timestamp.isoformat(),
            'value': round(cumulative_profit, 6)
        })
    
    return data

def generate_success_rate_data(num_points, interval):
    """Generate success rate data points for the chart."""
    import random
    from datetime import datetime, timedelta
    
    data = []
    end_time = datetime.now()
    
    # Start with base success rate
    base_rate = 75.0
    
    for i in range(num_points):
        if interval == 'hour':
            timestamp = end_time - timedelta(hours=num_points-i-1)
        elif interval == 'day':
            timestamp = end_time - timedelta(days=num_points-i-1)
        elif interval == 'month':
            timestamp = end_time - timedelta(days=30*(num_points-i-1))
            # Adjust to first day of month
            timestamp = timestamp.replace(day=1)
        
        # Generate success rate with small variations
        success_rate = base_rate + random.uniform(-5, 5)
        # Ensure rate is between 0 and 100
        success_rate = min(100, max(0, success_rate))
        
        data.append({
            'timestamp': timestamp.isoformat(),
            'value': round(success_rate, 1)
        })
        
        # Slightly adjust base rate for next point (with trend towards improvement)
        base_rate += random.uniform(-1, 1.2)
        base_rate = min(95, max(60, base_rate))
    
    return data

def generate_trade_count_data(num_points, interval):
    """Generate trade count data for the chart."""
    import random
    from datetime import datetime, timedelta
    
    data = []
    end_time = datetime.now()
    
    for i in range(num_points):
        if interval == 'hour':
            timestamp = end_time - timedelta(hours=num_points-i-1)
        elif interval == 'day':
            timestamp = end_time - timedelta(days=num_points-i-1)
        elif interval == 'month':
            timestamp = end_time - timedelta(days=30*(num_points-i-1))
            # Adjust to first day of month
            timestamp = timestamp.replace(day=1)
        
        # Generate total trades based on interval
        if interval == 'hour':
            total_trades = random.randint(10, 50)
        elif interval == 'day':
            total_trades = random.randint(100, 300)
        else:  # month
            total_trades = random.randint(2000, 5000)
        
        # Success rate between 70-80%
        success_rate = random.uniform(0.7, 0.8)
        successful = int(total_trades * success_rate)
        failed = total_trades - successful
        
        data.append({
            'timestamp': timestamp.isoformat(),
            'successful': successful,
            'failed': failed
        })
    
    return data

def generate_gas_data(num_points, interval):
    """Generate gas cost data points for the chart."""
    import random
    from datetime import datetime, timedelta
    
    data = []
    end_time = datetime.now()
    
    # Base gas cost with some variation
    base_gas = 0.00045
    
    for i in range(num_points):
        if interval == 'hour':
            timestamp = end_time - timedelta(hours=num_points-i-1)
        elif interval == 'day':
            timestamp = end_time - timedelta(days=num_points-i-1)
        elif interval == 'month':
            timestamp = end_time - timedelta(days=30*(num_points-i-1))
            # Adjust to first day of month
            timestamp = timestamp.replace(day=1)
        
        # Gas costs go up and down based on network congestion
        gas_cost = base_gas + random.uniform(-0.0001, 0.0001)
        gas_cost = max(0.0002, gas_cost)  # Ensure minimum value
        
        data.append({
            'timestamp': timestamp.isoformat(),
            'value': round(gas_cost, 6)
        })
        
        # Slightly adjust base gas for next point
        base_gas += random.uniform(-0.00002, 0.00002)
    
    return data

def generate_slippage_data(num_points, interval):
    """Generate slippage data points for the chart."""
    import random
    from datetime import datetime, timedelta
    
    data = []
    end_time = datetime.now()
    
    # Base slippage rate
    base_slippage = 0.25
    
    for i in range(num_points):
        if interval == 'hour':
            timestamp = end_time - timedelta(hours=num_points-i-1)
        elif interval == 'day':
            timestamp = end_time - timedelta(days=num_points-i-1)
        elif interval == 'month':
            timestamp = end_time - timedelta(days=30*(num_points-i-1))
            # Adjust to first day of month
            timestamp = timestamp.replace(day=1)
        
        # Slippage varies based on market volatility
        slippage = base_slippage + random.uniform(-0.15, 0.15)
        slippage = max(0.05, slippage)  # Ensure minimum value
        
        data.append({
            'timestamp': timestamp.isoformat(),
            'value': round(slippage, 2)
        })
        
        # Slightly adjust base slippage for next point
        base_slippage += random.uniform(-0.02, 0.02)
        base_slippage = min(0.5, max(0.1, base_slippage))
    
    return data

def generate_hourly_breakdown():
    """Generate hourly breakdown data for the table."""
    from datetime import datetime, timedelta
    import random
    
    breakdown = []
    now = datetime.now()
    
    # Add current hour
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    breakdown.append(generate_breakdown_row(f"{hour_start.hour}:00 - {hour_start.hour}:59", 15, 40))
    
    # Add past hours
    for i in range(1, 6):
        hour_start = now - timedelta(hours=i)
        hour_start = hour_start.replace(minute=0, second=0, microsecond=0)
        breakdown.append(generate_breakdown_row(f"{hour_start.hour}:00 - {hour_start.hour}:59", 20, 50))
    
    return breakdown

def generate_daily_breakdown(days=7):
    """Generate daily breakdown data for the table."""
    from datetime import datetime, timedelta
    import random
    
    breakdown = []
    now = datetime.now()
    
    # Add days
    for i in range(days):
        day = now - timedelta(days=i)
        breakdown.append(generate_breakdown_row(day.strftime("%Y-%m-%d"), 100, 300))
    
    return breakdown

def generate_monthly_breakdown():
    """Generate monthly breakdown data for the table."""
    from datetime import datetime, timedelta
    import random
    
    breakdown = []
    now = datetime.now()
    
    # Add months
    for i in range(12):
        month_start = datetime(now.year, now.month, 1) - timedelta(days=30*i)
        breakdown.append(generate_breakdown_row(month_start.strftime("%b %Y"), 2000, 5000))
    
    return breakdown

def generate_yearly_breakdown():
    """Generate yearly breakdown data for the table."""
    from datetime import datetime
    import random
    
    breakdown = []
    now = datetime.now()
    
    # Add years
    for i in range(3):
        year = now.year - i
        breakdown.append(generate_breakdown_row(str(year), 20000, 50000))
    
    return breakdown

def generate_breakdown_row(period, min_trades, max_trades):
    """Generate a single row for the breakdown table."""
    import random
    
    total_trades = random.randint(min_trades, max_trades)
    success_rate = random.uniform(70, 80)
    success_rate_str = f"{success_rate:.1f}%"
    
    avg_profit_per_trade = random.uniform(0.002, 0.005)
    total_profit = total_trades * success_rate/100 * avg_profit_per_trade
    
    profit_loss_str = f"{'+' if total_profit >= 0 else ''}{total_profit:.6f} ETH"
    
    avg_gas = random.uniform(0.0003, 0.0006)
    avg_gas_str = f"{avg_gas:.6f} ETH"
    
    avg_slippage = random.uniform(0.1, 0.4)
    avg_slippage_str = f"{avg_slippage:.2f}%"
    
    best_trade = random.uniform(0.01, 0.1)
    best_trade_str = f"+{best_trade:.6f} ETH"
    
    worst_trade = random.uniform(0.005, 0.02)
    worst_trade_str = f"-{worst_trade:.6f} ETH"
    
    return {
        'period': period,
        'total_trades': total_trades,
        'success_rate': success_rate_str,
        'profit_loss': profit_loss_str,
        'avg_gas': avg_gas_str,
        'avg_slippage': avg_slippage_str,
        'best_trade': best_trade_str,
        'worst_trade': worst_trade_str
    }

@app.route('/api/mev-protection/metrics')
@api_auth_required
def api_mev_protection_metrics():
    """Get MEV Protection metrics."""
    global mev_protection_insights
    
    try:
        if mev_protection_insights is None:
            mev_protection_insights = MEVProtectionInsights()
        
        metrics = mev_protection_insights.get_metrics()
        return jsonify(metrics)
    except Exception as e:
        app.logger.error(f"Error getting MEV protection metrics: {e}")
        return jsonify({
            "error": str(e),
            "protection_status": False,
            "protected_transactions": {
                "total": 0,
                "basic": 0,
                "enhanced": 0,
                "maximum": 0
            },
            "risk_levels": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "extreme": 0
            },
            "protection_methods": {
                "flashbots": 0,
                "eden_network": 0,
                "bloxroute": 0,
                "transaction_bundle": 0,
                "backrun_only": 0
            },
            "estimated_savings": 0.0,
            "last_updated": datetime.datetime.now().isoformat()
        })

@app.route('/api/mev-protection/insights')
@api_auth_required
def api_mev_protection_insights():
    """Get MEV Protection insights."""
    global mev_protection_insights
    
    try:
        if mev_protection_insights is None:
            mev_protection_insights = MEVProtectionInsights()
        
        insights = mev_protection_insights.get_insights()
        return jsonify(insights)
    except Exception as e:
        app.logger.error(f"Error getting MEV protection insights: {e}")
        return jsonify({
            "error": str(e),
            "historical_data": {
                "daily": {},
                "weekly": {},
                "monthly": {}
            },
            "high_risk_trades": [],
            "protected_vs_unprotected": {
                "protected": 0,
                "unprotected": 0
            },
            "savings_over_time": [],
            "last_updated": datetime.datetime.now().isoformat()
        })

@app.route('/api/mev-protection/summary')
@api_auth_required
def api_mev_protection_summary():
    """Get MEV Protection summary."""
    global mev_protection_insights
    
    try:
        if mev_protection_insights is None:
            mev_protection_insights = MEVProtectionInsights()
        
        summary = mev_protection_insights.get_protection_summary()
        return jsonify(summary)
    except Exception as e:
        app.logger.error(f"Error getting MEV protection summary: {e}")
        return jsonify({
            "error": str(e),
            "protection_status": False,
            "protected_transactions": 0,
            "protection_ratio": 0,
            "top_risk_level": "none",
            "top_protection_method": "none",
            "estimated_total_savings": 0.0,
            "estimated_daily_savings": 0.0,
            "high_risk_trades_count": 0,
            "last_updated": datetime.datetime.now().isoformat()
        })

@app.route('/api/mev-protection/toggle', methods=['POST'])
@api_auth_required
def api_mev_protection_toggle():
    """Toggle MEV Protection on/off."""
    global mev_protection_insights
    
    try:
        if mev_protection_insights is None:
            mev_protection_insights = MEVProtectionInsights()
        
        data = request.get_json()
        status = data.get('status', False)
        
        # Set the protection status
        success = mev_protection_insights.set_protection_status(status)
        
        if success:
            return jsonify({
                "success": True,
                "status": status
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to set protection status"
            })
    except Exception as e:
        app.logger.error(f"Error toggling MEV protection: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/mev-protection/settings', methods=['POST'])
@api_auth_required
def api_mev_protection_settings():
    """Save MEV Protection settings."""
    global mev_protection_insights
    
    try:
        if mev_protection_insights is None:
            mev_protection_insights = MEVProtectionInsights()
        
        data = request.get_json()
        
        # Get settings from request
        protection_status = data.get('protection_status', False)
        default_protection_level = data.get('default_protection_level', 'basic')
        preferred_protection_method = data.get('preferred_protection_method', 'auto')
        risk_threshold = data.get('risk_threshold', 'medium')
        
        # Set the protection status
        success_status = mev_protection_insights.set_protection_status(protection_status)
        
        # In a real implementation, we would save the other settings to the config
        # For now, we'll just log them
        app.logger.info(f"MEV Protection settings updated: default_level={default_protection_level}, "
                        f"preferred_method={preferred_protection_method}, risk_threshold={risk_threshold}")
        
        if success_status:
            return jsonify({
                "success": True
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update MEV protection settings"
            })
    except Exception as e:
        app.logger.error(f"Error saving MEV protection settings: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

# Main entry point
if __name__ == '__main__':
    port = dashboard_config.get('port', 5000)
    host = dashboard_config.get('host', '127.0.0.1')
    debug = dashboard_config.get('debug', False)
    
    logger.info(f"Starting ArbitrageX Dashboard on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug) 