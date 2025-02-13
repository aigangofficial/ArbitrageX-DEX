import { ethers } from 'hardhat';

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
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
