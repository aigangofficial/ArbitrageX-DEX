#!/usr/bin/env python3
"""
ArbitrageX Optimal Configuration Applier

This script applies the optimal configuration derived from mainnet fork testing
to the ArbitrageX system and validates the settings.
"""

import os
import json
import shutil
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('config_application.log')
    ]
)
logger = logging.getLogger('optimal_config_applier')

# Define paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '../..'))
OPTIMAL_CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config/optimal_strategy.json')
CONFIG_TARGETS = {
    'trade_selection': os.path.join(SCRIPT_DIR, 'config/trade_selection_config.json'),
    'mev_protection': os.path.join(SCRIPT_DIR, 'config/mev_protection_config.json'),
    'execution': os.path.join(PROJECT_ROOT, 'backend/execution/config/execution_config.json'),
    'bot': os.path.join(PROJECT_ROOT, 'backend/execution/config/bot_config.json')
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Apply optimal ArbitrageX configuration')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')
    parser.add_argument('--backup', action='store_true', help='Create backups of existing config files')
    parser.add_argument('--force', action='store_true', help='Apply config without confirmation')
    return parser.parse_args()

def load_json_file(file_path):
    """Load JSON from file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return {}

def save_json_file(file_path, data):
    """Save JSON to file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, sort_keys=False)
    logger.info(f"Updated configuration saved to: {file_path}")

def create_backup(file_path):
    """Create a backup of the specified file."""
    if not os.path.exists(file_path):
        logger.warning(f"Cannot backup non-existent file: {file_path}")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup of {file_path}: {e}")
        return False

def update_trade_selection_config(optimal_config, current_config):
    """Update trade selection configuration with optimal settings."""
    updated_config = current_config.copy()
    
    # Update network and token settings
    updated_config['networks'] = optimal_config['execution']['networks']
    updated_config['tokens'] = optimal_config['execution']['tokens']
    updated_config['dexes'] = optimal_config['execution']['dexes']
    
    # Update profit thresholds
    if 'profit_optimization' in optimal_config:
        profit_opt = optimal_config['profit_optimization']
        if 'thresholds' not in updated_config:
            updated_config['thresholds'] = {}
        
        updated_config['thresholds']['min_profit_usd'] = profit_opt['min_profit_usd']
        updated_config['thresholds']['min_profit_after_gas_percentage'] = profit_opt['min_profit_after_gas_percentage']
        
        # Add dynamic thresholds if they exist
        if 'dynamic_thresholds' in profit_opt:
            updated_config['thresholds']['dynamic'] = profit_opt['dynamic_thresholds']
    
    # Add priority pairs
    if 'priority_pairs' in optimal_config:
        updated_config['priority_pairs'] = optimal_config['priority_pairs']
    
    return updated_config

def update_mev_protection_config(optimal_config, current_config):
    """Update MEV protection configuration with optimal settings."""
    updated_config = current_config.copy()
    
    # Update MEV protection settings
    if 'mev_protection' in optimal_config:
        mev_config = optimal_config['mev_protection']
        
        # Ensure network-specific settings exist
        if 'network_settings' not in updated_config:
            updated_config['network_settings'] = {}
        
        # Update network-specific MEV protection settings
        for network, settings in mev_config.items():
            updated_config['network_settings'][network] = {
                **updated_config['network_settings'].get(network, {}),
                **settings
            }
    
    return updated_config

def update_execution_config(optimal_config, current_config):
    """Update execution configuration with optimal settings."""
    updated_config = current_config.copy()
    
    # Update batch size
    if 'execution' in optimal_config and 'batch_size' in optimal_config['execution']:
        updated_config['batch_size'] = optimal_config['execution']['batch_size']
    
    # Update gas strategy
    if 'execution' in optimal_config and 'gas_strategy' in optimal_config['execution']:
        updated_config['gas_strategy'] = optimal_config['execution']['gas_strategy']
    
    # Update network-specific execution settings
    if 'network_specific' in optimal_config:
        if 'networks' not in updated_config:
            updated_config['networks'] = {}
        
        for network, settings in optimal_config['network_specific'].items():
            updated_config['networks'][network] = {
                **updated_config['networks'].get(network, {}),
                **settings
            }
    
    return updated_config

