// @ts-nocheck
import "@nomicfoundation/hardhat-chai-matchers";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import { expect } from "chai";
import { Contract } from "ethers";
import { ethers } from "hardhat";

const IERC20_ABI = [
  'function totalSupply() external view returns (uint256)',
  'function balanceOf(address account) external view returns (uint256)',
  'function transfer(address to, uint256 amount) external returns (bool)',
  'function allowance(address owner, address spender) external view returns (uint256)',
  'function approve(address spender, uint256 amount) external returns (bool)',
  'function transferFrom(address from, address to, uint256 amount) external returns (bool)',
];

const FACTORY_ABI = [
  'function getPair(address tokenA, address tokenB) external view returns (address pair)',
  'function allPairs(uint256) external view returns (address pair)',
  'function allPairsLength() external view returns (uint256)',
  'function feeTo() external view returns (address)',
  'function feeToSetter() external view returns (address)',
  'function createPair(address tokenA, address tokenB) external returns (address pair)',
];

const PAIR_ABI = [
  'function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)',
  'function token0() external view returns (address)',
  'function token1() external view returns (address)',
  'function price0CumulativeLast() external view returns (uint256)',
  'function price1CumulativeLast() external view returns (uint256)',
];

const ROUTER_ABI = [
  'function factory() external view returns (address)',
  'function WETH() external view returns (address)',
  'function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts)',
  'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)',
];

const WETH_ABI = [
  "function deposit() external payable",
  "function withdraw(uint) external",
  "function balanceOf(address) external view returns (uint)",
  "function transfer(address, uint) external returns (bool)",
  "function approve(address, uint) external returns (bool)"
];

const ERC20_ABI = [
  "function balanceOf(address) external view returns (uint)",
  "function transfer(address, uint) external returns (bool)",
  "function approve(address, uint) external returns (bool)"
];

const UNISWAP_ROUTER_ABI = [
  "function factory() external view returns (address)",
  "function getAmountsOut(uint amountIn, address[] memory path) external view returns (uint[] memory amounts)"
];

const UNISWAP_FACTORY_ABI = [
  "function getPair(address tokenA, address tokenB) external view returns (address pair)"
];

const UNISWAP_PAIR_ABI = [
  "function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)",
  "function token0() external view returns (address)",
  "function token1() external view returns (address)",
  "function sync() external"
];

interface IWETH extends Contract {
  deposit(overrides?: { value: bigint }): Promise<any>;
  withdraw(amount: bigint): Promise<any>;
  balanceOf(account: string): Promise<bigint>;
  transfer(to: string, amount: bigint): Promise<boolean>;
  approve(spender: string, amount: bigint): Promise<boolean>;
}

interface IERC20 extends Contract {
  balanceOf(account: string): Promise<bigint>;
  transfer(to: string, amount: bigint): Promise<boolean>;
  approve(spender: string, amount: bigint): Promise<boolean>;
  allowance(owner: string, spender: string): Promise<bigint>;
  transferFrom(from: string, to: string, amount: bigint): Promise<boolean>;
}

interface IUniswapV2Router extends Contract {
  factory(): Promise<string>;
  getAmountsOut(amountIn: bigint, path: string[]): Promise<bigint[]>;
  swapExactTokensForTokens(
    amountIn: bigint,
    amountOutMin: bigint,
    path: string[],
    to: string,
    deadline: bigint
  ): Promise<bigint[]>;
}

interface IUniswapV2Factory extends Contract {
  getPair(tokenA: string, tokenB: string): Promise<string>;
  createPair(tokenA: string, tokenB: string): Promise<string>;
}

interface IUniswapV2Pair extends Contract {
  getReserves(): Promise<[bigint, bigint, number]>;
  token0(): Promise<string>;
  token1(): Promise<string>;
  sync(): Promise<void>;
  transfer(to: string, value: bigint): Promise<boolean>;
  transferFrom(from: string, to: string, value: bigint): Promise<boolean>;
}

