import { expect } from 'chai';
import { HardhatEthersSigner } from '@nomicfoundation/hardhat-ethers/signers';
import { loadFixture } from '@nomicfoundation/hardhat-toolbox/network-helpers';
import '@nomicfoundation/hardhat-ethers';
import { HardhatRuntimeEnvironment } from 'hardhat/types';
import hre from 'hardhat';
const { ethers } = hre as HardhatRuntimeEnvironment;
import type { Contract, ContractFactory } from 'ethers';
import type { 
  FlashLoanService,
  ArbitrageExecutor,
  MockPool,
  MockERC20,
  MockUniswapRouter
} from '../../typechain-types';

describe('Flash Loan Arbitrage', () => {
  let owner: HardhatEthersSigner;
  let mockPool: MockPool;
  let mockToken: MockERC20;
  let mockUniswapRouter: MockUniswapRouter;
  let mockSushiswapRouter: MockUniswapRouter;
  let flashLoanService: FlashLoanService;
  let arbitrageExecutor: ArbitrageExecutor;

  const INITIAL_LIQUIDITY = ethers.parseEther('1000');
  const FLASH_LOAN_AMOUNT = ethers.parseEther('100');

  async function deployContracts() {
    [owner] = await ethers.getSigners();
    
    // Deploy mock token with just name and symbol
    const MockToken = await ethers.getContractFactory('MockERC20');
    mockToken = await MockToken.deploy('Mock Token', 'MTK') as unknown as MockERC20;
    await mockToken.waitForDeployment();
    
    // Deploy mock pool with the same token for both addresses
    const MockPool = await ethers.getContractFactory('MockPool');
    mockPool = await MockPool.deploy(
      await mockToken.getAddress(),
      await mockToken.getAddress()
    ) as unknown as MockPool;
    await mockPool.waitForDeployment();
    
    // Deploy mock routers with WETH address
    const MockRouter = await ethers.getContractFactory('MockUniswapRouter');
    mockUniswapRouter = await MockRouter.deploy(await mockToken.getAddress()) as unknown as MockUniswapRouter;
    await mockUniswapRouter.waitForDeployment();
    mockSushiswapRouter = await MockRouter.deploy(await mockToken.getAddress()) as unknown as MockUniswapRouter;
    await mockSushiswapRouter.waitForDeployment();
    
    // Deploy main contracts
    const FlashLoanService = await ethers.getContractFactory('FlashLoanService');
    flashLoanService = await FlashLoanService.deploy(
      await mockPool.getAddress(),
      await mockUniswapRouter.getAddress(),
      await mockSushiswapRouter.getAddress()
    ) as unknown as FlashLoanService;
    await flashLoanService.waitForDeployment();
    
    const ArbitrageExecutor = await ethers.getContractFactory('ArbitrageExecutor');
    arbitrageExecutor = await ArbitrageExecutor.deploy(
      await mockUniswapRouter.getAddress(),
      await mockSushiswapRouter.getAddress(),
      await flashLoanService.getAddress()
    ) as unknown as ArbitrageExecutor;
    await arbitrageExecutor.waitForDeployment();

    // Setup initial state
    await mockToken.mint(await mockPool.getAddress(), INITIAL_LIQUIDITY);
    await mockToken.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
    await mockToken.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);

    // Setup exchange rates
    const baseRate = ethers.parseUnits('2000', 6); // 1 ETH = 2000 USDC
    await mockUniswapRouter.setExchangeRate(
      await mockToken.getAddress(),
      ethers.ZeroAddress,
      baseRate,
      INITIAL_LIQUIDITY,
      INITIAL_LIQUIDITY
    );
    await mockSushiswapRouter.setExchangeRate(
      await mockToken.getAddress(),
      ethers.ZeroAddress,
      baseRate * 98n / 100n, // 2% lower on Sushiswap
      INITIAL_LIQUIDITY,
      INITIAL_LIQUIDITY
    );

    return { owner, mockPool, mockToken, mockUniswapRouter, mockSushiswapRouter, flashLoanService, arbitrageExecutor };
  }

  beforeEach(async () => {
    const contracts = await loadFixture(deployContracts);
    owner = contracts.owner;
    mockPool = contracts.mockPool;
    mockToken = contracts.mockToken;
    mockUniswapRouter = contracts.mockUniswapRouter;
    mockSushiswapRouter = contracts.mockSushiswapRouter;
    flashLoanService = contracts.flashLoanService;
    arbitrageExecutor = contracts.arbitrageExecutor;
  });

  describe('Flash Loan Service', () => {
    it('should execute flash loan', async () => {
      // Deploy a second token for the test
      const MockToken2 = await ethers.getContractFactory('MockERC20');
      const mockToken2 = await MockToken2.deploy('Mock Token 2', 'MTK2') as unknown as MockERC20;
      await mockToken2.waitForDeployment();

      // Add liquidity to the mock pool
      await mockToken.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      
      // Set up profitable exchange rates
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseUnits('1.5', 18), // 50% higher rate
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY * 15n / 10n // 50% more liquidity
      );

      await mockSushiswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseUnits('1.1', 18), // 10% higher rate
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY * 11n / 10n // 10% more liquidity
      );

      // Set minimum profit to 1 bps (0.01%)
      await flashLoanService.setMinProfitBps(1);

      // Add liquidity to routers
      await mockToken.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY * 2n);
      await mockToken2.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY * 2n);
      await mockToken.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY * 2n);
      await mockToken2.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY * 2n);

      // Add liquidity to flash loan service for repayment
      await mockToken.mint(await flashLoanService.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.mint(await flashLoanService.getAddress(), FLASH_LOAN_AMOUNT * 2n);

      // Approve tokens for all contracts
      await mockToken.approve(await flashLoanService.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.approve(await flashLoanService.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken.approve(await mockUniswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.approve(await mockUniswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken.approve(await mockSushiswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.approve(await mockSushiswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);

      // Execute flash loan
      await expect(flashLoanService.executeArbitrage(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        FLASH_LOAN_AMOUNT
      )).to.emit(flashLoanService, 'FlashLoanExecuted');
    });

    it('should revert on unprofitable trade', async () => {
      // Deploy a second token for the test
      const MockToken2 = await ethers.getContractFactory('MockERC20');
      const mockToken2 = await MockToken2.deploy('Mock Token 2', 'MTK2') as unknown as MockERC20;
      await mockToken2.waitForDeployment();

      // Set equal rates to make trade unprofitable
      const baseRate = ethers.parseUnits('2000', 6);
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        baseRate,
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY
      );
      await mockSushiswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        baseRate,
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY
      );

      // Add liquidity to the mock pool
      await mockToken.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);

      await expect(
        arbitrageExecutor.executeArbitrage(
          await mockToken.getAddress(),
          await mockToken2.getAddress(),
          FLASH_LOAN_AMOUNT,
          true
        )
      ).to.be.revertedWithCustomError(arbitrageExecutor, "UnprofitableTrade");
    });
  });

  describe('Arbitrage Executor', () => {
    it('should execute arbitrage trade', async () => {
      // Deploy a second token for the test
      const MockToken2 = await ethers.getContractFactory('MockERC20');
      const mockToken2 = await MockToken2.deploy('Mock Token 2', 'MTK2') as unknown as MockERC20;
      await mockToken2.waitForDeployment();

      // Set up profitable exchange rates
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseUnits('1.5', 18), // 50% higher rate
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY * 15n / 10n // 50% more liquidity
      );

      await mockSushiswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseUnits('1.1', 18), // 10% higher rate
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY * 11n / 10n // 10% more liquidity
      );

      // Set minimum profit to 1 bps (0.01%)
      await flashLoanService.setMinProfitBps(1);

      // Add liquidity to routers
      await mockToken.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY * 2n);
      await mockToken2.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY * 2n);
      await mockToken.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY * 2n);
      await mockToken2.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY * 2n);

      // Add liquidity to flash loan service for repayment
      await mockToken.mint(await flashLoanService.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.mint(await flashLoanService.getAddress(), FLASH_LOAN_AMOUNT * 2n);

      // Approve tokens for all contracts
      await mockToken.approve(await arbitrageExecutor.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.approve(await arbitrageExecutor.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken.approve(await mockUniswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.approve(await mockUniswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken.approve(await mockSushiswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.approve(await mockSushiswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);

      // Execute arbitrage
      await expect(arbitrageExecutor.executeArbitrage(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        FLASH_LOAN_AMOUNT,
        true
      )).not.to.be.reverted;
    });

    it('should revert on unprofitable trade', async () => {
      // Deploy a second token for the test
      const MockToken2 = await ethers.getContractFactory('MockERC20');
      const mockToken2 = await MockToken2.deploy('Mock Token 2', 'MTK2') as unknown as MockERC20;
      await mockToken2.waitForDeployment();

      // Set equal rates to make trade unprofitable
      const baseRate = ethers.parseUnits('2000', 6);
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        baseRate,
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY
      );
      await mockSushiswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        baseRate,
        INITIAL_LIQUIDITY,
        INITIAL_LIQUIDITY
      );

      // Add liquidity to the mock pool
      await mockToken.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);

      await expect(
        arbitrageExecutor.executeArbitrage(
          await mockToken.getAddress(),
          await mockToken2.getAddress(),
          FLASH_LOAN_AMOUNT,
          true
        )
      ).to.be.revertedWithCustomError(arbitrageExecutor, "UnprofitableTrade");
    });
  });
}); 