import { loadFixture } from '@nomicfoundation/hardhat-toolbox/network-helpers';
import { expect } from 'chai';
import { ethers } from 'hardhat';
import type {
  FlashLoanService,
  MockERC20,
  MockUniswapRouter,
  MockPool,
  ArbitrageExecutor,
} from '../../typechain-types';
import { HardhatEthersSigner } from '@nomicfoundation/hardhat-ethers/signers';
import { BytesLike } from 'ethers';
import hre from 'hardhat';

describe('FlashLoanService', function () {
  let mockTokenA: MockERC20;
  let mockTokenB: MockERC20;
  let mockPool: MockPool;
  let mockDex1: MockUniswapRouter;
  let mockDex2: MockUniswapRouter;
  let flashLoanService: FlashLoanService;
  let arbitrageExecutor: ArbitrageExecutor;
  let owner: HardhatEthersSigner;
  let user: HardhatEthersSigner;
  const liquidityAmount = ethers.parseEther('10000');

  beforeEach(async function () {
    [owner, user] = await ethers.getSigners();

    // Deploy mock tokens
    const MockToken = await ethers.getContractFactory('MockERC20');
    mockTokenA = (await MockToken.deploy('Token A', 'TKA')).connect(owner) as unknown as MockERC20;
    mockTokenB = (await MockToken.deploy('Token B', 'TKB')).connect(owner) as unknown as MockERC20;
    await mockTokenA.waitForDeployment();
    await mockTokenB.waitForDeployment();

    // Deploy mock DEXes
    const MockRouter = await ethers.getContractFactory('MockUniswapRouter');
    mockDex1 = (await MockRouter.deploy(await mockTokenA.getAddress())).connect(
      owner
    ) as unknown as MockUniswapRouter;
    mockDex2 = (await MockRouter.deploy(await mockTokenA.getAddress())).connect(
      owner
    ) as unknown as MockUniswapRouter;
    await mockDex1.waitForDeployment();
    await mockDex2.waitForDeployment();

    // Deploy mock pool
    const MockPool = await ethers.getContractFactory('MockPool');
    mockPool = (
      await MockPool.deploy(
        await mockTokenA.getAddress(),
        await mockTokenB.getAddress(),
        await mockDex1.getAddress() // Use DEX1 as provider
      )
    ).connect(owner) as unknown as MockPool;
    await mockPool.waitForDeployment();

    // Create a temporary mock address for arbitrageExecutor
    const tempArbitrageExecutor = ethers.Wallet.createRandom();

    // Deploy FlashLoanService with temporary arbitrageExecutor
    const FlashLoanService = await ethers.getContractFactory('FlashLoanService');
    flashLoanService = (await FlashLoanService.deploy(await mockPool.getAddress())).connect(
      owner
    ) as unknown as FlashLoanService;
    await flashLoanService.waitForDeployment();

    // Add mock pool as authorized flash loan provider
    await flashLoanService.addFlashLoanProvider(await mockPool.getAddress());

    // Deploy ArbitrageExecutor with correct constructor arguments
    const ArbitrageExecutor = await ethers.getContractFactory('ArbitrageExecutor');
    arbitrageExecutor = (
      await ArbitrageExecutor.deploy(
        await mockDex1.getAddress(),
        await mockDex2.getAddress(),
        await flashLoanService.getAddress()
      )
    ).connect(owner) as unknown as ArbitrageExecutor;
    await arbitrageExecutor.waitForDeployment();

    // Set the arbitrage executor address in the flash loan service
    await flashLoanService.setArbitrageExecutor(await arbitrageExecutor.getAddress());

    // Set minimum profit to 0 for testing
    await flashLoanService.setMinProfitBps(1);

    // Set exchange rates for DEX1 (Uniswap)
    await mockDex1.setExchangeRate(
      await mockTokenA.getAddress(),
      await mockTokenB.getAddress(),
      ethers.parseUnits('1', 18),
      ethers.parseUnits('1000', 18)
    );

    // Set exchange rates for DEX2 (SushiSwap) with a profitable difference
    await mockDex2.setExchangeRate(
      await mockTokenB.getAddress(),
      await mockTokenA.getAddress(),
      ethers.parseUnits('1000', 18),
      ethers.parseUnits('1.2', 18)
    );

    // Add sufficient liquidity to both DEXes
    const LARGE_LIQUIDITY = ethers.parseUnits('1000000', 18);

    await mockTokenA.mint(await mockDex1.getAddress(), LARGE_LIQUIDITY);
    await mockTokenB.mint(await mockDex1.getAddress(), LARGE_LIQUIDITY * 1000n);

    await mockTokenA.mint(await mockDex2.getAddress(), LARGE_LIQUIDITY);
    await mockTokenB.mint(await mockDex2.getAddress(), LARGE_LIQUIDITY * 1000n);
  });

  describe('Flash Loan Execution', function () {
    it('Should execute flash loan and arbitrage', async function () {
      const amountIn = ethers.parseEther('1'); // Base trade amount

      // Calculate liquidity based on input amount
      const LIQUIDITY_MULTIPLIER = 1000n;
      const dexLiquidity = amountIn * LIQUIDITY_MULTIPLIER;
      const poolLiquidity = dexLiquidity * 2n; // Pool needs more liquidity for flash loans

      // Add liquidity to the mock pool
      await mockTokenA.mint(await mockPool.getAddress(), poolLiquidity);
      await mockTokenB.mint(await mockPool.getAddress(), poolLiquidity);

      // Add liquidity to DEXes with proper ratios for profitable arbitrage
      await mockTokenA.mint(await mockDex1.getAddress(), dexLiquidity);
      await mockTokenB.mint(await mockDex1.getAddress(), dexLiquidity * 20n); // 20x price ratio
      await mockTokenA.mint(await mockDex2.getAddress(), dexLiquidity);
      await mockTokenB.mint(await mockDex2.getAddress(), dexLiquidity * 15n); // 15x price ratio

      // Mint tokens to the arbitrage executor for repayment
      const repaymentAmount = amountIn * 2n; // Extra tokens for fees
      await mockTokenA.mint(await arbitrageExecutor.getAddress(), repaymentAmount);
      await mockTokenB.mint(await arbitrageExecutor.getAddress(), repaymentAmount);

      // Approve tokens from arbitrage executor to pool for repayment
      await mockTokenA.connect(owner).approve(await mockPool.getAddress(), ethers.MaxUint256);
      await mockTokenB.connect(owner).approve(await mockPool.getAddress(), ethers.MaxUint256);
      await mockTokenA
        .connect(owner)
        .approve(await arbitrageExecutor.getAddress(), ethers.MaxUint256);
      await mockTokenB
        .connect(owner)
        .approve(await arbitrageExecutor.getAddress(), ethers.MaxUint256);

      // Set token decimals
      await mockDex1.setTokenDecimals(await mockTokenA.getAddress(), 18);
      await mockDex1.setTokenDecimals(await mockTokenB.getAddress(), 18);
      await mockDex2.setTokenDecimals(await mockTokenA.getAddress(), 18);
      await mockDex2.setTokenDecimals(await mockTokenB.getAddress(), 18);

      // Set exchange rates for a profitable arbitrage
      // DEX1: 1 TokenA = 1000 TokenB
      await mockDex1.setExchangeRate(
        await mockTokenA.getAddress(),
        await mockTokenB.getAddress(),
        ethers.parseEther('1'),
        ethers.parseEther('1000')
      );

      // DEX2: 1 TokenB = 0.002 TokenA (higher return rate)
      await mockDex2.setExchangeRate(
        await mockTokenB.getAddress(),
        await mockTokenA.getAddress(),
        ethers.parseEther('1000'),
        ethers.parseEther('2')
      );

      // Calculate expected profit
      const expectedProfitBps = 50n; // 0.5% minimum profit
      const minExpectedProfit = (amountIn * expectedProfitBps) / 10000n;

      // Set minimum profit requirement
      await flashLoanService.setMinProfitBps(1); // 0.01% minimum profit

      // Get initial balances
      const initialBalance = await mockTokenA.balanceOf(owner.address);

      const executionData = ethers.AbiCoder.defaultAbiCoder().encode(
        ['bool'],
        [true] // Use DEX1 (Uniswap) first
      );

      // Execute the flash loan
      const tx = await flashLoanService.executeArbitrage(
        await mockTokenA.getAddress(),
        await mockTokenB.getAddress(),
        amountIn,
        executionData
      );

      // Wait for transaction and get receipt for gas analysis
      const receipt = await tx.wait();
      expect(receipt).to.not.be.null;

      // Verify profit
      const finalBalance = await mockTokenA.balanceOf(owner.address);
      const actualProfit = finalBalance - initialBalance;

      expect(actualProfit).to.be.gt(minExpectedProfit);
      expect(actualProfit).to.be.gt(0);

      // Verify events
      await expect(tx)
        .to.emit(flashLoanService, 'FlashLoanExecuted')
        .withArgs(await mockTokenA.getAddress(), amountIn, owner.address, 9); // 9 = FLASH_LOAN_FEE
    });

    it('should revert on insufficient funds for repayment', async function () {
      const amountIn = ethers.parseEther('10');

      // Add minimal liquidity to the mock pool
      await mockTokenA.mint(await mockPool.getAddress(), amountIn);

      // Set token decimals
      await mockDex1.setTokenDecimals(await mockTokenA.getAddress(), 18);
      await mockDex1.setTokenDecimals(await mockTokenB.getAddress(), 18);
      await mockDex2.setTokenDecimals(await mockTokenA.getAddress(), 18);
      await mockDex2.setTokenDecimals(await mockTokenB.getAddress(), 18);

      // Set exchange rates that would result in a significant loss
      await mockDex1.setExchangeRate(
        await mockTokenA.getAddress(),
        await mockTokenB.getAddress(),
        ethers.parseUnits('0.1', 18) // 90% loss
      );
      await mockDex2.setExchangeRate(
        await mockTokenB.getAddress(),
        await mockTokenA.getAddress(),
        ethers.parseUnits('0.1', 18) // Another 90% loss
      );

      // Add minimal liquidity to DEXes
      await mockTokenA.mint(await mockDex1.getAddress(), amountIn);
      await mockTokenB.mint(await mockDex1.getAddress(), amountIn);
      await mockTokenA.mint(await mockDex2.getAddress(), amountIn);
      await mockTokenB.mint(await mockDex2.getAddress(), amountIn);

      // Approve tokens
      await mockTokenA
        .connect(owner)
        .approve(await flashLoanService.getAddress(), ethers.MaxUint256);
      await mockTokenB
        .connect(owner)
        .approve(await flashLoanService.getAddress(), ethers.MaxUint256);
      await mockTokenA
        .connect(owner)
        .approve(await arbitrageExecutor.getAddress(), ethers.MaxUint256);
      await mockTokenB
        .connect(owner)
        .approve(await arbitrageExecutor.getAddress(), ethers.MaxUint256);
      await mockTokenA.connect(owner).approve(await mockPool.getAddress(), ethers.MaxUint256);
      await mockTokenB.connect(owner).approve(await mockPool.getAddress(), ethers.MaxUint256);
      await mockTokenA.connect(owner).approve(await mockDex1.getAddress(), ethers.MaxUint256);
      await mockTokenB.connect(owner).approve(await mockDex1.getAddress(), ethers.MaxUint256);
      await mockTokenA.connect(owner).approve(await mockDex2.getAddress(), ethers.MaxUint256);
      await mockTokenB.connect(owner).approve(await mockDex2.getAddress(), ethers.MaxUint256);

      const executionData = ethers.AbiCoder.defaultAbiCoder().encode(
        ['bool'],
        [true] // Use Uniswap first
      );

      await expect(
        flashLoanService.executeArbitrage(
          await mockTokenA.getAddress(),
          await mockTokenB.getAddress(),
          amountIn,
          executionData
        )
      ).to.be.revertedWithCustomError(flashLoanService, 'UnprofitableTrade');
    });
  });

  describe('Admin Functions', function () {
    it('should allow owner to set minimum profit', async function () {
      const newMinProfit = 100; // 1%
      await expect(flashLoanService.setMinProfitBps(newMinProfit))
        .to.emit(flashLoanService, 'MinProfitBpsUpdated')
        .withArgs(1, newMinProfit); // Initial value is 1 bps (0.01%)
      expect(await flashLoanService.minProfitBps()).to.equal(newMinProfit);
    });

    it('should allow owner to withdraw tokens', async function () {
      const amount = ethers.parseEther('1');
      await mockTokenA.mint(await flashLoanService.getAddress(), amount);

      await expect(
        flashLoanService.withdrawToken(await mockTokenA.getAddress(), amount)
      ).to.changeTokenBalance(mockTokenA, owner, amount);
    });

    it('should not allow non-owner to set minimum profit', async function () {
      const newMinProfit = 100; // 1%
      await expect(flashLoanService.connect(user).setMinProfitBps(newMinProfit))
        .to.be.revertedWithCustomError(flashLoanService, 'OwnableUnauthorizedAccount')
        .withArgs(await user.getAddress());
    });
  });
});
