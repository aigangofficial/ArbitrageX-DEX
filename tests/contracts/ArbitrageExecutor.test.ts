import type { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";
import { expect } from "chai";
import { ethers } from "hardhat";
import type { AITradingBot, ArbitrageExecutor, SecurityAdmin, IERC20, IWETH, IUniswapV2Router02, IUniswapV2Pair } from "../../typechain-types";

describe("ArbitrageExecutor", function () {
  let owner: HardhatEthersSigner;
  let wethWhale: HardhatEthersSigner;
  let usdcWhale: HardhatEthersSigner;
  let arbitrageExecutor: ArbitrageExecutor;
  let arbitrageExecutorAddr: string;
  let weth: IWETH;
  let usdc: IERC20;
  let uniswapRouter: IUniswapV2Router02;
  let sushiswapRouter: IUniswapV2Router02;
  let uniswapPair: IUniswapV2Pair;
  let sushiswapPair: IUniswapV2Pair;
  let path: string[];
  let amountIn: bigint;
  let securityAdmin: SecurityAdmin;

  const WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";
  const USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";
  const UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
  const SUSHISWAP_V2_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F";

  before(async function () {
    [owner] = await ethers.getSigners();

    // Get whales with enough tokens
    wethWhale = await ethers.getImpersonatedSigner("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"); // WETH contract
    usdcWhale = await ethers.getImpersonatedSigner("0x7713974908Be4BEd47172370115e8b1219F4A5f0"); // Circle

    // Fund whales with ETH for gas
    await owner.sendTransaction({
      to: wethWhale.address,
      value: ethers.parseEther("100"), // Increase ETH for gas
    });
    await owner.sendTransaction({
      to: usdcWhale.address,
      value: ethers.parseEther("100"), // Increase ETH for gas
    });

    // Get contract instances
    weth = await ethers.getContractAt("IWETH", WETH);
    usdc = await ethers.getContractAt("@openzeppelin/contracts/token/ERC20/IERC20.sol:IERC20", USDC);
    uniswapRouter = await ethers.getContractAt("IUniswapV2Router02", UNISWAP_V2_ROUTER);
    sushiswapRouter = await ethers.getContractAt("IUniswapV2Router02", SUSHISWAP_V2_ROUTER);

    // Ensure whales have enough tokens
    const mintAmount = ethers.parseEther("10000"); // Increase WETH amount
    const mintUsdcAmount = ethers.parseUnits("10000000", 6); // Increase USDC amount

    // Mint WETH by depositing ETH
    await weth.connect(wethWhale).deposit({ value: mintAmount });

    // Get USDC balance and ensure it's sufficient
    const usdcBalance = await usdc.balanceOf(usdcWhale.address);
    if (usdcBalance < mintUsdcAmount) {
        throw new Error("USDC whale does not have enough tokens");
    }
    console.log("\nUSDC whale balance:", ethers.formatUnits(usdcBalance, 6), "USDC");
  });

  beforeEach(async function () {
    // Deploy contracts
    const SecurityAdmin = await ethers.getContractFactory("SecurityAdmin");
    const ArbitrageExecutor = await ethers.getContractFactory("ArbitrageExecutor");

    securityAdmin = await SecurityAdmin.deploy() as unknown as SecurityAdmin;
    arbitrageExecutor = await ArbitrageExecutor.deploy(
        UNISWAP_V2_ROUTER,
        SUSHISWAP_V2_ROUTER,
        await securityAdmin.getAddress()
    ) as unknown as ArbitrageExecutor;
    arbitrageExecutorAddr = await arbitrageExecutor.getAddress();

    // Set up path and amount
    path = [WETH, USDC];
    amountIn = ethers.parseEther("1"); // 1 WETH

    // Set up DEX routers
    await arbitrageExecutor.setDexRouter(UNISWAP_V2_ROUTER, true);
    await arbitrageExecutor.setDexRouter(SUSHISWAP_V2_ROUTER, true);

    // Set supported tokens
    await arbitrageExecutor.setSupportedToken(WETH, true);
    await arbitrageExecutor.setSupportedToken(USDC, true);

    // Set minimum profit to a valid value (50 basis points = 0.5%)
    await arbitrageExecutor.setMinProfitBps(50);

    // Get DEX pairs
    const uniswapFactory = await ethers.getContractAt("IUniswapV2Factory", await uniswapRouter.factory());
    const sushiswapFactory = await ethers.getContractAt("IUniswapV2Factory", await sushiswapRouter.factory());

    const uniswapPairAddr = await uniswapFactory.getPair(WETH, USDC);
    const sushiswapPairAddr = await sushiswapFactory.getPair(WETH, USDC);

    uniswapPair = await ethers.getContractAt("IUniswapV2Pair", uniswapPairAddr) as unknown as IUniswapV2Pair;
    sushiswapPair = await ethers.getContractAt("IUniswapV2Pair", sushiswapPairAddr) as unknown as IUniswapV2Pair;

    // Create price difference between DEXs
    // First, check available balances and transfer what's available
    const burnAddress = "0x000000000000000000000000000000000000dEaD";
    const [uniReserve0, uniReserve1] = await uniswapPair.getReserves();
    const [sushiReserve0, sushiReserve1] = await sushiswapPair.getReserves();

    // Get token order
    const uniToken0 = await uniswapPair.token0();
    const sushiToken0 = await sushiswapPair.token0();

    // Check whale balances
    const wethWhaleBalance = await weth.balanceOf(wethWhale.address);
    const usdcWhaleBalance = await usdc.balanceOf(usdcWhale.address);

    // Add new liquidity based on token order
    if (uniToken0.toLowerCase() === WETH.toLowerCase()) {
      await weth.connect(wethWhale).transfer(uniswapPair.getAddress(), ethers.parseEther("10"));
      await usdc.connect(usdcWhale).transfer(uniswapPair.getAddress(), ethers.parseUnits("25000", 6));
    } else {
      await usdc.connect(usdcWhale).transfer(uniswapPair.getAddress(), ethers.parseUnits("25000", 6));
      await weth.connect(wethWhale).transfer(uniswapPair.getAddress(), ethers.parseEther("10"));
    }
    await uniswapPair.sync();

    if (sushiToken0.toLowerCase() === WETH.toLowerCase()) {
      await weth.connect(wethWhale).transfer(sushiswapPair.getAddress(), ethers.parseEther("10"));
      await usdc.connect(usdcWhale).transfer(sushiswapPair.getAddress(), ethers.parseUnits("24500", 6));
    } else {
      await usdc.connect(usdcWhale).transfer(sushiswapPair.getAddress(), ethers.parseUnits("24500", 6));
      await weth.connect(wethWhale).transfer(sushiswapPair.getAddress(), ethers.parseEther("10"));
    }
    await sushiswapPair.sync();

    // Get initial reserves after setup
    const [uniReserve0Before, uniReserve1Before] = await uniswapPair.getReserves();
    const [sushiReserve0Before, sushiReserve1Before] = await sushiswapPair.getReserves();

    console.log("\nInitial reserves after setup:");
    console.log("Uniswap reserves:",
      uniToken0.toLowerCase() === WETH.toLowerCase()
        ? `${ethers.formatEther(uniReserve0Before)} WETH, ${ethers.formatUnits(uniReserve1Before, 6)} USDC`
        : `${ethers.formatUnits(uniReserve0Before, 6)} USDC, ${ethers.formatEther(uniReserve1Before)} WETH`
    );
    console.log("Sushiswap reserves:",
      sushiToken0.toLowerCase() === WETH.toLowerCase()
        ? `${ethers.formatEther(sushiReserve0Before)} WETH, ${ethers.formatUnits(sushiReserve1Before, 6)} USDC`
        : `${ethers.formatUnits(sushiReserve0Before, 6)} USDC, ${ethers.formatEther(sushiReserve1Before)} WETH`
    );

    // Fund the contract with initial tokens
    await weth.connect(wethWhale).transfer(arbitrageExecutorAddr, ethers.parseEther("10"));
    await usdc.connect(usdcWhale).transfer(arbitrageExecutorAddr, ethers.parseUnits("30000", 6));
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await arbitrageExecutor.owner()).to.equal(owner.address);
    });

    it("Should set the correct DEX routers", async function () {
      expect(await arbitrageExecutor.dexRouters(UNISWAP_V2_ROUTER)).to.be.true;
      expect(await arbitrageExecutor.dexRouters(SUSHISWAP_V2_ROUTER)).to.be.true;
    });
  });

  describe("Token Management", function () {
    it("Should allow owner to withdraw tokens", async function () {
      const amount = ethers.parseUnits("1000", 6);
      await expect(arbitrageExecutor.withdraw(USDC, amount))
        .to.emit(arbitrageExecutor, "TokenWithdrawn")
        .withArgs(USDC, amount, owner.address);
    });

    it("Should not allow non-owner to withdraw tokens", async function () {
      const amount = ethers.parseUnits("1000", 6);
      await expect(
        arbitrageExecutor.connect(wethWhale).withdraw(USDC, amount)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });

  describe("Arbitrage Execution", function () {
    it("Should detect price differences between DEXs", async function () {
      // Get quotes from both DEXs
      const uniQuote = await uniswapRouter.getAmountsOut(amountIn, path);
      const sushiQuote = await sushiswapRouter.getAmountsOut(amountIn, path);

      console.log("\nQuotes for 1 WETH:");
      console.log("Uniswap quote:", ethers.formatUnits(uniQuote[1], 6), "USDC");
      console.log("Sushiswap quote:", ethers.formatUnits(sushiQuote[1], 6), "USDC");

      // Calculate expected returns
      const uniFirst = await arbitrageExecutor.getExpectedReturn(
        WETH,
        USDC,
        amountIn,
        true
      );
      const sushiFirst = await arbitrageExecutor.getExpectedReturn(
        WETH,
        USDC,
        amountIn,
        false
      );

      console.log("\nExpected returns:");
      console.log("Expected return (Uni first):", ethers.formatUnits(uniFirst, 6), "USDC");
      console.log("Expected return (Sushi first):", ethers.formatUnits(sushiFirst, 6), "USDC");

      // At least one return should be greater than zero
      expect(uniFirst > 0n || sushiFirst > 0n).to.be.true;
    });

    it("Should execute arbitrage trade when profitable", async function () {
      // Set minimum profit to 0.1% (10 BPS)
      await arbitrageExecutor.setMinProfitBps(10);

      // Fund the contract with WETH
      await weth.transfer(arbitrageExecutorAddr, amountIn);

      // Get initial balances
      const initialWethBalance = await weth.balanceOf(arbitrageExecutorAddr);
      const initialUsdcBalance = await usdc.balanceOf(arbitrageExecutorAddr);

      console.log("\nInitial balances:");
      console.log("Initial WETH balance:", ethers.formatEther(initialWethBalance));
      console.log("Initial USDC balance:", ethers.formatUnits(initialUsdcBalance, 6));

      // Get expected returns to determine which path is more profitable
      const uniFirst = await arbitrageExecutor.getExpectedReturn(WETH, USDC, amountIn, true);
      const sushiFirst = await arbitrageExecutor.getExpectedReturn(WETH, USDC, amountIn, false);

      // Use the more profitable path
      const useUniFirst = uniFirst > sushiFirst;
      console.log("\nUsing path:", useUniFirst ? "Uniswap -> Sushiswap" : "Sushiswap -> Uniswap");

      // Execute arbitrage
      const tx = await arbitrageExecutor.executeArbitrage(
        WETH,
        USDC,
        amountIn,
        useUniFirst ? [WETH, USDC] : [USDC, WETH],
        useUniFirst ? UNISWAP_V2_ROUTER : SUSHISWAP_V2_ROUTER
      );

      await expect(tx)
        .to.emit(arbitrageExecutor, "ArbitrageExecuted")
        .withArgs(WETH, USDC, amountIn, useUniFirst ? uniFirst : sushiFirst);
    });
  });
});
