#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX Security Manager

This module provides enhanced security features for the ArbitrageX trading bot,
including private key encryption, hardware wallet integration, spending limits,
and transaction validation.
"""

import os
import json
import time
import hmac
import base64
import logging
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Union
from eth_account import Account
from web3 import Web3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import keyring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend/ai/logs/security.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("security")

class SecurityManager:
    """
    Security manager for ArbitrageX trading bot.
    
    This class handles various security features including private key encryption,
    hardware wallet integration, spending limits, and transaction validation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the security manager.
        
        Args:
            config_path: Path to the security configuration file
        """
        self.config_path = config_path or "backend/ai/config/security.json"
        self.config = self._load_config()
        self.web3 = Web3()
        self.key_storage = KeyStorage(self.config.get("key_storage", {}))
        self.spending_limits = SpendingLimits(self.config.get("spending_limits", {}))
        self.transaction_validator = TransactionValidator(self.config.get("transaction_validator", {}))
        
        # Set up hardware wallet if enabled
        if self.config.get("hardware_wallet", {}).get("enabled", False):
            self.hardware_wallet = HardwareWalletManager(self.config.get("hardware_wallet", {}))
        else:
            self.hardware_wallet = None
        
        logger.info("Security manager initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load security configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Create default config
                config = self._create_default_config()
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
                return config
        except Exception as e:
            logger.error(f"Error loading security config: {str(e)}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default security configuration."""
        return {
            "key_storage": {
                "use_system_keyring": True,
                "encryption_enabled": True,
                "key_prefix": "arbitragex_"
            },
            "spending_limits": {
                "enabled": True,
                "max_daily_volume_eth": 10.0,
                "max_single_trade_eth": 2.0,
                "max_gas_price_gwei": 100.0,
                "max_daily_trades": 50,
                "cooldown_period_seconds": 60,
                "require_confirmation_above_eth": 1.0
            },
            "transaction_validator": {
                "enabled": True,
                "validate_all_transactions": True,
                "max_allowed_slippage": 0.01,
                "blacklisted_contracts": [],
                "whitelist_only": False,
                "whitelisted_contracts": []
            },
            "hardware_wallet": {
                "enabled": False,
                "provider": "ledger",  # "ledger" or "trezor"
                "derivation_path": "m/44'/60'/0'/0/0",
                "require_physical_confirmation": True
            },
            "access_control": {
                "api_auth_required": True,
                "api_token_expiry_hours": 24,
                "ip_whitelist": ["127.0.0.1"],
                "enable_jwt_auth": True,
                "require_2fa_for_withdrawals": True
            }
        }
    
    def secure_private_key(self, private_key: str, password: str) -> bool:
        """
        Securely store a private key.
        
        Args:
            private_key: The private key to store
            password: Password to encrypt the key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.key_storage.store_private_key(private_key, password)
        except Exception as e:
            logger.error(f"Error storing private key: {str(e)}")
            return False
    
    def get_private_key(self, password: str) -> Optional[str]:
        """
        Retrieve stored private key.
        
        Args:
            password: Password to decrypt the key
            
        Returns:
            The private key or None if not found/decryption failed
        """
        try:
            return self.key_storage.get_private_key(password)
        except Exception as e:
            logger.error(f"Error retrieving private key: {str(e)}")
            return None
    
    def validate_transaction(self, tx_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a transaction against security rules.
        
        Args:
            tx_data: Transaction data
            
        Returns:
            A tuple of (is_valid, reason)
        """
        try:
            # First check spending limits
            spending_check, spending_reason = self.spending_limits.check_limits(tx_data)
            if not spending_check:
                return False, spending_reason
            
            # Then validate transaction details
            tx_check, tx_reason = self.transaction_validator.validate(tx_data)
            if not tx_check:
                return False, tx_reason
            
            return True, "Transaction passed all security checks"
        except Exception as e:
            logger.error(f"Error validating transaction: {str(e)}")
            return False, f"Validation error: {str(e)}"
    
    def sign_transaction(self, tx_data: Dict[str, Any], password: Optional[str] = None) -> Optional[str]:
        """
        Sign a transaction using either stored private key or hardware wallet.
        
        Args:
            tx_data: Transaction data
            password: Password to decrypt private key (not needed for hardware wallet)
            
        Returns:
            Signed transaction or None if signing failed
        """
        try:
            # Validate transaction first
            is_valid, reason = self.validate_transaction(tx_data)
            if not is_valid:
                logger.error(f"Transaction validation failed: {reason}")
                return None
            
            # Use hardware wallet if available
            if self.hardware_wallet and self.hardware_wallet.is_connected():
                return self.hardware_wallet.sign_transaction(tx_data)
            
            # Otherwise use stored private key
            if password is None:
                logger.error("Password required for signing with stored private key")
                return None
            
            private_key = self.get_private_key(password)
            if not private_key:
                logger.error("Failed to retrieve private key")
                return None
            
            # Create transaction
            account = Account.from_key(private_key)
            
            # Build proper transaction based on EIP-1559 or legacy
            if 'maxFeePerGas' in tx_data:
                # EIP-1559 transaction
                signed_tx = account.sign_transaction(tx_data)
            else:
                # Legacy transaction
                signed_tx = account.sign_transaction(tx_data)
            
            return signed_tx.rawTransaction.hex()
        except Exception as e:
            logger.error(f"Error signing transaction: {str(e)}")
            return None
    
    def generate_api_token(self, user_id: str, expiry_hours: int = 24) -> str:
        """
        Generate a secure API token.
        
        Args:
            user_id: User identifier
            expiry_hours: Token expiry in hours
            
        Returns:
            Generated token
        """
        expiry = int(time.time()) + (expiry_hours * 3600)
        secret_key = self.config.get("access_control", {}).get("api_secret", os.urandom(32).hex())
        
        # Create payload
        payload = f"{user_id}:{expiry}"
        
        # Create signature
        signature = hmac.new(
            secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine and encode
        token = f"{payload}:{signature}"
        return base64.urlsafe_b64encode(token.encode()).decode()
    
    def validate_api_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an API token.
        
        Args:
            token: The token to validate
            
        Returns:
            A tuple of (is_valid, user_id)
        """
        try:
            # Decode token
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            parts = decoded.split(':')
            
            if len(parts) != 3:
                return False, None
            
            user_id, expiry_str, signature = parts
            
            # Check expiry
            expiry = int(expiry_str)
            if time.time() > expiry:
                return False, None
            
            # Validate signature
            secret_key = self.config.get("access_control", {}).get("api_secret", "")
            expected_signature = hmac.new(
                secret_key.encode(),
                f"{user_id}:{expiry_str}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            if signature != expected_signature:
                return False, None
            
            return True, user_id
        except Exception as e:
            logger.error(f"Error validating API token: {str(e)}")
            return False, None
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update security configuration.
        
        Args:
            new_config: New configuration values
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Merge with existing config
            self.config.update(new_config)
            
            # Update components
            if "key_storage" in new_config:
                self.key_storage.update_config(new_config["key_storage"])
            
            if "spending_limits" in new_config:
                self.spending_limits.update_config(new_config["spending_limits"])
            
            if "transaction_validator" in new_config:
                self.transaction_validator.update_config(new_config["transaction_validator"])
            
            if "hardware_wallet" in new_config:
                hw_config = new_config["hardware_wallet"]
                if hw_config.get("enabled", False):
                    if self.hardware_wallet:
                        self.hardware_wallet.update_config(hw_config)
                    else:
                        self.hardware_wallet = HardwareWalletManager(hw_config)
                elif self.hardware_wallet:
                    self.hardware_wallet = None
            
            # Save updated config
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error updating security config: {str(e)}")
            return False


class KeyStorage:
    """Manages secure storage and encryption of private keys."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize key storage.
        
        Args:
            config: Configuration for key storage
        """
        self.config = config
        self.use_system_keyring = config.get("use_system_keyring", True)
        self.encryption_enabled = config.get("encryption_enabled", True)
        self.key_prefix = config.get("key_prefix", "arbitragex_")
        
        # Key used for encryption if not using system keyring
        self.key_file = config.get("key_file", "backend/ai/config/key.enc")
        
        logger.info("Key storage initialized")
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update configuration."""
        self.config.update(config)
        self.use_system_keyring = self.config.get("use_system_keyring", True)
        self.encryption_enabled = self.config.get("encryption_enabled", True)
        self.key_prefix = self.config.get("key_prefix", "arbitragex_")
        self.key_file = self.config.get("key_file", "backend/ai/config/key.enc")
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password."""
        # Use a static salt (in a real app, this could be stored securely)
        salt = b'arbitragex_salt_static_value_123'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def store_private_key(self, private_key: str, password: str) -> bool:
        """
        Store private key securely.
        
        Args:
            private_key: The private key to store
            password: Password for encryption
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_system_keyring:
                # Use system keyring
                if self.encryption_enabled:
                    # Encrypt before storing in keyring
                    key = self._derive_key(password)
                    f = Fernet(key)
                    encrypted_key = f.encrypt(private_key.encode()).decode()
                    keyring.set_password("arbitragex", self.key_prefix + "private_key", encrypted_key)
                else:
                    # Store directly (not recommended)
                    keyring.set_password("arbitragex", self.key_prefix + "private_key", private_key)
            else:
                # Use file-based storage
                if not self.encryption_enabled:
                    logger.warning("Storing private key without encryption is not secure")
                    return False
                
                key = self._derive_key(password)
                f = Fernet(key)
                encrypted_key = f.encrypt(private_key.encode())
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
                
                # Save to file
                with open(self.key_file, 'wb') as file:
                    file.write(encrypted_key)
            
            return True
        except Exception as e:
            logger.error(f"Error storing private key: {str(e)}")
            return False
    
    def get_private_key(self, password: str) -> Optional[str]:
        """
        Retrieve private key.
        
        Args:
            password: Password for decryption
            
        Returns:
            The private key or None if not found/decryption failed
        """
        try:
            encrypted_key = None
            
            if self.use_system_keyring:
                # Get from system keyring
                encrypted_key = keyring.get_password("arbitragex", self.key_prefix + "private_key")
                if not encrypted_key:
                    logger.error("Private key not found in keyring")
                    return None
                
                if not self.encryption_enabled:
                    # Key is stored without encryption
                    return encrypted_key
                
                encrypted_key = encrypted_key.encode()
            else:
                # Get from file
                if not os.path.exists(self.key_file):
                    logger.error(f"Key file not found: {self.key_file}")
                    return None
                
                with open(self.key_file, 'rb') as file:
                    encrypted_key = file.read()
            
            # Decrypt
            key = self._derive_key(password)
            f = Fernet(key)
            decrypted_key = f.decrypt(encrypted_key).decode()
            
            return decrypted_key
        except Exception as e:
            logger.error(f"Error retrieving private key: {str(e)}")
            return None


class SpendingLimits:
    """Manages spending limits and trading restrictions."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize spending limits.
        
        Args:
            config: Configuration for spending limits
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.max_daily_volume_eth = config.get("max_daily_volume_eth", 10.0)
        self.max_single_trade_eth = config.get("max_single_trade_eth", 2.0)
        self.max_gas_price_gwei = config.get("max_gas_price_gwei", 100.0)
        self.max_daily_trades = config.get("max_daily_trades", 50)
        self.cooldown_period_seconds = config.get("cooldown_period_seconds", 60)
        
        # Thresholds
        self.require_confirmation_above_eth = config.get("require_confirmation_above_eth", 1.0)
        
        # Tracking daily usage
        self.daily_volume_eth = 0.0
        self.daily_trade_count = 0
        self.last_trade_time = 0
        self.usage_reset_time = time.time() + 86400  # Next 24 hours
        
        logger.info("Spending limits initialized")
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update configuration."""
        self.config.update(config)
        self.enabled = self.config.get("enabled", True)
        self.max_daily_volume_eth = self.config.get("max_daily_volume_eth", 10.0)
        self.max_single_trade_eth = self.config.get("max_single_trade_eth", 2.0)
        self.max_gas_price_gwei = self.config.get("max_gas_price_gwei", 100.0)
        self.max_daily_trades = self.config.get("max_daily_trades", 50)
        self.cooldown_period_seconds = self.config.get("cooldown_period_seconds", 60)
        self.require_confirmation_above_eth = self.config.get("require_confirmation_above_eth", 1.0)
    
    def _check_daily_reset(self) -> None:
        """Reset daily counters if needed."""
        current_time = time.time()
        if current_time > self.usage_reset_time:
            self.daily_volume_eth = 0.0
            self.daily_trade_count = 0
            self.usage_reset_time = current_time + 86400
            logger.info("Daily spending limits reset")
    
    def check_limits(self, tx_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if a transaction is within spending limits.
        
        Args:
            tx_data: Transaction data
            
        Returns:
            A tuple of (is_within_limits, reason)
        """
        if not self.enabled:
            return True, "Spending limits disabled"
        
        self._check_daily_reset()
        
        # Extract transaction value
        value_wei = int(tx_data.get("value", 0))
        value_eth = value_wei / 1e18
        
        # Extract gas price
        gas_price_wei = int(tx_data.get("gasPrice", 0))
        if gas_price_wei == 0:
            # Try EIP-1559 format
            gas_price_wei = int(tx_data.get("maxFeePerGas", 0))
        
        gas_price_gwei = gas_price_wei / 1e9
        
        # Check gas price limit
        if gas_price_gwei > self.max_gas_price_gwei:
            return False, f"Gas price ({gas_price_gwei} gwei) exceeds maximum limit ({self.max_gas_price_gwei} gwei)"
        
        # Check single trade limit
        if value_eth > self.max_single_trade_eth:
            return False, f"Trade size ({value_eth} ETH) exceeds maximum single trade limit ({self.max_single_trade_eth} ETH)"
        
        # Check daily volume limit
        if self.daily_volume_eth + value_eth > self.max_daily_volume_eth:
            return False, f"Trade would exceed daily volume limit of {self.max_daily_volume_eth} ETH"
        
        # Check daily trade count
        if self.daily_trade_count >= self.max_daily_trades:
            return False, f"Daily trade limit of {self.max_daily_trades} trades reached"
        
        # Check cooldown period
        current_time = time.time()
        if current_time - self.last_trade_time < self.cooldown_period_seconds:
            return False, f"Cooldown period not elapsed (wait {self.cooldown_period_seconds - (current_time - self.last_trade_time):.1f} seconds)"
        
        # Check confirmation threshold
        if value_eth > self.require_confirmation_above_eth:
            logger.warning(f"Trade exceeds confirmation threshold ({value_eth} ETH > {self.require_confirmation_above_eth} ETH)")
            # Note: This is just a warning, not a hard rejection
        
        return True, "Within spending limits"
    
    def record_trade(self, value_eth: float) -> None:
        """
        Record a completed trade for limit tracking.
        
        Args:
            value_eth: Value of the trade in ETH
        """
        self._check_daily_reset()
        
        self.daily_volume_eth += value_eth
        self.daily_trade_count += 1
        self.last_trade_time = time.time()
        
        logger.info(f"Trade recorded: {value_eth} ETH, daily total: {self.daily_volume_eth} ETH ({self.daily_trade_count} trades)")


class TransactionValidator:
    """Validates transactions for security and correctness."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize transaction validator.
        
        Args:
            config: Configuration for transaction validation
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.validate_all_transactions = config.get("validate_all_transactions", True)
        self.max_allowed_slippage = config.get("max_allowed_slippage", 0.01)  # 1%
        self.blacklisted_contracts = config.get("blacklisted_contracts", [])
        self.whitelist_only = config.get("whitelist_only", False)
        self.whitelisted_contracts = config.get("whitelisted_contracts", [])
        
        logger.info("Transaction validator initialized")
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update configuration."""
        self.config.update(config)
        self.enabled = self.config.get("enabled", True)
        self.validate_all_transactions = self.config.get("validate_all_transactions", True)
        self.max_allowed_slippage = self.config.get("max_allowed_slippage", 0.01)
        self.blacklisted_contracts = self.config.get("blacklisted_contracts", [])
        self.whitelist_only = self.config.get("whitelist_only", False)
        self.whitelisted_contracts = self.config.get("whitelisted_contracts", [])
    
    def validate(self, tx_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate a transaction.
        
        Args:
            tx_data: Transaction data
            
        Returns:
            A tuple of (is_valid, reason)
        """
        if not self.enabled:
            return True, "Transaction validation disabled"
        
        # Extract transaction data
        to_address = tx_data.get("to", "").lower()
        
        # Check blacklist
        if to_address in [addr.lower() for addr in self.blacklisted_contracts]:
            return False, f"Contract address {to_address} is blacklisted"
        
        # Check whitelist if enabled
        if self.whitelist_only and to_address not in [addr.lower() for addr in self.whitelisted_contracts]:
            return False, f"Contract address {to_address} is not whitelisted (whitelist-only mode enabled)"
        
        # Optional: Add more validation logic based on transaction data
        # For example, check expected token amounts, verify smart contract calls, etc.
        
        return True, "Transaction is valid"


class HardwareWalletManager:
    """Manages integration with hardware wallets."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize hardware wallet manager.
        
        Args:
            config: Configuration for hardware wallet
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        self.provider = config.get("provider", "ledger")  # "ledger" or "trezor"
        self.derivation_path = config.get("derivation_path", "m/44'/60'/0'/0/0")
        self.require_physical_confirmation = config.get("require_physical_confirmation", True)
        
        # This is a simulation for now
        # In a real implementation, this would connect to the hardware wallet
        self._connected = False
        if self.enabled:
            try:
                # Simulate connection
                self._connected = True
                logger.info(f"Connected to {self.provider} hardware wallet (simulated)")
            except Exception as e:
                logger.error(f"Failed to connect to hardware wallet: {str(e)}")
                self._connected = False
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """Update configuration."""
        self.config.update(config)
        self.enabled = self.config.get("enabled", False)
        self.provider = self.config.get("provider", "ledger")
        self.derivation_path = self.config.get("derivation_path", "m/44'/60'/0'/0/0")
        self.require_physical_confirmation = self.config.get("require_physical_confirmation", True)
    
    def is_connected(self) -> bool:
        """Check if hardware wallet is connected."""
        return self._connected
    
    def get_address(self) -> Optional[str]:
        """Get the Ethereum address from the hardware wallet."""
        if not self._connected:
            logger.error("Hardware wallet not connected")
            return None
        
        # Simulate getting address
        # In a real implementation, this would query the hardware wallet
        return "0x" + "0" * 40  # Dummy address
    
    def sign_transaction(self, tx_data: Dict[str, Any]) -> Optional[str]:
        """
        Sign a transaction using the hardware wallet.
        
        Args:
            tx_data: Transaction data
            
        Returns:
            Signed transaction or None if signing failed
        """
        if not self._connected:
            logger.error("Hardware wallet not connected")
            return None
        
        if self.require_physical_confirmation:
            logger.info("Waiting for physical confirmation on hardware wallet...")
            # In a real implementation, this would wait for user to confirm on device
            time.sleep(2)  # Simulate waiting for confirmation
        
        # Simulate signing
        # In a real implementation, this would send the transaction to the hardware wallet for signing
        return "0x" + "0" * 130  # Dummy signed transaction


def main():
    """Test the security manager functionality."""
    print("Initializing security manager...")
    security_manager = SecurityManager()
    
    # Test private key storage and retrieval
    print("\nTesting private key storage...")
    test_private_key = "0x" + "1" * 64  # Dummy private key
    test_password = "password123"
    
    success = security_manager.secure_private_key(test_private_key, test_password)
    print(f"Storing private key: {'Success' if success else 'Failed'}")
    
    retrieved_key = security_manager.get_private_key(test_password)
    print(f"Retrieving private key: {'Success' if retrieved_key == test_private_key else 'Failed'}")
    
    # Test transaction validation
    print("\nTesting transaction validation...")
    test_tx = {
        "to": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "value": int(0.5 * 1e18),  # 0.5 ETH
        "gasPrice": int(50 * 1e9),  # 50 gwei
        "gas": 21000
    }
    
    is_valid, reason = security_manager.validate_transaction(test_tx)
    print(f"Transaction valid: {is_valid}")
    print(f"Reason: {reason}")
    
    # Test API token generation and validation
    print("\nTesting API token generation...")
    test_user_id = "user123"
    token = security_manager.generate_api_token(test_user_id)
    print(f"Generated token: {token}")
    
    is_valid, user_id = security_manager.validate_api_token(token)
    print(f"Token validation: {'Success' if is_valid else 'Failed'}")
    print(f"User ID: {user_id}")
    
    print("\nSecurity manager test completed")


if __name__ == "__main__":
    main() 