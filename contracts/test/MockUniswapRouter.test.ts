import { expect } from "chai";
import { ethers } from "hardhat";
import { MockUniswapRouter, MockERC20 } from "../typechain-types";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";

describe("MockUniswapRouter", function () {
    let mockRouter: MockUniswapRouter;
    let weth: MockERC20;
    let usdc: MockERC20;
    let dai: MockERC20;
    let owner: SignerWithAddress;
    let user: SignerWithAddress;
    const PRECISION = ethers.parseEther("1"); // 1e18

    beforeEach(async function () {
        [owner, user] = await ethers.getSigners();

        // Deploy mock tokens
        const MockToken = await ethers.getContractFactory("MockERC20");
        weth = await MockToken.deploy("Wrapped Ether", "WETH", 18);
        usdc = await MockToken.deploy("USD Coin", "USDC", 6);
        dai = await MockToken.deploy("DAI", "DAI", 18);

        // Deploy mock router
        const MockRouter = await ethers.getContractFactory("MockUniswapRouter");
        mockRouter = await MockRouter.deploy();

        // Setup initial liquidity
        await weth.mint(await mockRouter.getAddress(), ethers.parseEther("100"));
        await usdc.mint(await mockRouter.getAddress(), ethers.parseUnits("200000", 6));

        // Setup exchange rate: 1 ETH = 2000 USDC
        const rate = ethers.parseUnits("2000", 6); // Adjusted for USDC's 6 decimals
        await mockRouter.setExchangeRate(
            await weth.getAddress(),
            await usdc.getAddress(),
            rate,
            ethers.parseEther("100"), // Initial WETH reserve
            ethers.parseUnits("200000", 6) // Initial USDC reserve
        );
    });

    describe("Exchange Rate Setting", function () {
        it("Should set exchange rate correctly", async function () {
            const amountIn = ethers.parseEther("1"); // 1 ETH
            const path = [await weth.getAddress(), await usdc.getAddress()];
            
            const amounts = await mockRouter.getAmountsOut(amountIn, path);
            expect(amounts[1]).to.equal(ethers.parseUnits("2000", 6));
        });

        it("Should handle reverse rate automatically", async function () {
            const amountIn = ethers.parseUnits("2000", 6); // 2000 USDC
            const path = [await usdc.getAddress(), await weth.getAddress()];
            
            const amounts = await mockRouter.getAmountsOut(amountIn, path);
            expect(amounts[1]).to.be.closeTo(
                ethers.parseEther("1"),
                ethers.parseEther("0.01") // Allow 1% deviation due to slippage
            );
        });
    });

    describe("Slippage Impact", function () {
        it("Should apply price impact for large trades", async function () {
            const amountIn = ethers.parseEther("10"); // 10 ETH (10% of reserve)
            const path = [await weth.getAddress(), await usdc.getAddress()];
            
            const amounts = await mockRouter.getAmountsOut(amountIn, path);
            // Should receive less than 20,000 USDC due to price impact
            expect(amounts[1]).to.be.lt(ethers.parseUnits("20000", 6));
        });

        it("Should maintain consistent rate for small trades", async function () {
            const amountIn = ethers.parseEther("0.1"); // 0.1 ETH
            const path = [await weth.getAddress(), await usdc.getAddress()];
            
            const amounts = await mockRouter.getAmountsOut(amountIn, path);
            expect(amounts[1]).to.be.closeTo(
                ethers.parseUnits("200", 6), // Should get ~200 USDC
                ethers.parseUnits("1", 6) // Allow small deviation
            );
        });
    });

    describe("Swap Execution", function () {
        it("Should execute swap with correct token transfers", async function () {
            const amountIn = ethers.parseEther("1");
            const path = [await weth.getAddress(), await usdc.getAddress()];
            
            // Mint tokens to user
            await weth.mint(user.address, amountIn);
            await weth.connect(user).approve(await mockRouter.getAddress(), amountIn);
            
            // Get expected output amount
            const amounts = await mockRouter.getAmountsOut(amountIn, path);
            
            // Execute swap
            await mockRouter.connect(user).swapExactTokensForTokens(
                amountIn,
                amounts[1],
                path,
                user.address,
                ethers.MaxUint256
            );
            
            // Verify balances
            expect(await usdc.balanceOf(user.address)).to.equal(amounts[1]);
            expect(await weth.balanceOf(user.address)).to.equal(0);
        });
    });

    describe("Cross-Exchange Arbitrage", function () {
        it("Should calculate profitable triangular arbitrage path", async function () {
            // Set up exchange rates for triangular arbitrage
            // ETH -> USDC -> DAI -> ETH
            const ethAmount = ethers.parseEther("1"); // 1 ETH
            
            // ETH -> USDC (1 ETH = 2000 USDC)
            await mockRouter.setExchangeRate(
                await weth.getAddress(),
                await usdc.getAddress(),
                ethers.parseUnits("2000", 6), // Scale to USDC decimals
                ethers.parseEther("100"),
                ethers.parseUnits("200000", 6)
            );
            
            // USDC -> DAI (1 USDC = 1.001 DAI)
            await mockRouter.setExchangeRate(
                await usdc.getAddress(),
                await dai.getAddress(),
                ethers.parseEther("1.001"),
                ethers.parseUnits("100000", 6),
                ethers.parseEther("100100")
            );
            
            // DAI -> ETH (2010 DAI = 1 ETH)
            await mockRouter.setExchangeRate(
                await dai.getAddress(),
                await weth.getAddress(),
                ethers.parseEther("0.0004975"), // 1/2010
                ethers.parseEther("201000"),
                ethers.parseEther("100")
            );
            
            // Execute triangular arbitrage path
            const path = [
                await weth.getAddress(),
                await usdc.getAddress(),
                await dai.getAddress(),
                await weth.getAddress()
            ];
            
            // Calculate expected amounts
            const step1 = await mockRouter.getAmountsOut(ethAmount, [path[0], path[1]]);
            const step2 = await mockRouter.getAmountsOut(step1[1], [path[1], path[2]]);
            const step3 = await mockRouter.getAmountsOut(step2[1], [path[2], path[3]]);
            
            // Final amount should be greater than initial amount (profitable arbitrage)
            expect(step3[1]).to.be.gt(ethAmount);
        });
    });
}); 