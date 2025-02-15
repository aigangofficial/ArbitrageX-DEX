import chalk from 'chalk';
import { ethers } from 'hardhat';

async function main() {
  // Generate new wallet
  const wallet = ethers.Wallet.createRandom();

  console.log(chalk.cyan('\n🔐 Generated New Wallet'));
  console.log(chalk.yellow('⚠️  SAVE THESE CREDENTIALS SECURELY AND NEVER SHARE THEM!\n'));

  console.log('Address:', chalk.green(wallet.address));
  console.log('Private Key:', chalk.red(wallet.privateKey));
  console.log('Mnemonic:', chalk.red(wallet.mnemonic?.phrase), '\n');

  // Get network info
  const provider = ethers.provider;
  const network = await provider.getNetwork();
  console.log(chalk.cyan('Network Information:'));
  console.log('Name:', chalk.yellow(network.name));
  console.log('Chain ID:', chalk.yellow(network.chainId.toString()));

  // Get gas prices
  const feeData = await provider.getFeeData();
  console.log('\nCurrent Gas Prices:');
  console.log(
    'Gas Price:',
    chalk.yellow(ethers.formatUnits(feeData.gasPrice || 0n, 'gwei')),
    'gwei'
  );

  console.log(chalk.cyan('\n📝 Next Steps:'));
  console.log('1. Save these credentials securely');
  console.log('2. Update DEPLOYER_PRIVATE_KEY in config/.env with the new private key');
  console.log('3. Fund this address with MATIC for deployment');
  console.log('4. Run npm run check-balance to verify funds\n');
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(chalk.red('Error generating wallet:'), error);
    process.exit(1);
  });
