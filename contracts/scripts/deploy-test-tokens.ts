import { writeFileSync } from 'fs';
import { ethers } from 'hardhat';
import { join } from 'path';

async function main() {
  console.log('Deploying test tokens to Amoy testnet...');

  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with account:', deployer.address);

  const gasLimit = 1000000; // Lower gas limit
  const gasPrice = ethers.parseUnits('10', 'gwei'); // Lower gas price

  console.log('Deploying mock tokens...');

  // Deploy WMATIC
  const MockWMATIC = await ethers.getContractFactory('contracts/mocks/MockWMATIC.sol:MockWMATIC');
  const mockWMATIC = await MockWMATIC.deploy({
    gasLimit,
    gasPrice,
  });
  await mockWMATIC.waitForDeployment();
  console.log('MockWMATIC deployed to:', await mockWMATIC.getAddress());

  // Deploy USDC
  const MockUSDC = await ethers.getContractFactory('contracts/mocks/MockUSDC.sol:MockUSDC');
  const mockUSDC = await MockUSDC.deploy({
    gasLimit,
    gasPrice,
  });
  await mockUSDC.waitForDeployment();
  console.log('MockUSDC deployed to:', await mockUSDC.getAddress());

  // Deploy USDT
  const MockUSDT = await ethers.getContractFactory('contracts/mocks/MockUSDT.sol:MockUSDT');
  const mockUSDT = await MockUSDT.deploy({
    gasLimit,
    gasPrice,
  });
  await mockUSDT.waitForDeployment();
  console.log('MockUSDT deployed to:', await mockUSDT.getAddress());

  // Mint some tokens to deployer
  const mintAmount = ethers.parseUnits('1000000', 18); // 1 million tokens

  await mockWMATIC.mint(deployer.address, mintAmount, {
    gasLimit: 100000,
    gasPrice,
  });
  await mockUSDC.mint(deployer.address, mintAmount, {
    gasLimit: 100000,
    gasPrice,
  });
  await mockUSDT.mint(deployer.address, mintAmount, {
    gasLimit: 100000,
    gasPrice,
  });

  console.log('Minted 1 million tokens each to:', deployer.address);

  // Save addresses to a JSON file
  const addresses = {
    WMATIC: await mockWMATIC.getAddress(),
    USDC: await mockUSDC.getAddress(),
    USDT: await mockUSDT.getAddress(),
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
