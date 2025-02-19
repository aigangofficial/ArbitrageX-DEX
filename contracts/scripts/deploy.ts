import { ethers } from 'hardhat';

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with the account:', deployer.address);

  // Deploy QuickSwap Router
  const QuickSwapRouter = await ethers.getContractFactory('UniswapV2Router02');
  const quickswapRouter = await QuickSwapRouter.deploy();
  await quickswapRouter.waitForDeployment();
  console.log('QuickSwap Router deployed to:', await quickswapRouter.getAddress());

  // Deploy SushiSwap Router
  const SushiSwapRouter = await ethers.getContractFactory('UniswapV2Router02');
  const sushiswapRouter = await SushiSwapRouter.deploy();
  await sushiswapRouter.waitForDeployment();
  console.log('SushiSwap Router deployed to:', await sushiswapRouter.getAddress());

  // Deploy WMATIC
  const WMATIC = await ethers.getContractFactory('WMATIC');
  const wmatic = await WMATIC.deploy();
  await wmatic.waitForDeployment();
  console.log('WMATIC deployed to:', await wmatic.getAddress());

  // Deploy USDC
  const USDC = await ethers.getContractFactory('USDC');
  const usdc = await USDC.deploy();
  await usdc.waitForDeployment();
  console.log('USDC deployed to:', await usdc.getAddress());

  // Deploy Aave Pool
  const AavePool = await ethers.getContractFactory('AavePool');
  const aavePool = await AavePool.deploy();
  await aavePool.waitForDeployment();
  console.log('Aave Pool deployed to:', await aavePool.getAddress());
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
