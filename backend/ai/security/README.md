# ArbitrageX Security Features

This module provides enhanced security features for the ArbitrageX trading bot, ensuring safe and controlled usage in production environments with real funds.

## Features

- **Private Key Encryption**: Secure storage of private keys using strong encryption
- **Hardware Wallet Integration**: Support for Ledger and Trezor hardware wallets
- **Spending Limits**: Configurable limits on trade sizes and daily volumes
- **Transaction Validation**: Validation against blacklists and whitelists
- **API Authentication**: Secure token-based authentication for API access
- **Access Control**: IP whitelisting and permission management

## Usage

### Command Line Interface

The security features can be managed using the command-line interface:

```bash
# Store a private key securely
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
```

### Integration with ArbitrageX

Security features can be integrated with the ArbitrageX trading bot:

```python
from backend.ai.security import SecurityManager

# Initialize security manager
security_manager = SecurityManager()

# Validate a transaction
is_valid, reason = security_manager.validate_transaction(tx_data)

# Sign a transaction
signed_tx = security_manager.sign_transaction(tx_data, password)
```

## Configuration

Security settings are stored in `backend/ai/config/security.json`:

```json
{
  "key_storage": {
    "use_system_keyring": true,
    "encryption_enabled": true,
    "key_prefix": "arbitragex_"
  },
  "spending_limits": {
    "enabled": true,
    "max_daily_volume_eth": 10.0,
    "max_single_trade_eth": 2.0,
    "max_gas_price_gwei": 100.0,
    "max_daily_trades": 50,
    "cooldown_period_seconds": 60,
    "require_confirmation_above_eth": 1.0
  },
  "transaction_validator": {
    "enabled": true,
    "validate_all_transactions": true,
    "max_allowed_slippage": 0.01,
    "blacklisted_contracts": [],
    "whitelist_only": false,
    "whitelisted_contracts": []
  },
  "hardware_wallet": {
    "enabled": false,
    "provider": "ledger",
    "derivation_path": "m/44'/60'/0'/0/0",
    "require_physical_confirmation": true
  },
  "access_control": {
    "api_auth_required": true,
    "api_token_expiry_hours": 24,
    "ip_whitelist": ["127.0.0.1"],
    "enable_jwt_auth": true,
    "require_2fa_for_withdrawals": true
  }
}
```

## Key Storage Options

Private keys can be stored using two methods:

1. **System Keyring**: Uses the operating system's secure keyring (recommended)
2. **Encrypted File**: Stores keys in an encrypted file

## Hardware Wallet Support

The security module supports the following hardware wallets:

- **Ledger**: Uses the Ledger Nano S/X for transaction signing
- **Trezor**: Uses the Trezor hardware wallet for transaction signing

## Transaction Validation

Transactions are validated against several criteria:

- **Gas Price Limits**: Prevents transactions with excessive gas prices
- **Trade Size Limits**: Enforces maximum transaction values
- **Daily Volume Limits**: Limits total daily trading volume
- **Contract Blacklists**: Blocks transactions to known malicious contracts
- **Whitelist Mode**: Optionally allows transactions only to approved contracts

## API Authentication

The module provides secure API authentication:

- **Token Generation**: Creates signed and expiring tokens
- **Token Validation**: Validates tokens and extracts user information
- **IP Whitelisting**: Restricts API access to trusted IP addresses

## Best Practices

1. **Always use encryption** for private key storage
2. **Use hardware wallets** for production environments
3. **Set conservative spending limits** initially and adjust as needed
4. **Enable whitelist-only mode** in production for maximum security
5. **Regularly update** blacklisted contracts
6. **Rotate API tokens** regularly

## Security Considerations

- Private keys are extremely sensitive; handle with care
- Hardware wallets provide the highest level of security
- Spending limits provide a safety net against bugs or attacks
- API tokens should be treated as sensitive as passwords
- Consider using 2FA for critical operations 