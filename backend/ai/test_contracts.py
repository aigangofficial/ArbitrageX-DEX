import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_network_connection(web3):
    """Test basic network connectivity and chain information."""
    try:
        # Get basic network info
        block_number = web3.eth.block_number
        chain_id = web3.eth.chain_id
        gas_price = web3.eth.gas_price

        logger.info(f"Connected to network:")
        logger.info(f"- Block number: {block_number}")
        logger.info(f"- Chain ID: {chain_id}")
        logger.info(f"- Gas price: {Web3.from_wei(gas_price, 'gwei')} Gwei")

        # Get latest block details
        latest_block = web3.eth.get_block('latest')
        logger.info(f"\nLatest block details:")
        logger.info(f"- Number: {latest_block['number']}")
        logger.info(f"- Hash: {latest_block['hash'].hex()}")
        logger.info(f"- Parent Hash: {latest_block['parentHash'].hex()}")
        logger.info(f"- Timestamp: {latest_block['timestamp']}")
        logger.info(f"- Gas Limit: {latest_block['gasLimit']}")
        logger.info(f"- Gas Used: {latest_block['gasUsed']}")
        logger.info(f"- Base Fee: {Web3.from_wei(latest_block.get('baseFeePerGas', 0), 'gwei')} Gwei")

        # Get network status
        is_syncing = web3.eth.syncing
        logger.info(f"\nNetwork status:")
        logger.info(f"- Syncing: {'Yes' if is_syncing else 'No'}")
        logger.info(f"- Peer count: {web3.net.peer_count}")

        return True
    except Exception as e:
        logger.error(f"Error testing network connection: {str(e)}")
        return False

def main():
    try:
        # Initialize Web3 with Amoy testnet
        rpc_url = "https://polygon-amoy.g.alchemy.com/v2/dTwNgMXtwagIb1lZBjP_A03m5ko7WaR1"
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if not web3.is_connected():
            logger.error("Failed to connect to the network")
            return

        logger.info("Successfully connected to the network")

        # Test network connection
        if not test_network_connection(web3):
            logger.error("Failed to get network information")
            return

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    main()
