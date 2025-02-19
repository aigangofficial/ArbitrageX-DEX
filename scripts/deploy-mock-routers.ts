import { writeFileSync } from 'fs';
import { ethers } from 'hardhat';
import { join } from 'path';

const colors = {
  reset: '\x1b[0m',
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
};

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log(colors.cyan + '\nDeploying mock routers...' + colors.reset);
  console.log('Deployer:', colors.yellow + deployer.address + colors.reset);

  // Deploy MockWMATIC first (needed for routers)
  console.log(colors.cyan + '\nDeploying MockWMATIC...' + colors.reset);
  const MockWMATIC = await ethers.getContractFactory('MockWMATIC');
  const mockWMATIC = await MockWMATIC.deploy();
  await mockWMATIC.waitForDeployment();
  console.log(colors.green + '✅ MockWMATIC deployed to:', mockWMATIC.target + colors.reset);

  // Deploy MockQuickSwapRouter
  console.log(colors.cyan + '\nDeploying MockQuickSwapRouter...' + colors.reset);
  const MockQuickSwapRouter = await ethers.getContractFactory('MockUniswapRouter');
  const mockQuickSwapRouter = await MockQuickSwapRouter.deploy(mockWMATIC.target);
  await mockQuickSwapRouter.waitForDeployment();
  console.log(
    colors.green + '✅ MockQuickSwapRouter deployed to:',
    mockQuickSwapRouter.target + colors.reset
  );

  // Deploy MockSushiSwapRouter
  console.log(colors.cyan + '\nDeploying MockSushiSwapRouter...' + colors.reset);
  const MockSushiSwapRouter = await ethers.getContractFactory('MockUniswapRouter');
  const mockSushiSwapRouter = await MockSushiSwapRouter.deploy(mockWMATIC.target);
  await mockSushiSwapRouter.waitForDeployment();
  console.log(
    colors.green + '✅ MockSushiSwapRouter deployed to:',
    mockSushiSwapRouter.target + colors.reset
  );

  // Save addresses
  const addresses = {
    wmatic: mockWMATIC.target,
    quickswapRouter: mockQuickSwapRouter.target,
    sushiswapRouter: mockSushiSwapRouter.target,
  };

  // Save to config file
  const configPath = join(__dirname, '../config/mock-addresses.json');
  writeFileSync(configPath, JSON.stringify(addresses, null, 2));
  console.log(colors.green + '\n✅ Mock addresses saved to:', configPath + colors.reset);

  // Update .env.root with mock addresses
  const envPath = join(__dirname, '../.env.root');
  const fs = require('fs');
  let envContent = fs.readFileSync(envPath, 'utf8');

  // Update each address
  const updates = {
    AMOY_WMATIC: mockWMATIC.target,
    AMOY_QUICKSWAP_ROUTER: mockQuickSwapRouter.target,
    AMOY_SUSHISWAP_ROUTER: mockSushiSwapRouter.target,
  };

  Object.entries(updates).forEach(([key, value]) => {
    const regex = new RegExp(`${key}=.*`);
    if (envContent.match(regex)) {
      envContent = envContent.replace(regex, `${key}=${value}`);
    } else {
      envContent += `\n${key}=${value}`;
    }
  });

  fs.writeFileSync(envPath, envContent);
  console.log(colors.green + '\n✅ Mock addresses updated in .env.root' + colors.reset);
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(colors.red + '\n❌ Deployment failed:' + colors.reset);
    console.error(error);
    process.exit(1);
  });
