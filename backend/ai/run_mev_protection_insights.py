#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ArbitrageX MEV Protection Insights Demo

This script demonstrates the usage of MEV Protection Insights functionality
to track and visualize MEV protection activities.
"""

import os
import json
import time
import random
import logging
import datetime
from typing import Dict, List, Any
from decimal import Decimal

# Import MEV protection components
from mev_protection import MEVProtectionManager, MEVRiskLevel, ProtectionMethod
from mev_protection_integration import MEVProtectionIntegrator, ProtectionLevel
from mev_protection_insights import MEVProtectionInsights

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mev_protection_insights_demo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mev_protection_insights_demo")

def generate_random_transaction(tx_index: int) -> Dict[str, Any]:
    """Generate a random transaction for testing."""
    networks = ["ethereum", "arbitrum", "optimism", "polygon"]
    tokens = ["ETH", "USDC", "WBTC", "DAI", "LINK"]
    pair_tokens = [("ETH", "USDC"), ("ETH", "WBTC"), ("WBTC", "USDC"), ("ETH", "DAI"), ("LINK", "ETH")]
    pair = random.choice(pair_tokens)
    
    # Generate a random value between 0.1 and 10 ETH
    value = round(random.uniform(0.1, 10), 4)
    
    # Base gas price + random fluctuation
    gas_price = round(random.uniform(15, 50), 2)
    
    return {
        "id": f"tx-{tx_index}",
        "timestamp": datetime.datetime.now().isoformat(),
        "pair": f"{pair[0]}/{pair[1]}",
        "network": random.choice(networks),
        "value": value,
        "gas_price": gas_price,
        "transaction": {
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": value * 10**18,  # Convert to wei
            "gas": 200000,
            "gasPrice": int(gas_price * 10**9),  # Convert to wei
            "data": "0x"
        }
    }

def simulate_transactions(count: int, insights_tracker: MEVProtectionInsights, integrator: MEVProtectionIntegrator) -> None:
    """Simulate a series of transactions with MEV protection."""
    logger.info(f"Simulating {count} transactions with MEV protection")
    
    # Enable protection
    insights_tracker.set_protection_status(True)
    
    # Generate and process transactions
    for i in range(count):
        # Generate a random transaction
        tx = generate_random_transaction(i)
        
        # Enhance with protection
        enhanced_tx = integrator.enhance_opportunity_with_protection(tx)
        
        # Log the transaction
        protection_details = enhanced_tx.get("mev_protection", {})
        is_protected = protection_details.get("enabled", False)
        protection_level = protection_details.get("protection_level", "none")
        risk_level = protection_details.get("risk_level", "unknown")
        
        if is_protected:
            logger.info(f"Transaction {i+1}: Protected with {protection_level} protection, Risk: {risk_level}")
        else:
            logger.info(f"Transaction {i+1}: Not protected")
        
        # Simulate transaction execution
        result = integrator.execute_protected_transaction(enhanced_tx, "0xPRIVATE_KEY_PLACEHOLDER")
        
        # Log the result
        if result.get("success", False):
            logger.info(f"Transaction {i+1}: Success")
        else:
            logger.error(f"Transaction {i+1}: Failed - {result.get('error', 'Unknown error')}")
        
        # Add a small delay to make it more realistic
        time.sleep(0.1)

def print_metrics(insights_tracker: MEVProtectionInsights) -> None:
    """Print MEV protection metrics."""
    # Get current metrics
    metrics = insights_tracker.get_metrics()
    insights = insights_tracker.get_insights()
    summary = insights_tracker.get_protection_summary()
    
    print("\n" + "="*50)
    print("MEV PROTECTION INSIGHTS METRICS")
    print("="*50)
    
    print("\nProtection Status:")
    print(f"  Status: {'ENABLED' if metrics['protection_status'] else 'DISABLED'}")
    print(f"  Protected Transactions: {metrics['protected_transactions']['total']}")
    print(f"  Unprotected Transactions: {insights['protected_vs_unprotected']['unprotected']}")
    
    print("\nProtection Levels:")
    for level, count in metrics['protected_transactions'].items():
        if level != 'total':
            print(f"  {level.capitalize()}: {count}")
    
    print("\nRisk Levels:")
    for level, count in metrics['risk_levels'].items():
        print(f"  {level.capitalize()}: {count}")
    
    print("\nProtection Methods:")
    for method, count in metrics['protection_methods'].items():
        if count > 0:
            print(f"  {method.replace('_', ' ').capitalize()}: {count}")
    
    print("\nEstimated Savings:")
    print(f"  Total: ${metrics['estimated_savings']:.2f}")
    print(f"  Daily (24h): ${summary['estimated_daily_savings']:.2f}")
    
    print("\nProtection Ratio:")
    print(f"  {summary['protection_ratio']*100:.1f}% of transactions protected")
    
    print("\nTop Risk Level: {0}".format(summary['top_risk_level'].capitalize()))
    print(f"Top Protection Method: {summary['top_protection_method'].replace('_', ' ').capitalize()}")
    
    if insights['high_risk_trades']:
        print("\nRecent High Risk Trades:")
        for i, trade in enumerate(insights['high_risk_trades'][-3:]):
            print(f"  {i+1}. Risk: {trade['risk_level']}, Protection: {trade['protection_level']}, Savings: ${trade['estimated_saving']:.2f}")
    
    print("\nLast Updated: {0}".format(datetime.datetime.fromisoformat(metrics['last_updated']).strftime('%Y-%m-%d %H:%M:%S')))
    print("="*50)

def main():
    """Main function to demonstrate MEV Protection Insights."""
    try:
        # Initialize components
        insights_tracker = MEVProtectionInsights()
        integrator = MEVProtectionIntegrator()
        
        # Print initial metrics
        print_metrics(insights_tracker)
        
        # Simulate transactions
        transaction_count = 50
        simulate_transactions(transaction_count, insights_tracker, integrator)
        
        # Print updated metrics
        print_metrics(insights_tracker)
        
        # Print path to metrics file
        print(f"\nMetrics saved to: {os.path.abspath(insights_tracker.metrics_path)}")
        print(f"Insights saved to: {os.path.abspath(insights_tracker.insights_path)}")
        
        # Print dashboard instructions
        print("\nTo view the MEV Protection Insights dashboard:")
        print("1. Start the dashboard server: cd backend/ai/dashboard && python app.py")
        print("2. Open your browser and navigate to: http://localhost:5000/mev_protection")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    main() 