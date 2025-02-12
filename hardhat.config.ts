import '@nomicfoundation/hardhat-chai-matchers';
import '@nomicfoundation/hardhat-ethers';
import '@nomicfoundation/hardhat-toolbox';
import '@typechain/hardhat';
import * as dotenv from 'dotenv';
import 'hardhat-gas-reporter';
import { HardhatUserConfig } from 'hardhat/config';
import { resolve } from 'path';
import 'solidity-coverage';

// Load environment variables from config/.env
dotenv.config({ path: resolve(__dirname, './config/.env') });

// Ensure required environment variables are set
const REQUIRED_ENV_VARS = [
  'SEPOLIA_RPC',
  'MAINNET_RPC',
  'AMOY_RPC',
  'DEPLOYER_PRIVATE_KEY',
  'ETHERSCAN_API_KEY',
  'POLYGONSCAN_API_KEY',
];

for (const envVar of REQUIRED_ENV_VARS) {
  if (!process.env[envVar]) {
    console.warn(`Warning: ${envVar} is not set in config/.env`);
  }
}

const config = {
  solidity: {
    version: '0.8.21',
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
        details: {
          yul: true,
          yulDetails: {
            stackAllocation: true,
            optimizerSteps: 'dhfoDgvulfnTUtnIf',
          },
        },
      },
      viaIR: true,
      metadata: {
        bytecodeHash: 'none',
      },
    },
  },
  networks: {
    hardhat: {
      chainId: 31337,
      allowUnlimitedContractSize: true,
      forking: {
        url: process.env.MAINNET_RPC || '',
        enabled: false,
      },
    },
    amoy: {
      url: 'https://rpc-amoy.polygon.technology',
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      gasPrice: 50000000000, // 50 Gwei
      gas: 5000000,
      timeout: 120000, // 2 minutes
      chainId: 80002, // Polygon Amoy chainId
    },
    mumbai: {
      url: process.env.MUMBAI_RPC || '',
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      gasPrice: 'auto',
      gas: 5000000,
      timeout: 120000, // 2 minutes
    },
    sepolia: {
      url:
        process.env.SEPOLIA_RPC?.replace('YOUR-PROJECT-ID', process.env.INFURA_API_KEY || '') || '',
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      gasPrice: 'auto',
      gas: 8000000,
      timeout: 120000,
    },
    mainnet: {
      url:
        process.env.MAINNET_RPC?.replace('YOUR-PROJECT-ID', process.env.INFURA_API_KEY || '') || '',
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
      gasPrice: 'auto',
    },
  },
  gasReporter: {
    enabled: process.env.REPORT_GAS !== undefined,
    currency: 'USD',
    coinmarketcap: process.env.COINMARKETCAP_API_KEY,
    gasPrice: 30,
    excludeContracts: ['Mock'],
  },
  etherscan: {
    apiKey: {
      sepolia: process.env.ETHERSCAN_API_KEY || '',
      polygonAmoy: process.env.POLYGONSCAN_API_KEY || '',
    },
  },
  paths: {
    sources: './contracts',
    tests: './test',
    cache: './cache',
    artifacts: './artifacts',
    root: '.',
  },
  mocha: {
    timeout: 40000,
  },
  sourcify: {
    enabled: true,
  },
  typechain: {
    outDir: 'typechain-types',
    target: 'ethers-v6',
    alwaysGenerateOverloads: true,
    discriminateTypes: true,
  },
} as HardhatUserConfig;

export default config;
