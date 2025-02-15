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
  console.log(colors.cyan + '\nDeploying mock tokens...' + colors.reset);
  console.log('Deployer:', colors.yellow + deployer.address + colors.reset);

  // Deploy MockWMATIC
  console.log(colors.cyan + '\nDeploying MockWMATIC...' + colors.reset);
  const MockWMATIC = await ethers.getContractFactory('MockWMATIC');
  const mockWMATIC = await MockWMATIC.deploy();
  await mockWMATIC.waitForDeployment();
  console.log(colors.green + '✅ MockWMATIC deployed to:', mockWMATIC.target + colors.reset);

  // Save addresses
  const addresses = {
    wmatic: mockWMATIC.target,
  };

  // Save to config file
  const configPath = join(__dirname, '../config/mock-addresses.json');
  writeFileSync(configPath, JSON.stringify(addresses, null, 2));
  console.log(colors.green + '\n✅ Mock addresses saved to:', configPath + colors.reset);
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(colors.red + '\n❌ Deployment failed:' + colors.reset);
    console.error(error);
    process.exit(1);
  });
