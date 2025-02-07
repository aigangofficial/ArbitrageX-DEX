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
  let mockToken2: MockERC20;
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

    // Deploy second mock token
    const MockToken2 = await ethers.getContractFactory('MockERC20');
    const mockToken2 = await MockToken2.deploy('Mock Token 2', 'MTK2') as unknown as MockERC20;
    await mockToken2.waitForDeployment();
    
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
    await mockToken2.mint(await mockPool.getAddress(), INITIAL_LIQUIDITY);
    await mockToken2.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
    await mockToken2.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);

    // Setup exchange rates
    await mockUniswapRouter.setExchangeRate(
      await mockToken.getAddress(),
      await mockToken2.getAddress(),
      ethers.parseUnits('1.0', 18)
    );
    await mockSushiswapRouter.setExchangeRate(
      await mockToken2.getAddress(),
      await mockToken.getAddress(),
      ethers.parseUnits('1.2', 18)
    );

    // Set reverse rates
    await mockUniswapRouter.setExchangeRate(
      await mockToken2.getAddress(),
      await mockToken.getAddress(),
      ethers.parseUnits('1.0', 18)
    );

    await mockSushiswapRouter.setExchangeRate(
      await mockToken.getAddress(),
      await mockToken2.getAddress(),
      ethers.parseUnits('0.8', 18)
    );

    return { owner, mockPool, mockToken, mockToken2, mockUniswapRouter, mockSushiswapRouter, flashLoanService, arbitrageExecutor };
  }

  beforeEach(async () => {
    const contracts = await loadFixture(deployContracts);
    owner = contracts.owner;
    mockPool = contracts.mockPool;
    mockToken = contracts.mockToken;
    mockToken2 = contracts.mockToken2;
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

      // Add high liquidity to the mock pool
      await mockToken.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 20n);
      await mockToken2.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 20n);
      
      // Add very high liquidity to routers to minimize price impact
      const ROUTER_LIQUIDITY = FLASH_LOAN_AMOUNT * 1000n; // 1000x flash loan amount
      await mockToken.mint(await mockUniswapRouter.getAddress(), ROUTER_LIQUIDITY);
      await mockToken2.mint(await mockUniswapRouter.getAddress(), ROUTER_LIQUIDITY);
      await mockToken.mint(await mockSushiswapRouter.getAddress(), ROUTER_LIQUIDITY);
      await mockToken2.mint(await mockSushiswapRouter.getAddress(), ROUTER_LIQUIDITY);

      // Set token decimals to 18 for both tokens
      await mockUniswapRouter.setTokenDecimals(await mockToken.getAddress(), 18);
      await mockUniswapRouter.setTokenDecimals(await mockToken2.getAddress(), 18);
      await mockSushiswapRouter.setTokenDecimals(await mockToken.getAddress(), 18);
      await mockSushiswapRouter.setTokenDecimals(await mockToken2.getAddress(), 18);

      // Set up highly profitable exchange rates
      // On Uniswap: 1 TokenA = 1 TokenB
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseUnits('1.0', 18)
      );

      // On Sushiswap: 1 TokenB = 3 TokenA (200% profit opportunity before fees)
      await mockSushiswapRouter.setExchangeRate(
        await mockToken2.getAddress(),
        await mockToken.getAddress(),
        ethers.parseUnits('3.0', 18)
      );

      // Lower minimum profit requirement
      await flashLoanService.setMinProfitBps(1); // 0.01% minimum profit

      // Approve tokens for all contracts with unlimited amounts
      await mockToken.connect(owner).approve(await flashLoanService.getAddress(), ethers.MaxUint256);
      await mockToken2.connect(owner).approve(await flashLoanService.getAddress(), ethers.MaxUint256);
      await mockToken.connect(owner).approve(await mockUniswapRouter.getAddress(), ethers.MaxUint256);
      await mockToken2.connect(owner).approve(await mockUniswapRouter.getAddress(), ethers.MaxUint256);
      await mockToken.connect(owner).approve(await mockSushiswapRouter.getAddress(), ethers.MaxUint256);
      await mockToken2.connect(owner).approve(await mockSushiswapRouter.getAddress(), ethers.MaxUint256);

      // Execute flash loan
      await expect(flashLoanService.executeArbitrage(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        FLASH_LOAN_AMOUNT
      )).to.emit(flashLoanService, 'FlashLoanExecuted');
    });

    it('should revert on unprofitable trade', async () => {
      // Deploy a second token for the test
      const MockToken3 = await ethers.getContractFactory('MockERC20');
      const mockToken3 = await MockToken3.deploy('Mock Token 3', 'MTK3') as unknown as MockERC20;
      await mockToken3.waitForDeployment();

      // Set equal rates to make trade unprofitable
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseEther('1.0')
      );
      await mockSushiswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseEther('1.0')
      );

      // Add liquidity to the mock pool
      await mockToken.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken3.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);

      await expect(
        flashLoanService.executeArbitrage(
          await mockToken.getAddress(),
          await mockToken2.getAddress(),
          FLASH_LOAN_AMOUNT
        )
      ).to.be.revertedWithCustomError(flashLoanService, "InsufficientFundsForRepayment");
    });
  });

  describe('Arbitrage Executor', () => {
    it('should execute arbitrage trade', async () => {
      // Deploy a second token for the test
      const MockToken3 = await ethers.getContractFactory('MockERC20');
      const mockToken3 = await MockToken3.deploy('Mock Token 3', 'MTK3') as unknown as MockERC20;
      await mockToken3.waitForDeployment();

      // Add liquidity to routers
      await mockToken.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken2.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken3.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken2.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken3.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);

      // Set up profitable exchange rates with high enough spread to cover fees
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseUnits('1.0', 18)  // 1:1 on Uniswap
      );

      await mockSushiswapRouter.setExchangeRate(
        await mockToken2.getAddress(),
        await mockToken.getAddress(),
        ethers.parseUnits('1.5', 18)  // 50% higher return on Sushiswap
      );

      // Add extra liquidity to minimize price impact
      await mockToken.mint(await mockUniswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 100n);
      await mockToken2.mint(await mockUniswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 100n);
      await mockToken.mint(await mockSushiswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 100n);
      await mockToken2.mint(await mockSushiswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 100n);

      // Lower minimum profit requirement
      await flashLoanService.setMinProfitBps(1);  // 0.01% minimum profit

      // Approve tokens for all contracts
      await mockToken.approve(await arbitrageExecutor.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.approve(await arbitrageExecutor.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken3.approve(await arbitrageExecutor.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken.approve(await mockUniswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.approve(await mockUniswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken3.approve(await mockUniswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken.approve(await mockSushiswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.approve(await mockSushiswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken3.approve(await mockSushiswapRouter.getAddress(), FLASH_LOAN_AMOUNT * 2n);

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
      const MockToken3 = await ethers.getContractFactory('MockERC20');
      const mockToken3 = await MockToken3.deploy('Mock Token 3', 'MTK3') as unknown as MockERC20;
      await mockToken3.waitForDeployment();

      // Set equal rates to make trade unprofitable
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseUnits('1.0', 18)
      );
      await mockSushiswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseUnits('1.0', 18)
      );

      // Add liquidity to routers
      await mockToken.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken2.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken2.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);

      // Approve tokens
      await mockToken.approve(await arbitrageExecutor.getAddress(), FLASH_LOAN_AMOUNT);
      await mockToken2.approve(await arbitrageExecutor.getAddress(), FLASH_LOAN_AMOUNT);

      await expect(
        arbitrageExecutor.executeArbitrage(
          await mockToken.getAddress(),
          await mockToken2.getAddress(),
          FLASH_LOAN_AMOUNT,
          true
        )
      ).to.be.revertedWithCustomError(arbitrageExecutor, "UnprofitableTrade");
    });

    it('should revert on insufficient funds for repayment', async () => {
      // Deploy a second token for the test
      const MockToken3 = await ethers.getContractFactory('MockERC20');
      const mockToken3 = await MockToken3.deploy('Mock Token 3', 'MTK3') as unknown as MockERC20;
      await mockToken3.waitForDeployment();

      // Set up exchange rates that would make the trade profitable
      await mockUniswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseEther('1.0005')
      );

      await mockSushiswapRouter.setExchangeRate(
        await mockToken.getAddress(),
        await mockToken2.getAddress(),
        ethers.parseEther('1.0005')
      );

      // Add liquidity to the mock pool
      await mockToken.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken2.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);
      await mockToken3.mint(await mockPool.getAddress(), FLASH_LOAN_AMOUNT * 2n);

      // Add liquidity to routers but NOT to flash loan service
      await mockToken.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken2.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken3.mint(await mockUniswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken2.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);
      await mockToken3.mint(await mockSushiswapRouter.getAddress(), INITIAL_LIQUIDITY);

      // Set minimum profit to 1 bps (0.01%)
      await flashLoanService.setMinProfitBps(1);

      await expect(
        flashLoanService.executeArbitrage(
          await mockToken.getAddress(),
          await mockToken2.getAddress(),
          FLASH_LOAN_AMOUNT
        )
      ).to.be.revertedWithCustomError(flashLoanService, "InsufficientFundsForRepayment");
    });
  });
}); 