"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const chai_1 = require("chai");
const hardhat_1 = require("hardhat");
describe('Flash Loan Arbitrage Integration', () => {
    let owner;
    let mockTokenA;
    let mockTokenB;
    let mockPool;
    let mockDex1;
    let mockDex2;
    let flashLoanService;
    let arbitrageExecutor;
    const INITIAL_LIQUIDITY = hardhat_1.ethers.parseEther('1000');
    const FLASH_LOAN_AMOUNT = hardhat_1.ethers.parseEther('100');
    const MOCK_WETH = process.env.MOCK_WETH || '0x7969c5eD335650692Bc04293B07F5BF2e7A673C0';
    beforeEach(async () => {
        [owner] = await hardhat_1.ethers.getSigners();
        // Deploy mock tokens
        const MockToken = await hardhat_1.ethers.getContractFactory('MockToken');
        mockTokenA = await MockToken.deploy('Token A', 'TKA', 18);
        mockTokenB = await MockToken.deploy('Token B', 'TKB', 18);
        await mockTokenA.waitForDeployment();
        await mockTokenB.waitForDeployment();
        // Deploy mock DEXes
        const MockDEX = await hardhat_1.ethers.getContractFactory('MockDEX');
        mockDex1 = await MockDEX.deploy(MOCK_WETH);
        mockDex2 = await MockDEX.deploy(MOCK_WETH);
        await mockDex1.waitForDeployment();
        await mockDex2.waitForDeployment();
        // Deploy mock pool
        const MockPool = await hardhat_1.ethers.getContractFactory('MockPool');
        mockPool = await MockPool.deploy(await mockTokenA.getAddress(), await mockTokenB.getAddress(), await mockDex1.getAddress());
        await mockPool.waitForDeployment();
        // Deploy FlashLoanService
        const FlashLoanService = await hardhat_1.ethers.getContractFactory('FlashLoanService');
        flashLoanService = await FlashLoanService.deploy(await mockPool.getAddress());
        await flashLoanService.waitForDeployment();
        // Add mock pool as authorized flash loan provider
        await flashLoanService.addFlashLoanProvider(await mockPool.getAddress());
        // Deploy ArbitrageExecutor
        const ArbitrageExecutor = await hardhat_1.ethers.getContractFactory('ArbitrageExecutor');
        arbitrageExecutor = await ArbitrageExecutor.deploy(await mockDex1.getAddress(), await mockDex2.getAddress(), await flashLoanService.getAddress());
        await arbitrageExecutor.waitForDeployment();
        // Set up FlashLoanService with ArbitrageExecutor
        await flashLoanService.setArbitrageExecutor(await arbitrageExecutor.getAddress());
        // Setup initial liquidity and exchange rates
        await setupLiquidityAndRates();
    });
    async function setupLiquidityAndRates() {
        // Add liquidity to pool
        await mockTokenA.mint(await mockPool.getAddress(), INITIAL_LIQUIDITY);
        await mockTokenB.mint(await mockPool.getAddress(), INITIAL_LIQUIDITY);
        // Set profitable exchange rates
        await mockDex1.setExchangeRate(await mockTokenA.getAddress(), await mockTokenB.getAddress(), hardhat_1.ethers.parseUnits('1', 18), hardhat_1.ethers.parseUnits('1000', 18));
        await mockDex2.setExchangeRate(await mockTokenB.getAddress(), await mockTokenA.getAddress(), hardhat_1.ethers.parseUnits('1000', 18), hardhat_1.ethers.parseUnits('1.2', 18));
        // Set reserves for price impact
        await mockDex1.setReserves(await mockTokenA.getAddress(), hardhat_1.ethers.parseUnits('1000000', 18));
        await mockDex1.setReserves(await mockTokenB.getAddress(), hardhat_1.ethers.parseUnits('1000000000', 18));
        await mockDex2.setReserves(await mockTokenA.getAddress(), hardhat_1.ethers.parseUnits('1000000', 18));
        await mockDex2.setReserves(await mockTokenB.getAddress(), hardhat_1.ethers.parseUnits('1000000000', 18));
        // Approve all necessary token transfers
        await approveTokens();
    }
    async function approveTokens() {
        const contracts = [
            await flashLoanService.getAddress(),
            await arbitrageExecutor.getAddress(),
            await mockDex1.getAddress(),
            await mockDex2.getAddress(),
            await mockPool.getAddress(),
        ];
        for (const contract of contracts) {
            await mockTokenA.approve(contract, hardhat_1.ethers.MaxUint256);
            await mockTokenB.approve(contract, hardhat_1.ethers.MaxUint256);
        }
    }
    describe('End-to-End Arbitrage Flow', () => {
        it('should execute profitable arbitrage through flash loan', async () => {
            const initialBalance = await mockTokenA.balanceOf(owner.address);
            await flashLoanService.executeArbitrage(await mockTokenA.getAddress(), await mockTokenB.getAddress(), FLASH_LOAN_AMOUNT, hardhat_1.ethers.AbiCoder.defaultAbiCoder().encode(['bool'], [true]));
            const finalBalance = await mockTokenA.balanceOf(owner.address);
            (0, chai_1.expect)(finalBalance).to.be.gt(initialBalance);
        });
        it('should revert on unprofitable arbitrage attempt', async () => {
            // Set unprofitable rates (20% loss)
            await mockDex1.setExchangeRate(await mockTokenA.getAddress(), await mockTokenB.getAddress(), hardhat_1.ethers.parseUnits('1', 18), hardhat_1.ethers.parseUnits('1000', 18));
            await mockDex2.setExchangeRate(await mockTokenB.getAddress(), await mockTokenA.getAddress(), hardhat_1.ethers.parseUnits('1000', 18), hardhat_1.ethers.parseUnits('0.8', 18));
            await (0, chai_1.expect)(flashLoanService.executeArbitrage(await mockTokenA.getAddress(), await mockTokenB.getAddress(), FLASH_LOAN_AMOUNT, hardhat_1.ethers.AbiCoder.defaultAbiCoder().encode(['bool'], [true]))).to.be.revertedWithCustomError(flashLoanService, 'UnprofitableTrade');
        });
        it('should handle multiple consecutive arbitrage attempts', async () => {
            for (let i = 0; i < 3; i++) {
                const initialBalance = await mockTokenA.balanceOf(owner.address);
                await flashLoanService.executeArbitrage(await mockTokenA.getAddress(), await mockTokenB.getAddress(), FLASH_LOAN_AMOUNT, hardhat_1.ethers.AbiCoder.defaultAbiCoder().encode(['bool'], [true]));
                const finalBalance = await mockTokenA.balanceOf(owner.address);
                (0, chai_1.expect)(finalBalance).to.be.gt(initialBalance);
            }
        });
    });
    describe('Error Handling & Edge Cases', () => {
        it('should handle zero liquidity gracefully', async () => {
            // Remove all liquidity
            await mockDex1.setReserves(await mockTokenA.getAddress(), 0);
            await mockDex1.setReserves(await mockTokenB.getAddress(), 0);
            await (0, chai_1.expect)(flashLoanService.executeArbitrage(await mockTokenA.getAddress(), await mockTokenB.getAddress(), FLASH_LOAN_AMOUNT, hardhat_1.ethers.AbiCoder.defaultAbiCoder().encode(['bool'], [true]))).to.be.reverted;
        });
        it('should validate token addresses', async () => {
            await (0, chai_1.expect)(flashLoanService.executeArbitrage(hardhat_1.ethers.ZeroAddress, await mockTokenB.getAddress(), FLASH_LOAN_AMOUNT, hardhat_1.ethers.AbiCoder.defaultAbiCoder().encode(['bool'], [true]))).to.be.revertedWithCustomError(flashLoanService, 'InvalidTokenAddresses');
        });
    });
});
