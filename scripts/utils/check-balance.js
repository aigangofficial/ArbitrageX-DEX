"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const hardhat_1 = require("hardhat");
// Console colors
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
};
async function main() {
    console.log(colors.blue + `\n🔍 Checking balances on ${hardhat_1.network.name.toUpperCase()}...\n` + colors.reset);
    const [deployer] = await hardhat_1.ethers.getSigners();
    const provider = deployer.provider;
    // Get account balance
    const balance = await provider.getBalance(deployer.address);
    const currency = hardhat_1.network.name === 'amoy' ? 'MATIC' : 'ETH';
    console.log(colors.cyan + 'Account Information:' + colors.reset);
    console.log(`Address: ${colors.yellow}${deployer.address}${colors.reset}`);
    console.log(`Balance: ${colors.green}${hardhat_1.ethers.formatEther(balance)}${colors.reset} ${currency}\n`);
    // Get network info
    const blockNumber = await provider.getBlockNumber();
    const feeData = await provider.getFeeData();
    console.log(colors.cyan + 'Network Information:' + colors.reset);
    console.log(`Network: ${colors.yellow}${hardhat_1.network.name.toUpperCase()}${colors.reset}`);
    console.log(`Chain ID: ${colors.yellow}${hardhat_1.network.config.chainId}${colors.reset}`);
    console.log(`Latest Block: ${colors.yellow}${blockNumber}${colors.reset}`);
    console.log(`Base Fee: ${colors.yellow}${hardhat_1.ethers.formatUnits(feeData.gasPrice || 0n, 'gwei')}${colors.reset} gwei`);
    console.log(`Max Priority Fee: ${colors.yellow}${hardhat_1.ethers.formatUnits(feeData.maxPriorityFeePerGas || 0n, 'gwei')}${colors.reset} gwei`);
    console.log(`Max Fee: ${colors.yellow}${hardhat_1.ethers.formatUnits(feeData.maxFeePerGas || 0n, 'gwei')}${colors.reset} gwei\n`);
    // Check if balance is sufficient for deployment
    const minBalance = hardhat_1.ethers.parseEther(hardhat_1.network.name === 'amoy' ? '0.5' : '0.1');
    if (balance < minBalance) {
        console.log(colors.red +
            `⚠️  Insufficient balance for deployment. Please fund this address with at least ${hardhat_1.network.name === 'amoy' ? '0.5 MATIC' : '0.1 ETH'}\n` +
            colors.reset);
        if (hardhat_1.network.name === 'amoy') {
            console.log(colors.cyan + 'Polygon Amoy Faucets:' + colors.reset);
            console.log('1. Polygon Faucet: https://faucet.polygon.technology/');
            console.log('2. QuickNode Faucet: https://faucet.quicknode.com/polygon/amoy');
            console.log('3. Request in Polygon Discord: https://discord.gg/polygon\n');
        }
        else {
            console.log(colors.cyan + 'Sepolia Faucets:' + colors.reset);
            console.log('1. Alchemy Faucet: https://sepoliafaucet.com/');
            console.log('2. Infura Faucet: https://www.infura.io/faucet/sepolia');
            console.log('3. QuickNode Faucet: https://faucet.quicknode.com/ethereum/sepolia\n');
        }
    }
    else {
        console.log(colors.green +
            `✅ Balance is sufficient for deployment (${hardhat_1.ethers.formatEther(balance)} ${currency})\n` +
            colors.reset);
    }
}
main().catch(error => {
    console.error(colors.red + '\n❌ Script failed:' + colors.reset, error);
    process.exit(1);
});
