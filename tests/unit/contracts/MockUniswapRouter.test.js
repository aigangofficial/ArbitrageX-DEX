"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const chai_1 = require("chai");
const hardhat_1 = __importDefault(require("hardhat"));
const { ethers } = hardhat_1.default;
describe('MockUniswapRouter', () => {
    let mockRouter;
    let mockTokenA;
    let mockTokenB;
    let owner;
    let user;
    let amountIn;
    let amountOutMin;
    let path;
    beforeEach(async () => {
        [owner, user] = await ethers.getSigners();
        // Deploy mock tokens
        const MockToken = await ethers.getContractFactory('MockERC20');
        mockTokenA = (await MockToken.deploy('Token A', 'TKA'));
        mockTokenB = (await MockToken.deploy('Token B', 'TKB'));
        await mockTokenA.waitForDeployment();
        await mockTokenB.waitForDeployment();
        // Deploy mock router
        const MockRouter = await ethers.getContractFactory('MockUniswapRouter');
        const router = await MockRouter.deploy(await mockTokenA.getAddress());
        mockRouter = router.connect(owner);
        await mockRouter.waitForDeployment();
        // Setup test values
        amountIn = ethers.parseEther('1');
        amountOutMin = ethers.parseEther('0.95'); // 5% slippage
        path = [await mockTokenA.getAddress(), await mockTokenB.getAddress()];
        // Set token decimals
        await mockRouter.setTokenDecimals(await mockTokenA.getAddress(), 18);
        await mockRouter.setTokenDecimals(await mockTokenB.getAddress(), 18);
        // Set exchange rate (1:1 for simplicity)
        await mockRouter.setExchangeRate(await mockTokenA.getAddress(), await mockTokenB.getAddress(), ethers.parseEther('1'));
        // Mint tokens and approve router with sufficient liquidity
        const LIQUIDITY = ethers.parseEther('10000'); // Much larger liquidity pool
        await mockTokenA.mint(owner.address, LIQUIDITY);
        await mockTokenB.mint(owner.address, LIQUIDITY);
        await mockTokenA.mint(await mockRouter.getAddress(), LIQUIDITY);
        await mockTokenB.mint(await mockRouter.getAddress(), LIQUIDITY);
        await mockTokenA.connect(owner).approve(await mockRouter.getAddress(), ethers.MaxUint256);
        await mockTokenB.connect(owner).approve(await mockRouter.getAddress(), ethers.MaxUint256);
    });
    it('should revert on expired deadline', async () => {
        const expiredDeadline = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago
        await (0, chai_1.expect)(mockRouter.swapExactTokensForTokens(amountIn, amountOutMin, path, owner.address, expiredDeadline)).to.be.revertedWithCustomError(mockRouter, 'Expired');
    });
    it('should execute swap with correct token transfers', async () => {
        const deadline = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
        const initialBalance = await mockTokenB.balanceOf(owner.address);
        await mockRouter.swapExactTokensForTokens(amountIn, amountOutMin, path, owner.address, deadline);
        const finalBalance = await mockTokenB.balanceOf(owner.address);
        (0, chai_1.expect)(finalBalance - initialBalance).to.be.gte(amountOutMin);
    });
    it('should apply price impact for large trades', async () => {
        const largeAmount = ethers.parseEther('1000'); // 10% of pool liquidity
        const deadline = Math.floor(Date.now() / 1000) + 3600;
        // Get the amount out for a large trade
        const [, amountOut] = await mockRouter.getAmountsOut(largeAmount, path);
        // Calculate expected amount with 0.3% fee
        const expectedAmount = (largeAmount * 997n) / 1000n;
        // Expect exact match since we're using fixed fee
        (0, chai_1.expect)(amountOut).to.equal(expectedAmount);
    });
});
