"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const alchemy_sdk_1 = require("alchemy-sdk");
const hardhat_1 = require("hardhat");
async function main() {
    // Initialize Alchemy SDK
    const settings = {
        apiKey: 'dTwNgMXtwagIb1lZBjP_A03m5ko7WaR1',
        network: alchemy_sdk_1.Network.MATIC_AMOY,
    };
    const alchemy = new alchemy_sdk_1.Alchemy(settings);
    console.log('\nConnecting to Polygon Amoy testnet...');
    try {
        // Get latest block
        const latestBlock = await alchemy.core.getBlockNumber();
        console.log(`\nLatest block number: ${latestBlock}`);
        // Get block details
        const block = await alchemy.core.getBlock(latestBlock);
        console.log('\nLatest block details:');
        console.log(`Hash: ${block.hash}`);
        console.log(`Parent Hash: ${block.parentHash}`);
        console.log(`Number: ${block.number}`);
        console.log(`Timestamp: ${new Date(block.timestamp * 1000).toISOString()}`);
        console.log(`Gas Limit: ${block.gasLimit.toString()}`);
        console.log('Gas Used:', block.gasUsed.toString());
        console.log(`Base Fee Per Gas: ${block.baseFeePerGas ? hardhat_1.ethers.formatUnits(block.baseFeePerGas.toString(), 'gwei') : '0'} Gwei`);
        console.log(`Transactions: ${block.transactions.length}`);
        // Get network info
        const network = await alchemy.core.getNetwork();
        console.log('\nNetwork info:');
        console.log(`Name: ${network.name}`);
        console.log(`Chain ID: ${network.chainId.toString()}`);
        console.log(`ENS Address: ${network.ensAddress || 'Not available'}`);
        // Get gas price
        const gasPrice = await alchemy.core.getFeeData();
        console.log('\nGas Price:', {
            maxFeePerGas: gasPrice.maxFeePerGas
                ? hardhat_1.ethers.formatUnits(gasPrice.maxFeePerGas.toString(), 'gwei') + ' gwei'
                : 'Not available',
            maxPriorityFeePerGas: gasPrice.maxPriorityFeePerGas
                ? hardhat_1.ethers.formatUnits(gasPrice.maxPriorityFeePerGas.toString(), 'gwei') + ' gwei'
                : 'Not available',
            gasPrice: gasPrice.gasPrice
                ? hardhat_1.ethers.formatUnits(gasPrice.gasPrice.toString(), 'gwei') + ' gwei'
                : 'Not available',
        });
        // Check some known contract addresses
        const addresses = {
            WMATIC: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
            USDC: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
            QUICKSWAP_ROUTER: '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
        };
        console.log('\nChecking contract addresses:');
        for (const [name, address] of Object.entries(addresses)) {
            const code = await alchemy.core.getCode(address);
            console.log(`${name}: ${address} - ${code !== '0x' ? '✅ Contract' : '❌ Not deployed'}`);
        }
    }
    catch (error) {
        console.error('Error connecting to Amoy testnet:', error);
        throw error;
    }
}
main()
    .then(() => process.exit(0))
    .catch(error => {
    console.error(error);
    process.exit(1);
});
