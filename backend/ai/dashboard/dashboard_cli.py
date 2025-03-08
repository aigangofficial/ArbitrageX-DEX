#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Dashboard CLI

Command-line interface for running and managing the ArbitrageX web dashboard.
"""

import os
import sys
import json
import argparse
import logging
import subprocess
import webbrowser
import time
from typing import Dict, Any

# Ensure dashboard directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Dashboard configuration path
DASHBOARD_CONFIG_PATH = "backend/ai/config/dashboard.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/ai/logs/dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dashboard_cli")

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="ArbitrageX Web Dashboard CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start dashboard
    start_parser = subparsers.add_parser("start", help="Start the web dashboard")
    start_parser.add_argument("--host", help="Host to bind to")
    start_parser.add_argument("--port", type=int, help="Port to run on")
    start_parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    start_parser.add_argument("--browser", action="store_true", help="Open in browser automatically")
    
    # Stop dashboard
    stop_parser = subparsers.add_parser("stop", help="Stop the running dashboard")
    
    # Create admin user
    user_parser = subparsers.add_parser("create-user", help="Create a new admin user")
    user_parser.add_argument("--username", required=True, help="Admin username")
    user_parser.add_argument("--password", required=True, help="Admin password")
    user_parser.add_argument("--email", help="Admin email")
    
    # Generate API key
    api_parser = subparsers.add_parser("generate-key", help="Generate a new API key")
    
    # Configure dashboard
    config_parser = subparsers.add_parser("configure", help="Configure dashboard settings")
    config_parser.add_argument("--host", help="Host to bind to")
    config_parser.add_argument("--port", type=int, help="Port to run on")
    config_parser.add_argument("--debug", type=bool, help="Debug mode")
    config_parser.add_argument("--theme", choices=["light", "dark"], help="Dashboard theme")
    config_parser.add_argument("--session-lifetime", type=int, help="Session lifetime in seconds")
    
    # Reset dashboard
    reset_parser = subparsers.add_parser("reset", help="Reset dashboard to defaults")
    reset_parser.add_argument("--confirm", action="store_true", help="Confirm reset")
    
    # Status
    status_parser = subparsers.add_parser("status", help="Check if dashboard is running")
    
    return parser.parse_args()

def load_config() -> Dict[str, Any]:
    """Load dashboard configuration or return default."""
    if os.path.exists(DASHBOARD_CONFIG_PATH):
        try:
            with open(DASHBOARD_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    return {
        "port": 5000,
        "host": "127.0.0.1",
        "debug": False,
        "users": [],
        "session_lifetime": 3600,
        "enable_api_auth": True,
        "api_keys": []
    }

def save_config(config: Dict[str, Any]) -> bool:
    """Save dashboard configuration to file."""
    try:
        os.makedirs(os.path.dirname(DASHBOARD_CONFIG_PATH), exist_ok=True)
        with open(DASHBOARD_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def get_dashboard_pid() -> int:
    """Get the PID of the running dashboard process."""
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if proc.info['cmdline'] and len(proc.info['cmdline']) > 1:
                cmdline = ' '.join(proc.info['cmdline'])
                if 'python' in cmdline and 'dashboard/app.py' in cmdline:
                    return proc.info['pid']
    except Exception as e:
        logger.error(f"Error getting dashboard PID: {e}")
    
    return None

def start_dashboard(args):
    """Start the web dashboard."""
    # Check if already running
    if get_dashboard_pid():
        print("Dashboard is already running. Use 'stop' command to stop it first.")
        return
    
    # Load config
    config = load_config()
    
    # Override with command-line args
    host = args.host or config.get('host', '127.0.0.1')
    port = args.port or config.get('port', 5000)
    debug = args.debug or config.get('debug', False)
    
    # Command to run dashboard
    cmd = [
        sys.executable,  # Current Python interpreter
        "backend/ai/dashboard/app.py"
    ]
    
    # Environment variables for configuration
    env = os.environ.copy()
    env["FLASK_APP"] = "backend/ai/dashboard/app.py"
    env["DASHBOARD_HOST"] = host
    env["DASHBOARD_PORT"] = str(port)
    env["DASHBOARD_DEBUG"] = "1" if debug else "0"
    
    # Start process
    print(f"Starting ArbitrageX Dashboard on {host}:{port}...")
    
    with open("backend/ai/logs/dashboard_stdout.log", "a") as stdout_log:
        with open("backend/ai/logs/dashboard_stderr.log", "a") as stderr_log:
            process = subprocess.Popen(
                cmd,
                stdout=stdout_log,
                stderr=stderr_log,
                env=env,
                start_new_session=True  # Detach from parent process
            )
    
    # Wait a moment to ensure it starts
    time.sleep(2)
    
    # Check if it's running
    if process.poll() is None:
        print(f"Dashboard started successfully with PID {process.pid}")
        print(f"Access at http://{host}:{port}/")
        
        # Open in browser if requested
        if args.browser:
            try:
                webbrowser.open(f"http://{host}:{port}/")
                print("Dashboard opened in browser")
            except Exception as e:
                print(f"Failed to open dashboard in browser: {e}")
    else:
        print("Failed to start dashboard. Check logs for details.")
        return

def stop_dashboard(args):
    """Stop the running dashboard."""
    pid = get_dashboard_pid()
    if not pid:
        print("Dashboard is not running.")
        return
    
    try:
        import signal
        import psutil
        
        process = psutil.Process(pid)
        process.send_signal(signal.SIGTERM)
        
        # Wait for process to terminate
        try:
            process.wait(timeout=5)
            print(f"Dashboard stopped (PID {pid})")
        except psutil.TimeoutExpired:
            # Force kill if it doesn't terminate gracefully
            process.kill()
            print(f"Dashboard process {pid} forcefully terminated")
    except Exception as e:
        print(f"Error stopping dashboard: {e}")

def create_user(args):
    """Create a new admin user."""
    from werkzeug.security import generate_password_hash
    
    # Load config
    config = load_config()
    
    # Create user object
    user = {
        "username": args.username,
        "password_hash": generate_password_hash(args.password),
        "email": args.email or f"{args.username}@example.com"
    }
    
    # Check if user already exists
    for existing_user in config.get("users", []):
        if existing_user.get("username") == args.username:
            print(f"User {args.username} already exists. Delete it first or choose a different username.")
            return
    
    # Add user to config
    if "users" not in config:
        config["users"] = []
    
    config["users"].append(user)
    
    # Save config
    if save_config(config):
        print(f"User {args.username} created successfully.")
    else:
        print("Failed to save configuration.")

def generate_api_key(args):
    """Generate a new API key."""
    import secrets
    
    # Generate a secure API key
    api_key = secrets.token_urlsafe(32)
    
    # Load config
    config = load_config()
    
    # Add API key
    if "api_keys" not in config:
        config["api_keys"] = []
    
    config["api_keys"].append(api_key)
    
    # Save config
    if save_config(config):
        print(f"New API key generated: {api_key}")
        print("Keep this key secure. It will not be shown again.")
    else:
        print("Failed to save configuration.")

def configure_dashboard(args):
    """Configure dashboard settings."""
    # Load config
    config = load_config()
    
    # Update configuration
    changes = False
    
    if args.host is not None:
        config["host"] = args.host
        changes = True
    
    if args.port is not None:
        config["port"] = args.port
        changes = True
    
    if args.debug is not None:
        config["debug"] = args.debug
        changes = True
    
    if args.theme is not None:
        if "appearance" not in config:
            config["appearance"] = {}
        config["appearance"]["theme"] = args.theme
        changes = True
    
    if args.session_lifetime is not None:
        config["session_lifetime"] = args.session_lifetime
        changes = True
    
    # Save if changes were made
    if changes:
        if save_config(config):
            print("Dashboard configuration updated successfully.")
        else:
            print("Failed to save configuration.")
    else:
        print("No configuration changes specified.")

def reset_dashboard(args):
    """Reset dashboard to defaults."""
    if not args.confirm:
        print("WARNING: This will reset all dashboard settings, users, and API keys.")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Reset canceled.")
            return
    
    # Default configuration
    default_config = {
        "port": 5000,
        "host": "127.0.0.1",
        "debug": False,
        "users": [],
        "session_lifetime": 3600,
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
    if save_config(default_config):
        print("Dashboard reset to default settings.")
    else:
        print("Failed to reset dashboard configuration.")

def check_status(args):
    """Check if the dashboard is running."""
    pid = get_dashboard_pid()
    if pid:
        import psutil
        try:
            process = psutil.Process(pid)
            # Get process info
            config = load_config()
            port = config.get('port', 5000)
            host = config.get('host', '127.0.0.1')
            
            print(f"Dashboard is running (PID {pid}):")
            print(f"- URL: http://{host}:{port}/")
            print(f"- Process: {process.name()} {' '.join(process.cmdline())}")
            print(f"- Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(process.create_time()))}")
            print(f"- Memory: {process.memory_info().rss / (1024 * 1024):.2f} MB")
        except Exception as e:
            print(f"Dashboard is running (PID {pid}), but error getting details: {e}")
    else:
        print("Dashboard is not running.")

def main():
    """Main function."""
    args = parse_args()
    
    if args.command == "start":
        start_dashboard(args)
    elif args.command == "stop":
        stop_dashboard(args)
    elif args.command == "create-user":
        create_user(args)
    elif args.command == "generate-key":
        generate_api_key(args)
    elif args.command == "configure":
        configure_dashboard(args)
    elif args.command == "reset":
        reset_dashboard(args)
    elif args.command == "status":
        check_status(args)
    else:
        print("Error: No command specified")
        print("Run 'dashboard_cli.py --help' for usage information")

if __name__ == "__main__":
    main() 