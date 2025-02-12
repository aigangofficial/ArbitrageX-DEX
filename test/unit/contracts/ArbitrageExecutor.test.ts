import { expect } from 'chai';
import { ethers } from 'hardhat';
import { BigNumberish } from 'ethers';
import type {
  ArbitrageExecutor,
  FlashLoanService,
  MockToken,
  MockUniswapRouter,
  MockPool,
} from '../../typechain-types';
import { HardhatEthersSigner } from '@nomicfoundation/hardhat-ethers/signers';
import { Wallet } from 'ethers';

describe('ArbitrageExecutor', function () {
  let owner: HardhatEthersSigner;
  let user: HardhatEthersSigner;
  let mockToken: MockToken;
  let mockToken2: MockToken;
  let mockUniswapRouter: MockUniswapRouter;
  let mockSushiswapRouter: MockUniswapRouter;
  let mockPool: MockPool;
  let flashLoanService: FlashLoanService;
  let arbitrageExecutor: ArbitrageExecutor;
  const TEMP_ADDRESS = '0x0000000000000000000000000000000000000001';
  const TRADE_AMOUNT = ethers.parseEther('1'); // Use 1 token for test
  const LIQUIDITY = ethers.parseEther('1000000'); // 1M tokens for deep liquidity

  const INITIAL_LIQUIDITY = ethers.parseEther('1000');

  beforeEach(async function () {
    [owner, user] = await ethers.getSigners();

    // Deploy mock tokens first
    const MockToken = await ethers.getContractFactory('MockToken');
    mockToken = (await MockToken.deploy('Token A', 'TKA', 18)).connect(
      owner
    ) as unknown as MockToken;
    await mockToken.waitForDeployment();

    const MockToken2 = await ethers.getContractFactory('MockToken');
    mockToken2 = (await MockToken2.deploy('Token B', 'TKB', 18)).connect(
      owner
    ) as unknown as MockToken;
    await mockToken2.waitForDeployment();

    // Deploy mock routers with WETH address
    const MockUniswapRouter = await ethers.getContractFactory('MockUniswapRouter');
    mockUniswapRouter = (
      await MockUniswapRouter.deploy('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
    ).connect(owner) as unknown as MockUniswapRouter;
    await mockUniswapRouter.waitForDeployment();

    const MockSushiswapRouter = await ethers.getContractFactory('MockUniswapRouter');
    mockSushiswapRouter = (
      await MockSushiswapRouter.deploy('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
    ).connect(owner) as unknown as MockUniswapRouter;
    await mockSushiswapRouter.waitForDeployment();

    // Deploy mock pool with both tokens
    const MockPool = await ethers.getContractFactory('MockPool');
    mockPool = (
      await MockPool.deploy(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        await mockUniswapRouter.getAddress() // Use Uniswap router as provider
      )
    ).connect(owner) as unknown as MockPool;
    await mockPool.waitForDeployment();

    // Deploy flash loan service
    const FlashLoanService = await ethers.getContractFactory('FlashLoanService');
    flashLoanService = (await FlashLoanService.deploy(await mockPool.getAddress())).connect(
      owner
    ) as unknown as FlashLoanService;
    await flashLoanService.waitForDeployment();

    // Deploy arbitrage executor
    const ArbitrageExecutor = await ethers.getContractFactory('ArbitrageExecutor');
    arbitrageExecutor = (
      await ArbitrageExecutor.deploy(
        await mockUniswapRouter.getAddress(),
        await mockSushiswapRouter.getAddress(),
        await flashLoanService.getAddress()
      )
    ).connect(owner) as unknown as ArbitrageExecutor;
    await arbitrageExecutor.waitForDeployment();

    // Set max slippage to 1%
    await arbitrageExecutor.setMaxSlippage(100);

    // Mint tokens to owner for testing
    await mockToken.mint(owner.address, TRADE_AMOUNT);

    // Add liquidity to DEXes with proper ratios
    await mockToken.mint(await mockUniswapRouter.getAddress(), LIQUIDITY);
    await mockToken2.mint(await mockUniswapRouter.getAddress(), LIQUIDITY * 20n); // 20x for TokenB
    await mockToken.mint(await mockSushiswapRouter.getAddress(), LIQUIDITY);
    await mockToken2.mint(await mockSushiswapRouter.getAddress(), LIQUIDITY * 16n); // 16x for TokenB

    // Set token decimals
    await mockUniswapRouter.setTokenDecimals(await mockToken.getAddress(), 18);
    await mockUniswapRouter.setTokenDecimals(await mockToken2.getAddress(), 18);
    await mockSushiswapRouter.setTokenDecimals(await mockToken.getAddress(), 18);
    await mockSushiswapRouter.setTokenDecimals(await mockToken2.getAddress(), 18);

    // Set up exchange rates for profitable arbitrage
    await mockUniswapRouter.setExchangeRate(
      await mockToken.getAddress(),
      await mockToken2.getAddress(),
      ethers.parseEther('1000')
    );
    await mockSushiswapRouter.setExchangeRate(
      await mockToken2.getAddress(),
      await mockToken.getAddress(),
      ethers.parseEther('0.003')
    );
  });

  describe('Constructor', function () {
    it('Should set the correct addresses', async function () {
      expect(await arbitrageExecutor.uniswapRouter()).to.equal(
        await mockUniswapRouter.getAddress()
      );
      expect(await arbitrageExecutor.sushiswapRouter()).to.equal(
        await mockSushiswapRouter.getAddress()
      );
      expect(await arbitrageExecutor.flashLoanService()).to.equal(
        await flashLoanService.getAddress()
      );
    });
  });

  describe('Arbitrage Execution', function () {
    it('Should execute profitable arbitrage from Uniswap to SushiSwap', async function () {
      // Listen for DebugProfitCalculation events
      arbitrageExecutor.on(
        arbitrageExecutor.filters.DebugProfitCalculation(),
        (
          amountIn: BigNumberish,
          amountOut: BigNumberish,
          flashLoanFee: BigNumberish,
          minProfitAmount: BigNumberish,
          grossProfit: BigNumberish,
          isProfit: boolean
        ) => {
          console.log('\nProfit Calculation Debug:');
          console.log('Amount In:', ethers.formatEther(amountIn));
          console.log('Amount Out:', ethers.formatEther(amountOut));
          console.log('Flash Loan Fee:', ethers.formatEther(flashLoanFee));
          console.log('Min Profit Required:', ethers.formatEther(minProfitAmount));
          console.log('Gross Profit:', ethers.formatEther(grossProfit));
          console.log('Is Profitable:', isProfit);
        }
      );

      mockUniswapRouter.on(
        mockUniswapRouter.filters.DebugSwapCalculation(),
        (
          amountIn: BigNumberish,
          rate: BigNumberish,
          baseAmountOut: BigNumberish,
          afterFee: BigNumberish,
          afterImpact: BigNumberish,
          impactRatio: BigNumberish,
          impact: BigNumberish
        ) => {
          console.log('\nUniswap Swap Calculation:');
          console.log('Amount In:', ethers.formatEther(amountIn));
          console.log('Rate:', ethers.formatEther(rate));
          console.log('Base Amount Out:', ethers.formatEther(baseAmountOut));
          console.log('After Fee:', ethers.formatEther(afterFee));
          console.log('After Impact:', ethers.formatEther(afterImpact));
          console.log('Impact Ratio:', ethers.formatEther(impactRatio));
          console.log('Impact:', ethers.formatEther(impact));
        }
      );

      mockSushiswapRouter.on(
        mockSushiswapRouter.filters.DebugSwapCalculation(),
        (
          amountIn: BigNumberish,
          rate: BigNumberish,
          baseAmountOut: BigNumberish,
          afterFee: BigNumberish,
          afterImpact: BigNumberish,
          impactRatio: BigNumberish,
          impact: BigNumberish
        ) => {
          console.log('\nSushiSwap Swap Calculation:');
          console.log('Amount In:', ethers.formatEther(amountIn));
          console.log('Rate:', ethers.formatEther(rate));
          console.log('Base Amount Out:', ethers.formatEther(baseAmountOut));
          console.log('After Fee:', ethers.formatEther(afterFee));
          console.log('After Impact:', ethers.formatEther(afterImpact));
          console.log('Impact Ratio:', ethers.formatEther(impactRatio));
          console.log('Impact:', ethers.formatEther(impact));
        }
      );

      // Log expected amounts before executing swaps
      const path = [await mockToken.getAddress(), await mockToken2.getAddress()];
      const reversePath = [await mockToken2.getAddress(), await mockToken.getAddress()];

      console.log('\nExpected Amounts:');
      const uniExpected = await mockUniswapRouter.getAmountsOut(TRADE_AMOUNT, path);
      console.log('Expected Uniswap Out:', ethers.formatEther(uniExpected[1]));
      const sushiExpected = await mockSushiswapRouter.getAmountsOut(uniExpected[1], reversePath);
      console.log('Expected SushiSwap Out:', ethers.formatEther(sushiExpected[1]));
      console.log('Expected Profit:', ethers.formatEther(sushiExpected[1] - TRADE_AMOUNT));

      // Approve tokens for arbitrage executor and routers
      await mockToken
        .connect(owner)
        .approve(await arbitrageExecutor.getAddress(), ethers.MaxUint256);
      await mockToken2
        .connect(owner)
        .approve(await arbitrageExecutor.getAddress(), ethers.MaxUint256);
      await mockToken
        .connect(owner)
        .approve(await mockUniswapRouter.getAddress(), ethers.MaxUint256);
      await mockToken2
        .connect(owner)
        .approve(await mockUniswapRouter.getAddress(), ethers.MaxUint256);
      await mockToken
        .connect(owner)
        .approve(await mockSushiswapRouter.getAddress(), ethers.MaxUint256);
      await mockToken2
        .connect(owner)
        .approve(await mockSushiswapRouter.getAddress(), ethers.MaxUint256);

      // Execute the arbitrage with a smaller amount
      const initialBalance = await mockToken.balanceOf(owner.address);

      await expect(
        arbitrageExecutor.executeArbitrage(
          await mockToken.getAddress(),
          await mockToken2.getAddress(),
          TRADE_AMOUNT,
          true // Use Uniswap first
        )
      ).to.emit(arbitrageExecutor, 'ArbitrageExecuted');

      const finalBalance = await mockToken.balanceOf(owner.address);
      console.log('\nActual Results:');
      console.log('Initial Balance:', ethers.formatEther(initialBalance));
      console.log('Final Balance:', ethers.formatEther(finalBalance));
      console.log('Actual Profit:', ethers.formatEther(finalBalance - initialBalance));

      expect(finalBalance).to.be.gt(initialBalance);
    });

    it('Should fail if trade is not profitable', async function () {
      // Set up liquidity with proper ratios
      const LIQUIDITY = TRADE_AMOUNT * 100n;

      // Add liquidity to DEXes
      await mockToken.mint(await mockUniswapRouter.getAddress(), LIQUIDITY);
      await mockToken2.mint(await mockUniswapRouter.getAddress(), LIQUIDITY); // 1:1 ratio
      await mockToken.mint(await mockSushiswapRouter.getAddress(), LIQUIDITY);
      await mockToken2.mint(await mockSushiswapRouter.getAddress(), LIQUIDITY); // 1:1 ratio

      // Mint tokens to owner for the trade
      await mockToken.mint(owner.address, TRADE_AMOUNT * 2n);
      await mockToken2.mint(owner.address, TRADE_AMOUNT * 2n);

      // Set token decimals
      await mockUniswapRouter.setTokenDecimals(await mockToken.getAddress(), 18);
      await mockUniswapRouter.setTokenDecimals(await mockToken2.getAddress(), 18);
      await mockSushiswapRouter.setTokenDecimals(await mockToken.getAddress(), 18);
      await mockSushiswapRouter.setTokenDecimals(await mockToken2.getAddress(), 18);

      // Set exchange rates that would result in getting back exactly the input amount after fees
      // Each swap has a 0.3% fee, so we need 1.003 rate to compensate
      // Uniswap: 1A = 1.003B (compensates for first 0.3% fee)
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseEther('1.003')
      );

      // SushiSwap: 1B = 1.003A (compensates for second 0.3% fee)
      await mockSushiswapRouter.setExchangeRate(
        await mockToken2.getAddress(),
        await mockToken.getAddress(),
        ethers.parseEther('1.003')
      );

      // Approve tokens for arbitrage executor
      await mockToken
        .connect(owner)
        .approve(await arbitrageExecutor.getAddress(), ethers.MaxUint256);
      await mockToken2
        .connect(owner)
        .approve(await arbitrageExecutor.getAddress(), ethers.MaxUint256);
      await mockToken
        .connect(owner)
        .approve(await mockUniswapRouter.getAddress(), ethers.MaxUint256);
      await mockToken2
        .connect(owner)
        .approve(await mockUniswapRouter.getAddress(), ethers.MaxUint256);
      await mockToken
        .connect(owner)
        .approve(await mockSushiswapRouter.getAddress(), ethers.MaxUint256);
      await mockToken2
        .connect(owner)
        .approve(await mockSushiswapRouter.getAddress(), ethers.MaxUint256);

      // Execute the arbitrage - should fail due to unprofitable trade
      await expect(
        arbitrageExecutor.executeArbitrage(
          await mockToken.getAddress(),
          await mockToken2.getAddress(),
          TRADE_AMOUNT,
          true // Use Uniswap first
        )
      ).to.be.revertedWithCustomError(arbitrageExecutor, 'UnprofitableTrade');
    });
  });

  describe('Admin Functions', function () {
    it('Should allow owner to set max slippage', async function () {
      const newSlippage = 200; // 2%
      await arbitrageExecutor.setMaxSlippage(newSlippage);
      expect(await arbitrageExecutor.maxSlippage()).to.equal(newSlippage);
    });

    it('Should not allow non-owner to set max slippage', async function () {
      await expect(arbitrageExecutor.connect(user).setMaxSlippage(200)).to.be.revertedWith(
        'Ownable: caller is not the owner'
      );
    });
  });
});
