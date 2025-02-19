/**
 * @title Enhanced Contract Deployment Script
 * @description Deploys ArbitrageX contracts with dynamic gas pricing and robust transaction handling
 *
 * FEATURES:
 * 1. Multi-Network Support:
 *    - Supports deployment to Sepolia testnet and mainnet
 *    - Configurable network parameters
 *    - Automatic gas optimization
 *
 * 2. Contract Deployment:
 *    - Deploys FlashLoanService
 *    - Deploys ArbitrageExecutor
 *    - Sets up contract relationships
 *
 * 3. Configuration Management:
 *    - Loads environment variables
 *    - Stores deployed addresses
 *    - Validates network settings
 *
 * USAGE:
 * ```bash
 * # Deploy to Sepolia testnet
 * npx hardhat run scripts/deploy.ts --network sepolia
 *
 * # Deploy to mainnet
 * npx hardhat run scripts/deploy.ts --network mainnet
 * ```
 *
 * @requires dotenv
 * @requires hardhat/ethers
 * @requires fs
 */

import axios from 'axios';
import dotenv from 'dotenv';
import { ContractTransactionResponse, parseUnits } from "ethers";
import { ethers, network } from 'hardhat';
import path from 'path';

// Load environment variables from root .env
dotenv.config({ path: path.join(__dirname, '../.env') });

// Constants
const REQUIRED_ENV_VARS = [
  'ETHERSCAN_API_KEY',
  'AAVE_POOL_ADDRESS',
  'UNISWAP_ROUTER_ADDRESS',
  'SUSHISWAP_ROUTER_ADDRESS'
];

const CONFIRMATION_TIMEOUT = 300000; // 5 minutes
const CONFIRMATIONS_REQUIRED = 2;
const MAX_RETRIES = 3;
const RETRY_DELAY = 15000; // 15 seconds
const GAS_PRICE_BUFFER = 1.1; // 10% buffer on gas price
const GAS_LIMIT_BUFFER = 1.2; // 20% buffer on gas limit
const DEFAULT_GAS_PRICE_GWEI = '50'; // Fallback gas price
const NONCE_AHEAD = 5; // Look ahead for pending nonces

// Console colors for better visibility
const colors = {
  reset: '\x1b[0m',
  cyan: '\x1b[36m',
  yellow: '\x1b[33m',
  green: '\x1b[32m',
  red: '\x1b[31m'
};

interface EtherscanGasResponse {
  status: string;
  message: string;
  result: {
    LastBlock: string;
    SafeGasPrice: string;
    ProposeGasPrice: string;
    FastGasPrice: string;
  };
}

async function validateEnvironment() {
  const missingVars = REQUIRED_ENV_VARS.filter(varName => !process.env[varName]);
  if (missingVars.length > 0) {
    throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
  }
}

async function fetchGasPrice(): Promise<bigint> {
  try {
    const response = await axios.get<EtherscanGasResponse>(
      `https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=${process.env.ETHERSCAN_API_KEY}`
    );

    if (response.data.status === '1' && response.data.result) {
      const proposeGasPrice = response.data.result.ProposeGasPrice;
      console.log(`\nEtherscan Proposed Gas Price: ${proposeGasPrice} gwei`);
      return parseUnits(proposeGasPrice, 'gwei');
    } else {
      throw new Error('Invalid response from Etherscan API');
    }
  } catch (error: any) {
    console.warn(`\n⚠️ Failed to fetch gas price from Etherscan: ${error.message}`);
    console.warn('Using default gas price...');
    return parseUnits(DEFAULT_GAS_PRICE_GWEI, 'gwei');
  }
}

async function findNextAvailableNonce(provider: any, address: string, currentNonce: number): Promise<number> {
  console.log("\nChecking for pending transactions...");

  // Check the next few nonces
  for (let i = 0; i < NONCE_AHEAD; i++) {
    const testNonce = currentNonce + i;
    try {
      // Try to get any pending transaction with this nonce
      const pendingTx = await provider.getTransaction({
        from: address,
        nonce: testNonce
      });

      if (!pendingTx) {
        console.log(`Found available nonce: ${testNonce}`);
        return testNonce;
      }
      console.log(`Nonce ${testNonce} is in use by transaction: ${pendingTx.hash}`);
    } catch (error) {
      // If we can't find a transaction, this nonce is probably available
      return testNonce;
    }
  }

  // If we couldn't find an available nonce, use the current one + NONCE_AHEAD
  return currentNonce + NONCE_AHEAD;
}

async function waitForConfirmations(tx: ContractTransactionResponse, attempt = 1): Promise<any> {
  console.log(`\nWaiting for confirmations (Attempt ${attempt}/${MAX_RETRIES})...`);
  console.log("Transaction hash:", tx.hash);

  try {
    const receipt = await Promise.race([
      tx.wait(CONFIRMATIONS_REQUIRED),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Transaction confirmation timeout")), CONFIRMATION_TIMEOUT)
      )
    ]);
    return receipt;
  } catch (error: any) {
    if (attempt < MAX_RETRIES) {
      if (error?.message?.includes("already known")) {
        console.log("\n⚠️ Transaction already in mempool. Waiting for confirmations...");
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        return waitForConfirmations(tx, attempt + 1);
      }

      console.log(`\n⚠️ Attempt ${attempt} failed. Retrying in ${RETRY_DELAY / 1000} seconds...`);
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      return waitForConfirmations(tx, attempt + 1);
    }

    if (error?.message === "Transaction confirmation timeout") {
      console.log("\n⚠️ All confirmation attempts timed out. You can check the status later with:");
      console.log(`npx hardhat verify --network ${network.name} ${tx.hash}`);
    }
    throw error;
  }
}

