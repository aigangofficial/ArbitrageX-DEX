import { ethers } from 'hardhat';

async function main() {
  // Connect to Amoy network
  const provider = new ethers.JsonRpcProvider(process.env.AMOY_RPC);

  // Create wallet instance
  const wallet = new ethers.Wallet(process.env.DEPLOYER_PRIVATE_KEY!, provider);

  console.log('\n=== Wallet Info ===');
  console.log('Address:', wallet.address);
  const balance = await provider.getBalance(wallet.address);
  console.log('Balance:', ethers.formatEther(balance), 'MATIC');

  // Get network info
  const network = await provider.getNetwork();
  console.log('\n=== Network Info ===');
  console.log('Network Name:', network.name);
  console.log('Chain ID:', network.chainId);

  // Get latest block
  const block = await provider.getBlock('latest');
  console.log('\n=== Latest Block ===');
  console.log('Block Number:', block?.number);
  console.log('Block Time:', new Date((block?.timestamp || 0) * 1000).toLocaleString());
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
