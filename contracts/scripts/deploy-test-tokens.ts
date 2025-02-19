import { ethers } from 'hardhat';
import { join } from 'path';

async function main() {
  console.log('Deploying test tokens to Amoy testnet...');

  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with account:', deployer.address);

  // Deploy USDC
  console.log('\nDeploying MockUSDC...');
  const MockUSDC = await ethers.getContractFactory('MockToken');
  const mockUSDC = await MockUSDC.deploy('USD Coin', 'USDC', 6);
  await mockUSDC.waitForDeployment();
  console.log('MockUSDC deployed to:', await mockUSDC.getAddress());

  // Deploy USDT
  console.log('\nDeploying MockUSDT...');
  const MockUSDT = await ethers.getContractFactory('MockToken');
  const mockUSDT = await MockUSDT.deploy('Tether USD', 'USDT', 6);
  await mockUSDT.waitForDeployment();
  console.log('MockUSDT deployed to:', await mockUSDT.getAddress());

  // Deploy DAI
  console.log('\nDeploying MockDAI...');
  const MockDAI = await ethers.getContractFactory('MockToken');
  const mockDAI = await MockDAI.deploy('Dai Stablecoin', 'DAI', 18);
  await mockDAI.waitForDeployment();
  console.log('MockDAI deployed to:', await mockDAI.getAddress());

  // Save addresses to config/.env
  const addresses = {
    AMOY_USDC: await mockUSDC.getAddress(),
    AMOY_USDT: await mockUSDT.getAddress(),
    AMOY_DAI: await mockDAI.getAddress(),
  };

  // Update .env file
  const envPath = join(__dirname, '../../config/.env');
  const fs = require('fs');
  let envContent = fs.readFileSync(envPath, 'utf8');

  // Update each token address
  Object.entries(addresses).forEach(([key, value]) => {
    const regex = new RegExp(`${key}=.*`);
    if (envContent.match(regex)) {
      envContent = envContent.replace(regex, `${key}=${value}`);
    } else {
      envContent += `\n${key}=${value}`;
    }
  });

  fs.writeFileSync(envPath, envContent);
  console.log('\nToken addresses saved to config/.env');
  console.log(addresses);
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error('Deployment failed:', error);
    process.exit(1);
  });
