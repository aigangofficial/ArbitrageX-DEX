#!/usr/bin/env python3
"""
ArbitrageX Main Runner

This script starts all components of the ArbitrageX application:
- API Server
- Network Scanner
- Bot Core (if available)

Usage:
    python run.py
"""

import os
import sys
import time
import signal
import logging
import subprocess
import threading
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arbitragex.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ArbitrageX")

# Global variables
processes: Dict[str, subprocess.Popen] = {}
running = True

def start_component(name: str, command: List[str]) -> None:
    """Start a component of the application."""
    try:
        logger.info(f"Starting {name}...")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        processes[name] = process
        
        # Start threads to read output
        threading.Thread(target=read_output, args=(process.stdout, f"{name} [OUT]"), daemon=True).start()
        threading.Thread(target=read_output, args=(process.stderr, f"{name} [ERR]"), daemon=True).start()
        
        logger.info(f"{name} started with PID {process.pid}")
    except Exception as e:
        logger.error(f"Failed to start {name}: {e}")

def read_output(pipe, prefix: str) -> None:
    """Read output from a process pipe and log it."""
    for line in iter(pipe.readline, ''):
        if line.strip():
            logger.info(f"{prefix}: {line.strip()}")

def stop_all() -> None:
    """Stop all running processes."""
    global running
    running = False
    
    logger.info("Stopping all components...")
    for name, process in processes.items():
        try:
            logger.info(f"Stopping {name} (PID {process.pid})...")
            process.terminate()
            # Give it some time to terminate gracefully
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning(f"{name} did not terminate gracefully, killing...")
            process.kill()
        except Exception as e:
            logger.error(f"Error stopping {name}: {e}")
    
    logger.info("All components stopped")

def signal_handler(sig, frame) -> None:
    """Handle termination signals."""
    logger.info(f"Received signal {sig}, shutting down...")
    stop_all()
    sys.exit(0)

def main() -> None:
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting ArbitrageX components...")
    
    # Start API server
    start_component("API Server", [sys.executable, "backend/api/server.py"])
    
    # Give the API server some time to start
    time.sleep(2)
    
    # Start Network Scanner
    try:
        start_component("Network Scanner", [sys.executable, "backend/bot/network_scanner.py"])
    except Exception as e:
        logger.warning(f"Could not start Network Scanner: {e}")
    
    # Start Bot Core if available
    try:
        start_component("Bot Core", [sys.executable, "backend/bot/bot_core.py"])
    except Exception as e:
        logger.warning(f"Could not start Bot Core: {e}")
    
    logger.info("All components started. Press Ctrl+C to stop.")
    
    # Keep the main thread alive
    try:
        while running:
            # Check if any process has terminated
            for name, process in list(processes.items()):
                if process.poll() is not None:
                    logger.error(f"{name} terminated unexpectedly with code {process.returncode}")
                    # Remove from processes dict
                    del processes[name]
                    
                    # Try to restart it
                    if name == "API Server":
                        start_component("API Server", [sys.executable, "backend/api/server.py"])
                    elif name == "Network Scanner":
                        start_component("Network Scanner", [sys.executable, "backend/bot/network_scanner.py"])
                    elif name == "Bot Core":
                        start_component("Bot Core", [sys.executable, "backend/bot/bot_core.py"])
            
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        stop_all()

if __name__ == "__main__":
    main() 