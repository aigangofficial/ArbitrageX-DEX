/**
 * @title Contract Deployment Script
 * @description Deploys and configures the ArbitrageX smart contracts on specified networks
 *
 * FEATURES:
 * 1. Multi-Network Support:
 *    - Supports deployment to Sepolia testnet and mainnet
 *    - Configurable network parameters
 *    - Automatic gas optimization
 *
 * 2. Contract Deployment:
 *    - Deploys FlashLoanService
 *    - Deploys ArbitrageExecutor
 *    - Sets up contract relationships
 *
 * 3. Configuration Management:
 *    - Loads environment variables
 *    - Stores deployed addresses
 *    - Validates network settings
 *
 * USAGE:
 * ```bash
 * # Deploy to Sepolia testnet
 * npx hardhat run scripts/deploy.ts --network sepolia
 *
 * # Deploy to mainnet
 * npx hardhat run scripts/deploy.ts --network mainnet
 * ```
 *
 * @requires dotenv
 * @requires hardhat/ethers
 * @requires fs
 */

import dotenv from 'dotenv';
import { writeFileSync } from 'fs';
import { ethers, network } from 'hardhat';
import path from 'path';
import { ArbitrageExecutor, FlashLoanService } from '../typechain-types';

// Load environment variables from root .env
dotenv.config({ path: path.join(__dirname, '../.env') });

// Console colors for better visibility
const colors = {
  reset: '\x1b[0m',
  cyan: '\x1b[36m',
  yellow: '\x1b[33m',
  green: '\x1b[32m',
  red: '\x1b[31m'
};

// Required environment variables
const REQUIRED_ENV_VARS = [
  'AAVE_POOL_ADDRESS',
  'UNISWAP_ROUTER_ADDRESS',
  'SUSHISWAP_ROUTER_ADDRESS'
];

async function validateEnvironment() {
  const missingVars = REQUIRED_ENV_VARS.filter(varName => !process.env[varName]);
  if (missingVars.length > 0) {
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }
}

async function main() {
  try {
    // Validate environment variables
    await validateEnvironment();

    const networkName = network.name;
    console.log(colors.cyan + '\nDeploying contracts to network:', networkName + colors.reset);

    const [deployer] = await ethers.getSigners();
    console.log('Deployer address:', colors.yellow + deployer.address + colors.reset);

    // Get network configuration
    const provider = ethers.provider;
    const feeData = await provider.getFeeData();
    console.log(
      `\nGas Price: ${colors.yellow}${ethers.formatUnits(feeData.gasPrice || 0n, 'gwei')}${colors.reset} gwei`
    );

    // Deploy FlashLoanService
    console.log(colors.cyan + '\nDeploying FlashLoanService...' + colors.reset);
    const FlashLoanServiceFactory = await ethers.getContractFactory('FlashLoanService');
    const flashLoanService = (await FlashLoanServiceFactory.deploy(
      process.env.AAVE_POOL_ADDRESS!,
      process.env.AAVE_POOL_ADDRESS!, // Using same address for both pool and aavePool
      deployer.address
    )) as FlashLoanService;
    await flashLoanService.waitForDeployment();
    console.log(
      colors.green + '✅ FlashLoanService deployed to:',
      await flashLoanService.getAddress() + colors.reset
    );

    // Deploy ArbitrageExecutor
    console.log(colors.cyan + '\nDeploying ArbitrageExecutor...' + colors.reset);
    const ArbitrageExecutorFactory = await ethers.getContractFactory('ArbitrageExecutor');
    const arbitrageExecutor = (await ArbitrageExecutorFactory.deploy(
      process.env.UNISWAP_ROUTER_ADDRESS!,
      process.env.SUSHISWAP_ROUTER_ADDRESS!,
      await flashLoanService.getAddress()
    )) as ArbitrageExecutor;
    await arbitrageExecutor.waitForDeployment();
    console.log(
      colors.green + '✅ ArbitrageExecutor deployed to:',
      await arbitrageExecutor.getAddress() + colors.reset
    );

    // Set up FlashLoanService with ArbitrageExecutor
    console.log(colors.cyan + '\nConfiguring FlashLoanService...' + colors.reset);
    const setArbitrageExecutorTx = await flashLoanService.setArbitrageExecutor(
      await arbitrageExecutor.getAddress()
    );
    await setArbitrageExecutorTx.wait();
    console.log(colors.green + '✅ ArbitrageExecutor set in FlashLoanService' + colors.reset);

    // Save contract addresses
    const addresses = {
      flashLoanService: await flashLoanService.getAddress(),
      arbitrageExecutor: await arbitrageExecutor.getAddress(),
      network: networkName,
      chainId: network.config.chainId,
      timestamp: new Date().toISOString(),
    };

    const addressesPath = path.resolve(__dirname, '../backend/config/contract-addresses.json');
    writeFileSync(addressesPath, JSON.stringify(addresses, null, 2));
    console.log(colors.green + '\n✅ Contract addresses saved to:', addressesPath + colors.reset);

    // Final deployment summary
    console.log(colors.cyan + '\nDeployment Summary:' + colors.reset);
    console.log('Network:', colors.yellow + networkName.toUpperCase() + colors.reset);
    console.log(
      'FlashLoanService:',
      colors.yellow + (await flashLoanService.getAddress()) + colors.reset
    );
    console.log(
      'ArbitrageExecutor:',
      colors.yellow + (await arbitrageExecutor.getAddress()) + colors.reset
    );
    console.log(colors.green + '\n✨ Deployment completed successfully!\n' + colors.reset);
  } catch (error: any) {
    console.error(colors.red + '\n❌ Deployment failed:' + colors.reset, error?.message || error);
    console.error(colors.yellow + '\nStack trace:' + colors.reset, error?.stack);
    process.exit(1);
  }
}

main().catch(error => {
  console.error(colors.red + '\n❌ Unhandled error:' + colors.reset, error);
  process.exit(1);
});
