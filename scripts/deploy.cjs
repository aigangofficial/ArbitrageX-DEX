/**
 * @title Mainnet Deployment Script
 * @description Deploys ArbitrageX contracts to Ethereum mainnet with robust error handling and gas optimization
 */

const { ethers } = require('hardhat');
const fs = require('fs');
const path = require('path');

// Mainnet contract addresses
const UNISWAP_V2_ROUTER = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D';
const SUSHISWAP_V2_ROUTER = '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F';
const USDC = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';
const WETH = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';

// Only wait for confirmations on mainnet
const isMainnet = process.env.DEPLOY_NETWORK === 'mainnet';
const CONFIRMATIONS = isMainnet ? 5 : 0;

// Gas settings for local deployment
const LOCAL_GAS_SETTINGS = {
  gasLimit: 5000000,
  gasPrice: ethers.parseUnits('50', 'gwei'),
};

async function main() {
  console.time('Total Deployment');
  console.log('\n🚀 Starting deployment on', isMainnet ? 'mainnet' : 'local fork');

  // Get deployer account
  const [deployer] = await ethers.getSigners();
  const balance = await ethers.provider.getBalance(deployer.address);

  console.log(`Deploying from: ${deployer.address}`);
  console.log(`Account balance: ${ethers.formatEther(balance)} ETH\n`);

  // Deploy SecurityAdmin
  console.time('SecurityAdmin Deploy');
  console.log('Deploying SecurityAdmin...');
  const SecurityAdmin = await ethers.getContractFactory('SecurityAdmin');
  const securityAdmin = await SecurityAdmin.deploy(isMainnet ? {} : LOCAL_GAS_SETTINGS);
  const securityAdminAddress = await securityAdmin.getAddress();
  console.log(`SecurityAdmin deployed to: ${securityAdminAddress}`);
  console.timeEnd('SecurityAdmin Deploy');

  // Deploy ArbitrageExecutor
  console.time('ArbitrageExecutor Deploy');
  console.log('\nDeploying ArbitrageExecutor...');
  const ArbitrageExecutor = await ethers.getContractFactory('ArbitrageExecutor');
  const arbitrageExecutor = await ArbitrageExecutor.deploy(
    UNISWAP_V2_ROUTER,
    SUSHISWAP_V2_ROUTER,
    deployer.address,
    isMainnet ? {} : LOCAL_GAS_SETTINGS
  );
  const arbitrageExecutorAddress = await arbitrageExecutor.getAddress();
  console.log(`ArbitrageExecutor deployed to: ${arbitrageExecutorAddress}`);
  console.timeEnd('ArbitrageExecutor Deploy');

  // Configure ArbitrageExecutor
  console.time('Configuration');
  console.log('\nConfiguring ArbitrageExecutor...');

  // If on fork, don't wait for confirmations and use local gas settings
  const txOptions = isMainnet ? {} : LOCAL_GAS_SETTINGS;

  try {
    console.time('USDC Support');
    await arbitrageExecutor.setSupportedToken(USDC, true, txOptions);
    console.timeEnd('USDC Support');

    console.time('WETH Support');
    await arbitrageExecutor.setSupportedToken(WETH, true, txOptions);
    console.timeEnd('WETH Support');

    console.time('Profit BPS');
    await arbitrageExecutor.setMinProfitBps(10, txOptions);
    console.timeEnd('Profit BPS');

    console.log('✅ All configurations completed');
  } catch (error) {
    console.error('Error during configuration:', error.message);
    throw error;
  }
  console.timeEnd('Configuration');

  // Save deployment addresses
  const deploymentAddresses = {
    securityAdmin: securityAdminAddress,
    arbitrageExecutor: arbitrageExecutorAddress,
    uniswapRouter: UNISWAP_V2_ROUTER,
    sushiswapRouter: SUSHISWAP_V2_ROUTER,
    usdc: USDC,
    weth: WETH,
  };

  const addressesPath = path.join(__dirname, '../backend/config/contractAddresses.json');
  fs.writeFileSync(addressesPath, JSON.stringify(deploymentAddresses, null, 2));

  console.log('\n✅ Deployment complete!');
  console.log('Contract addresses saved to:', addressesPath);
  console.log('\nDeployed Addresses:');
  console.log(JSON.stringify(deploymentAddresses, null, 2));
  console.timeEnd('Total Deployment');
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error('\n❌ Deployment failed!');
    console.error(error);
    process.exit(1);
  });
