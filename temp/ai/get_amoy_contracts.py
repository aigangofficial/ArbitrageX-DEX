import asyncio
import aiohttp
import logging
from web3 import Web3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path='config/.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
POLYGONSCAN_API_KEY = os.getenv('POLYGONSCAN_API_KEY')
AMOY_API_URL = "https://api-amoy.polygonscan.com/api"

async def get_contract_info(session, address):
    """Get contract info from Amoy explorer API."""
    try:
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
            'apikey': POLYGONSCAN_API_KEY
        }

        async with session.get(AMOY_API_URL, params=params) as response:
            data = await response.json()
            if data['status'] == '1' and data['result'][0].get('ContractName'):
                return data['result'][0]
    except Exception as e:
        logger.error(f"Error getting contract info: {str(e)}")
    return None

async def check_token_contract(session, address):
    """Check if address is a token contract."""
    try:
        params = {
            'module': 'token',
            'action': 'tokeninfo',
            'contractaddress': address,
            'apikey': POLYGONSCAN_API_KEY
        }

        async with session.get(AMOY_API_URL, params=params) as response:
            data = await response.json()
            if data['status'] == '1':
                return data['result']
    except Exception as e:
        logger.error(f"Error checking token: {str(e)}")
    return None

async def get_contract_transactions(session, address):
    """Get transactions for a specific contract."""
    try:
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': '0',
            'endblock': '999999999',
            'sort': 'desc',
            'apikey': POLYGONSCAN_API_KEY
        }

        async with session.get(AMOY_API_URL, params=params) as response:
            data = await response.json()
            if data['status'] == '1':
                return data['result']
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
    return []

async def scan_contracts():
    """Scan for deployed contracts on Amoy testnet."""
    if not POLYGONSCAN_API_KEY:
        logger.error("POLYGONSCAN_API_KEY not set in environment variables")
        return {}

    async with aiohttp.ClientSession() as session:
        # Known contract addresses to check
        addresses_to_check = [
            # WMATIC addresses
            '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889',
            '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
            # USDC addresses
            '0x9999f7Fea5938fD3b1E26A12c3f2fb024e194f97',
            '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            # USDT addresses
            '0x7e4C234B1d634DB790592d1550816b19E862F744',
            '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
            # QuickSwap addresses
            '0x8954AfA98594b838bda56FE4C12a09D7739D179b',
            '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
            # SushiSwap addresses
            '0x0C8b5D4Bf676BD283c4F343c260bC668aa07aF49',
            '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
        ]

        found_contracts = {}

        for address in addresses_to_check:
            logger.info(f"\nChecking address: {address}")

            # Get contract info
            contract_info = await get_contract_info(session, address)
            if contract_info:
                contract_name = contract_info.get('ContractName', '')
                logger.info(f"Found contract: {contract_name}")

                # Get token info if it's a token
                token_info = await check_token_contract(session, address)

                # Get recent transactions
                transactions = await get_contract_transactions(session, address)

                # Store contract info
                contract_data = {
                    'address': address,
                    'name': contract_name,
                    'verified': bool(contract_info.get('SourceCode')),
                    'implementation': contract_info.get('Implementation', ''),
                    'proxy': bool(contract_info.get('Proxy', '0') == '1'),
                    'last_transaction': transactions[0] if transactions else None
                }

                if token_info:
                    contract_data.update({
                        'symbol': token_info.get('symbol'),
                        'decimals': token_info.get('decimals'),
                        'total_supply': token_info.get('totalSupply')
                    })

                # Categorize contract
                if 'WMATIC' in contract_name or 'Wrapped MATIC' in contract_name:
                    found_contracts['WMATIC'] = contract_data
                elif 'USDC' in contract_name or 'USD Coin' in contract_name:
                    found_contracts['USDC'] = contract_data
                elif 'USDT' in contract_name or 'Tether' in contract_name:
                    found_contracts['USDT'] = contract_data
                elif 'Quick' in contract_name:
                    if 'Router' in contract_name:
                        found_contracts['QUICKSWAP_ROUTER'] = contract_data
                    elif 'Factory' in contract_name:
                        found_contracts['QUICKSWAP_FACTORY'] = contract_data
                elif 'Sushi' in contract_name:
                    if 'Router' in contract_name:
                        found_contracts['SUSHISWAP_ROUTER'] = contract_data
                    elif 'Factory' in contract_name:
                        found_contracts['SUSHISWAP_FACTORY'] = contract_data

        return found_contracts

async def main():
    """Main function to discover contracts."""
    logger.info("Starting contract discovery on Amoy testnet...")

    contracts = await scan_contracts()

    if contracts:
        logger.info("\nDiscovered contracts:")
        logger.info(json.dumps(contracts, indent=2))

        # Update contract addresses in web3_connector.py
        logger.info("\nUpdating contract addresses in web3_connector.py...")
        contract_addresses = {}
        for key, data in contracts.items():
            if data.get('last_transaction'):  # Only use active contracts
                contract_addresses[key] = data['address']

        if contract_addresses:
            logger.info("Found active contracts:")
            logger.info(json.dumps(contract_addresses, indent=2))
    else:
        logger.warning("No contracts discovered")

if __name__ == "__main__":
    asyncio.run(main())
