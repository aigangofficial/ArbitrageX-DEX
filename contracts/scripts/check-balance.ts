import { ethers } from 'ethers';

async function main() {
  console.log(`\n🔍 Checking balances on AMOY...\n`);

  const provider = new ethers.JsonRpcProvider(process.env.AMOY_RPC);
  const wallet = new ethers.Wallet(process.env.DEPLOYER_PRIVATE_KEY || '', provider);

  // Get account balance
  const balance = await provider.getBalance(wallet.address);
  console.log('Account Information:');
  console.log(`Address: ${wallet.address}`);
  console.log(`Balance: ${ethers.formatEther(balance)} MATIC\n`);

  // Get network info
  const blockNumber = await provider.getBlockNumber();
  const feeData = await provider.getFeeData();

  console.log('Network Information:');
  console.log(`Network: AMOY`);
  console.log(`Chain ID: 80002`);
  console.log(`Latest Block: ${blockNumber}`);
  console.log(`Base Fee: ${ethers.formatUnits(feeData.gasPrice || 0n, 'gwei')} gwei`);
  console.log(
    `Max Priority Fee: ${ethers.formatUnits(feeData.maxPriorityFeePerGas || 0n, 'gwei')} gwei`
  );
  console.log(`Max Fee: ${ethers.formatUnits(feeData.maxFeePerGas || 0n, 'gwei')} gwei\n`);

  // Check if balance is sufficient for deployment
  const minBalance = ethers.parseEther('0.5');
  if (balance < minBalance) {
    console.log(
      `⚠️  Insufficient balance for deployment. Please fund this address with at least 0.5 MATIC\n`
    );
    console.log('Polygon Amoy Faucets:');
    console.log('1. Polygon Faucet: https://faucet.polygon.technology/');
    console.log('2. QuickNode Faucet: https://faucet.quicknode.com/polygon/amoy');
    console.log('3. Request in Polygon Discord: https://discord.gg/polygon\n');
  } else {
    console.log(`✅ Balance is sufficient for deployment (${ethers.formatEther(balance)} MATIC)\n`);
  }
}

main().catch(error => {
  console.error('\n❌ Script failed:', error);
  process.exit(1);
});
