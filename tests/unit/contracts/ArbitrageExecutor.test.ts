import { expect } from 'chai';
import { Contract, Signer } from 'ethers';
import { ethers, network } from 'hardhat';
import { FORK_CONFIG, NETWORKS } from '../../../config/network';

describe('ArbitrageExecutor', () => {
  let owner: Signer;
  let flashLoanService: Contract;
  let arbitrageExecutor: Contract;
  let uniswapRouter: Contract;
  let sushiswapRouter: Contract;
  let aavePool: Contract;

  const TRADE_AMOUNT = ethers.parseEther('1');
  const WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
  const USDC_ADDRESS = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';

  before(async () => {
    // Reset fork to clean state
    await network.provider.request({
      method: "hardhat_reset",
      params: [{
        forking: {
          jsonRpcUrl: process.env.MAINNET_RPC_URL,
          blockNumber: FORK_CONFIG.blockNumber
        }
      }]
    });

    [owner] = await ethers.getSigners();

    // Connect to real mainnet contracts
    uniswapRouter = await ethers.getContractAt(
      'IUniswapV2Router02',
      NETWORKS.fork.contracts.uniswapV2Router
    );

    sushiswapRouter = await ethers.getContractAt(
      'IUniswapV2Router02',
      NETWORKS.fork.contracts.sushiswapRouter
    );

    aavePool = await ethers.getContractAt(
      'IPool',
      NETWORKS.fork.contracts.aavePool
    );

    // Deploy our contracts
    const FlashLoanService = await ethers.getContractFactory('FlashLoanService');
    flashLoanService = await FlashLoanService.deploy(
      NETWORKS.fork.contracts.aavePool,
      NETWORKS.fork.contracts.uniswapV2Router,
      NETWORKS.fork.contracts.sushiswapRouter
    );
    await flashLoanService.waitForDeployment();

    const ArbitrageExecutor = await ethers.getContractFactory('ArbitrageExecutor');
    arbitrageExecutor = await ArbitrageExecutor.deploy(
      NETWORKS.fork.contracts.uniswapV2Router,
      NETWORKS.fork.contracts.sushiswapRouter,
        await flashLoanService.getAddress()
    );
    await arbitrageExecutor.waitForDeployment();

    // Set up contract relationships
    await flashLoanService.setArbitrageExecutor(await arbitrageExecutor.getAddress());
  });

  beforeEach(async () => {
    // Take a snapshot before each test
    await network.provider.send("evm_snapshot", []);
  });

  afterEach(async () => {
    // Revert to snapshot after each test
    await network.provider.send("evm_revert", ["latest"]);
  });

  describe('Flash Loan Arbitrage', () => {
    it('should execute flash loan and arbitrage trade', async () => {
      // Get amounts out from both DEXes to find arbitrage opportunity
      const uniswapAmountOut = await uniswapRouter.getAmountsOut(
        TRADE_AMOUNT,
        [WETH_ADDRESS, USDC_ADDRESS]
      );

      const sushiswapAmountOut = await sushiswapRouter.getAmountsOut(
        TRADE_AMOUNT,
        [WETH_ADDRESS, USDC_ADDRESS]
      );

      // Calculate expected profit
      const expectedProfit = sushiswapAmountOut[1] - uniswapAmountOut[1];
      console.log('Expected profit:', ethers.formatUnits(expectedProfit, 6), 'USDC');

      // Execute arbitrage
      const tx = await arbitrageExecutor.executeArbitrage(
        WETH_ADDRESS,
        USDC_ADDRESS,
        TRADE_AMOUNT,
        0 // Min profit amount
      );

      const receipt = await tx.wait();
      expect(receipt.status).to.equal(1);

      // Verify flash loan was repaid
      const flashLoanBalance = await aavePool.getUserAccountData(await flashLoanService.getAddress());
      expect(flashLoanBalance.totalDebtBase).to.equal(0);
    });

    it('should revert if profit is below minimum', async () => {
      const minProfit = ethers.parseUnits('1000', 6); // 1000 USDC
      await arbitrageExecutor.setMinProfitAmount(minProfit);

      await expect(
        arbitrageExecutor.executeArbitrage(
          WETH_ADDRESS,
          USDC_ADDRESS,
          TRADE_AMOUNT,
          minProfit
        )
      ).to.be.revertedWith('Insufficient profit');
    });

    it('should handle gas price spikes', async () => {
      // Set very high gas price
      await network.provider.send("evm_setNextBlockBaseFeePerGas", [
        ethers.parseUnits('500', 'gwei').toString()
      ]);

      // Should revert due to high gas cost eating into profit
      await expect(
        arbitrageExecutor.executeArbitrage(
          WETH_ADDRESS,
          USDC_ADDRESS,
          TRADE_AMOUNT,
          0
        )
      ).to.be.revertedWith('Gas cost too high');
    });
  });
});
