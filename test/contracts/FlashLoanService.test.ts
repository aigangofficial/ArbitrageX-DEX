import { expect } from "chai";
import { ethers } from "hardhat";
import type { FlashLoanService, MockERC20, MockUniswapRouter, MockPool } from "../../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("FlashLoanService", function () {
    let mockTokenA: MockERC20;
    let mockTokenB: MockERC20;
    let mockPool: MockPool;
    let mockDex1: MockUniswapRouter;
    let mockDex2: MockUniswapRouter;
    let flashLoanService: FlashLoanService;
    let owner: HardhatEthersSigner;
    let user: HardhatEthersSigner;
    const liquidityAmount = ethers.parseEther("10000");

    beforeEach(async function () {
        [owner, user] = await ethers.getSigners();

        // Deploy mock tokens
        const MockToken = await ethers.getContractFactory("MockERC20");
        mockTokenA = (await MockToken.deploy("Token A", "TKA")).connect(owner) as unknown as MockERC20;
        mockTokenB = (await MockToken.deploy("Token B", "TKB")).connect(owner) as unknown as MockERC20;
        await mockTokenA.waitForDeployment();
        await mockTokenB.waitForDeployment();

        // Deploy mock DEXes
        const MockRouter = await ethers.getContractFactory("MockUniswapRouter");
        mockDex1 = (await MockRouter.deploy(await mockTokenA.getAddress())).connect(owner) as unknown as MockUniswapRouter;
        mockDex2 = (await MockRouter.deploy(await mockTokenA.getAddress())).connect(owner) as unknown as MockUniswapRouter;
        await mockDex1.waitForDeployment();
        await mockDex2.waitForDeployment();

        // Deploy mock pool
        const MockPool = await ethers.getContractFactory("MockPool");
        mockPool = (await MockPool.deploy(
            await mockTokenA.getAddress(),
            await mockTokenB.getAddress()
        )).connect(owner) as unknown as MockPool;
        await mockPool.waitForDeployment();

        // Deploy FlashLoanService
        const FlashLoanService = await ethers.getContractFactory("FlashLoanService");
        flashLoanService = (await FlashLoanService.deploy(
            await mockPool.getAddress(),
            await mockDex1.getAddress(),
            await mockDex2.getAddress()
        )).connect(owner) as unknown as FlashLoanService;
        await flashLoanService.waitForDeployment();

        // Set minimum profit to 0 for testing
        await flashLoanService.setMinProfitBps(1);

        // Set up exchange rates (DEX1: 1A = 1.2B, DEX2: 1B = 1.2A)
        await mockDex1.setExchangeRate(
            await mockTokenA.getAddress(),
            await mockTokenB.getAddress(),
            ethers.parseEther("1.2")
        );
        await mockDex2.setExchangeRate(
            await mockTokenB.getAddress(),
            await mockTokenA.getAddress(),
            ethers.parseEther("1.2")
        );

        // Add liquidity to DEXes
        await mockTokenA.mint(await mockDex1.getAddress(), liquidityAmount);
        await mockTokenB.mint(await mockDex1.getAddress(), liquidityAmount);
        await mockTokenA.mint(await mockDex2.getAddress(), liquidityAmount);
        await mockTokenB.mint(await mockDex2.getAddress(), liquidityAmount);
    });

    describe("Flash Loan Execution", function () {
        it("Should execute flash loan and arbitrage", async function () {
            const amountIn = ethers.parseEther("1"); // 1 ETH worth
            
            // Mint initial tokens to owner for transfer
            await mockTokenA.mint(await owner.getAddress(), amountIn * 20n);
            await mockTokenB.mint(await owner.getAddress(), amountIn * 20n);
            
            // Add liquidity to DEXes with proper reserves
            await mockTokenA.transfer(await mockDex1.getAddress(), amountIn * 10n);
            await mockTokenB.transfer(await mockDex1.getAddress(), amountIn * 12n);
            
            await mockTokenA.transfer(await mockDex2.getAddress(), amountIn * 13n);
            await mockTokenB.transfer(await mockDex2.getAddress(), amountIn * 10n);
            
            // Add liquidity to the mock pool and flash loan service
            await mockTokenA.mint(await mockPool.getAddress(), amountIn * 2n);
            await mockTokenA.mint(await flashLoanService.getAddress(), amountIn * 2n);
            
            // Set up profitable exchange rates
            await mockDex1.setExchangeRate(
                await mockTokenA.getAddress(),
                await mockTokenB.getAddress(),
                ethers.parseEther("1.2") // 1A = 1.2B
            );
            await mockDex2.setExchangeRate(
                await mockTokenB.getAddress(),
                await mockTokenA.getAddress(),
                ethers.parseEther("1.3") // 1B = 1.3A
            );

            // Execute flash loan
            await expect(flashLoanService.executeArbitrage(
                await mockTokenA.getAddress(),
                await mockTokenB.getAddress(),
                amountIn
            )).to.emit(flashLoanService, "FlashLoanExecuted");
        });

        it("should fail if flash loan cannot be repaid", async function () {
            const amountIn = ethers.parseEther("100");
            
            // Add liquidity to the mock pool but not to the flash loan service
            await mockTokenA.mint(await mockPool.getAddress(), amountIn * 2n);
            
            // Set unfavorable exchange rates
            await mockDex1.setExchangeRate(
                await mockTokenA.getAddress(),
                await mockTokenB.getAddress(),
                ethers.parseEther("0.8") // 1A = 0.8B (20% loss)
            );
            await mockDex2.setExchangeRate(
                await mockTokenB.getAddress(),
                await mockTokenA.getAddress(),
                ethers.parseEther("0.8") // 1B = 0.8A (another 20% loss)
            );

            await expect(flashLoanService.executeArbitrage(
                await mockTokenA.getAddress(),
                await mockTokenB.getAddress(),
                amountIn
            )).to.be.revertedWithCustomError(flashLoanService, "InsufficientFundsForRepayment");
        });
    });

    describe("Admin Functions", function () {
        it("should allow owner to set minimum profit", async function () {
            const newMinProfit = 100; // 1%
            await expect(flashLoanService.setMinProfitBps(newMinProfit))
                .to.emit(flashLoanService, "MinProfitBpsUpdated")
                .withArgs(1, newMinProfit); // Initial value is 1 bps (0.01%)
            expect(await flashLoanService.minProfitBps()).to.equal(newMinProfit);
        });

        it("should allow owner to withdraw tokens", async function () {
            const amount = ethers.parseEther("1");
            await mockTokenA.mint(await flashLoanService.getAddress(), amount);
            
            await expect(flashLoanService.withdrawToken(
                await mockTokenA.getAddress(),
                amount
            )).to.changeTokenBalance(mockTokenA, owner, amount);
        });

        it("should not allow non-owner to set minimum profit", async function () {
            const newMinProfit = 100; // 1%
            await expect(flashLoanService.connect(user).setMinProfitBps(newMinProfit))
                .to.be.revertedWithCustomError(flashLoanService, "OwnableUnauthorizedAccount")
                .withArgs(await user.getAddress());
        });
    });
}); 