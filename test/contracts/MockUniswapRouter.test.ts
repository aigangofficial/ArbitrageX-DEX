import { expect } from "chai";
import { ethers } from "hardhat";
import { parseUnits, parseEther } from "ethers";
import type { MockUniswapRouter, MockERC20 } from "../../typechain-types";
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
        weth = await MockToken.deploy("Wrapped Ether", "WETH") as unknown as MockERC20;
        usdc = await MockToken.deploy("USD Coin", "USDC") as unknown as MockERC20;
        dai = await MockToken.deploy("DAI", "DAI") as unknown as MockERC20;

        // Deploy mock router
        const MockRouter = await ethers.getContractFactory("MockUniswapRouter");
        mockRouter = await MockRouter.deploy(await weth.getAddress()) as unknown as MockUniswapRouter;

        // Setup initial liquidity
        await weth.mint(await mockRouter.getAddress(), ethers.parseEther("100"));
        await usdc.mint(await mockRouter.getAddress(), ethers.parseUnits("200000", 6));

        // Setup exchange rate: 1 ETH = 2000 USDC
        const rate = ethers.parseUnits("2000", 6); // Adjusted for USDC's 6 decimals
        await mockRouter.setExchangeRate(
            await weth.getAddress(),
            await usdc.getAddress(),
            rate
        );
    });

    describe("Exchange Rate Setting", function () {
        it("Should set exchange rate correctly", async function () {
            await mockRouter.setExchangeRate(await weth.getAddress(), await usdc.getAddress(), parseUnits("1.954", 9));
            const rate = await mockRouter.exchangeRates(await weth.getAddress(), await usdc.getAddress());
            expect(rate).to.equal(1954000000);
        });

        it("Should handle reverse rate automatically", async function () {
            // Set token decimals
            await mockRouter.setTokenDecimals(await weth.getAddress(), 18);
            await mockRouter.setTokenDecimals(await usdc.getAddress(), 6);
            
            // Set rate: 1 ETH = 2000 USDC
            await mockRouter.setExchangeRate(await weth.getAddress(), await usdc.getAddress(), parseUnits("2000", 6));
            
            // Check reverse rate: 1 USDC = 0.0005 ETH
            const reverseRate = await mockRouter.exchangeRates(await usdc.getAddress(), await weth.getAddress());
            expect(reverseRate).to.equal(parseUnits("0.0005", 18));
        });

        it("Should maintain consistent rate for small trades", async function () {
            // Set token decimals
            await mockRouter.setTokenDecimals(await weth.getAddress(), 18);
            await mockRouter.setTokenDecimals(await usdc.getAddress(), 6);
            
            // Set rate: 1 ETH = 2000 USDC
            await mockRouter.setExchangeRate(await weth.getAddress(), await usdc.getAddress(), parseUnits("2000", 6));
            
            // Test small trade: 0.1 ETH
            const amountIn = parseEther("0.1");
            const amountOut = await mockRouter.getAmountOut(
                amountIn,
                parseEther("100"),
                parseUnits("200000", 6)
            );
            
            // Should get ~199.2 USDC (0.3% fee, no slippage for small trade)
            expect(amountOut).to.equal(parseUnits("199.201396", 6));
        });

        it("Should apply correct slippage for trades", async function () {
            // Set token decimals
            await mockRouter.setTokenDecimals(await weth.getAddress(), 18);
            await mockRouter.setTokenDecimals(await usdc.getAddress(), 6);
            
            // Set rate: 1 ETH = 2000 USDC
            await mockRouter.setExchangeRate(await weth.getAddress(), await usdc.getAddress(), parseUnits("2000", 6));
            
            // Test trade with slippage
            const amountIn = parseEther("1");
            const amountOut = await mockRouter.getAmountOut(
                amountIn,
                parseEther("100"),
                parseUnits("200000", 6)
            );
            
            // Should get ~1974.32 USDC (0.3% fee + slippage for 1% of reserves)
            expect(amountOut).to.equal(parseUnits("1974.316068", 6));
        });

        it("Should maintain consistent rate for small trades in slippage test", async function () {
            // Set token decimals
            await mockRouter.setTokenDecimals(await weth.getAddress(), 18);
            await mockRouter.setTokenDecimals(await usdc.getAddress(), 6);
            
            // Set rate: 1 ETH = 2000 USDC
            await mockRouter.setExchangeRate(await weth.getAddress(), await usdc.getAddress(), parseUnits("2000", 6));
            
            // Test very small trade: 0.1 ETH
            const amountIn = parseEther("0.1");
            const amountOut = await mockRouter.getAmountOut(
                amountIn,
                parseEther("1000"),
                parseUnits("2000000", 6)
            );
            
            // Should get ~199.38 USDC (0.3% fee, minimal slippage)
            expect(amountOut).to.equal(parseUnits("199.380121", 6));
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
            // Set token decimals
            await mockRouter.setTokenDecimals(await weth.getAddress(), 18);
            await mockRouter.setTokenDecimals(await usdc.getAddress(), 6);
            
            // Set rate: 1 ETH = 2000 USDC
            await mockRouter.setExchangeRate(await weth.getAddress(), await usdc.getAddress(), parseUnits("2000", 6));
            
            // Test small trade: 0.1 ETH
            const amountIn = parseEther("0.1");
            const amountOut = await mockRouter.getAmountOut(
                amountIn,
                parseEther("1000"),
                parseUnits("2000000", 6)
            );
            
            // Should get ~199.38 USDC (0.3% fee, minimal slippage)
            expect(amountOut).to.equal(parseUnits("199.380121", 6));
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
            await mockRouter.setExchangeRate(await weth.getAddress(), await usdc.getAddress(), parseUnits("2.1", 18));
            await mockRouter.setExchangeRate(await usdc.getAddress(), await dai.getAddress(), parseUnits("1.02", 18));
            await mockRouter.setExchangeRate(await dai.getAddress(), await weth.getAddress(), parseUnits("0.48", 18));

            const initialAmount = parseEther("1");
            
            // Execute the triangular arbitrage
            const amountAToB = await mockRouter.getAmountOut(
                initialAmount,
                parseEther("1000"),
                parseEther("2100")
            );
            
            const amountBToC = await mockRouter.getAmountOut(
                amountAToB,
                parseEther("1000"),
                parseEther("1020")
            );
            
            const finalAmount = await mockRouter.getAmountOut(
                amountBToC,
                parseEther("1000"),
                parseEther("480")
            );

            // Should be profitable after fees (>1.01 ETH return on 1 ETH input)
            expect(finalAmount).to.be.above(parseEther("1.01"));
        });
    });
}); 