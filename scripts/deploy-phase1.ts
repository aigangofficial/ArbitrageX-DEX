import * as dotenv from 'dotenv';
import * as fs from 'fs';
import { ethers, network, run } from 'hardhat';
import { resolve } from 'path';

dotenv.config({ path: resolve(__dirname, '../config/.env') });

interface DeploymentInfo {
  network: {
    name: string;
    chainId: number;
  };
  contracts: {
    flashLoanService: {
      address: string;
      constructorArgs: string[];
    };
    arbitrageExecutor: {
      address: string;
      constructorArgs: string[];
    };
  };
  securityParams: {
    maxSlippage: number;
    minProfitBps: number;
    emergencyWithdrawalDelay: number;
    paramChangeDelay: number;
  };
  transactions: {
    flashLoanService: {
      hash: string;
      gasUsed: string;
      gasPrice: string;
      cost: string;
    };
    arbitrageExecutor: {
      hash: string;
      gasUsed: string;
      gasPrice: string;
      cost: string;
    };
  };
  verification: {
    flashLoanService: boolean;
    arbitrageExecutor: boolean;
  };
  timestamp: string;
  deployer: string;
}

async function verifyContract(name: string, address: string, constructorArguments: any[]) {
  console.log(`\nVerifying ${name}...`);
  try {
    await run('verify:verify', {
      address,
      constructorArguments,
    });
    return true;
  } catch (error) {
    console.log(`Error verifying ${name}:`, error);
    return false;
  }
}

async function initializeSecurityParams(arbitrageExecutor: any, flashLoanService: any) {
  console.log('\nInitializing security parameters...');

  // Set up FlashLoanService
  console.log('\nSetting up FlashLoanService...');
  const setupTx = await flashLoanService.setArbitrageExecutor(await arbitrageExecutor.getAddress());
  await setupTx.wait();
  console.log('ArbitrageExecutor set in FlashLoanService');

  return {
    maxSlippage: 100, // 1%
    minProfitBps: 50, // 0.5%
    emergencyWithdrawalDelay: 24 * 60 * 60, // 24 hours
    paramChangeDelay: 24 * 60 * 60, // 24 hours
  };
}

