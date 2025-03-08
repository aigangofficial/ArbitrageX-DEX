#!/usr/bin/env python3
"""
Test script for the Trade Validator

This script demonstrates the functionality of the Trade Validator by:
1. Creating sample trades with different characteristics
2. Validating each trade using the TradeValidator
3. Displaying the validation results
4. Demonstrating adaptive thresholds based on market conditions
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

from trade_validator import TradeValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestTradeValidator")

def create_sample_trades() -> List[Dict[str, Any]]:
    """
    Create a list of sample trades with different characteristics.
    
    Returns:
        List of sample trades
    """
    return [
        # Profitable trade with good characteristics
        {
            "trade_id": "good_trade_1",
            "token_pair": "WETH-USDC",
            "dex": "uniswap_v3",
            "network": "ethereum",
            "amount": 1000.0,
            "expected_profit": 20.0,
            "gas_price": 40.0,  # Gwei
            "gas_used": 200000,
            "gas_cost": 4.0,  # USD
            "expected_slippage": 0.01,  # 1%
            "liquidity_score": 0.9,
            "historical_success_rate": 0.85,
            "front_running_risk": 0.2,
            "network_congestion": 0.4
        },
        
        # Low profit trade
        {
            "trade_id": "low_profit_trade",
            "token_pair": "WBTC-USDT",
            "dex": "sushiswap",
            "network": "arbitrum",
            "amount": 1000.0,
            "expected_profit": 8.0,
            "gas_price": 30.0,
            "gas_used": 180000,
            "gas_cost": 3.0,
            "expected_slippage": 0.015,
            "liquidity_score": 0.8,
            "historical_success_rate": 0.75,
            "front_running_risk": 0.3,
            "network_congestion": 0.5
        },
        
        # High gas cost trade
        {
            "trade_id": "high_gas_trade",
            "token_pair": "WETH-DAI",
            "dex": "uniswap_v3",
            "network": "ethereum",
            "amount": 1000.0,
            "expected_profit": 15.0,
            "gas_price": 80.0,
            "gas_used": 250000,
            "gas_cost": 10.0,
            "expected_slippage": 0.01,
            "liquidity_score": 0.85,
            "historical_success_rate": 0.8,
            "front_running_risk": 0.25,
            "network_congestion": 0.45
        },
        
        # High slippage trade
        {
            "trade_id": "high_slippage_trade",
            "token_pair": "LINK-USDC",
            "dex": "sushiswap",
            "network": "polygon",
            "amount": 1000.0,
            "expected_profit": 18.0,
            "gas_price": 35.0,
            "gas_used": 190000,
            "gas_cost": 3.5,
            "expected_slippage": 0.04,
            "liquidity_score": 0.75,
            "historical_success_rate": 0.7,
            "front_running_risk": 0.35,
            "network_congestion": 0.55
        },
        
        # Low liquidity trade
        {
            "trade_id": "low_liquidity_trade",
            "token_pair": "UNI-USDT",
            "dex": "uniswap_v3",
            "network": "bsc",
            "amount": 1000.0,
            "expected_profit": 16.0,
            "gas_price": 25.0,
            "gas_used": 170000,
            "gas_cost": 2.5,
            "expected_slippage": 0.02,
            "liquidity_score": 0.5,
            "historical_success_rate": 0.65,
            "front_running_risk": 0.4,
            "network_congestion": 0.6
        },
        
        # High front-running risk trade
        {
            "trade_id": "high_front_running_trade",
            "token_pair": "AAVE-USDC",
            "dex": "sushiswap",
            "network": "ethereum",
            "amount": 1000.0,
            "expected_profit": 25.0,
            "gas_price": 45.0,
            "gas_used": 210000,
            "gas_cost": 4.5,
            "expected_slippage": 0.015,
            "liquidity_score": 0.8,
            "historical_success_rate": 0.75,
            "front_running_risk": 0.8,
            "network_congestion": 0.5
        },
        
        # High network congestion trade
        {
            "trade_id": "high_congestion_trade",
            "token_pair": "WETH-USDC",
            "dex": "uniswap_v3",
            "network": "ethereum",
            "amount": 1000.0,
            "expected_profit": 22.0,
            "gas_price": 60.0,
            "gas_used": 220000,
            "gas_cost": 6.0,
            "expected_slippage": 0.015,
            "liquidity_score": 0.85,
            "historical_success_rate": 0.8,
            "front_running_risk": 0.3,
            "network_congestion": 0.9
        },
        
        # Extremely risky trade (multiple issues)
        {
            "trade_id": "extremely_risky_trade",
            "token_pair": "SHIB-USDT",
            "dex": "sushiswap",
            "network": "bsc",
            "amount": 1000.0,
            "expected_profit": 9.0,
            "gas_price": 70.0,
            "gas_used": 300000,
            "gas_cost": 8.0,
            "expected_slippage": 0.05,
            "liquidity_score": 0.4,
            "historical_success_rate": 0.5,
            "front_running_risk": 0.95,
            "network_congestion": 0.85
        }
    ]

def print_validation_result(validation_result: Dict[str, Any]):
    """
    Print validation result in a readable format.
    
    Args:
        validation_result: Validation result dictionary
    """
    print("\n" + "=" * 80)
    print(f"Trade ID: {validation_result['trade_id']}")
    print(f"Timestamp: {validation_result['timestamp']}")
    print(f"Valid: {'✅ YES' if validation_result['is_valid'] else '❌ NO'}")
    print(f"Validation Score: {validation_result['validation_score']:.2f}/100")
    
    if validation_result['failure_reasons']:
        print("\nFailure Reasons:")
        for reason in validation_result['failure_reasons']:
            print(f"  ❌ {reason}")
    
    if validation_result['warnings']:
        print("\nWarnings:")
        for warning in validation_result['warnings']:
            print(f"  ⚠️ {warning}")
    
    print("\nValidation Details:")
    for category, details in validation_result['validation_details'].items():
        print(f"  {category.capitalize()}:")
        for key, value in details.items():
            if isinstance(value, float):
                print(f"    {key}: {value:.2f}")
            else:
                print(f"    {key}: {value}")
    
    print("=" * 80)

def test_adaptive_thresholds(validator: TradeValidator):
    """
    Test adaptive thresholds based on market conditions.
    
    Args:
        validator: TradeValidator instance
    """
    print("\n" + "=" * 80)
    print("TESTING ADAPTIVE THRESHOLDS")
    print("=" * 80)
    
    # Get original thresholds
    original_profit_threshold = validator.config["min_profit_threshold"]
    original_slippage_tolerance = validator.config["max_slippage_tolerance"]
    original_gas_cost_percentage = validator.config["max_gas_cost_percentage"]
    
    print(f"Original Thresholds:")
    print(f"  Min Profit Threshold: ${original_profit_threshold:.2f}")
    print(f"  Max Slippage Tolerance: {original_slippage_tolerance:.2f}%")
    print(f"  Max Gas Cost Percentage: {original_gas_cost_percentage:.2f}%")
    
    # Test with low volatility and congestion
    low_market_conditions = {
        "market_volatility": 0.1,
        "network_congestion": 0.2
    }
    
    validator.adjust_thresholds(low_market_conditions)
    
    print(f"\nLow Volatility ({low_market_conditions['market_volatility']:.2f}) and Congestion ({low_market_conditions['network_congestion']:.2f}):")
    print(f"  Min Profit Threshold: ${validator.config['min_profit_threshold']:.2f}")
    print(f"  Max Slippage Tolerance: {validator.config['max_slippage_tolerance']:.2f}%")
    print(f"  Max Gas Cost Percentage: {validator.config['max_gas_cost_percentage']:.2f}%")
    
    # Test with medium volatility and congestion
    medium_market_conditions = {
        "market_volatility": 0.5,
        "network_congestion": 0.5
    }
    
    validator.adjust_thresholds(medium_market_conditions)
    
    print(f"\nMedium Volatility ({medium_market_conditions['market_volatility']:.2f}) and Congestion ({medium_market_conditions['network_congestion']:.2f}):")
    print(f"  Min Profit Threshold: ${validator.config['min_profit_threshold']:.2f}")
    print(f"  Max Slippage Tolerance: {validator.config['max_slippage_tolerance']:.2f}%")
    print(f"  Max Gas Cost Percentage: {validator.config['max_gas_cost_percentage']:.2f}%")
    
    # Test with high volatility and congestion
    high_market_conditions = {
        "market_volatility": 0.9,
        "network_congestion": 0.8
    }
    
    validator.adjust_thresholds(high_market_conditions)
    
    print(f"\nHigh Volatility ({high_market_conditions['market_volatility']:.2f}) and Congestion ({high_market_conditions['network_congestion']:.2f}):")
    print(f"  Min Profit Threshold: ${validator.config['min_profit_threshold']:.2f}")
    print(f"  Max Slippage Tolerance: {validator.config['max_slippage_tolerance']:.2f}%")
    print(f"  Max Gas Cost Percentage: {validator.config['max_gas_cost_percentage']:.2f}%")
    
    print("=" * 80)

def print_validation_stats(validator: TradeValidator):
    """
    Print validation statistics.
    
    Args:
        validator: TradeValidator instance
    """
    stats = validator.get_validation_stats()
    
    print("\n" + "=" * 80)
    print("VALIDATION STATISTICS")
    print("=" * 80)
    print(f"Total Validations: {stats['total_validations']}")
    print(f"Passed Validations: {stats['passed_validations']} ({stats['passed_validations'] / stats['total_validations'] * 100:.2f}%)")
    print(f"Failed Validations: {stats['failed_validations']} ({stats['failed_validations'] / stats['total_validations'] * 100:.2f}%)")
    
    if stats['failure_reasons']:
        print("\nFailure Reasons:")
        for reason, count in stats['failure_reasons'].items():
            print(f"  {reason}: {count} ({count / stats['failed_validations'] * 100:.2f}%)")
    
    print("=" * 80)

def test_enhanced_features():
    """
    Test the enhanced features of the Trade Validator.
    
    This function demonstrates:
    1. Machine learning validation
    2. Cross-chain validation
    3. Enhanced MEV protection
    4. Validation caching
    5. A/B testing
    6. Portfolio-based threshold adjustment
    """
    logger.info("Testing enhanced Trade Validator features")
    
    # Create validator with enhanced features enabled
    config_path = "backend/ai/config/trade_validator_config.json"
    
    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Enable enhanced features
    config["enable_ml_validation"] = True
    config["enable_validation_cache"] = True
    config["enable_ab_testing"] = True
    config["enable_portfolio_based_thresholds"] = True
    
    # Create temporary config file
    temp_config_path = "backend/ai/config/temp_enhanced_config.json"
    with open(temp_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Create validator with enhanced features
    validator = TradeValidator(config_path=temp_config_path)
    
    # 1. Test machine learning validation
    logger.info("1. Testing machine learning validation")
    
    # Create sample historical data for training
    historical_data = []
    for i in range(20):
        # Successful trades (high profit, low gas, good liquidity)
        historical_data.append({
            "trade_id": f"historical_success_{i}",
            "token_pair": "WETH-USDC",
            "dex": "uniswap_v3",
            "network": "ethereum",
            "amount": 1000.0,
            "expected_profit": 20.0 + i,
            "gas_price": 40.0,
            "gas_used": 200000,
            "gas_cost": 4.0,
            "expected_slippage": 0.01,
            "liquidity_score": 0.9,
            "historical_success_rate": 0.85,
            "front_running_risk": 0.2,
            "network_congestion": 0.4,
            "status": "completed",
            "actual_profit": 18.0 + i
        })
        
        # Failed trades (low profit, high gas, poor liquidity)
        historical_data.append({
            "trade_id": f"historical_failure_{i}",
            "token_pair": "LINK-DAI",
            "dex": "sushiswap",
            "network": "polygon",
            "amount": 1000.0,
            "expected_profit": 5.0 + (i * 0.2),
            "gas_price": 80.0,
            "gas_used": 300000,
            "gas_cost": 12.0,
            "expected_slippage": 0.03,
            "liquidity_score": 0.5,
            "historical_success_rate": 0.6,
            "front_running_risk": 0.7,
            "network_congestion": 0.8,
            "status": "failed",
            "actual_profit": 0
        })
    
    # Train the model
    logger.info("Training ML model with sample historical data")
    training_success = validator.train_validation_model(historical_data)
    logger.info(f"ML model training {'successful' if training_success else 'failed'}")
    
    # Test ML validation with new trades
    good_trade = {
        "trade_id": "ml_good_trade",
        "token_pair": "WETH-USDC",
        "dex": "uniswap_v3",
        "network": "ethereum",
        "amount": 1000.0,
        "expected_profit": 25.0,
        "gas_price": 35.0,
        "gas_used": 180000,
        "gas_cost": 3.5,
        "expected_slippage": 0.01,
        "liquidity_score": 0.95,
        "historical_success_rate": 0.9,
        "front_running_risk": 0.1,
        "network_congestion": 0.3
    }
    
    bad_trade = {
        "trade_id": "ml_bad_trade",
        "token_pair": "LINK-DAI",
        "dex": "sushiswap",
        "network": "polygon",
        "amount": 1000.0,
        "expected_profit": 6.0,
        "gas_price": 90.0,
        "gas_used": 320000,
        "gas_cost": 14.0,
        "expected_slippage": 0.035,
        "liquidity_score": 0.45,
        "historical_success_rate": 0.55,
        "front_running_risk": 0.75,
        "network_congestion": 0.85
    }
    
    # Validate trades with ML
    good_result = validator.validate_trade(good_trade)
    bad_result = validator.validate_trade(bad_trade)
    
    logger.info(f"ML validation for good trade: {good_result['is_valid']}, score: {good_result['validation_score']:.2f}")
    if "ml_validation" in good_result["validation_details"]:
        logger.info(f"ML success probability: {good_result['validation_details']['ml_validation']['success_probability']:.2f}")
    
    logger.info(f"ML validation for bad trade: {bad_result['is_valid']}, score: {bad_result['validation_score']:.2f}")
    if "ml_validation" in bad_result["validation_details"]:
        logger.info(f"ML success probability: {bad_result['validation_details']['ml_validation']['success_probability']:.2f}")
    
    # 2. Test cross-chain validation
    logger.info("\n2. Testing cross-chain validation")
    
    cross_chain_trade = {
        "trade_id": "cross_chain_trade",
        "token_pair": "WETH-USDC",
        "dex": "uniswap_v3",
        "is_cross_chain": True,
        "source_network": "ethereum",
        "destination_network": "arbitrum",
        "amount": 5000.0,
        "expected_profit": 50.0,
        "gas_price": 40.0,
        "gas_used": 200000,
        "gas_cost": 4.0,
        "expected_slippage": 0.01,
        "liquidity_score": 0.9,
        "historical_success_rate": 0.85,
        "front_running_risk": 0.2,
        "network_congestion": 0.4
    }
    
    cross_chain_result = validator.validate_trade(cross_chain_trade)
    
    logger.info(f"Cross-chain validation: {cross_chain_result['is_valid']}, score: {cross_chain_result['validation_score']:.2f}")
    if "cross_chain" in cross_chain_result["validation_details"]:
        cc_details = cross_chain_result["validation_details"]["cross_chain"]
        logger.info(f"Bridge fee: ${cc_details['bridge_fee']:.2f} ({cc_details['bridge_fee_percentage']:.2f}%)")
        logger.info(f"Bridge time: {cc_details['bridge_time']}s")
        logger.info(f"Bridge reliability: {cc_details['bridge_reliability']:.2f}")
    
    # 3. Test enhanced MEV protection
    logger.info("\n3. Testing enhanced MEV protection")
    
    high_mev_risk_trade = {
        "trade_id": "high_mev_risk_trade",
        "token_pair": "WETH-USDC",
        "dex": "uniswap_v2",
        "network": "ethereum",
        "amount": 10000.0,
        "expected_profit": 100.0,
        "gas_price": 50.0,
        "gas_used": 250000,
        "gas_cost": 6.0,
        "expected_slippage": 0.01,
        "liquidity_score": 0.9,
        "historical_success_rate": 0.85,
        "front_running_risk": 0.8,
        "network_congestion": 0.7
    }
    
    mev_result = validator.validate_trade(high_mev_risk_trade)
    
    logger.info(f"MEV protection validation: {mev_result['is_valid']}, score: {mev_result['validation_score']:.2f}")
    if "front_running_risk" in mev_result["validation_details"]:
        mev_details = mev_result["validation_details"]["front_running_risk"]
        logger.info(f"MEV risk score: {mev_details['front_running_risk']:.2f}")
        logger.info(f"MEV factors: {mev_details['mev_factors']}")
        logger.info(f"Recommended protection: {mev_details['recommended_protection']}")
    
    # 4. Test validation caching
    logger.info("\n4. Testing validation caching")
    
    # First validation (cache miss)
    cache_trade = {
        "trade_id": "cache_test_trade",
        "token_pair": "WBTC-USDC",
        "dex": "uniswap_v3",
        "network": "ethereum",
        "amount": 2000.0,
        "expected_profit": 30.0,
        "gas_price": 45.0,
        "gas_used": 220000,
        "gas_cost": 5.0,
        "expected_slippage": 0.01,
        "liquidity_score": 0.85,
        "historical_success_rate": 0.8,
        "front_running_risk": 0.3,
        "network_congestion": 0.5
    }
    
    logger.info("First validation (cache miss)")
    start_time = time.time()
    cache_result1 = validator.validate_trade(cache_trade)
    first_time = time.time() - start_time
    
    # Second validation (cache hit)
    logger.info("Second validation (cache hit)")
    start_time = time.time()
    cache_result2 = validator.validate_trade(cache_trade)
    second_time = time.time() - start_time
    
    logger.info(f"First validation time: {first_time:.6f}s")
    logger.info(f"Second validation time: {second_time:.6f}s")
    logger.info(f"Cache stats: {validator.get_cache_stats()}")
    
    # 5. Test A/B testing
    logger.info("\n5. Testing A/B testing")
    
    # Test different strategies
    strategies = ["default", "conservative", "aggressive"]
    for strategy in strategies:
        logger.info(f"Testing '{strategy}' strategy")
        ab_trade = {
            "trade_id": f"ab_test_{strategy}_trade",
            "token_pair": "WETH-USDC",
            "dex": "uniswap_v3",
            "network": "ethereum",
            "amount": 1000.0,
            "expected_profit": 15.0,
            "gas_price": 40.0,
            "gas_used": 200000,
            "gas_cost": 4.0,
            "expected_slippage": 0.02,
            "liquidity_score": 0.8,
            "historical_success_rate": 0.75,
            "front_running_risk": 0.4,
            "network_congestion": 0.5
        }
        
        strategy_result = validator.validate_trade_with_strategy(ab_trade, strategy)
        logger.info(f"Strategy '{strategy}' validation: {strategy_result['is_valid']}, score: {strategy_result['validation_score']:.2f}")
        
        # Update A/B testing stats with simulated execution result
        execution_result = {
            "status": "completed" if strategy_result["is_valid"] else "failed",
            "actual_profit": 14.0 if strategy_result["is_valid"] else 0,
            "gas_cost": 4.0
        }
        validator.update_ab_testing_stats(strategy, execution_result)
    
    # Get A/B testing stats
    ab_stats = validator.get_ab_testing_stats()
    logger.info(f"A/B testing stats: {json.dumps(ab_stats, indent=2)}")
    
    # 6. Test portfolio-based threshold adjustment
    logger.info("\n6. Testing portfolio-based threshold adjustment")
    
    # Test with negative daily PnL
    negative_portfolio = {
        "daily_pnl": -50.0,
        "weekly_pnl": 100.0,
        "daily_target": 100.0
    }
    
    logger.info("Adjusting thresholds with negative daily PnL")
    validator.adjust_thresholds_based_on_portfolio(negative_portfolio)
    
    # Test with positive daily PnL exceeding target
    positive_portfolio = {
        "daily_pnl": 150.0,
        "weekly_pnl": 500.0,
        "daily_target": 100.0
    }
    
    logger.info("Adjusting thresholds with positive daily PnL exceeding target")
    validator.adjust_thresholds_based_on_portfolio(positive_portfolio)
    
    # Clean up
    os.remove(temp_config_path)
    logger.info("Enhanced features test completed")

def main():
    """Main function to test the trade validator."""
    logger.info("Starting Trade Validator Test")
    
    # Create validator
    validator = TradeValidator()
    logger.info("Trade Validator initialized")
    
    # Create sample trades
    sample_trades = create_sample_trades()
    logger.info(f"Created {len(sample_trades)} sample trades")
    
    # Validate each trade
    for trade in sample_trades:
        logger.info(f"Validating trade {trade['trade_id']}")
        validation_result = validator.validate_trade(trade)
        print_validation_result(validation_result)
    
    # Print validation statistics
    print_validation_stats(validator)
    
    # Test adaptive thresholds
    test_adaptive_thresholds(validator)
    
    # Test enhanced features
    test_enhanced_features()
    
    # Save validation statistics
    validator.save_validation_stats()
    logger.info("Validation statistics saved")
    
    logger.info("Trade Validator Test completed")

if __name__ == "__main__":
    main() 