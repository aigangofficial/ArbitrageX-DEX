#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Create MEV-Protected Strategy Setup Tool

This script sets up the MEV-protected strategy by:
1. Creating necessary directories
2. Copying the required files
3. Setting up proper imports
4. Making files executable
"""

import os
import shutil
import stat
import subprocess
import sys

def create_directory(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def copy_file(source, destination):
    """Copy file from source to destination."""
    if os.path.exists(source):
        shutil.copy2(source, destination)
        print(f"Copied: {source} to {destination}")
    else:
        print(f"Error: Source file not found: {source}")
        sys.exit(1)

def make_executable(file_path):
    """Make file executable."""
    if os.path.exists(file_path):
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC)
        print(f"Made executable: {file_path}")
    else:
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

def run_command(command):
    """Run a shell command."""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Command executed successfully: {command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error message: {e.stderr}")
        sys.exit(1)

def check_imports():
    """Check if the necessary imports are available."""
    try:
        import web3
        import eth_account
        print("Required packages are installed: web3, eth_account")
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages:")
        print("pip install web3 eth-account")
        sys.exit(1)

def create_mev_protected_setup():
    """Set up the MEV-protected strategy."""
    # Check for required imports
    check_imports()
    
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_ai_dir = os.path.join(base_dir, "backend", "ai")
    tools_dir = os.path.join(base_dir, "tools")
    metrics_dir = os.path.join(backend_ai_dir, "metrics")
    
    # Create necessary directories
    create_directory(os.path.join(metrics_dir, "mev_protected"))
    create_directory(os.path.join(metrics_dir, "mev_protection"))
    create_directory(os.path.join(metrics_dir, "mev_protection_integration"))
    
    # Copy strategy files if they don't exist
    mev_protection_py = os.path.join(backend_ai_dir, "mev_protection.py")
    mev_protection_integration_py = os.path.join(backend_ai_dir, "mev_protection_integration.py")
    optimized_strategy_mev_protected_py = os.path.join(backend_ai_dir, "optimized_strategy_mev_protected.py")
    
    # Ensure MEV protection script exists
    if not os.path.exists(mev_protection_py):
        print("Error: MEV protection script not found. Please create it first.")
        print("This file should be located at:", mev_protection_py)
        sys.exit(1)
    
    # Ensure MEV protection integration script exists
    if not os.path.exists(mev_protection_integration_py):
        print("Error: MEV protection integration script not found. Please create it first.")
        print("This file should be located at:", mev_protection_integration_py)
        sys.exit(1)
    
    # Ensure MEV-protected strategy script exists
    if not os.path.exists(optimized_strategy_mev_protected_py):
        print("Error: MEV-protected strategy script not found. Please create it first.")
        print("This file should be located at:", optimized_strategy_mev_protected_py)
        sys.exit(1)
    
    # Make scripts executable
    make_executable(mev_protection_py)
    make_executable(mev_protection_integration_py)
    make_executable(optimized_strategy_mev_protected_py)
    
    # Ensure the shell script is executable
    run_mev_protected_strategy_sh = os.path.join(backend_ai_dir, "run_mev_protected_strategy.sh")
    if os.path.exists(run_mev_protected_strategy_sh):
        make_executable(run_mev_protected_strategy_sh)
    else:
        print("Warning: MEV-protected strategy shell script not found.")
        print("This file should be located at:", run_mev_protected_strategy_sh)
    
    print("\nMEV-Protected Strategy Setup Complete!")
    print("You can now run the MEV-protected strategy using:")
    print(f"  {run_mev_protected_strategy_sh}")
    print("\nFor full protection, make sure to provide valid private keys and API keys in production.")

if __name__ == "__main__":
    create_mev_protected_setup() 