import asyncio
import logging
from datetime import datetime
from web3 import Web3
from web3_connector import CONTRACT_ADDRESSES, Web3Connector
import json
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def verify_contract(web3, address):
    """Verify if a contract exists at the given address with retry logic."""
    try:
        code = await web3.eth.get_code(Web3.to_checksum_address(address))
        return len(code) > 2  # If there's code at the address
    except Exception as e:
        logger.error(f"Error verifying contract at {address}: {str(e)}")
        raise  # Raise for retry

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_token_price_with_retry(connector, router, token_in, token_out, amount):
    """Get token price with retry logic."""
    return await connector.get_token_price(router, token_in, token_out, amount)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def get_pool_liquidity_with_retry(connector, factory, token_a, token_b):
    """Get pool liquidity with retry logic."""
    return await connector.get_pool_liquidity(factory, token_a, token_b)

async def main():
    try:
        logger.info("Starting Amoy integration tests...")

        # Initialize Web3 connection with multiple RPC endpoints
        rpc_urls = [
            "https://polygon-amoy.g.alchemy.com/v2/dTwNgMXtwagIb1lZBjP_A03m5ko7WaR1",
            "https://rpc.ankr.com/polygon_amoy",
            "https://rpc-amoy.polygon.technology"
        ]

        connector = None
        for rpc_url in rpc_urls:
            try:
                logger.info(f"Attempting to connect to RPC: {rpc_url}")
                connector = await Web3Connector.create(rpc_url)
                logger.info(f"Connected to RPC: {rpc_url}")
                break
            except Exception as e:
                logger.warning(f"Failed to connect to {rpc_url}: {str(e)}")
                continue

        if not connector:
            raise Exception("Failed to connect to any RPC endpoint")

        # Verify all contract addresses with improved error handling
        logger.info("\nVerifying contract deployments:")
        contract_status = {}
        for name, address in CONTRACT_ADDRESSES.items():
            try:
                exists = await verify_contract(connector.w3, address)
                contract_status[name] = exists
                logger.info(f"{name}: {address} - {'✓ Deployed' if exists else '✗ Not deployed'}")
            except Exception as e:
                logger.error(f"Failed to verify {name}: {str(e)}")
                contract_status[name] = False

        # Test network connection with enhanced error handling
        try:
            network_info = await connector.get_network_info()
            logger.info(f"\nConnected to Amoy testnet:")
            logger.info(f"Chain ID: {network_info['chain_id']}")
            logger.info(f"Block: {network_info['block']}")
            logger.info(f"Gas Price: {Web3.from_wei(network_info['gas_price'], 'gwei')} Gwei")
        except Exception as e:
            logger.error(f"Error getting network info: {str(e)}")
            raise

        # Test price fetching with enhanced error handling
        logger.info("\nTesting price fetching from Amoy DEXs...")
        amount_in = Web3.to_wei(1, 'ether')  # 1 MATIC

        # Test WMATIC/USDC pair with detailed error handling
        try:
            # Get token decimals with validation
            wmatic_decimals = await connector.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACT_ADDRESSES['WMATIC']),
                abi=[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]
            ).functions.decimals().call()

            usdc_decimals = await connector.w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACT_ADDRESSES['USDC']),
                abi=[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}]
            ).functions.decimals().call()

            logger.info(f"\nToken decimals:")
            logger.info(f"WMATIC: {wmatic_decimals}")
            logger.info(f"USDC: {usdc_decimals}")

            # Get price with retry logic
            wmatic_usdc_price = await get_token_price_with_retry(
                connector,
                CONTRACT_ADDRESSES['QUICKSWAP_ROUTER'],
                CONTRACT_ADDRESSES['WMATIC'],
                CONTRACT_ADDRESSES['USDC'],
                amount_in
            )
            logger.info(f"\nWMATIC/USDC Price: {wmatic_usdc_price}")

            # Get liquidity with retry logic
            wmatic_usdc_liquidity = await get_pool_liquidity_with_retry(
                connector,
                CONTRACT_ADDRESSES['QUICKSWAP_FACTORY'],
                CONTRACT_ADDRESSES['WMATIC'],
                CONTRACT_ADDRESSES['USDC']
            )
            logger.info(f"WMATIC/USDC Liquidity:")
            logger.info(f"WMATIC: {Web3.from_wei(wmatic_usdc_liquidity[0], 'ether')}")
            logger.info(f"USDC: {Web3.from_wei(wmatic_usdc_liquidity[1], 'mwei')}")  # USDC has 6 decimals

        except Exception as e:
            logger.error(f"Error fetching WMATIC/USDC data: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            if hasattr(e, '__cause__'):
                logger.error(f"Caused by: {str(e.__cause__)}")

        # Test market state updates with improved error handling
        logger.info("\nTesting market state updates...")
        try:
            market_state = {
                'WMATIC/USDC': {
                    'last_price': wmatic_usdc_price if 'wmatic_usdc_price' in locals() else 0,
                    'price_change': 0.0,
                    'volume': Web3.from_wei(sum(wmatic_usdc_liquidity), 'ether') if 'wmatic_usdc_liquidity' in locals() else 0
                },
                'gas_price_history': [network_info['gas_price']]
            }

            logger.info("\nCurrent market state:")
            logger.info(json.dumps(market_state, indent=2))

        except Exception as e:
            logger.error(f"Error updating market state: {str(e)}")

        logger.info("\nIntegration tests completed")

    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
