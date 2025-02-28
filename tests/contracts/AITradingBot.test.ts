import { expect } from "chai";
import { ethers, network } from "hardhat";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";
import type { AITradingBot, ArbitrageExecutor, SecurityAdmin } from "../../typechain-types";

describe("AITradingBot", function () {
    let aiTradingBot: AITradingBot;
    let arbitrageExecutor: ArbitrageExecutor;
    let securityAdmin: SecurityAdmin;
    let owner: HardhatEthersSigner;
    let wethWhale: HardhatEthersSigner;
    let USDC: any;
    let WETH: any;

    // Mainnet addresses
    const USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";
    const WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";
    const UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
    const SUSHISWAP_V2_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F";
    const WETH_WHALE = "0x2fEb1512183545f48f6b9C5b4EbfCaF49CfCa6F3"; // Large WETH holder

    // Trading parameters
    const minTradeAmount = ethers.parseEther("0.1"); // 0.1 ETH
    const maxTradeAmount = ethers.parseEther("10");  // 10 ETH
    const minProfitBps = 50; // 0.5%

    beforeEach(async function () {
        [owner] = await ethers.getSigners();

        // Deploy SecurityAdmin first
        const SecurityAdmin = await ethers.getContractFactory("SecurityAdmin");
        securityAdmin = await SecurityAdmin.deploy() as unknown as SecurityAdmin;
        await securityAdmin.waitForDeployment();

        // Deploy ArbitrageExecutor with routers
        const ArbitrageExecutor = await ethers.getContractFactory("ArbitrageExecutor");
        arbitrageExecutor = await ArbitrageExecutor.deploy(
            UNISWAP_V2_ROUTER,
            SUSHISWAP_V2_ROUTER,
            owner.address
        ) as unknown as ArbitrageExecutor;
        await arbitrageExecutor.waitForDeployment();

        // Configure ArbitrageExecutor
        await arbitrageExecutor.setDexRouter(UNISWAP_V2_ROUTER, true);
        await arbitrageExecutor.setDexRouter(SUSHISWAP_V2_ROUTER, true);
        await arbitrageExecutor.setSupportedToken(WETH_ADDRESS, true);
        await arbitrageExecutor.setSupportedToken(USDC_ADDRESS, true);
        await arbitrageExecutor.setMinProfitBps(10); // 0.1% minimum profit

        // Deploy AITradingBot with parameters
        const AITradingBot = await ethers.getContractFactory("AITradingBot");
        aiTradingBot = await AITradingBot.deploy(
            await arbitrageExecutor.getAddress(),
            await securityAdmin.getAddress(),
            minTradeAmount,
            maxTradeAmount,
            minProfitBps
        ) as unknown as AITradingBot;
        await aiTradingBot.waitForDeployment();

        // Whitelist tokens in SecurityAdmin
        await securityAdmin.whitelistToken(WETH_ADDRESS);
        await securityAdmin.whitelistToken(USDC_ADDRESS);

        // Get mainnet contracts
        WETH = await ethers.getContractAt("@openzeppelin/contracts/token/ERC20/IERC20.sol:IERC20", WETH_ADDRESS);
        USDC = await ethers.getContractAt("@openzeppelin/contracts/token/ERC20/IERC20.sol:IERC20", USDC_ADDRESS);

        // Fund and impersonate the WETH whale
        await network.provider.send("hardhat_setBalance", [
            WETH_WHALE,
            "0x56BC75E2D63100000" // 100 ETH in hex
        ]);

        await network.provider.request({
            method: "hardhat_impersonateAccount",
            params: [WETH_WHALE]
        });

        wethWhale = await ethers.getImpersonatedSigner(WETH_WHALE);

        // Fund owner with ETH for gas
        await owner.sendTransaction({
            to: wethWhale.address,
            value: ethers.parseEther("10")
        });

        // Setup approvals for contracts
        const arbitrageExecutorAddress = await arbitrageExecutor.getAddress();
        const aiTradingBotAddress = await aiTradingBot.getAddress();

        // Approve AITradingBot to spend owner's tokens
        await WETH.connect(owner).approve(aiTradingBotAddress, ethers.MaxUint256);
        await USDC.connect(owner).approve(aiTradingBotAddress, ethers.MaxUint256);

        // Approve ArbitrageExecutor to spend AITradingBot's tokens
        await aiTradingBot.approveTokens(
            [WETH_ADDRESS, USDC_ADDRESS],
            arbitrageExecutorAddress
        );
    });

    describe("Initialization", function () {
        it("Should set correct initial parameters", async function () {
            expect(await aiTradingBot.arbitrageExecutor()).to.equal(await arbitrageExecutor.getAddress());
            expect(await aiTradingBot.securityAdmin()).to.equal(await securityAdmin.getAddress());
            expect(await aiTradingBot.minTradeAmount()).to.equal(minTradeAmount);
            expect(await aiTradingBot.maxTradeAmount()).to.equal(maxTradeAmount);
            expect(await aiTradingBot.minProfitBps()).to.equal(minProfitBps);
        });
    });

    describe("Trade Execution", function () {
        it("Should execute trade successfully", async function () {
            const amount = ethers.parseEther("1");
            const expectedProfit = 100; // 1%

            // Transfer WETH from whale to owner
            await WETH.connect(wethWhale).transfer(owner.address, amount);

            // Verify balances and allowances
            const ownerBalance = await WETH.balanceOf(owner.address);
            const aiTradingBotAllowance = await WETH.allowance(owner.address, await aiTradingBot.getAddress());
            
            console.log("Owner WETH Balance:", ethers.formatEther(ownerBalance));
            console.log("AITradingBot WETH Allowance:", ethers.formatEther(aiTradingBotAllowance));

            await expect(
                aiTradingBot.executeTrade(
                    WETH_ADDRESS,
                    USDC_ADDRESS,
                    amount,
                    expectedProfit
                )
            ).to.emit(aiTradingBot, "TradeExecuted")
                .withArgs(WETH_ADDRESS, USDC_ADDRESS, amount, expectedProfit);
        });

        it("Should revert if amount is below minimum", async function () {
            const amount = ethers.parseEther("0.01");
            const expectedProfit = 100;

            await expect(
                aiTradingBot.executeTrade(
                    WETH_ADDRESS,
                    USDC_ADDRESS,
                    amount,
                    expectedProfit
                )
            ).to.be.revertedWithCustomError(aiTradingBot, "InvalidAmount")
                .withArgs(amount, minTradeAmount, maxTradeAmount);
        });

        it("Should revert if amount is above maximum", async function () {
            const amount = ethers.parseEther("20");
            const expectedProfit = 100;

            await expect(
                aiTradingBot.executeTrade(
                    WETH_ADDRESS,
                    USDC_ADDRESS,
                    amount,
                    expectedProfit
                )
            ).to.be.revertedWithCustomError(aiTradingBot, "InvalidAmount")
                .withArgs(amount, minTradeAmount, maxTradeAmount);
        });

        it("Should revert if profit is too low", async function () {
            const amount = ethers.parseEther("1");
            const expectedProfit = 10; // 0.1%

            await expect(
                aiTradingBot.executeTrade(
                    WETH_ADDRESS,
                    USDC_ADDRESS,
                    amount,
                    expectedProfit
                )
            ).to.be.revertedWithCustomError(aiTradingBot, "InsufficientProfit")
                .withArgs(expectedProfit, minProfitBps);
        });
    });

    describe("Parameter Updates", function () {
        it("Should update parameters successfully", async function () {
            const newMinTradeAmount = ethers.parseEther("0.2");
            const newMaxTradeAmount = ethers.parseEther("20");
            const newMinProfitBps = 75;

            await expect(
                aiTradingBot.updateParameters(
                    newMinTradeAmount,
                    newMaxTradeAmount,
                    newMinProfitBps
                )
            ).to.emit(aiTradingBot, "ParametersUpdated")
                .withArgs(newMinTradeAmount, newMaxTradeAmount, newMinProfitBps);

            expect(await aiTradingBot.minTradeAmount()).to.equal(newMinTradeAmount);
            expect(await aiTradingBot.maxTradeAmount()).to.equal(newMaxTradeAmount);
            expect(await aiTradingBot.minProfitBps()).to.equal(newMinProfitBps);
        });

        it("Should revert if min amount is greater than max amount", async function () {
            await expect(
                aiTradingBot.updateParameters(
                    ethers.parseEther("10"),
                    ethers.parseEther("5"),
                    minProfitBps
                )
            ).to.be.revertedWithCustomError(aiTradingBot, "InvalidParameters")
                .withArgs("min > max");
        });

        it("Should revert if profit threshold is zero", async function () {
            await expect(
                aiTradingBot.updateParameters(
                    minTradeAmount,
                    maxTradeAmount,
                    0
                )
            ).to.be.revertedWithCustomError(aiTradingBot, "InvalidParameters")
                .withArgs("zero profit threshold");
        });
    });

    describe("Access Control", function () {
        it("Should revert if non-owner tries to execute trade", async function () {
            const nonOwner = (await ethers.getSigners())[1];
            const amount = ethers.parseEther("1");
            const expectedProfit = 100;

            await expect(
                aiTradingBot.connect(nonOwner).executeTrade(
                    WETH_ADDRESS,
                    USDC_ADDRESS,
                    amount,
                    expectedProfit
                )
            ).to.be.revertedWith("Ownable: caller is not the owner");
        });

        it("Should revert if non-owner tries to update parameters", async function () {
            const nonOwner = (await ethers.getSigners())[1];
            await expect(
                aiTradingBot.connect(nonOwner).updateParameters(
                    minTradeAmount,
                    maxTradeAmount,
                    minProfitBps
                )
            ).to.be.revertedWith("Ownable: caller is not the owner");
        });
    });

    describe("Pause/Unpause", function () {
        it("Should pause and unpause trading", async function () {
            await aiTradingBot.pause();
            
            const amount = ethers.parseEther("1");
            const expectedProfit = 100;

            await expect(
                aiTradingBot.executeTrade(
                    WETH_ADDRESS,
                    USDC_ADDRESS,
                    amount,
                    expectedProfit
                )
            ).to.be.revertedWith("Pausable: paused");

            await aiTradingBot.unpause();

            await expect(
                aiTradingBot.executeTrade(
                    WETH_ADDRESS,
                    USDC_ADDRESS,
                    amount,
                    expectedProfit
                )
            ).to.emit(aiTradingBot, "TradeExecuted");
        });
    });
}); 