import * as dotenv from 'dotenv';
import * as fs from 'fs';
import { ethers, network, run } from 'hardhat';
import * as path from 'path';

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../config/.env') });

// Testnet-specific parameters
const TESTNET_PARAMS = {
  gasLimit: network.name === 'amoy' ? 15_000_000n : 5_000_000n,
  gasPrice: network.name === 'amoy' ? 50_000_000_000n : undefined, // 50 Gwei for Amoy
  confirmations: network.name === 'amoy' ? 2 : 1,
  deploymentTimeout: network.name === 'amoy' ? 120000 : 60000, // 2 minutes for Amoy
};

async function main() {
  console.log('Starting deployment of Phase 1 contracts...');

  // Get network info
  const network = await ethers.provider.getNetwork();
  console.log(`Network: ${network.name} (${network.chainId})`);

  // Get deployer account
  const [deployer] = await ethers.getSigners();
  const balance = await deployer.provider.getBalance(deployer.address);
  const nonce = await deployer.getNonce();

  console.log(`\nDeploying contracts with account: ${deployer.address}`);
  console.log(`Account balance: ${ethers.formatEther(balance)} ETH`);
  console.log(`Current nonce: ${nonce}`);

  // Set deployment parameters
  const maxFeePerGas = ethers.parseUnits('35', 'gwei');
  const maxPriorityFeePerGas = ethers.parseUnits('25', 'gwei');
  console.log(`\nUsing max fee per gas: ${ethers.formatUnits(maxFeePerGas, 'gwei')} Gwei`);
  console.log(
    `Using max priority fee per gas: ${ethers.formatUnits(maxPriorityFeePerGas, 'gwei')} Gwei`
  );

  // Contract addresses for Amoy testnet
  const AAVE_POOL = '0x357D51124f59836DeD84c8a1730D72B749d8BC23';
  const DEX_ROUTER_1 = '0x8954AfA98594b838bda56FE4C12a09D7739D179b';
  const DEX_ROUTER_2 = '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506';

  console.log('\nUsing addresses:');
  console.log(`AAVE Pool: ${AAVE_POOL}`);
  console.log(`DEX Router 1: ${DEX_ROUTER_1}`);
  console.log(`DEX Router 2: ${DEX_ROUTER_2}`);

  // Deploy FlashLoanService
  console.log('\nDeploying FlashLoanService...');
  const FlashLoanService = await ethers.getContractFactory('FlashLoanService');
  const flashLoanService = await FlashLoanService.deploy(AAVE_POOL, {
    maxFeePerGas,
    maxPriorityFeePerGas,
    gasLimit: 3000000,
  });
  await flashLoanService.waitForDeployment();
  const flashLoanAddress = await flashLoanService.getAddress();
  console.log(`FlashLoanService deployed to: ${flashLoanAddress}`);

  // Deploy ArbitrageExecutor
  console.log('\nDeploying ArbitrageExecutor...');
  const ArbitrageExecutor = await ethers.getContractFactory('ArbitrageExecutor');
  const arbitrageExecutor = await ArbitrageExecutor.deploy(
    flashLoanAddress,
    DEX_ROUTER_1,
    DEX_ROUTER_2,
    {
      maxFeePerGas,
      maxPriorityFeePerGas,
      gasLimit: 3000000,
    }
  );
  await arbitrageExecutor.waitForDeployment();
  const arbitrageAddress = await arbitrageExecutor.getAddress();
  console.log(`ArbitrageExecutor deployed to: ${arbitrageAddress}`);

  // Save deployed addresses
  const deployedAddresses = {
    flashLoanService: flashLoanAddress,
    arbitrageExecutor: arbitrageAddress,
  };

  console.log('\nDeployment complete! Addresses:', deployedAddresses);

  // Save deployment addresses
  const deploymentInfo = {
    network: network.name,
    flashLoanService: flashLoanAddress,
    arbitrageExecutor: arbitrageAddress,
    timestamp: new Date().toISOString(),
    params: {
      gasLimit: TESTNET_PARAMS.gasLimit.toString(),
      gasPrice: TESTNET_PARAMS.gasPrice?.toString() || 'auto',
      confirmations: TESTNET_PARAMS.confirmations,
    },
  };

  // Ensure the config directory exists
  const configDir = path.join(__dirname, '../backend/config');
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }

  // Save deployment info
  const deploymentPath = path.join(configDir, 'contractAddresses.json');
  fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
  console.log(`📝 Deployment info saved to: ${deploymentPath}`);

  // Wait for etherscan to index the contracts
  if (network.name !== 'hardhat' && network.name !== 'localhost') {
    console.log('⏳ Waiting for Etherscan to index contracts...');
    await new Promise(resolve => setTimeout(resolve, TESTNET_PARAMS.deploymentTimeout));

    // Verify contracts on Etherscan/Polygonscan
    try {
      console.log('🔍 Verifying contracts on block explorer...');
      await run('verify:verify', {
        address: flashLoanAddress,
        constructorArguments: [AAVE_POOL],
      });
      await run('verify:verify', {
        address: arbitrageAddress,
        constructorArguments: [flashLoanAddress, DEX_ROUTER_1, DEX_ROUTER_2],
        contract: 'contracts/core/ArbitrageExecutor.sol:ArbitrageExecutor',
      });
      console.log('✅ Contract verification complete!');
    } catch (error) {
      console.error('❌ Error verifying contracts:', error);
    }
  }

  console.log('🎉 Deployment complete!');
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
