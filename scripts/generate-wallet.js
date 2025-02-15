"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const chalk_1 = __importDefault(require("chalk"));
const hardhat_1 = require("hardhat");
async function main() {
    // Generate new wallet
    const wallet = hardhat_1.ethers.Wallet.createRandom();
    console.log(chalk_1.default.cyan('\n🔐 Generated New Wallet'));
    console.log(chalk_1.default.yellow('⚠️  SAVE THESE CREDENTIALS SECURELY AND NEVER SHARE THEM!\n'));
    console.log('Address:', chalk_1.default.green(wallet.address));
    console.log('Private Key:', chalk_1.default.red(wallet.privateKey));
    console.log('Mnemonic:', chalk_1.default.red(wallet.mnemonic?.phrase), '\n');
    // Get network info
    const provider = hardhat_1.ethers.provider;
    const network = await provider.getNetwork();
    console.log(chalk_1.default.cyan('Network Information:'));
    console.log('Name:', chalk_1.default.yellow(network.name));
    console.log('Chain ID:', chalk_1.default.yellow(network.chainId.toString()));
    // Get gas prices
    const feeData = await provider.getFeeData();
    console.log('\nCurrent Gas Prices:');
    console.log('Gas Price:', chalk_1.default.yellow(hardhat_1.ethers.formatUnits(feeData.gasPrice || 0n, 'gwei')), 'gwei');
    console.log(chalk_1.default.cyan('\n📝 Next Steps:'));
    console.log('1. Save these credentials securely');
    console.log('2. Update DEPLOYER_PRIVATE_KEY in config/.env with the new private key');
    console.log('3. Fund this address with MATIC for deployment');
    console.log('4. Run npm run check-balance to verify funds\n');
}
main()
    .then(() => process.exit(0))
    .catch(error => {
    console.error(chalk_1.default.red('Error generating wallet:'), error);
    process.exit(1);
});
