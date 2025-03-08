#!/usr/bin/env python3
"""
Main script to migrate the project from TypeScript to Python.
This script will:
1. Remove TypeScript files
2. Replace TypeScript files with Python versions
3. Update references to TypeScript files in shell scripts and package.json
"""

import os
import sys
import logging
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_script(script_path):
    """Run a Python script."""
    try:
        logger.info(f"Running script: {script_path}")
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Script output: {result.stdout}")
        if result.stderr:
            logger.warning(f"Script errors: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running script {script_path}: {e}")
        logger.error(f"Script output: {e.stdout}")
        logger.error(f"Script errors: {e.stderr}")
        return False

def main():
    """Main function to migrate the project from TypeScript to Python."""
    logger.info("Starting migration from TypeScript to Python")
    
    # Define the scripts to run
    scripts = [
        "scripts/remove_typescript.py",
        "scripts/replace_typescript_files.py"
    ]
    
    # Run each script
    for script in scripts:
        if not os.path.exists(script):
            logger.error(f"Script {script} not found")
            continue
        
        success = run_script(script)
        if not success:
            logger.error(f"Script {script} failed")
            logger.error("Migration aborted")
            return
        
        # Wait a bit between scripts
        time.sleep(1)
    
    logger.info("Migration from TypeScript to Python completed successfully")
    logger.info("Next steps:")
    logger.info("1. Test the Python implementation")
    logger.info("2. Update any remaining references to TypeScript files")
    logger.info("3. Remove any unnecessary TypeScript configuration files")

if __name__ == "__main__":
    main() 