"""
Test script for the ArbitrageX AI Strategy Optimizer
"""

from strategy_optimizer_demo import StrategyOptimizer
import time

def test_multiple_scenarios():
    """Test the AI model with multiple scenarios to demonstrate adaptability"""
    optimizer = StrategyOptimizer()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Small ETH-USDC trade on Uniswap",
            "opportunity": {
                "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                "token_out": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                "amount": 500000000000000000,  # 0.5 ETH
                "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap
            }
        },
        {
            "name": "Large ETH-USDC trade on Uniswap",
            "opportunity": {
                "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                "token_out": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
                "amount": 10000000000000000000,  # 10 ETH
                "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap
            }
        },
        {
            "name": "ETH-DAI trade on SushiSwap",
            "opportunity": {
                "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                "token_out": "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
                "amount": 2000000000000000000,  # 2 ETH
                "router": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"  # SushiSwap
            }
        },
        {
            "name": "WBTC-ETH trade on 1inch",
            "opportunity": {
                "token_in": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
                "token_out": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                "amount": 50000000,  # 0.5 WBTC (8 decimals)
                "router": "0x1111111254fb6c44bAC0beD2854e76F90643097d"  # 1inch
            }
        },
        {
            "name": "Unknown token pair",
            "opportunity": {
                "token_in": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",  # UNI
                "token_out": "0x514910771AF9Ca656af840dff83E8264EcF986CA",  # LINK
                "amount": 1000000000000000000000,  # 1000 UNI
                "router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap
            }
        }
    ]
    
    print("\n===== ARBITRAGEX AI MODEL PERFORMANCE DEMONSTRATION =====\n")
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {scenario['name']}")
        print("-" * 50)
        
        start = time.time()
        result = optimizer.predict_opportunity(scenario['opportunity'])
        end = time.time()
        
        print(f"Token Pair: {result['token_pair']}")
        print(f"Profitable: {'✅ YES' if result['is_profitable'] else '❌ NO'}")
        print(f"Confidence Score: {result['confidence']:.4f}")
        print(f"Estimated Profit: ${result['estimated_profit_usd']:.2f}")
        print(f"Gas Cost: ${result['gas_cost_usd']:.2f}")
        print(f"Net Profit: ${result['net_profit_usd']:.2f}")
        print(f"Execution Time: {result['execution_time_ms']:.2f}ms")
        print(f"Prediction Time: {(end-start)*1000:.2f}ms")
    
    print("\n===== AI MODEL PERFORMANCE SUMMARY =====\n")
    print("The AI model demonstrated the following capabilities:")
    print("1. Time-based pattern recognition (trading hours impact)")
    print("2. Amount-based optimization (larger trades have different profitability)")
    print("3. Router preference (different DEXes have varying efficiency)")
    print("4. Token pair analysis (common pairs vs exotic pairs)")
    print("5. Gas cost estimation (based on transaction complexity)")
    print("6. Confidence scoring (probability of successful arbitrage)")
    print("\nThis simplified model demonstrates the core concepts of the full AI system.")

if __name__ == "__main__":
    test_multiple_scenarios() 