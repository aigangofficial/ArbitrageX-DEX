#!/usr/bin/env python3
"""
Start Learning Loop Script

This script initializes and starts the learning loop for the ArbitrageX system.
It should be run when the system starts to enable continuous learning.
"""

import os
import sys
import time
import logging
import signal
import json
import argparse
from datetime import datetime

# Add the parent directory to the path so we can import the learning_loop module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.learning_loop import LearningLoop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("learning_loop_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LearningLoopService")

# Global variable to hold the learning loop instance
learning_loop = None

def signal_handler(sig, frame):
    """Handle signals to gracefully stop the learning loop."""
    logger.info(f"Received signal {sig}, stopping learning loop...")
    if learning_loop:
        learning_loop.stop()
    sys.exit(0)

def update_status_file(status_file, learning_loop_instance):
    """Update the status file with current learning loop statistics."""
    try:
        # Get current stats from the learning loop
        stats = learning_loop_instance.get_learning_stats()
        
        # Create the status data
        status_data = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "pid": os.getpid(),
            "stats": stats
        }
        
        # Write to the status file
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        logger.debug(f"Updated status file with stats: {stats}")
        return True
    except Exception as e:
        logger.error(f"Error updating status file: {e}")
        return False

def main():
    """Main function to start the learning loop."""
    global learning_loop
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start the ArbitrageX Learning Loop")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--update-interval", type=int, default=60, help="Status file update interval in seconds")
    args = parser.parse_args()
    
    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger("LearningLoop").setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    logger.info("Starting Learning Loop Service")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create the learning loop instance
    config_path = args.config if args.config else "backend/ai/config/learning_loop_config.json"
    learning_loop = LearningLoop(config_path=config_path)
    
    # Start the learning loop
    learning_loop.start()
    
    logger.info("Learning Loop Service started")
    
    # Create a status file to indicate the learning loop is running
    status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learning_loop_status.json")
    update_status_file(status_file, learning_loop)
    
    # Keep the script running
    try:
        update_interval = args.update_interval
        last_update_time = time.time()
        
        while True:
            current_time = time.time()
            
            # Update the status file at the specified interval
            if current_time - last_update_time >= update_interval:
                update_status_file(status_file, learning_loop)
                last_update_time = current_time
                
                # Log the current status
                stats = learning_loop.get_learning_stats()
                logger.info(f"Learning Loop Service is running. Stats: "
                           f"Queue: {stats.get('queue_size', 0)}, "
                           f"Processed: {stats.get('total_processed_results', 0)}, "
                           f"Updates: {stats.get('successful_model_updates', 0)}")
            
            # Process any pending tasks
            # This helps ensure the learning loop is actively processing
            # even if it's not doing so in its own thread
            try:
                # Check if there are any pending execution results
                if hasattr(learning_loop, '_process_execution_results'):
                    learning_loop._process_execution_results()
                
                # Check if it's time to update models
                if hasattr(learning_loop, '_check_and_update_models'):
                    learning_loop._check_and_update_models()
                
                # Check if it's time to adapt strategies
                if hasattr(learning_loop, '_check_and_adapt_strategies'):
                    learning_loop._check_and_adapt_strategies()
            except Exception as e:
                logger.error(f"Error processing learning loop tasks: {e}")
            
            # Sleep to prevent high CPU usage
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping learning loop...")
        learning_loop.stop()
    except Exception as e:
        logger.error(f"Error in Learning Loop Service: {e}")
        learning_loop.stop()
    finally:
        # Remove the status file
        if os.path.exists(status_file):
            os.remove(status_file)
        
        logger.info("Learning Loop Service stopped")

if __name__ == "__main__":
    main() 