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

import * as dotenv from 'dotenv';
import { writeFileSync } from 'fs';
import { ethers, network } from 'hardhat';
import * as path from 'path';
import { resolve } from 'path';

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../config/.env') });

// Console colors for better visibility
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

interface NetworkAddresses {
  aavePool: string;
  uniswapRouter: string;
  sushiswapRouter: string;
  wmatic: string;
}

interface NetworkConfig {
  gas: {
    limit: bigint;
    maxPriorityFeePerGas: bigint;
    maxFeePerGas: bigint;
  };
  addresses: NetworkAddresses;
}

// Network-specific configurations
const networkConfigs: Record<string, NetworkConfig> = {
  amoy: {
    gas: {
      limit: 3_000_000n,
      maxPriorityFeePerGas: 3_000_000_000n, // 3 gwei
      maxFeePerGas: 30_000_000_000n, // 30 gwei
    },
    addresses: {
      aavePool: process.env.AMOY_AAVE_POOL || '',
      uniswapRouter: process.env.AMOY_QUICKSWAP_ROUTER || '',
      sushiswapRouter: process.env.AMOY_SUSHISWAP_ROUTER || '',
      wmatic: process.env.AMOY_WMATIC || '',
    },
  },
  sepolia: {
    gas: {
      limit: 3_000_000n,
      maxPriorityFeePerGas: network.name === 'amoy' ? 35_000_000_000n : 3_000_000_000n, // 35 gwei for Amoy, 3 gwei for others
      maxFeePerGas: network.name === 'amoy' ? 50_000_000_000n : 10_000_000_000n, // 50 gwei for Amoy, 10 gwei for others
    },
    addresses: {
      aavePool: process.env.SEPOLIA_AAVE_POOL || '',
      uniswapRouter: process.env.SEPOLIA_UNISWAP_ROUTER || '',
      sushiswapRouter: process.env.SEPOLIA_SUSHISWAP_ROUTER || '',
      wmatic: process.env.SEPOLIA_WETH || '',
    },
  },
};