describe("CrossDEXArbitrage", function () {
  let owner: SignerWithAddress;
  let wethWhale: SignerWithAddress;
  let usdcWhale: SignerWithAddress;
  let arbitrageExecutor: Contract;
  let arbitrageExecutorAddr: string;
  let weth: Contract;
  let usdc: Contract;
  let uniswapRouter: Contract;
  let sushiswapRouter: Contract;
  let uniswapPair: Contract;
  let sushiswapPair: Contract;
  let path: string[];
  let amountIn: bigint;

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
      value: ethers.parseEther("10"),
    });
    await owner.sendTransaction({
      to: usdcWhale.address,
      value: ethers.parseEther("10"),
    });

    // Get contract instances
    weth = await ethers.getContractAt("contracts/interfaces/IWETH.sol:IWETH", WETH);
    usdc = await ethers.getContractAt("@openzeppelin/contracts/token/ERC20/IERC20.sol:IERC20", USDC);
    uniswapRouter = await ethers.getContractAt("contracts/interfaces/IUniswapV2Router02.sol:IUniswapV2Router02", UNISWAP_V2_ROUTER);
    sushiswapRouter = await ethers.getContractAt("contracts/interfaces/IUniswapV2Router02.sol:IUniswapV2Router02", SUSHISWAP_V2_ROUTER);

    // Ensure whales have enough tokens
    const mintAmount = ethers.parseEther("1000"); // 1000 WETH
    const mintUsdcAmount = ethers.parseUnits("3000000", 6); // 3M USDC

    // Mint WETH by depositing ETH
    await (weth as any).connect(wethWhale).deposit({ value: mintAmount });

    // Get USDC balance
    const usdcBalance = await usdc.balanceOf(usdcWhale.address);
    console.log("\nUSDC whale balance:", ethers.formatUnits(usdcBalance, 6), "USDC");
  });

  beforeEach(async function () {
    // Deploy ArbitrageExecutor
    const ArbitrageExecutor = await ethers.getContractFactory("ArbitrageExecutor");
    arbitrageExecutor = await ArbitrageExecutor.deploy(
      UNISWAP_V2_ROUTER,
      SUSHISWAP_V2_ROUTER,
      owner.address
    );
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

    uniswapPair = await ethers.getContractAt("IUniswapV2Pair", uniswapPairAddr);
    sushiswapPair = await ethers.getContractAt("IUniswapV2Pair", sushiswapPairAddr);

    // Create price difference between DEXs
    // Uniswap: 1 WETH = 2500 USDC
    // Sushiswap: 1 WETH = 2450 USDC

    // First, remove all liquidity by transferring to a burn address
    const burnAddress = "0x000000000000000000000000000000000000dEaD";
    const [uniReserve0, uniReserve1] = await uniswapPair.getReserves();
    const [sushiReserve0, sushiReserve1] = await sushiswapPair.getReserves();

    // Get token order
    const uniToken0 = await uniswapPair.token0();
    const sushiToken0 = await sushiswapPair.token0();

    // Transfer existing liquidity to burn address
    await (weth as any).connect(wethWhale).transfer(burnAddress, uniReserve0);
    await (usdc as any).connect(usdcWhale).transfer(burnAddress, uniReserve1);
    await (weth as any).connect(wethWhale).transfer(burnAddress, sushiReserve0);
    await (usdc as any).connect(usdcWhale).transfer(burnAddress, sushiReserve1);

    // Add new liquidity based on token order
    if (uniToken0.toLowerCase() === WETH.toLowerCase()) {
      await (weth as any).connect(wethWhale).transfer(await uniswapPair.getAddress(), ethers.parseEther("100"));
      await (usdc as any).connect(usdcWhale).transfer(await uniswapPair.getAddress(), ethers.parseUnits("250000", 6));
    } else {
      await (usdc as any).connect(usdcWhale).transfer(await uniswapPair.getAddress(), ethers.parseUnits("250000", 6));
      await (weth as any).connect(wethWhale).transfer(await uniswapPair.getAddress(), ethers.parseEther("100"));
    }
    await uniswapPair.sync();

    if (sushiToken0.toLowerCase() === WETH.toLowerCase()) {
      await (weth as any).connect(wethWhale).transfer(await sushiswapPair.getAddress(), ethers.parseEther("100"));
      await (usdc as any).connect(usdcWhale).transfer(await sushiswapPair.getAddress(), ethers.parseUnits("245000", 6));
    } else {
      await (usdc as any).connect(usdcWhale).transfer(await sushiswapPair.getAddress(), ethers.parseUnits("245000", 6));
      await (weth as any).connect(wethWhale).transfer(await sushiswapPair.getAddress(), ethers.parseEther("100"));
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

    // Log initial balances
    const initialWethBalance = await weth.balanceOf(arbitrageExecutorAddr);
    const initialUsdcBalance = await usdc.balanceOf(arbitrageExecutorAddr);

    console.log("\nInitial contract balances:");
    console.log("Initial WETH balance:", ethers.formatEther(initialWethBalance));
    console.log("Initial USDC balance:", ethers.formatUnits(initialUsdcBalance, 6));

    // Fund the contract with initial tokens
    await (weth as any).connect(wethWhale).transfer(arbitrageExecutorAddr, ethers.parseEther("10"));
    await (usdc as any).connect(usdcWhale).transfer(arbitrageExecutorAddr, ethers.parseUnits("30000", 6));
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
      await arbitrageExecutor.withdraw(USDC, amount);
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
      expect(BigInt(uniFirst.toString()) > 0n || BigInt(sushiFirst.toString()) > 0n).to.be.true;
    });

    it("Should execute arbitrage trade when profitable", async function () {
      // Get initial balances
      const initialWethBalance = await weth.balanceOf(arbitrageExecutorAddr);
      const initialUsdcBalance = await usdc.balanceOf(arbitrageExecutorAddr);

      console.log("\nInitial balances:");
      console.log("Initial WETH balance:", ethers.formatEther(initialWethBalance));
      console.log("Initial USDC balance:", ethers.formatUnits(initialUsdcBalance, 6));

      // Execute arbitrage using Uniswap as source (higher price)
      await arbitrageExecutor.executeArbitrage(
        WETH,
        USDC,
        amountIn,
        path,
        UNISWAP_V2_ROUTER
      );

      // Get final balances
      const finalWethBalance = await weth.balanceOf(arbitrageExecutorAddr);
      const finalUsdcBalance = await usdc.balanceOf(arbitrageExecutorAddr);

      console.log("\nFinal balances:");
      console.log("Final WETH balance:", ethers.formatEther(finalWethBalance));
      console.log("Final USDC balance:", ethers.formatUnits(finalUsdcBalance, 6));

      // Calculate profit in USDC
      const profit = BigInt(finalUsdcBalance.toString()) - BigInt(initialUsdcBalance.toString());
      console.log("\nProfit:", ethers.formatUnits(profit, 6), "USDC");

      // Profit should be greater than zero
      expect(profit > 0n).to.be.true;
    });
  });
});