async function main() {
  console.log('Starting deployment of Phase 1 contracts...');
  console.log(`Network: ${network.name} (${network.config.chainId})`);

  // Set optimized gas settings for Amoy
  const deploymentConfig = {
    maxFeePerGas: ethers.parseUnits('35', 'gwei'),
    maxPriorityFeePerGas: ethers.parseUnits('25', 'gwei'),
    gasLimit: 3000000,
  };
  console.log(
    'Using max fee per gas:',
    ethers.formatUnits(deploymentConfig.maxFeePerGas, 'gwei'),
    'Gwei'
  );
  console.log(
    'Using max priority fee per gas:',
    ethers.formatUnits(deploymentConfig.maxPriorityFeePerGas, 'gwei'),
    'Gwei'
  );

  // Get network-specific addresses
  const AAVE_POOL =
    network.name === 'amoy'
      ? process.env.AMOY_AAVE_POOL
      : network.name === 'sepolia'
        ? process.env.SEPOLIA_AAVE_POOL
        : process.env.AAVE_POOL_ADDRESS;

  const UNISWAP =
    network.name === 'amoy'
      ? process.env.AMOY_QUICKSWAP_ROUTER // QuickSwap is Uniswap equivalent on Polygon
      : network.name === 'sepolia'
        ? process.env.SEPOLIA_UNISWAP_ROUTER
        : process.env.UNISWAP_ROUTER;

  const SUSHISWAP =
    network.name === 'amoy'
      ? process.env.AMOY_SUSHISWAP_ROUTER
      : network.name === 'sepolia'
        ? process.env.SEPOLIA_SUSHISWAP_ROUTER
        : process.env.SUSHISWAP_ROUTER;

  // Validate environment variables
  if (!AAVE_POOL || !UNISWAP || !SUSHISWAP) {
    throw new Error('Missing required environment variables');
  }

  // Validate addresses
  if (!ethers.isAddress(AAVE_POOL) || !ethers.isAddress(UNISWAP) || !ethers.isAddress(SUSHISWAP)) {
    throw new Error('Invalid contract addresses provided');
  }

  console.log('\nUsing addresses:');
  console.log('AAVE Pool:', AAVE_POOL);
  console.log('DEX Router 1:', UNISWAP);
  console.log('DEX Router 2:', SUSHISWAP);

  // Get deployer
  const [deployer] = await ethers.getSigners();
  console.log('\nDeploying contracts with account:', deployer.address);
  const balance = await deployer.provider.getBalance(deployer.address);
  console.log(
    'Account balance:',
    ethers.formatEther(balance),
    network.name === 'mumbai' ? 'MATIC' : 'ETH'
  );

  // Get current nonce
  const currentNonce = await deployer.getNonce();
  console.log('Current nonce:', currentNonce);

  // Deploy FlashLoanService
  const FlashLoanService = await ethers.getContractFactory('FlashLoanService');
  console.log('Deploying FlashLoanService...');
  const flashLoanService = await FlashLoanService.deploy(AAVE_POOL, { ...deploymentConfig });
  await flashLoanService.waitForDeployment();
  const flashLoanAddress = await flashLoanService.getAddress();
  console.log('FlashLoanService deployed to:', flashLoanAddress);

  // Deploy ArbitrageExecutor
  const ArbitrageExecutor = await ethers.getContractFactory('ArbitrageExecutor');
  console.log('\nDeploying ArbitrageExecutor...');
  const arbitrageExecutor = await ArbitrageExecutor.deploy(UNISWAP, SUSHISWAP, flashLoanAddress, {
    ...deploymentConfig,
  });
  await arbitrageExecutor.waitForDeployment();
  const arbitrageAddress = await arbitrageExecutor.getAddress();
  console.log('ArbitrageExecutor deployed to:', arbitrageAddress);

  // Initialize security parameters
  const securityParams = await initializeSecurityParams(arbitrageExecutor, flashLoanService);

  // Verify contracts on Etherscan with retry logic
  const verificationResults = {
    flashLoanService: false,
    arbitrageExecutor: false,
  };

  if (network.name !== 'hardhat') {
    console.log('\nWaiting for contract deployments to propagate...');
    await new Promise(resolve => setTimeout(resolve, 30000));

    const maxRetries = 3;
    for (let i = 0; i < maxRetries && !verificationResults.flashLoanService; i++) {
      try {
        verificationResults.flashLoanService = await verifyContract(
          'FlashLoanService',
          await flashLoanService.getAddress(),
          [AAVE_POOL]
        );
      } catch (error) {
        console.log(`Retry ${i + 1}/${maxRetries} for FlashLoanService verification`);
        await new Promise(resolve => setTimeout(resolve, 10000));
      }
    }

    for (let i = 0; i < maxRetries && !verificationResults.arbitrageExecutor; i++) {
      try {
        verificationResults.arbitrageExecutor = await verifyContract(
          'ArbitrageExecutor',
          await arbitrageExecutor.getAddress(),
          [UNISWAP, SUSHISWAP, await flashLoanService.getAddress()]
        );
      } catch (error) {
        console.log(`Retry ${i + 1}/${maxRetries} for ArbitrageExecutor verification`);
        await new Promise(resolve => setTimeout(resolve, 10000));
      }
    }
  }

  // Prepare deployment info
  const deploymentInfo: DeploymentInfo = {
    network: {
      name: network.name,
      chainId: network.config.chainId || 0,
    },
    contracts: {
      flashLoanService: {
        address: await flashLoanService.getAddress(),
        constructorArgs: [AAVE_POOL],
      },
      arbitrageExecutor: {
        address: await arbitrageExecutor.getAddress(),
        constructorArgs: [UNISWAP, SUSHISWAP, await flashLoanService.getAddress()],
      },
    },
    securityParams,
    transactions: {
      flashLoanService: {
        hash: 'unknown',
        gasUsed: 'unknown',
        gasPrice: 'unknown',
        cost: 'unknown',
      },
      arbitrageExecutor: {
        hash: 'unknown',
        gasUsed: 'unknown',
        gasPrice: 'unknown',
        cost: 'unknown',
      },
    },
    verification: verificationResults,
    timestamp: new Date().toISOString(),
    deployer: deployer.address,
  };

  // Save deployment info
  const deploymentPath = `deployments/${network.name}`;
  if (!fs.existsSync(deploymentPath)) {
    fs.mkdirSync(deploymentPath, { recursive: true });
  }

  fs.writeFileSync(
    `${deploymentPath}/deployment-phase1.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );

  // Print deployment summary
  console.log('\n=== Deployment Summary ===');
  console.log(`Network: ${network.name} (Chain ID: ${network.config.chainId})`);
  console.log(`Deployer: ${deployer.address}`);
  console.log('\nContracts:');
  console.log(`- FlashLoanService: ${await flashLoanService.getAddress()}`);
  console.log(`- ArbitrageExecutor: ${await arbitrageExecutor.getAddress()}`);
  console.log('\nSecurity Parameters:');
  console.log(`- Max Slippage: ${securityParams.maxSlippage} bps`);
  console.log(`- Min Profit: ${securityParams.minProfitBps} bps`);
  console.log(
    `- Emergency Withdrawal Delay: ${securityParams.emergencyWithdrawalDelay / 3600} hours`
  );
  console.log(`- Parameter Change Delay: ${securityParams.paramChangeDelay / 3600} hours`);
  console.log('\nVerification Status:');
  console.log(`- FlashLoanService: ${verificationResults.flashLoanService ? '✅' : '❌'}`);
  console.log(`- ArbitrageExecutor: ${verificationResults.arbitrageExecutor ? '✅' : '❌'}`);

  const totalGasUsed = 'unknown';
  console.log('\nTotal Gas Used:', totalGasUsed);

  return deploymentInfo;
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
