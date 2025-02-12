const { ethers } = require('ethers');
require('dotenv').config({ path: './config/.env' });

async function main() {
  try {
    // Connect to Amoy network using official RPC
    const provider = new ethers.JsonRpcProvider('https://rpc-amoy.polygon.technology');

    // Check specific address
    const address = '0x2A0bC541884459c4cBB6fCBf81396A47fD670098';

    console.log('\n=== Wallet Info ===');
    console.log('Address:', address);
    const balance = await provider.getBalance(address);
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

    // Check if we have enough balance for deployment
    const minBalance = ethers.parseEther('0.1'); // We need at least 0.1 MATIC
    if (balance < minBalance) {
      console.log('\n⚠️ Warning: Low balance');
      console.log('Current balance:', ethers.formatEther(balance), 'MATIC');
      console.log('Recommended minimum:', ethers.formatEther(minBalance), 'MATIC');
    } else {
      console.log('\n✅ Balance is sufficient for deployment');
      console.log('You can proceed with deploying the contracts using:');
      console.log('npx hardhat run scripts/deploy-phase1.ts --network amoy');
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
