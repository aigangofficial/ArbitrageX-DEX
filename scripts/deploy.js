"use strict";
/**
 * @title Contract Deployment Script
 * @description Deploys and configures the ArbitrageX smart contracts on specified networks
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
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const dotenv = __importStar(require("dotenv"));
const fs_1 = require("fs");
const hardhat_1 = require("hardhat");
const path = __importStar(require("path"));
const path_1 = require("path");
// Load environment variables
dotenv.config({ path: path.join(__dirname, '../config/.env') });
// Console colors for better visibility
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
};
// Network-specific configurations
const networkConfigs = {
    amoy: {
        gas: {
            limit: 3000000n,
            maxPriorityFeePerGas: 3000000000n, // 3 gwei
            maxFeePerGas: 30000000000n, // 30 gwei
        },
        addresses: {
            aavePool: process.env.AMOY_AAVE_POOL || '',
            uniswapRouter: process.env.AMOY_QUICKSWAP_ROUTER || '',
            sushiswapRouter: process.env.AMOY_SUSHISWAP_ROUTER || '',
            wmatic: process.env.AMOY_WMATIC || '',
        },
    },
    sepolia: {
        gas: {
            limit: 3000000n,
            maxPriorityFeePerGas: hardhat_1.network.name === 'amoy' ? 35000000000n : 3000000000n, // 35 gwei for Amoy, 3 gwei for others
            maxFeePerGas: hardhat_1.network.name === 'amoy' ? 50000000000n : 10000000000n, // 50 gwei for Amoy, 10 gwei for others
        },
        addresses: {
            aavePool: process.env.SEPOLIA_AAVE_POOL || '',
            uniswapRouter: process.env.SEPOLIA_UNISWAP_ROUTER || '',
            sushiswapRouter: process.env.SEPOLIA_SUSHISWAP_ROUTER || '',
            wmatic: process.env.SEPOLIA_WETH || '',
        },
    },
};
async function main() {
    try {
        // Get network configuration
        const networkName = hardhat_1.network.name.toLowerCase();
        const config = networkConfigs[networkName];
        if (!config) {
            throw new Error(`Unsupported network: ${networkName}`);
        }
        // Validate required addresses
        Object.entries(config.addresses).forEach(([key, value]) => {
            if (!value) {
                throw new Error(`Missing ${key} address for network ${networkName}`);
            }
        });
        console.log(colors.blue + '\n🚀 Starting deployment on ' + networkName.toUpperCase() + colors.reset);
        // Get deployer info
        const [deployer] = await hardhat_1.ethers.getSigners();
        const balance = await deployer.provider.getBalance(deployer.address);
        console.log(colors.cyan + '\nDeployer Information:' + colors.reset);
        console.log(`Address: ${colors.yellow}${deployer.address}${colors.reset}`);
        console.log(`Balance: ${colors.green}${hardhat_1.ethers.formatEther(balance)}${colors.reset} ${networkName === 'amoy' ? 'MATIC' : 'ETH'}`);
        // Get current gas prices
        const feeData = await deployer.provider.getFeeData();
        console.log(colors.cyan + '\nCurrent Gas Prices:' + colors.reset);
        console.log(`Base Fee: ${colors.yellow}${hardhat_1.ethers.formatUnits(feeData.gasPrice || 0n, 'gwei')}${colors.reset} gwei`);
        console.log(`Max Priority Fee: ${colors.yellow}${hardhat_1.ethers.formatUnits(feeData.maxPriorityFeePerGas || 0n, 'gwei')}${colors.reset} gwei`);
        console.log(`Max Fee: ${colors.yellow}${hardhat_1.ethers.formatUnits(feeData.maxFeePerGas || 0n, 'gwei')}${colors.reset} gwei`);
        // Log network configuration
        console.log(colors.cyan + '\nNetwork Configuration:' + colors.reset);
        console.log('AAVE Pool:', colors.yellow + config.addresses.aavePool + colors.reset);
        console.log('Uniswap Router:', colors.yellow + config.addresses.uniswapRouter + colors.reset);
        console.log('Sushiswap Router:', colors.yellow + config.addresses.sushiswapRouter + colors.reset);
        console.log('WMATIC:', colors.yellow + config.addresses.wmatic + colors.reset);
        // Load mock addresses
        const mockAddresses = JSON.parse((0, fs_1.readFileSync)((0, path_1.join)(__dirname, '../config/mock-addresses.json'), 'utf-8'));
        // Configure network settings
        const mockConfig = {
            gas: {
                limit: 3000000n,
                maxPriorityFeePerGas: hardhat_1.network.name === 'amoy' ? 35000000000n : 3000000000n, // 35 gwei for Amoy, 3 gwei for others
                maxFeePerGas: hardhat_1.network.name === 'amoy' ? 50000000000n : 10000000000n, // 50 gwei for Amoy, 10 gwei for others
            },
            addresses: {
                aavePool: process.env.SEPOLIA_AAVE_POOL || '',
                uniswapRouter: process.env.UNISWAP_ROUTER || '0x8954AfA98594b838bda56FE4C12a09D7739D179b',
                sushiswapRouter: process.env.SUSHISWAP_ROUTER || '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                wmatic: mockAddresses.wmatic,
            },
        };
        // Deploy FlashLoanService
        console.log(colors.cyan + '\nDeploying FlashLoanService...' + colors.reset);
        const FlashLoanService = await hardhat_1.ethers.getContractFactory('FlashLoanService');
        const flashLoanService = await FlashLoanService.deploy(mockConfig.addresses.aavePool);
        await flashLoanService.waitForDeployment();
        console.log(colors.green + '✅ FlashLoanService deployed to:', flashLoanService.target + colors.reset);
        // Deploy ArbitrageExecutor
        console.log(colors.cyan + '\nDeploying ArbitrageExecutor...' + colors.reset);
        const ArbitrageExecutor = await hardhat_1.ethers.getContractFactory('ArbitrageExecutor');
        const arbitrageExecutor = await ArbitrageExecutor.deploy(mockConfig.addresses.uniswapRouter, mockConfig.addresses.sushiswapRouter);
        await arbitrageExecutor.waitForDeployment();
        console.log(colors.green + '✅ ArbitrageExecutor deployed to:', arbitrageExecutor.target + colors.reset);
        // Set up FlashLoanService with ArbitrageExecutor
        console.log(colors.cyan + '\nConfiguring FlashLoanService...' + colors.reset);
        const setArbitrageExecutorTx = await flashLoanService.setArbitrageExecutor(arbitrageExecutor.target);
        await setArbitrageExecutorTx.wait();
        console.log(colors.green + '✅ ArbitrageExecutor set in FlashLoanService' + colors.reset);
        // Whitelist WMATIC token in ArbitrageExecutor
        console.log(colors.cyan + '\nWhitelisting WMATIC token...' + colors.reset);
        const whitelistTokenTx = await arbitrageExecutor.whitelistToken(mockConfig.addresses.wmatic);
        await whitelistTokenTx.wait();
        console.log(colors.green + '✅ WMATIC token whitelisted' + colors.reset);
        // Check WMATIC token
        console.log(colors.cyan + '\nChecking WMATIC token...' + colors.reset);
        const wmatic = await hardhat_1.ethers.getContractAt('MockWMATIC', mockConfig.addresses.wmatic);
        const wmaticBalance = await wmatic.balanceOf(deployer.address);
        console.log('WMATIC Balance:', hardhat_1.ethers.formatEther(wmaticBalance), 'WMATIC');
        // Approve tokens for FlashLoanService
        console.log(colors.cyan + '\nApproving tokens for FlashLoanService...' + colors.reset);
        const approveTokensTx = await wmatic.approve(flashLoanService.target, hardhat_1.ethers.MaxUint256);
        await approveTokensTx.wait();
        console.log(colors.green + '✅ WMATIC approved for FlashLoanService' + colors.reset);
        // Set up token approvals in FlashLoanService
        console.log(colors.cyan + '\nSetting up token approvals in FlashLoanService...' + colors.reset);
        const setupApprovalsTx = await flashLoanService.approveTokens([mockConfig.addresses.wmatic], [arbitrageExecutor.target]);
        await setupApprovalsTx.wait();
        console.log(colors.green + '✅ Token approvals set up in FlashLoanService' + colors.reset);
        // Save contract addresses
        const addresses = {
            flashLoanService: await flashLoanService.getAddress(),
            arbitrageExecutor: await arbitrageExecutor.getAddress(),
            network: networkName,
            chainId: hardhat_1.network.config.chainId,
            timestamp: new Date().toISOString(),
        };
        const addressesPath = (0, path_1.resolve)(__dirname, '../backend/config/contract-addresses.json');
        (0, fs_1.writeFileSync)(addressesPath, JSON.stringify(addresses, null, 2));
        console.log(colors.green + '\n✅ Contract addresses saved to:', addressesPath + colors.reset);
        // Final deployment summary
        console.log(colors.cyan + '\nDeployment Summary:' + colors.reset);
        console.log('Network:', colors.yellow + networkName.toUpperCase() + colors.reset);
        console.log('FlashLoanService:', colors.yellow + (await flashLoanService.getAddress()) + colors.reset);
        console.log('ArbitrageExecutor:', colors.yellow + (await arbitrageExecutor.getAddress()) + colors.reset);
        console.log(colors.green + '\n✨ Deployment completed successfully!\n' + colors.reset);
    }
    catch (error) {
        console.error(colors.red + '\n❌ Deployment failed:' + colors.reset, error?.message || error);
        console.error(colors.yellow + '\nStack trace:' + colors.reset, error?.stack);
        process.exit(1);
    }
}
main().catch(error => {
    console.error(colors.red + '\n❌ Unhandled error:' + colors.reset, error);
    process.exit(1);
});
