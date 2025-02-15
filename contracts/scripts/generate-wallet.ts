import { ethers } from 'ethers';
import { AMOY_CONFIG } from '../../config/network';

async function main() {
  // Generate new wallet
  const wallet = ethers.Wallet.createRandom();

  console.log('\n🔐 Generated New Wallet');
  console.log('⚠️  SAVE THESE CREDENTIALS SECURELY AND NEVER SHARE THEM!\n');

  console.log('Address:', wallet.address);
  console.log('Private Key:', wallet.privateKey);
  console.log('Mnemonic:', wallet.mnemonic?.phrase, '\n');

  // Get network info
  const provider = new ethers.JsonRpcProvider(AMOY_CONFIG.rpc);
  const network = await provider.getNetwork();
  console.log('Network Information:');
  console.log('Name:', network.name);
  console.log('Chain ID:', network.chainId.toString());

  // Get gas prices
  const feeData = await provider.getFeeData();
  console.log('\nCurrent Gas Prices:');
  console.log('Gas Price:', ethers.formatUnits(feeData.gasPrice || 0n, 'gwei'), 'gwei');

  console.log('\n📝 Next Steps:');
  console.log('1. Save these credentials securely');
  console.log('2. Update DEPLOYER_PRIVATE_KEY in config/.env with the new private key');
  console.log('3. Fund this address with MATIC for deployment');
  console.log('4. Run npm run check-balance to verify funds\n');
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error('Error generating wallet:', error);
    process.exit(1);
  });
