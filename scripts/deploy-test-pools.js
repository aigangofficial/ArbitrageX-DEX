"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const dotenv_1 = __importDefault(require("dotenv"));
const ethers_1 = require("ethers");
// Load environment variables
dotenv_1.default.config();
const ROUTER_ABI = [
    'function addLiquidity(address tokenA, address tokenB, uint amountADesired, uint amountBDesired, uint amountAMin, uint amountBMin, address to, uint deadline) returns (uint amountA, uint amountB, uint liquidity)',
    'function factory() external pure returns (address)',
];
async function main() {
    // Initialize provider and wallet
    const provider = new ethers_1.ethers.JsonRpcProvider(process.env.NETWORK_RPC);
    const wallet = new ethers_1.ethers.Wallet(process.env.PRIVATE_KEY, provider);
    // Token addresses
    const WMATIC = '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889';
    const USDC = '0x742DfA5Aa70a8212857966D491D67B09Ce7D6ec7';
    // Router addresses
    const QUICKSWAP_ROUTER = '0x4aEa2f3bB6A9d06A4FCA03fa02899a20432E5e3D';
    const SUSHISWAP_ROUTER = '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506';
    // Initialize router contracts
    const quickswapRouter = new ethers_1.ethers.Contract(QUICKSWAP_ROUTER, ROUTER_ABI, wallet);
    const sushiswapRouter = new ethers_1.ethers.Contract(SUSHISWAP_ROUTER, ROUTER_ABI, wallet);
    // Amount of tokens to add as liquidity
    const wmaticAmount = ethers_1.ethers.parseEther('100'); // 100 WMATIC
    const usdcAmount = ethers_1.ethers.parseUnits('100', 6); // 100 USDC (6 decimals)
    console.log('Adding liquidity to QuickSwap...');
    try {
        const tx1 = await quickswapRouter.addLiquidity(WMATIC, USDC, wmaticAmount, usdcAmount, 0, // amountAMin
        0, // amountBMin
        wallet.address, Math.floor(Date.now() / 1000) + 3600 // 1 hour deadline
        );
        await tx1.wait();
        console.log('Added liquidity to QuickSwap successfully');
    }
    catch (error) {
        console.error('Error adding liquidity to QuickSwap:', error);
    }
    console.log('Adding liquidity to SushiSwap...');
    try {
        const tx2 = await sushiswapRouter.addLiquidity(WMATIC, USDC, wmaticAmount, usdcAmount, 0, // amountAMin
        0, // amountBMin
        wallet.address, Math.floor(Date.now() / 1000) + 3600 // 1 hour deadline
        );
        await tx2.wait();
        console.log('Added liquidity to SushiSwap successfully');
    }
    catch (error) {
        console.error('Error adding liquidity to SushiSwap:', error);
    }
}
main()
    .then(() => process.exit(0))
    .catch(error => {
    console.error(error);
    process.exit(1);
});
