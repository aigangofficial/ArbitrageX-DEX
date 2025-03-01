import * as dotenv from 'dotenv';
import { ethers } from 'hardhat';
import { resolve } from 'path';
import fs from 'fs';
import path from 'path';

// Execution Mode enum
enum ExecutionMode {
  MAINNET = 'mainnet',
  FORK = 'fork'
}

async function main() {
  // Load fork environment configuration
  dotenv.config({ path: resolve(__dirname, '../config/.env.fork') });

  console.log('Starting Mainnet Fork...');
  console.log(`Fork Block Number: ${process.env.FORK_BLOCK_NUMBER}`);

  // Get network information
  const provider = ethers.provider;
  const network = await provider.getNetwork();

  console.log(`Connected to network:`);
  console.log(`- Chain ID: ${network.chainId}`);
  console.log(`- Network Name: ${network.name}`);

  // Get a test account
  const [signer] = await ethers.getSigners();
  const balance = await provider.getBalance(await signer.getAddress());
  console.log(`\nTest account address: ${await signer.getAddress()}`);
  console.log(`Balance: ${ethers.formatEther(balance)} ETH`);

  // Verify access to mainnet contracts
  const uniswapRouter = process.env.UNISWAP_V2_ROUTER;
  const sushiswapRouter = process.env.SUSHISWAP_ROUTER;

  console.log('\nVerifying DEX Router Contracts:');
  console.log(`- Uniswap V2 Router: ${uniswapRouter}`);
  console.log(`- SushiSwap Router: ${sushiswapRouter}`);
  
  // Update .env file to set execution mode to FORK
  updateEnvFile();
  
  // Update execution mode config file
  updateExecutionModeConfig();

  console.log('\nMainnet fork is running and ready for testing!');
  console.log('Execution mode set to FORK');
  console.log('Use Ctrl+C to stop the fork.');
}

function updateEnvFile() {
  try {
    const envPath = path.join(__dirname, '../.env');
    let envContent = '';
    
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
      
      // Update or add EXECUTION_MODE
      if (envContent.includes('EXECUTION_MODE=')) {
        envContent = envContent.replace(/EXECUTION_MODE=\w+/g, `EXECUTION_MODE=${ExecutionMode.FORK}`);
      } else {
        envContent += `\nEXECUTION_MODE=${ExecutionMode.FORK}`;
      }
    } else {
      // Create new .env file with execution mode
      envContent = `EXECUTION_MODE=${ExecutionMode.FORK}`;
    }
    
    fs.writeFileSync(envPath, envContent);
    console.log('\nUpdated .env file with FORK execution mode');
  } catch (error) {
    console.error('Error updating .env file:', error);
  }
}

function updateExecutionModeConfig() {
  try {
    const configDir = path.join(__dirname, '../backend/config');
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
    
    const configPath = path.join(configDir, 'execution-mode.json');
    const executionModeConfig = {
      mode: ExecutionMode.FORK,
      lastUpdated: new Date().toISOString(),
      updatedBy: 'start-fork.ts'
    };
    
    fs.writeFileSync(configPath, JSON.stringify(executionModeConfig, null, 2));
    console.log('Updated execution mode config file');
  } catch (error) {
    console.error('Error updating execution mode config:', error);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
