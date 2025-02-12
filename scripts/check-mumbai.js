const { ethers } = require('ethers');
require('dotenv').config({ path: './config/.env' });

async function main() {
  try {
    // Connect to Mumbai network
    const provider = new ethers.JsonRpcProvider(process.env.MUMBAI_RPC);

    // Create wallet instance
    const wallet = new ethers.Wallet(process.env.DEPLOYER_PRIVATE_KEY, provider);

    console.log('\n=== Wallet Info ===');
    console.log('Address:', wallet.address);
    const balance = await provider.getBalance(wallet.address);
    console.log('Balance:', ethers.formatEther(balance), 'MATIC');

    // Get network info
    const network = await provider.getNetwork();
    console.log('\n=== Network Info ===');
    console.log('Chain ID:', network.chainId);

    // Get latest block
    const block = await provider.getBlock('latest');
    console.log('\n=== Latest Block ===');
    console.log('Block Number:', block?.number);
    console.log('Block Time:', new Date((block?.timestamp || 0) * 1000).toLocaleString());

    console.log('\n=== Get Test MATIC ===');
    console.log('1. Visit Mumbai Faucet: https://faucet.polygon.technology/');
    console.log('2. Or Alchemy Faucet: https://mumbaifaucet.com/');
    console.log('3. Enter your wallet address:', wallet.address);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
