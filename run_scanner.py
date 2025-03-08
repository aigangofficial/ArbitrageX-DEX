#!/usr/bin/env python3
"""
Run the Network Scanner directly.
"""

import os
import sys
import logging
import json
from backend.bot.network_scanner import NetworkScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scanner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ScannerRunner")

def main():
    """Main entry point."""
    logger.info("Starting Network Scanner")
    
    # Load configuration
    config_path = "backend/bot/bot_settings.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        logger.warning(f"Config file not found at {config_path}, using default values")
        config = {}
    
    # Initialize scanner
    scanner = NetworkScanner(config)
    
    # Run scanner
    try:
        logger.info("Running scanner...")
        scanner.scan()
    except Exception as e:
        logger.error(f"Error running scanner: {e}")
    
    logger.info("Scanner completed")

if __name__ == "__main__":
    main() 