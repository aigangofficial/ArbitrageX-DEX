import { writeFileSync } from 'fs';
import { ethers } from 'hardhat';
import { join } from 'path';

async function main() {
  console.log('Deploying test tokens to Amoy testnet...');

  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with account:', deployer.address);

  const gasLimit = 2000000; // Reduced gas limit
  const gasPrice = ethers.parseUnits('25', 'gwei'); // Adjusted gas price to meet minimum requirement

  // Deploy Mock WMATIC
  const MockWMATIC = await ethers.getContractFactory('MockWMATIC');
  const wmatic = await MockWMATIC.deploy({ gasLimit, gasPrice });
  await wmatic.waitForDeployment();
  const wmaticAddress = await wmatic.getAddress();
  console.log('MockWMATIC deployed to:', wmaticAddress);

  // Deploy Mock USDC
  const MockUSDC = await ethers.getContractFactory('MockUSDC');
  const usdc = await MockUSDC.deploy({ gasLimit, gasPrice });
  await usdc.waitForDeployment();
  const usdcAddress = await usdc.getAddress();
  console.log('MockUSDC deployed to:', usdcAddress);

  // Deploy Mock USDT
  const MockUSDT = await ethers.getContractFactory('MockUSDT');
  const usdt = await MockUSDT.deploy({ gasLimit, gasPrice });
  await usdt.waitForDeployment();
  const usdtAddress = await usdt.getAddress();
  console.log('MockUSDT deployed to:', usdtAddress);

  // Save addresses to a JSON file
  const addresses = {
    WMATIC: wmaticAddress,
    USDC: usdcAddress,
    USDT: usdtAddress,
  };

  const addressesPath = join(__dirname, '../..', 'backend/config/testnet-addresses.json');
  writeFileSync(addressesPath, JSON.stringify(addresses, null, 2));
  console.log('Contract addresses saved to:', addressesPath);
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