def update_bot_config(optimal_config, current_config):
    """Update bot configuration with optimal settings."""
    updated_config = current_config.copy()
    
    # Update monitoring settings
    if 'monitoring' in optimal_config:
        monitoring = optimal_config['monitoring']
        if 'monitoring' not in updated_config:
            updated_config['monitoring'] = {}
        
        updated_config['monitoring'] = {
            **updated_config['monitoring'],
            **monitoring
        }
    
    # Update active networks
    if 'execution' in optimal_config and 'networks' in optimal_config['execution']:
        updated_config['active_networks'] = optimal_config['execution']['networks']
    
    return updated_config

def validate_config(config_type, config):
    """Validate the updated configuration."""
    # Basic validation checks
    if config_type == 'trade_selection':
        if 'networks' not in config or not config['networks']:
            return False, "Missing or empty networks in trade selection config"
        if 'tokens' not in config or not config['tokens']:
            return False, "Missing or empty tokens in trade selection config"
    
    elif config_type == 'mev_protection':
        if 'network_settings' not in config:
            return False, "Missing network_settings in MEV protection config"
    
    elif config_type == 'execution':
        if 'batch_size' not in config:
            return False, "Missing batch_size in execution config"
        if 'gas_strategy' not in config:
            return False, "Missing gas_strategy in execution config"
    
    elif config_type == 'bot':
        if 'active_networks' not in config or not config['active_networks']:
            return False, "Missing or empty active_networks in bot config"
    
    return True, "Configuration validated successfully"

def apply_optimal_config(args):
    """Apply the optimal configuration to all target configs."""
    # Load optimal configuration
    optimal_config = load_json_file(OPTIMAL_CONFIG_PATH)
    if not optimal_config:
        logger.error("Failed to load optimal configuration")
        return False
    
    logger.info("Loaded optimal configuration from: %s", OPTIMAL_CONFIG_PATH)
    
    # Process each configuration target
    success = True
    for config_type, config_path in CONFIG_TARGETS.items():
        logger.info(f"Processing {config_type} configuration...")
        
        # Load current configuration
        current_config = load_json_file(config_path)
        
        # Update configuration based on type
        if config_type == 'trade_selection':
            updated_config = update_trade_selection_config(optimal_config, current_config)
        elif config_type == 'mev_protection':
            updated_config = update_mev_protection_config(optimal_config, current_config)
        elif config_type == 'execution':
            updated_config = update_execution_config(optimal_config, current_config)
        elif config_type == 'bot':
            updated_config = update_bot_config(optimal_config, current_config)
        else:
            logger.warning(f"Unknown configuration type: {config_type}")
            continue
        
        # Validate updated configuration
        is_valid, message = validate_config(config_type, updated_config)
        if not is_valid:
            logger.error(f"Validation failed for {config_type}: {message}")
            success = False
            continue
        
        # Show changes in dry-run mode
        if args.dry_run:
            logger.info(f"[DRY RUN] Would update {config_path} with new configuration")
            continue
        
        # Create backup if requested
        if args.backup:
            create_backup(config_path)
        
        # Save updated configuration
        save_json_file(config_path, updated_config)
        logger.info(f"Updated {config_type} configuration at {config_path}")
    
    return success

def main():
    """Main function."""
    args = parse_args()
    
    logger.info("Starting optimal configuration application")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Create backups: {args.backup}")
    
    if not args.force and not args.dry_run:
        confirmation = input("This will update ArbitrageX configuration files. Continue? (y/n): ")
        if confirmation.lower() != 'y':
            logger.info("Operation cancelled by user")
            return
    
    success = apply_optimal_config(args)
    
    if success:
        if args.dry_run:
            logger.info("Dry run completed successfully. No changes were made.")
        else:
            logger.info("Optimal configuration applied successfully to all targets")
    else:
        logger.error("Failed to apply optimal configuration to all targets")

if __name__ == "__main__":
    main() 