async function main() {
  try {
    // Get network configuration
    const networkName = network.name.toLowerCase();
    const config = networkConfigs[networkName];

    if (!config) {
      throw new Error(`Unsupported network: ${networkName}`);
    }

    // Validate required addresses
    Object.entries(config.addresses).forEach(([key, value]) => {
      if (!value) {
        throw new Error(`Missing ${key} address for network ${networkName}`);
      }
    });

    console.log(
      colors.blue + '\n🚀 Starting deployment on ' + networkName.toUpperCase() + colors.reset
    );

    // Get deployer info
    const [deployer] = await ethers.getSigners();
    const balance = await deployer.provider.getBalance(deployer.address);

    console.log(colors.cyan + '\nDeployer Information:' + colors.reset);
    console.log(`Address: ${colors.yellow}${deployer.address}${colors.reset}`);
    console.log(
      `Balance: ${colors.green}${ethers.formatEther(balance)}${colors.reset} ${networkName === 'amoy' ? 'MATIC' : 'ETH'}`
    );

    // Get current gas prices
    const feeData = await deployer.provider.getFeeData();
    console.log(colors.cyan + '\nCurrent Gas Prices:' + colors.reset);
    console.log(
      `Base Fee: ${colors.yellow}${ethers.formatUnits(feeData.gasPrice || 0n, 'gwei')}${colors.reset} gwei`
    );
    console.log(
      `Max Priority Fee: ${colors.yellow}${ethers.formatUnits(feeData.maxPriorityFeePerGas || 0n, 'gwei')}${colors.reset} gwei`
    );
    console.log(
      `Max Fee: ${colors.yellow}${ethers.formatUnits(feeData.maxFeePerGas || 0n, 'gwei')}${colors.reset} gwei`
    );

    // Log network configuration
    console.log(colors.cyan + '\nNetwork Configuration:' + colors.reset);
    console.log('AAVE Pool:', colors.yellow + config.addresses.aavePool + colors.reset);
    console.log('Uniswap Router:', colors.yellow + config.addresses.uniswapRouter + colors.reset);
    console.log(
      'Sushiswap Router:',
      colors.yellow + config.addresses.sushiswapRouter + colors.reset
    );
    console.log('WMATIC:', colors.yellow + config.addresses.wmatic + colors.reset);

    // Deploy FlashLoanService
    console.log(colors.cyan + '\nDeploying FlashLoanService...' + colors.reset);
    const FlashLoanService = await ethers.getContractFactory('FlashLoanService');
    const flashLoanService = await FlashLoanService.deploy(config.addresses.aavePool);
    await flashLoanService.waitForDeployment();
    console.log(
      colors.green + '✅ FlashLoanService deployed to:',
      flashLoanService.target + colors.reset
    );

    // Deploy ArbitrageExecutor
    console.log(colors.cyan + '\nDeploying ArbitrageExecutor...' + colors.reset);
    const ArbitrageExecutor = await ethers.getContractFactory('ArbitrageExecutor');
    const arbitrageExecutor = await ArbitrageExecutor.deploy(
      config.addresses.uniswapRouter,
      config.addresses.sushiswapRouter
    );
    await arbitrageExecutor.waitForDeployment();
    console.log(
      colors.green + '✅ ArbitrageExecutor deployed to:',
      arbitrageExecutor.target + colors.reset
    );

    // Set up FlashLoanService with ArbitrageExecutor
    console.log(colors.cyan + '\nConfiguring FlashLoanService...' + colors.reset);
    const setArbitrageExecutorTx = await flashLoanService.setArbitrageExecutor(
      arbitrageExecutor.target
    );
    await setArbitrageExecutorTx.wait();
    console.log(colors.green + '✅ ArbitrageExecutor set in FlashLoanService' + colors.reset);

    // Whitelist WMATIC token in ArbitrageExecutor
    console.log(colors.cyan + '\nWhitelisting WMATIC token...' + colors.reset);
    const whitelistTokenTx = await arbitrageExecutor.whitelistToken(config.addresses.wmatic);
    await whitelistTokenTx.wait();
    console.log(colors.green + '✅ WMATIC token whitelisted' + colors.reset);

    // Check WMATIC token
    console.log(colors.cyan + '\nChecking WMATIC token...' + colors.reset);
    const wmatic = await ethers.getContractAt('MockWMATIC', config.addresses.wmatic);
    const wmaticBalance = await wmatic.balanceOf(deployer.address);
    console.log('WMATIC Balance:', ethers.formatEther(wmaticBalance), 'WMATIC');

    // Approve tokens for FlashLoanService
    console.log(colors.cyan + '\nApproving tokens for FlashLoanService...' + colors.reset);
    const approveTokensTx = await wmatic.approve(flashLoanService.target, ethers.MaxUint256);
    await approveTokensTx.wait();
    console.log(colors.green + '✅ WMATIC approved for FlashLoanService' + colors.reset);

    // Set up token approvals in FlashLoanService
    console.log(colors.cyan + '\nSetting up token approvals in FlashLoanService...' + colors.reset);
    const setupApprovalsTx = await flashLoanService.approveTokens(
      [config.addresses.wmatic],
      [arbitrageExecutor.target]
    );
    await setupApprovalsTx.wait();
    console.log(colors.green + '✅ Token approvals set up in FlashLoanService' + colors.reset);

    // Save contract addresses
    const addresses = {
      flashLoanService: await flashLoanService.getAddress(),
      arbitrageExecutor: await arbitrageExecutor.getAddress(),
      network: networkName,
      chainId: network.config.chainId,
      timestamp: new Date().toISOString(),
    };

    const addressesPath = resolve(__dirname, '../backend/config/contract-addresses.json');
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
