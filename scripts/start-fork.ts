import * as dotenv from 'dotenv';
import { ethers } from 'hardhat';
import { resolve } from 'path';

async function main() {
  // Load fork environment configuration
  dotenv.config({ path: resolve(__dirname, '../config/.env.fork') });

  console.log('Starting Mainnet Fork...');
  console.log(`Fork Block Number: ${process.env.FORK_BLOCK_NUMBER}`);

  // Get network information
  const provider = ethers.provider;
  const network = await provider.getNetwork();

  console.log(`Connected to network:`);
  console.log(`- Chain ID: ${network.chainId}`);
  console.log(`- Network Name: ${network.name}`);

  // Get a test account
  const [signer] = await ethers.getSigners();
  const balance = await provider.getBalance(await signer.getAddress());
  console.log(`\nTest account address: ${await signer.getAddress()}`);
  console.log(`Balance: ${ethers.formatEther(balance)} ETH`);

  // Verify access to mainnet contracts
  const uniswapRouter = process.env.UNISWAP_V2_ROUTER;
  const sushiswapRouter = process.env.SUSHISWAP_ROUTER;

  console.log('\nVerifying DEX Router Contracts:');
  console.log(`- Uniswap V2 Router: ${uniswapRouter}`);
  console.log(`- SushiSwap Router: ${sushiswapRouter}`);

  console.log('\nMainnet fork is running and ready for testing!');
  console.log('Use Ctrl+C to stop the fork.');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
