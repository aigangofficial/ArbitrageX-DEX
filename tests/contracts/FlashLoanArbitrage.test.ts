import type { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";
import { loadFixture } from "@nomicfoundation/hardhat-toolbox/network-helpers";
import { expect } from "chai";
import { ethers, network } from "hardhat";
import type { ArbitrageExecutor, FlashLoanService, IERC20, IWETH } from "../../typechain-types";

describe("Flash Loan Arbitrage", function () {
  let flashLoanService: FlashLoanService;
  let arbitrageExecutor: ArbitrageExecutor;
  let owner: HardhatEthersSigner;
  let user: HardhatEthersSigner;
  let weth: IWETH;
  let usdc: IERC20;

  // Mainnet addresses
  const AAVE_V3_POOL = "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"; // Aave V3 Pool on Mainnet
  const UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
  const SUSHISWAP_V2_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F";
  const WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";
  const USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";
  const USDC_WHALE = "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503"; // Binance Hot Wallet with USDC

  async function deployFixture() {
    // Reset fork to clean state
    await network.provider.request({
      method: "hardhat_reset",
      params: [{
        forking: {
          jsonRpcUrl: process.env.MAINNET_RPC_URL,
          blockNumber: 19000000 // Historical block
        }
      }]
    });

    [owner, user] = await ethers.getSigners();

    // Get USDC whale
    const usdcWhale = await ethers.getImpersonatedSigner(USDC_WHALE);

    // Fund whale with ETH for gas
    await owner.sendTransaction({
      to: usdcWhale.address,
      value: ethers.parseEther("10"),
    });

    // Get contract instances
    weth = await ethers.getContractAt("contracts/interfaces/IWETH.sol:IWETH", WETH_ADDRESS) as unknown as IWETH;
    usdc = await ethers.getContractAt("@openzeppelin/contracts/token/ERC20/IERC20.sol:IERC20", USDC_ADDRESS) as unknown as IERC20;

    // Check USDC balance of whale
    const usdcBalance = await usdc.balanceOf(usdcWhale.address);
    console.log(`USDC Whale balance: ${ethers.formatUnits(usdcBalance, 6)} USDC`);

    // Deploy MEVProtection first
    const mockFlashbotsRelayerFactory = await ethers.getContractFactory("MockFlashbotsRelayer");
    const mockFlashbotsRelayer = await mockFlashbotsRelayerFactory.deploy();
    
    const mevProtectionFactory = await ethers.getContractFactory("MEVProtection");
    const mevProtection = await mevProtectionFactory.deploy(await mockFlashbotsRelayer.getAddress());

    // Deploy ArbitrageExecutor with MEVProtection
    const ArbitrageExecutor = await ethers.getContractFactory("ArbitrageExecutor");
    arbitrageExecutor = await ArbitrageExecutor.deploy(
      UNISWAP_V2_ROUTER,
      SUSHISWAP_V2_ROUTER,
      ethers.parseEther("0.01"), // minProfitAmount
      await mevProtection.getAddress()
    ) as unknown as ArbitrageExecutor;

    // Deploy FlashLoanService with ArbitrageExecutor and MEVProtection
    const FlashLoanService = await ethers.getContractFactory("FlashLoanService");
    flashLoanService = await FlashLoanService.deploy(
      AAVE_V3_POOL,
      await arbitrageExecutor.getAddress(),
      ethers.parseEther("0.1"),  // minAmount
      ethers.parseEther("10"),   // maxAmount
      await mevProtection.getAddress()
    ) as unknown as FlashLoanService;

    // Fund contracts with WETH by depositing ETH
    await weth.deposit({ value: ethers.parseEther("20") });
    await weth.transfer(await flashLoanService.getAddress(), ethers.parseEther("10"));
    
    // Fund contracts with USDC
    await usdc.connect(usdcWhale).transfer(await flashLoanService.getAddress(), ethers.parseUnits("30000", 6));

    // Setup token support and flash loan provider
    await flashLoanService.connect(owner).updateTokenSupport(WETH_ADDRESS, true);
    await flashLoanService.connect(owner).updateTokenSupport(USDC_ADDRESS, true);
    await flashLoanService.connect(owner).addFlashLoanProvider(AAVE_V3_POOL);

    // Set up DEX routers
    await arbitrageExecutor.connect(owner).setRouterApproval(UNISWAP_V2_ROUTER, true);
    await arbitrageExecutor.connect(owner).setRouterApproval(SUSHISWAP_V2_ROUTER, true);

    // Whitelist tokens in ArbitrageExecutor
    await arbitrageExecutor.connect(owner).whitelistToken(WETH_ADDRESS);
    await arbitrageExecutor.connect(owner).whitelistToken(USDC_ADDRESS);

    // Set trade amount limits (maxTradeAmount first, then minTradeAmount)
    const maxTradeAmountId = ethers.keccak256(ethers.toUtf8Bytes("maxTradeAmount"));
    await flashLoanService.connect(owner).requestChange(maxTradeAmountId);
    await network.provider.send("evm_increaseTime", [24 * 60 * 60]); // Fast forward 24 hours
    await network.provider.send("evm_mine"); // Mine a new block to update timestamp
    await flashLoanService.connect(owner).executeParameterChange("maxTradeAmount", ethers.parseEther("10"));

    const minTradeAmountId = ethers.keccak256(ethers.toUtf8Bytes("minTradeAmount"));
    await flashLoanService.connect(owner).requestChange(minTradeAmountId);
    await network.provider.send("evm_increaseTime", [24 * 60 * 60]); // Fast forward 24 hours
    await network.provider.send("evm_mine"); // Mine a new block to update timestamp
    await flashLoanService.connect(owner).executeParameterChange("minTradeAmount", ethers.parseEther("0.001"));

    // Set flash loan amount limits
    const maxFlashLoanAmountId = ethers.keccak256(ethers.toUtf8Bytes("maxFlashLoanAmount"));
    await flashLoanService.connect(owner).requestChange(maxFlashLoanAmountId);
    await network.provider.send("evm_increaseTime", [24 * 60 * 60]); // Fast forward 24 hours
    await network.provider.send("evm_mine"); // Mine a new block to update timestamp
    await flashLoanService.connect(owner).executeParameterChange("maxFlashLoanAmount", ethers.parseEther("100"));

    const minFlashLoanAmountId = ethers.keccak256(ethers.toUtf8Bytes("minFlashLoanAmount"));
    await flashLoanService.connect(owner).requestChange(minFlashLoanAmountId);
    await network.provider.send("evm_increaseTime", [24 * 60 * 60]); // Fast forward 24 hours
    await network.provider.send("evm_mine"); // Mine a new block to update timestamp
    await flashLoanService.connect(owner).executeParameterChange("minFlashLoanAmount", ethers.parseEther("0.1"));

    // Enable test mode for flash loans
    await flashLoanService.connect(owner).toggleTestMode(true);
    
    // Disable MEV protection for testing
    await flashLoanService.connect(owner).toggleMEVProtection(false);

    return { flashLoanService, arbitrageExecutor, owner, user, weth, usdc };
  }

  beforeEach(async function () {
    const fixture = await loadFixture(deployFixture);
    flashLoanService = fixture.flashLoanService;
    arbitrageExecutor = fixture.arbitrageExecutor;
    owner = fixture.owner;
    user = fixture.user;
    weth = fixture.weth;
    usdc = fixture.usdc;
  });

  describe("Arbitrage Execution", () => {
    it("Should revert with 'Unauthorized' when calling executeArbitrage directly", async () => {
      // Get historical reserves from Uniswap pair
      const uniswapPair = await ethers.getContractAt(
        "IUniswapV2Pair",
        "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc" // WETH/USDC pair
      );
      const reserves = await uniswapPair.getReserves();
      const historicalPrice = (BigInt(reserves[1]) * BigInt(10n ** 12n)) / BigInt(reserves[0]);
      console.log("Historical Price:", historicalPrice.toString(), "USDC per WETH");

      // Execute arbitrage with 0.01 ETH - should revert with Unauthorized
      await expect(
        flashLoanService.connect(owner).executeArbitrage(
          WETH_ADDRESS,
          USDC_ADDRESS,
          UNISWAP_V2_ROUTER,
          ethers.parseEther("0.01"),
          0 // Required amount
        )
      ).to.be.revertedWith("Unauthorized");
    });
  });

  describe("Flash Loan Operations", () => {
    it("Should execute flash loan successfully in test mode", async () => {
      const amount = ethers.parseEther("0.5");

      // Execute flash loan in test mode
      await expect(
        flashLoanService.connect(owner).executeFlashLoan(
          WETH_ADDRESS,
          amount
        )
      ).to.emit(flashLoanService, "FlashLoanExecuted")
        .withArgs(WETH_ADDRESS, amount, 0, owner.address);
    });

    it("Should revert if flash loan amount is too high", async () => {
      const amount = ethers.parseEther("1000");
      
      await expect(
        flashLoanService.connect(owner).executeFlashLoan(
          WETH_ADDRESS,
          amount
        )
      ).to.be.revertedWithCustomError(flashLoanService, "InvalidAmount")
        .withArgs(amount, ethers.parseEther("10"));
    });
  });

  describe("Admin Functions", function () {
    it("Should allow owner to add flash loan provider", async function () {
      const newProvider = user.address;
      await flashLoanService.connect(owner).addFlashLoanProvider(newProvider);
      expect(await flashLoanService.flashLoanProviders(newProvider)).to.be.true;
    });

    it("Should not allow non-owner to add flash loan provider", async function () {
      const newProvider = user.address;
      await expect(
        flashLoanService.connect(user).addFlashLoanProvider(newProvider)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Should allow owner to set min profit BPS", async function () {
      const newMinProfitBps = 200; // 2%
      await flashLoanService.connect(owner).setMinProfitBps(newMinProfitBps);
      expect(await flashLoanService.minProfitBps()).to.equal(newMinProfitBps);
    });

    it("Should not allow non-owner to set min profit BPS", async function () {
      await expect(
        flashLoanService.connect(user).setMinProfitBps(200)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Security Checks", function () {
    it("should revert with unapproved router", async function () {
      const unapprovedRouter = user.address;
      
      await expect(
        flashLoanService.connect(owner).executeArbitrage(
          WETH_ADDRESS,
          USDC_ADDRESS,
          unapprovedRouter,
          ethers.parseEther("1"),
          0
        )
      ).to.be.revertedWith("Unauthorized");
    });
  });
});
