import '@nomiclabs/hardhat-ethers';
import { task } from 'hardhat/config';
import { HardhatRuntimeEnvironment } from 'hardhat/types';
import { logger } from '../backend/api/utils/logger';

task('check-security', 'Runs security checks on deployed contracts')
  .setAction(async (args, hre: HardhatRuntimeEnvironment) => {
    await main(hre);
  });

async function checkContractOwnership(hre: HardhatRuntimeEnvironment) {
  const [deployer] = await hre.ethers.getSigners();
  logger.info('Checking contract ownership...', { deployer: deployer.address });

  const contracts = {
    FlashLoanService: await hre.ethers.getContractAt('FlashLoanService', process.env.FLASH_LOAN_ADDRESS!),
    ArbitrageExecutor: await hre.ethers.getContractAt('ArbitrageExecutor', process.env.ARBITRAGE_EXECUTOR_ADDRESS!),
    SecurityAdmin: await hre.ethers.getContractAt('SecurityAdmin', process.env.SECURITY_ADMIN_ADDRESS!)
  };

  for (const [name, contract] of Object.entries(contracts)) {
    const owner = await contract.owner();
    logger.info(`${name} owner:`, { owner, isDeployer: owner === deployer.address });
  }
}

async function checkSecurityRoles(hre: HardhatRuntimeEnvironment) {
  const securityAdmin = await hre.ethers.getContractAt('SecurityAdmin', process.env.SECURITY_ADMIN_ADDRESS!);
  const [deployer, ...accounts] = await hre.ethers.getSigners();

  logger.info('Checking security roles...');

  // Check operator status
  const isDeployerOperator = await securityAdmin.operators(deployer.address);
  logger.info('Deployer operator status:', { address: deployer.address, isOperator: isDeployerOperator });

  // Check other accounts
  for (const account of accounts.slice(0, 3)) {
    const isOperator = await securityAdmin.operators(account.address);
    logger.info('Account operator status:', { address: account.address, isOperator });
  }
}

async function checkContractParameters(hre: HardhatRuntimeEnvironment) {
  logger.info('Checking contract parameters...');

  const flashLoanService = await hre.ethers.getContractAt('FlashLoanService', process.env.FLASH_LOAN_ADDRESS!);
  const arbitrageExecutor = await hre.ethers.getContractAt('ArbitrageExecutor', process.env.ARBITRAGE_EXECUTOR_ADDRESS!);

  const params = {
    'FlashLoanService': {
      minProfitBps: await flashLoanService.minProfitBps(),
      flashLoanFee: await flashLoanService.FLASH_LOAN_FEE(),
      minFlashLoanAmount: await flashLoanService.minFlashLoanAmount(),
      maxFlashLoanAmount: await flashLoanService.maxFlashLoanAmount()
    },
    'ArbitrageExecutor': {
      minProfitBps: await arbitrageExecutor.minProfitBps(),
      minTradeAmount: await arbitrageExecutor.minTradeAmount(),
      maxTradeAmount: await arbitrageExecutor.maxTradeAmount()
    }
  };

  logger.info('Contract parameters:', params);
}

async function checkPauseStatus(hre: HardhatRuntimeEnvironment) {
  logger.info('Checking pause status...');

  const flashLoanService = await hre.ethers.getContractAt('FlashLoanService', process.env.FLASH_LOAN_ADDRESS!);
  const arbitrageExecutor = await hre.ethers.getContractAt('ArbitrageExecutor', process.env.ARBITRAGE_EXECUTOR_ADDRESS!);

  const status = {
    'FlashLoanService': await flashLoanService.paused(),
    'ArbitrageExecutor': await arbitrageExecutor.paused()
  };

  logger.info('Pause status:', status);
}

async function checkTokenApprovals(hre: HardhatRuntimeEnvironment) {
  logger.info('Checking token approvals...');

  const flashLoanService = await hre.ethers.getContractAt('FlashLoanService', process.env.FLASH_LOAN_ADDRESS!);
  const arbitrageExecutor = await hre.ethers.getContractAt('ArbitrageExecutor', process.env.ARBITRAGE_EXECUTOR_ADDRESS!);

  // Get token addresses from environment or config
  const tokens = {
    WETH: process.env.WETH_TOKEN_ADDRESS,
    USDC: process.env.USDC_TOKEN_ADDRESS,
    USDT: process.env.USDT_TOKEN_ADDRESS
  };

  for (const [symbol, address] of Object.entries(tokens)) {
    if (!address) continue;

    const token = await hre.ethers.getContractAt('IERC20', address);

    const approvals = {
      flashLoanService: await token.allowance(flashLoanService.target, arbitrageExecutor.target),
      arbitrageExecutor: await token.allowance(arbitrageExecutor.target, flashLoanService.target)
    };

    logger.info(`${symbol} approvals:`, approvals);
  }
}

async function main(hre: HardhatRuntimeEnvironment) {
  try {
    logger.info('Starting security checks...');

    await checkContractOwnership(hre);
    await checkSecurityRoles(hre);
    await checkContractParameters(hre);
    await checkPauseStatus(hre);
    await checkTokenApprovals(hre);

    logger.info('Security checks completed successfully');
  } catch (error) {
    logger.error('Security check failed:', error);
    process.exit(1);
  }
}

// Export the task
export default {};
