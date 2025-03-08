#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Security CLI

This module provides a command-line interface for configuring and using
the ArbitrageX security features, including key management, spending limits,
and transaction validation.
"""

import os
import sys
import json
import argparse
import getpass
import logging
from typing import Dict, Any, Optional

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from security.security_manager import SecurityManager
except ImportError:
    # Try relative import for when running from parent directory
    from security_manager import SecurityManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/ai/logs/security_cli.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("security_cli")


def store_private_key(security_manager: SecurityManager, args: argparse.Namespace) -> None:
    """
    Store a private key securely.
    
    Args:
        security_manager: The security manager instance
        args: Command line arguments
    """
    if args.key:
        private_key = args.key
    else:
        private_key = getpass.getpass("Enter private key to store: ")
    
    if not private_key.startswith("0x"):
        private_key = "0x" + private_key
    
    if len(private_key) != 66:  # 0x + 64 hex chars
        print("Error: Invalid private key format. Expected 64 hex characters with 0x prefix.")
        return
    
    password = getpass.getpass("Enter password for encryption: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        print("Error: Passwords do not match.")
        return
    
    success = security_manager.secure_private_key(private_key, password)
    
    if success:
        print("Private key stored successfully.")
    else:
        print("Failed to store private key. Check logs for details.")


def validate_tx(security_manager: SecurityManager, args: argparse.Namespace) -> None:
    """
    Validate a transaction.
    
    Args:
        security_manager: The security manager instance
        args: Command line arguments
    """
    tx_file = args.tx_file
    
    try:
        with open(tx_file, 'r') as f:
            tx_data = json.load(f)
        
        is_valid, reason = security_manager.validate_transaction(tx_data)
        
        if is_valid:
            print(f"Transaction is valid: {reason}")
        else:
            print(f"Transaction validation failed: {reason}")
    except FileNotFoundError:
        print(f"Error: Transaction file not found: {tx_file}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in transaction file: {tx_file}")
    except Exception as e:
        print(f"Error: {str(e)}")


def sign_tx(security_manager: SecurityManager, args: argparse.Namespace) -> None:
    """
    Sign a transaction.
    
    Args:
        security_manager: The security manager instance
        args: Command line arguments
    """
    tx_file = args.tx_file
    
    try:
        with open(tx_file, 'r') as f:
            tx_data = json.load(f)
        
        use_hardware = args.hardware
        
        if use_hardware:
            # Check if hardware wallet is available
            if not security_manager.hardware_wallet or not security_manager.hardware_wallet.is_connected():
                print("Error: Hardware wallet not connected or not enabled.")
                return
            
            signed_tx = security_manager.sign_transaction(tx_data)
        else:
            # Using software wallet
            password = getpass.getpass("Enter password to decrypt private key: ")
            signed_tx = security_manager.sign_transaction(tx_data, password)
        
        if signed_tx:
            # Save signed transaction to file
            output_file = args.output or tx_file.replace('.json', '_signed.json')
            with open(output_file, 'w') as f:
                json.dump({"signed_transaction": signed_tx}, f, indent=2)
            
            print(f"Transaction signed successfully. Saved to: {output_file}")
        else:
            print("Failed to sign transaction. Check logs for details.")
    except FileNotFoundError:
        print(f"Error: Transaction file not found: {tx_file}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in transaction file: {tx_file}")
    except Exception as e:
        print(f"Error: {str(e)}")


def generate_token(security_manager: SecurityManager, args: argparse.Namespace) -> None:
    """
    Generate an API token.
    
    Args:
        security_manager: The security manager instance
        args: Command line arguments
    """
    user_id = args.user
    expiry_hours = args.expiry
    
    token = security_manager.generate_api_token(user_id, expiry_hours)
    
    print("Generated API token:")
    print(token)
    print(f"\nThis token will expire in {expiry_hours} hours.")
    print("Keep it secure and do not share it with others.")


def validate_token(security_manager: SecurityManager, args: argparse.Namespace) -> None:
    """
    Validate an API token.
    
    Args:
        security_manager: The security manager instance
        args: Command line arguments
    """
    token = args.token
    
    is_valid, user_id = security_manager.validate_api_token(token)
    
    if is_valid:
        print(f"Token is valid for user: {user_id}")
    else:
        print("Token is invalid or expired.")


def update_config(security_manager: SecurityManager, args: argparse.Namespace) -> None:
    """
    Update security configuration.
    
    Args:
        security_manager: The security manager instance
        args: Command line arguments
    """
    config_file = args.config_file
    
    try:
        with open(config_file, 'r') as f:
            new_config = json.load(f)
        
        success = security_manager.update_config(new_config)
        
        if success:
            print("Security configuration updated successfully.")
        else:
            print("Failed to update security configuration. Check logs for details.")
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {config_file}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in configuration file: {config_file}")
    except Exception as e:
        print(f"Error: {str(e)}")


def enable_hw_wallet(security_manager: SecurityManager, args: argparse.Namespace) -> None:
    """
    Enable/configure hardware wallet.
    
    Args:
        security_manager: The security manager instance
        args: Command line arguments
    """
    provider = args.provider
    path = args.path
    
    hw_config = {
        "hardware_wallet": {
            "enabled": True,
            "provider": provider,
            "derivation_path": path,
            "require_physical_confirmation": True
        }
    }
    
    success = security_manager.update_config(hw_config)
    
    if success:
        if security_manager.hardware_wallet and security_manager.hardware_wallet.is_connected():
            print(f"Hardware wallet ({provider}) enabled and connected successfully.")
            
            # Get address from hardware wallet
            address = security_manager.hardware_wallet.get_address()
            if address:
                print(f"Ethereum address: {address}")
        else:
            print(f"Hardware wallet configuration updated, but connection not established.")
    else:
        print("Failed to enable hardware wallet. Check logs for details.")


def show_config(security_manager: SecurityManager, args: argparse.Namespace) -> None:
    """
    Show current security configuration.
    
    Args:
        security_manager: The security manager instance
        args: Command line arguments
    """
    # Sanitize config to hide sensitive information
    config = security_manager.config.copy()
    
    # Hide API secrets
    if "access_control" in config and "api_secret" in config["access_control"]:
        config["access_control"]["api_secret"] = "********"
    
    # Format and print
    json_str = json.dumps(config, indent=2)
    print("Current Security Configuration:")
    print(json_str)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="ArbitrageX Security Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Store a private key
  python security_cli.py store-key

  # Validate a transaction
  python security_cli.py validate-tx --tx-file transaction.json

  # Sign a transaction with stored private key
  python security_cli.py sign-tx --tx-file transaction.json

  # Sign a transaction with hardware wallet
  python security_cli.py sign-tx --tx-file transaction.json --hardware

  # Generate an API token
  python security_cli.py generate-token --user user123

  # Validate an API token
  python security_cli.py validate-token --token TOKEN_STRING

  # Update security configuration
  python security_cli.py update-config --config-file new_config.json

  # Enable hardware wallet
  python security_cli.py enable-hw-wallet --provider ledger

  # Show current configuration
  python security_cli.py show-config
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Store private key command
    store_key_parser = subparsers.add_parser("store-key", help="Store a private key securely")
    store_key_parser.add_argument("--key", help="Private key to store (if not provided, will prompt)")
    
    # Validate transaction command
    validate_tx_parser = subparsers.add_parser("validate-tx", help="Validate a transaction")
    validate_tx_parser.add_argument("--tx-file", required=True, help="Path to transaction JSON file")
    
    # Sign transaction command
    sign_tx_parser = subparsers.add_parser("sign-tx", help="Sign a transaction")
    sign_tx_parser.add_argument("--tx-file", required=True, help="Path to transaction JSON file")
    sign_tx_parser.add_argument("--hardware", action="store_true", help="Use hardware wallet for signing")
    sign_tx_parser.add_argument("--output", help="Output file for signed transaction")
    
    # Generate API token command
    gen_token_parser = subparsers.add_parser("generate-token", help="Generate an API token")
    gen_token_parser.add_argument("--user", required=True, help="User ID for the token")
    gen_token_parser.add_argument("--expiry", type=int, default=24, help="Token expiry in hours (default: 24)")
    
    # Validate API token command
    val_token_parser = subparsers.add_parser("validate-token", help="Validate an API token")
    val_token_parser.add_argument("--token", required=True, help="Token to validate")
    
    # Update configuration command
    update_config_parser = subparsers.add_parser("update-config", help="Update security configuration")
    update_config_parser.add_argument("--config-file", required=True, help="Path to configuration JSON file")
    
    # Enable hardware wallet command
    hw_wallet_parser = subparsers.add_parser("enable-hw-wallet", help="Enable hardware wallet")
    hw_wallet_parser.add_argument("--provider", choices=["ledger", "trezor"], default="ledger", help="Hardware wallet provider")
    hw_wallet_parser.add_argument("--path", default="m/44'/60'/0'/0/0", help="Derivation path")
    
    # Show configuration command
    subparsers.add_parser("show-config", help="Show current security configuration")
    
    return parser


def main():
    """Process command line arguments and execute commands."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Initialize security manager
        security_manager = SecurityManager()
        
        # Execute command
        if args.command == "store-key":
            store_private_key(security_manager, args)
        elif args.command == "validate-tx":
            validate_tx(security_manager, args)
        elif args.command == "sign-tx":
            sign_tx(security_manager, args)
        elif args.command == "generate-token":
            generate_token(security_manager, args)
        elif args.command == "validate-token":
            validate_token(security_manager, args)
        elif args.command == "update-config":
            update_config(security_manager, args)
        elif args.command == "enable-hw-wallet":
            enable_hw_wallet(security_manager, args)
        elif args.command == "show-config":
            show_config(security_manager, args)
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main() 