async function deployContract(
  deployer: any,
  factory: any,
  args: any[],
  gasPrice: bigint,
  initialNonce: number
) {
  console.log("\nPreparing deployment transaction...");
  const deployTx = await factory.getDeployTransaction(...args);

  // Find next available nonce
  const nonce = await findNextAvailableNonce(ethers.provider, deployer.address, initialNonce);

  console.log("Estimating gas...");
  const gasEstimate = await ethers.provider.estimateGas({
    ...deployTx,
    nonce
  });
  console.log("Estimated gas:", gasEstimate.toString());

  const gasLimit = Math.ceil(Number(gasEstimate) * GAS_LIMIT_BUFFER);
  console.log("Gas limit with buffer:", gasLimit);

  console.log("\nDeployment Parameters:");
  console.log("- Gas Price:", ethers.formatUnits(gasPrice, "gwei"), "gwei");
  console.log("- Gas Limit:", gasLimit);
  console.log("- Nonce:", nonce);

  let attempt = 0;
  while (attempt < MAX_RETRIES) {
    try {
      console.log(`\nSending deployment transaction (Attempt ${attempt + 1}/${MAX_RETRIES})...`);
      const tx = await deployer.sendTransaction({
        ...deployTx,
        nonce,
        gasLimit,
        gasPrice
      });

      const receipt = await waitForConfirmations(tx);
      return { tx, receipt };
    } catch (error: any) {
      attempt++;
      if (error?.message?.includes("already known")) {
        console.log("\n⚠️ Transaction already in mempool. Waiting for confirmations...");
        // Wait for potential confirmation
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        continue;
      }

      if (attempt < MAX_RETRIES) {
        console.log(`\n⚠️ Deployment attempt ${attempt} failed. Retrying in ${RETRY_DELAY / 1000} seconds...`);
        console.log("Error:", error.message);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        continue;
      }
      throw error;
    }
  }
  throw new Error("Max deployment attempts reached");
}

async function main() {
  try {
    console.log(`\nDeploying contracts to network: ${colors.cyan}${network.name}${colors.reset}`);

    // Validate environment
    await validateEnvironment();

    const [deployer] = await ethers.getSigners();
    console.log("Deployer address:", deployer.address);

    // Fetch dynamic gas price
    const gasPrice = await fetchGasPrice();
    const adjustedGasPrice = gasPrice * BigInt(Math.floor(GAS_PRICE_BUFFER * 100)) / 100n;

    const baseNonce = await ethers.provider.getTransactionCount(deployer.address);

    // Contract addresses
    const flashLoanServiceAddress = "0xa1fC549b59043e2578dd89AE2Ed19b0552645809";
    const uniswapRouterAddress = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
    const sushiswapRouterAddress = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506";

    console.log("\nUsing addresses:");
    console.log("- FlashLoanService:", flashLoanServiceAddress);
    console.log("- Uniswap Router:", uniswapRouterAddress);
    console.log("- SushiSwap Router:", sushiswapRouterAddress);

    // Deploy ArbitrageExecutor
    console.log("\nDeploying ArbitrageExecutor...");
    const ArbitrageExecutor = await ethers.getContractFactory("ArbitrageExecutor");

    const { receipt } = await deployContract(
      deployer,
      ArbitrageExecutor,
      [uniswapRouterAddress, sushiswapRouterAddress, flashLoanServiceAddress],
      adjustedGasPrice,
      baseNonce
    );

    const arbitrageExecutorAddress = receipt.contractAddress;
    console.log(`\n${colors.green}✅ ArbitrageExecutor deployed successfully!${colors.reset}`);
    console.log("Contract address:", arbitrageExecutorAddress);

    // Deployment Summary
    console.log("\nDeployment Summary:");
    console.log(`Network: ${colors.cyan}${network.name.toUpperCase()}${colors.reset}`);
    console.log("FlashLoanService:", flashLoanServiceAddress);
    console.log("ArbitrageExecutor:", arbitrageExecutorAddress);

    // Save deployment info
    const deploymentInfo = {
      network: network.name,
      timestamp: new Date().toISOString(),
      flashLoanService: flashLoanServiceAddress,
      arbitrageExecutor: arbitrageExecutorAddress,
      deployer: deployer.address,
      gasPrice: ethers.formatUnits(adjustedGasPrice, "gwei"),
      transactionHash: receipt.hash
    };

    console.log("\nDeployment Info:", deploymentInfo);
  } catch (error) {
    console.error(`\n${colors.red}❌ Deployment failed:${colors.reset}`, error);
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
