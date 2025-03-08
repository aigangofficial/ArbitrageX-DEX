"""
Install Dependencies for Enhanced Monitoring System

This script installs the required dependencies for the enhanced monitoring system.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("InstallDeps")

def install_package(package_name):
    """
    Install a Python package using pip.
    
    Args:
        package_name: Name of the package to install
        
    Returns:
        True if installation was successful, False otherwise
    """
    try:
        logger.info(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logger.info(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package_name}: {e}")
        return False

def main():
    """
    Main function to install dependencies.
    """
    # List of required packages
    required_packages = [
        "psutil",       # For system monitoring
        "matplotlib",   # For visualization
        "pandas",       # For data analysis
        "numpy",        # For numerical operations
        "tensorflow",   # For machine learning
        "scikit-learn", # For machine learning
        "web3",         # For blockchain interaction
    ]
    
    # Install each package
    success = True
    for package in required_packages:
        if not install_package(package):
            success = False
    
    if success:
        logger.info("All dependencies installed successfully")
    else:
        logger.warning("Some dependencies failed to install")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 