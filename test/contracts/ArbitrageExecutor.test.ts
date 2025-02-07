import { expect } from "chai";
import { ethers } from "hardhat";
import type { ArbitrageExecutor, FlashLoanService, MockERC20, MockUniswapRouter } from "../../typechain-types";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";
import { Contract } from "ethers";

describe("ArbitrageExecutor", function () {
    let mockTokenA: MockERC20;
    let mockTokenB: MockERC20;
    let mockUniswapRouter: MockUniswapRouter;
    let mockSushiswapRouter: MockUniswapRouter;
    let flashLoanService: FlashLoanService;
    let arbitrageExecutor: ArbitrageExecutor;
    let owner: HardhatEthersSigner;
    let user: HardhatEthersSigner;

    const INITIAL_LIQUIDITY = ethers.parseEther("1000");
    const TRADE_AMOUNT = ethers.parseEther("10");

    beforeEach(async function () {
        [owner, user] = await ethers.getSigners();

        // Deploy mock tokens
        const MockToken = await ethers.getContractFactory("MockERC20");
        mockTokenA = (await MockToken.deploy("Token A", "TKA")).connect(owner) as unknown as MockERC20;
        mockTokenB = (await MockToken.deploy("Token B", "TKB")).connect(owner) as unknown as MockERC20;
        await mockTokenA.waitForDeployment();
        await mockTokenB.waitForDeployment();

        // Deploy mock routers
        const MockRouter = await ethers.getContractFactory("MockUniswapRouter");
        mockUniswapRouter = (await MockRouter.deploy(await mockTokenA.getAddress())).connect(owner) as unknown as MockUniswapRouter;
        mockSushiswapRouter = (await MockRouter.deploy(await mockTokenA.getAddress())).connect(owner) as unknown as MockUniswapRouter;
        await mockUniswapRouter.waitForDeployment();
        await mockSushiswapRouter.waitForDeployment();

        // Deploy FlashLoanService first
        const FlashLoanService = await ethers.getContractFactory("FlashLoanService");
        flashLoanService = (await FlashLoanService.deploy(
            await mockUniswapRouter.getAddress(),  // Using Uniswap as mock Aave pool for testing
            await mockUniswapRouter.getAddress(),
            await mockSushiswapRouter.getAddress()
        )).connect(owner) as unknown as FlashLoanService;
        await flashLoanService.waitForDeployment();

        // Deploy ArbitrageExecutor with correct constructor arguments
        const ArbitrageExecutor = await ethers.getContractFactory("ArbitrageExecutor");
        arbitrageExecutor = (await ArbitrageExecutor.deploy(
            await mockUniswapRouter.getAddress(),    // _uniswapRouter
            await mockSushiswapRouter.getAddress(),  // _sushiswapRouter
            await flashLoanService.getAddress()      // _flashLoanService
        )).connect(owner) as unknown as ArbitrageExecutor;
        await arbitrageExecutor.waitForDeployment();

        // Setup initial liquidity and exchange rates
        const UNISWAP_RATE = ethers.parseEther("1.2");  // 1 TokenA = 1.2 TokenB
        const SUSHISWAP_RATE = ethers.parseEther("1.1"); // 1 TokenA = 1.1 TokenB
        const UNISWAP_LIQUIDITY_B = INITIAL_LIQUIDITY * 12n / 10n; // 20% more TokenB
        const SUSHISWAP_LIQUIDITY_B = INITIAL_LIQUIDITY * 11n / 10n; // 10% more TokenB
        
        // Set initial liquidity with proper ratios
        await mockTokenA.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
        await mockTokenB.mint(await mockUniswapRouter.getAddress(), UNISWAP_LIQUIDITY_B);
        await mockTokenA.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);
        await mockTokenB.mint(await mockSushiswapRouter.getAddress(), SUSHISWAP_LIQUIDITY_B);

        // Set exchange rates with proper reserves
        await mockUniswapRouter.setExchangeRate(
            await mockTokenA.getAddress(),
            await mockTokenB.getAddress(),
            ethers.parseEther("1.2")
        );

        await mockSushiswapRouter.setExchangeRate(
            await mockTokenB.getAddress(),
            await mockTokenA.getAddress(),
            ethers.parseEther("1.1")
        );

        // Set a reasonable slippage tolerance for testing
        await arbitrageExecutor.setMaxSlippage(100); // 1% slippage
    });

    describe("Constructor", function () {
        it("Should set the correct addresses", async function () {
            expect(await arbitrageExecutor.uniswapRouter()).to.equal(await mockUniswapRouter.getAddress());
            expect(await arbitrageExecutor.sushiswapRouter()).to.equal(await mockSushiswapRouter.getAddress());
            expect(await arbitrageExecutor.flashLoanService()).to.equal(await flashLoanService.getAddress());
        });
    });

    describe("Arbitrage Execution", function () {
        it("Should execute profitable arbitrage from Uniswap to SushiSwap", async function () {
            // Mint tokens to owner for the trade
            await mockTokenA.mint(owner.address, TRADE_AMOUNT);
            await mockTokenA.approve(await arbitrageExecutor.getAddress(), TRADE_AMOUNT);

            // Set up profitable exchange rates
            // Uniswap: 1A = 1.2B
            await mockUniswapRouter.setExchangeRate(
                await mockTokenA.getAddress(),
                await mockTokenB.getAddress(),
                ethers.parseEther("1.2")
            );

            // SushiSwap: 1B = 1.1A (making arbitrage profitable)
            await mockSushiswapRouter.setExchangeRate(
                await mockTokenB.getAddress(),
                await mockTokenA.getAddress(),
                ethers.parseEther("1.1")
            );

            // Approve tokens for routers
            await mockTokenA.approve(await mockUniswapRouter.getAddress(), TRADE_AMOUNT);
            await mockTokenB.approve(await mockSushiswapRouter.getAddress(), ethers.parseEther("100000"));

            await expect(arbitrageExecutor.executeArbitrage(
                await mockTokenA.getAddress(),
                await mockTokenB.getAddress(),
                TRADE_AMOUNT,
                true
            )).to.emit(arbitrageExecutor, "ArbitrageExecuted");
        });

        it("Should fail if trade is not profitable", async function () {
            // Set equal rates to make trade unprofitable
            await mockUniswapRouter.setExchangeRate(
                await mockTokenA.getAddress(),
                await mockTokenB.getAddress(),
                ethers.parseEther("1.0")
            );
            await mockSushiswapRouter.setExchangeRate(
                await mockTokenA.getAddress(),
                await mockTokenB.getAddress(),
                ethers.parseEther("1.0")
            );

            await mockTokenA.mint(owner.address, TRADE_AMOUNT);
            await mockTokenA.approve(await arbitrageExecutor.getAddress(), TRADE_AMOUNT);

            await expect(arbitrageExecutor.executeArbitrage(
                await mockTokenA.getAddress(),
                await mockTokenB.getAddress(),
                TRADE_AMOUNT,
                true
            )).to.be.revertedWithCustomError(arbitrageExecutor, "UnprofitableTrade");
        });
    });

    describe("Admin Functions", function () {
        it("Should allow owner to set max slippage", async function () {
            const newSlippage = 200; // 2%
            await arbitrageExecutor.setMaxSlippage(newSlippage);
            expect(await arbitrageExecutor.maxSlippage()).to.equal(newSlippage);
        });

        it("Should not allow non-owner to set max slippage", async function () {
            const newSlippage = 200;
            await expect(
                arbitrageExecutor.connect(user).setMaxSlippage(newSlippage)
            ).to.be.revertedWithCustomError(arbitrageExecutor, "OwnableUnauthorizedAccount");
        });
    });
}); 