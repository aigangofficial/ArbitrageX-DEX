import asyncio
import aiohttp
import logging
from web3 import Web3
from web3_connector import CONTRACT_ADDRESSES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

AMOY_EXPLORER_API = "https://api-amoy.polygonscan.com/api"
AMOY_EXPLORER_URL = "https://amoy.polygonscan.com/address/"

async def verify_contract_on_explorer(session, address):
    """Verify contract using Polygon Amoy explorer API."""
    try:
        params = {
            'module': 'contract',
            'action': 'getabi',
            'address': address,
            'format': 'json'
        }

        async with session.get(AMOY_EXPLORER_API, params=params) as response:
            data = await response.json()
            if data['status'] == '1' and data['message'] == 'OK':
                logger.info(f"✓ Contract verified at {address}")
                logger.info(f"  Explorer URL: {AMOY_EXPLORER_URL}{address}")
                return True
            else:
                logger.warning(f"✗ Contract not verified at {address}")
                logger.warning(f"  Explorer URL: {AMOY_EXPLORER_URL}{address}")
                return False
    except Exception as e:
        logger.error(f"Error verifying contract at {address}: {str(e)}")
        return False

async def main():
    """Main function to verify all contracts."""
    async with aiohttp.ClientSession() as session:
        logger.info("Starting contract verification on Polygon Amoy testnet...")

        # Verify each contract
        for name, address in CONTRACT_ADDRESSES.items():
            logger.info(f"\nVerifying {name}...")
            verified = await verify_contract_on_explorer(session, address)

            if verified:
                # Try to get contract bytecode
                try:
                    w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/polygon_amoy"))
                    code = await w3.eth.get_code(Web3.to_checksum_address(address))
                    if len(code) > 2:
                        logger.info(f"  Contract has bytecode (length: {len(code)})")
                    else:
                        logger.warning(f"  Contract has no bytecode")
                except Exception as e:
                    logger.error(f"  Error getting bytecode: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
