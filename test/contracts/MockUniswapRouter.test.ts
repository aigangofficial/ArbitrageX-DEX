import { expect } from "chai";
import { ethers } from "hardhat";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import type { MockUniswapRouter, MockERC20 } from "../typechain-types";
import type { Contract } from "ethers";

describe("MockUniswapRouter", function () {
    let mockRouter: Contract;
    let weth: Contract;
    let usdc: Contract;
    let dai: Contract;
    let owner: SignerWithAddress;
    let user: SignerWithAddress;
    const PRECISION = ethers.parseEther("1"); // 1e18

    beforeEach(async function () {
        [owner, user] = await ethers.getSigners();

        // Deploy mock tokens
        const MockToken = await ethers.getContractFactory("MockERC20");
        weth = await MockToken.deploy("Wrapped Ether", "WETH");
        usdc = await MockToken.deploy("USD Coin", "USDC");
        dai = await MockToken.deploy("DAI", "DAI");

        // Deploy mock router
        const MockRouter = await ethers.getContractFactory("MockUniswapRouter");
        mockRouter = await MockRouter.deploy(await weth.getAddress());

        // Setup initial liquidity
        await weth.mint(await mockRouter.getAddress(), ethers.parseEther("100"));
        await usdc.mint(await mockRouter.getAddress(), ethers.parseUnits("200000", 6));
        await dai.mint(await mockRouter.getAddress(), ethers.parseEther("200000"));

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
            const amountIn = ethers.parseEther("1");
            const path = [await weth.getAddress(), await usdc.getAddress()];
            
            await mockRouter.setExchangeRate(
                await weth.getAddress(),
                await usdc.getAddress(),
                ethers.parseUnits("2000", 6),
                ethers.parseEther("100"),
                ethers.parseUnits("200000", 6)
            );
            
            const amountsOut = await mockRouter.getAmountsOut(amountIn, path);
            // Account for 0.3% fee: 2000 * 0.997 = 1994
            expect(amountsOut[1]).to.equal(ethers.parseUnits("1994", 6));
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
                ethers.parseUnits("2000", 18), // Scale to match ETH decimals
                ethers.parseEther("100"),
                ethers.parseUnits("200000", 18)
            );
            
            // USDC -> DAI (1 USDC = 1.05 DAI)
            await mockRouter.setExchangeRate(
                await usdc.getAddress(),
                await dai.getAddress(),
                ethers.parseEther("1.05"), // 1.05 DAI per USDC
                ethers.parseUnits("100000", 18),
                ethers.parseEther("105000")
            );
            
            // DAI -> ETH (1900 DAI = 1 ETH)
            await mockRouter.setExchangeRate(
                await dai.getAddress(),
                await weth.getAddress(),
                ethers.parseUnits("0.000526315789473684", 18), // 1/1900
                ethers.parseEther("190000"),
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
            const minExpectedAmount = BigInt(ethAmount) * 101n / 100n; // At least 1% profit
            expect(BigInt(step3[1])).to.be.gt(minExpectedAmount);
        });
    });

    describe("Reserve-Based Price Impact", function () {
        it("Should calculate price impact based on pool reserves", async function () {
            const amountIn = ethers.parseEther("10"); // 10 ETH (10% of Router B's reserve)
            const path = [await weth.getAddress(), await usdc.getAddress()];
            
            await mockRouter.setExchangeRate(
                await weth.getAddress(),
                await usdc.getAddress(),
                ethers.parseUnits("1980", 6),
                ethers.parseEther("100"),
                ethers.parseUnits("198000", 6)
            );
            
            const amountsB = await mockRouter.getAmountsOut(amountIn, path);
            const expectedWithoutImpact = ethers.parseUnits("19800", 6); // 10 * 1980
            
            // Actual output should be less due to price impact and fee
            expect(amountsB[1]).to.be.lt(expectedWithoutImpact);
            
            // Calculate expected price impact (roughly 2-3% for this size)
            const priceImpact = ((expectedWithoutImpact - amountsB[1]) * 100n) / expectedWithoutImpact;
            
            expect(priceImpact).to.be.gte(2n); // At least 2% impact
            expect(priceImpact).to.be.lte(4n); // No more than 4% impact (including 0.3% fee)
        });

        it("Should demonstrate diminishing returns for large trades", async function () {
            const smallTrade = ethers.parseEther("1");
            const mediumTrade = ethers.parseEther("5");
            const largeTrade = ethers.parseEther("20");
            const path = [await weth.getAddress(), await usdc.getAddress()];

            await mockRouter.setExchangeRate(
                await weth.getAddress(),
                await usdc.getAddress(),
                ethers.parseUnits("1980", 6),
                ethers.parseEther("100"),
                ethers.parseUnits("198000", 6)
            );

            const smallOutput = await mockRouter.getAmountsOut(smallTrade, path);
            const mediumOutput = await mockRouter.getAmountsOut(mediumTrade, path);
            const largeOutput = await mockRouter.getAmountsOut(largeTrade, path);

            // Calculate effective rates
            const smallRate = smallOutput[1] * PRECISION / smallTrade;
            const mediumRate = mediumOutput[1] * PRECISION / mediumTrade;
            const largeRate = largeOutput[1] * PRECISION / largeTrade;

            // Verify diminishing returns
            expect(smallRate).to.be.gt(mediumRate);
            expect(mediumRate).to.be.gt(largeRate);
        });
    });
}); 