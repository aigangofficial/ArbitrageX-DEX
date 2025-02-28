import { expect } from "chai";
import { ethers, network } from "hardhat";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";
import { Contract, ContractFactory, AbiCoder } from "ethers";
import { FlashLoanService, ArbitrageExecutor } from "../typechain-types";
import "@nomicfoundation/hardhat-chai-matchers";
import { AddressLike, BytesLike } from "ethers";

const WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";
const USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";
const UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
const SUSHISWAP_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F";
const AAVE_POOL = "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9";
const ZERO_ADDRESS = "0x0000000000000000000000000000000000000000";
const WETH_WHALE = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";

describe("FlashLoanArbitrage", () => {
    let owner: HardhatEthersSigner;
    let user: HardhatEthersSigner;
    let flashLoanService: FlashLoanService;
    let arbitrageExecutor: ArbitrageExecutor;
    let wethContract: Contract;
    let usdcContract: Contract;
    let abiCoder: AbiCoder;
    let aavePool: Contract;

    beforeEach(async () => {
        [owner, user] = await ethers.getSigners();
        abiCoder = AbiCoder.defaultAbiCoder();

        // Get contract instances using our local interfaces
        aavePool = await ethers.getContractAt("contracts/interfaces/aave/IPool.sol:IPool", AAVE_POOL);
        wethContract = await ethers.getContractAt("contracts/interfaces/IERC20.sol:IERC20", WETH_ADDRESS);
        usdcContract = await ethers.getContractAt("contracts/interfaces/IERC20.sol:IERC20", USDC_ADDRESS);

        // Deploy ArbitrageExecutor first
        const ArbitrageExecutor = await ethers.getContractFactory("ArbitrageExecutor");
        arbitrageExecutor = await ArbitrageExecutor.deploy(
            UNISWAP_ROUTER,
            SUSHISWAP_ROUTER,
            ethers.parseEther("0.1"), // Min profit amount: 0.1 ETH
            ethers.ZeroAddress // No MEV protection for tests
        ) as unknown as ArbitrageExecutor;
        await arbitrageExecutor.waitForDeployment();

        // Set profit thresholds
        await arbitrageExecutor.setMinProfitAmount(ethers.parseEther("0.1")); // 0.1 ETH minimum profit

        // Deploy FlashLoanService
        const FlashLoanServiceFactory = await ethers.getContractFactory("FlashLoanService");
        const flashLoanServiceContract = await FlashLoanServiceFactory.deploy(
            AAVE_POOL,
            await arbitrageExecutor.getAddress(),
            ethers.parseEther("0.1"), // Min amount: 0.1 ETH
            ethers.parseEther("1000"), // Max amount: 1000 ETH
            ethers.ZeroAddress // No MEV protection for tests
        );
        await flashLoanServiceContract.waitForDeployment();
        flashLoanService = flashLoanServiceContract as unknown as FlashLoanService;

        // Fund the owner with ETH for testing
        await network.provider.send("hardhat_setBalance", [
            owner.address,
            "0x56BC75E2D63100000" // 100 ETH in hex
        ]);

        // Convert ETH to WETH and send to contract
        await owner.sendTransaction({
            to: WETH_ADDRESS,
            value: ethers.parseEther("10")
        });

        // Transfer WETH to the contract
        await wethContract["transfer(address,uint256)"](await flashLoanService.getAddress(), ethers.parseEther("10"));

        // Enable WETH and USDC as supported tokens in both contracts
        await flashLoanService.updateTokenSupport(WETH_ADDRESS, true);
        await flashLoanService.updateTokenSupport(USDC_ADDRESS, true);
        
        // The ArbitrageExecutor doesn't have setSupportedToken method, so we need to check how tokens are supported
        // For now, we'll skip these lines as they're not in the interface
        // await arbitrageExecutor.setSupportedToken(WETH_ADDRESS, true);
        // await arbitrageExecutor.setSupportedToken(USDC_ADDRESS, true);

        // Enable routers in ArbitrageExecutor
        // The ArbitrageExecutor uses setRouterApproval instead of setDexRouter
        await arbitrageExecutor.setRouterApproval(UNISWAP_ROUTER, true);
        await arbitrageExecutor.setRouterApproval(SUSHISWAP_ROUTER, true);

        // Approve WETH spending for ArbitrageExecutor
        await wethContract["approve(address,uint256)"](await arbitrageExecutor.getAddress(), ethers.parseEther("1000"));
    });

    describe("Security Checks", () => {
        it("should revert with unauthorized initiator", async () => {
            const params = abiCoder.encode(
                ["address", "address", "address"],
                [WETH_ADDRESS, USDC_ADDRESS, UNISWAP_ROUTER]
            ) as BytesLike;

            await expect(
                flashLoanService.executeOperation(
                    WETH_ADDRESS as AddressLike,
                    ethers.parseEther("1"),
                    ethers.parseEther("0.0005"),
                    user.address as AddressLike,
                    params
                )
            ).to.be.revertedWithCustomError(flashLoanService, "UnauthorizedInitiator")
             .withArgs(user.address);
        });

        it("should revert with unsupported asset", async () => {
            const DAI_ADDRESS = "0x6B175474E89094C44Da98b954EedeAC495271d0F";
            const params = abiCoder.encode(
                ["address", "address", "address"],
                [DAI_ADDRESS, USDC_ADDRESS, UNISWAP_ROUTER]
            ) as BytesLike;

            await expect(
                flashLoanService.executeOperation(
                    DAI_ADDRESS as AddressLike,
                    ethers.parseEther("1"),
                    ethers.parseEther("0.0005"),
                    await flashLoanService.getAddress(),
                    params
                )
            ).to.be.revertedWithCustomError(flashLoanService, "UnsupportedToken");
        });

        it("should revert when exceeding flash loan amount boundaries", async () => {
            const params = abiCoder.encode(
                ["address", "address", "address"],
                [WETH_ADDRESS, USDC_ADDRESS, UNISWAP_ROUTER]
            ) as BytesLike;

            // Test too low amount
            const tooLow = ethers.parseEther("0.01");
            await expect(
                flashLoanService.executeOperation(
                    WETH_ADDRESS as AddressLike,
                    tooLow,
                    ethers.parseEther("0.0005"),
                    await flashLoanService.getAddress(),
                    params
                )
            ).to.be.revertedWithCustomError(flashLoanService, "InvalidFlashLoanAmount")
             .withArgs(tooLow, ethers.parseEther("0.1"), ethers.parseEther("1000"));

            // Test too high amount
            const tooHigh = ethers.parseEther("2000");
            await expect(
                flashLoanService.executeOperation(
                    WETH_ADDRESS as AddressLike,
                    tooHigh,
                    ethers.parseEther("1"),
                    await flashLoanService.getAddress(),
                    params
                )
            ).to.be.revertedWithCustomError(flashLoanService, "InvalidFlashLoanAmount")
             .withArgs(tooHigh, ethers.parseEther("0.1"), ethers.parseEther("1000"));
        });

        it("should revert with insufficient funds for repayment", async () => {
            const params = abiCoder.encode(
                ["address", "address", "address"],
                [WETH_ADDRESS, USDC_ADDRESS, UNISWAP_ROUTER]
            ) as BytesLike;

            // Drain the contract first
            const balance = await wethContract.balanceOf(await flashLoanService.getAddress());
            if (balance > 0) {
                await flashLoanService.emergencyWithdraw(
                    WETH_ADDRESS as AddressLike,
                    balance,
                    owner.address as AddressLike
                );
            }

            await expect(
                flashLoanService.executeOperation(
                    WETH_ADDRESS as AddressLike,
                    ethers.parseEther("1"),
                    ethers.parseEther("0.0005"),
                    await flashLoanService.getAddress(),
                    params
                )
            ).to.be.revertedWithCustomError(flashLoanService, "InsufficientFundsForRepayment");
        });

        it("should revert with invalid router", async () => {
            const params = abiCoder.encode(
                ["address", "address", "address"],
                [WETH_ADDRESS, USDC_ADDRESS, ZERO_ADDRESS]
            ) as BytesLike;

            await expect(
                flashLoanService.executeOperation(
                    WETH_ADDRESS as AddressLike,
                    ethers.parseEther("1"),
                    ethers.parseEther("0.0005"),
                    await flashLoanService.getAddress(),
                    params
                )
            ).to.be.revertedWithCustomError(flashLoanService, "InvalidPath");
        });

        it("should revert with execution failure when profit is insufficient", async () => {
            // Set high minimum profit requirement
            await flashLoanService.setMinProfitBps(1000); // 10%

            // Fund the contract with enough WETH for repayment
            await owner.sendTransaction({
                to: WETH_ADDRESS,
                value: ethers.parseEther("10")
            });

            // Convert ETH to WETH and send to contract
            await wethContract["transfer(address,uint256)"](await flashLoanService.getAddress(), ethers.parseEther("10"));

            // Impersonate USDC whale for real USDC
            const USDC_WHALE = "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503";
            await network.provider.request({
                method: "hardhat_impersonateAccount",
                params: [USDC_WHALE],
            });

            const usdcWhale = await ethers.getSigner(USDC_WHALE);
            await usdcContract.connect(usdcWhale)["transfer(address,uint256)"](
                await flashLoanService.getAddress(), 
                ethers.parseUnits("10000", 6)
            );

            // Execute flash loan operation with real Uniswap router
            // The trade will fail due to insufficient liquidity or high slippage
            const params = abiCoder.encode(
                ["address", "address", "address"],
                [WETH_ADDRESS, USDC_ADDRESS, UNISWAP_ROUTER]
            ) as BytesLike;

            await expect(
                flashLoanService.executeOperation(
                    WETH_ADDRESS as AddressLike,
                    ethers.parseEther("1"),
                    ethers.parseEther("0.0005"), // 0.05% flash loan fee
                    await flashLoanService.getAddress(),
                    params
                )
            ).to.be.revertedWithCustomError(flashLoanService, "ExecutionFailed");
        });
    });
}); 