import { expect } from 'chai';
import { ethers } from 'hardhat';
import { MockPool, MockToken } from '../../../../typechain-types';
import { HardhatEthersSigner } from '@nomicfoundation/hardhat-ethers/signers';

describe('MockPool', () => {
  let mockPool: MockPool;
  let mockTokenA: MockToken;
  let mockTokenB: MockToken;
  let owner: HardhatEthersSigner;
  let user: HardhatEthersSigner;
  const INITIAL_LIQUIDITY = ethers.parseEther('1000');
  const FLASH_LOAN_AMOUNT = ethers.parseEther('100');

  beforeEach(async function () {
    [owner, user] = await ethers.getSigners();

    // Deploy mock tokens
    const MockToken = await ethers.getContractFactory('MockToken');
    mockTokenA = await MockToken.deploy('Token A', 'TKA', 18);
    mockTokenB = await MockToken.deploy('Token B', 'TKB', 18);
    await mockTokenA.waitForDeployment();
    await mockTokenB.waitForDeployment();

    // Deploy mock pool
    const MockPool = await ethers.getContractFactory('MockPool');
    mockPool = await MockPool.deploy(
      await mockTokenA.getAddress(),
      await mockTokenB.getAddress(),
      owner.address
    );
    await mockPool.waitForDeployment();

    // Add initial liquidity to the pool
    await mockTokenA.mint(await mockPool.getAddress(), INITIAL_LIQUIDITY);
    await mockTokenB.mint(await mockPool.getAddress(), INITIAL_LIQUIDITY);
  });

  describe('Flash Loan Functionality', function () {
    it('should execute flash loan with proper repayment', async function () {
      // Create a receiver contract that will repay
      const MockReceiver = await ethers.getContractFactory('MockFlashLoanReceiver');
      const receiver = await MockReceiver.deploy();
      await receiver.waitForDeployment();

      // Fund the receiver for repayment
      const amount = FLASH_LOAN_AMOUNT;
      const fee = (amount * 9n) / 10000n; // 0.09% fee
      const totalRepayment = amount + fee;
      await mockTokenA.mint(await receiver.getAddress(), totalRepayment);

      // Prepare flash loan parameters
      const assets = [await mockTokenA.getAddress()];
      const amounts = [amount];
      const modes = [0];

      await expect(
        mockPool.flashLoan(
          await receiver.getAddress(),
          assets,
          amounts,
          modes,
          owner.address,
          '0x',
          0
        )
      ).to.not.be.reverted;

      // Verify pool balance includes the fee
      const finalBalance = await mockTokenA.balanceOf(await mockPool.getAddress());
      expect(finalBalance).to.equal(INITIAL_LIQUIDITY + fee);
    });

    it('should revert if loan is not repaid', async function () {
      // Create a receiver contract that won't have enough funds to repay
      const MockReceiver = await ethers.getContractFactory('MockFlashLoanReceiver');
      const receiver = await MockReceiver.deploy();
      await receiver.waitForDeployment();

      // Don't fund the receiver

      // Prepare flash loan parameters
      const assets = [await mockTokenA.getAddress()];
      const amounts = [FLASH_LOAN_AMOUNT];
      const modes = [0];

      await expect(
        mockPool.flashLoan(
          await receiver.getAddress(),
          assets,
          amounts,
          modes,
          owner.address,
          '0x',
          0
        )
      ).to.be.revertedWith('Flash loan not repaid');
    });

    it('should charge correct flash loan fee', async function () {
      const amount = ethers.parseEther('100');
      const expectedFee = (amount * 9n) / 10000n; // 0.09% fee

      // Create a receiver that will repay with fee
      const MockReceiver = await ethers.getContractFactory('MockFlashLoanReceiver');
      const receiver = await MockReceiver.deploy();
      await receiver.waitForDeployment();

      // Fund the receiver with amount + fee
      await mockTokenA.mint(await receiver.getAddress(), amount + expectedFee);

      const assets = [await mockTokenA.getAddress()];
      const amounts = [amount];
      const modes = [0];

      // Execute flash loan
      await mockPool.flashLoan(
        await receiver.getAddress(),
        assets,
        amounts,
        modes,
        owner.address,
        '0x',
        0
      );

      // Verify the pool received the fee
      const poolBalance = await mockTokenA.balanceOf(await mockPool.getAddress());
      expect(poolBalance).to.equal(INITIAL_LIQUIDITY + expectedFee);
    });
  });

  describe('Pool Management', () => {
    it('should track token balances correctly', async () => {
      const balanceA = await mockTokenA.balanceOf(await mockPool.getAddress());
      const balanceB = await mockTokenB.balanceOf(await mockPool.getAddress());

      expect(balanceA).to.equal(INITIAL_LIQUIDITY);
      expect(balanceB).to.equal(INITIAL_LIQUIDITY);
    });

    it('should allow supply and withdrawal', async () => {
      const supplyAmount = ethers.parseEther('100');
      await mockTokenA.mint(owner.address, supplyAmount);
      await mockTokenA.approve(await mockPool.getAddress(), supplyAmount);

      // Supply tokens
      await mockPool.supply(await mockTokenA.getAddress(), supplyAmount, owner.address, 0);
      expect(await mockPool.balances(owner.address)).to.equal(supplyAmount);

      // Withdraw tokens
      await mockPool.withdraw(await mockTokenA.getAddress(), supplyAmount, owner.address);
      expect(await mockPool.balances(owner.address)).to.equal(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero amount flash loans', async () => {
      const MockReceiver = await ethers.getContractFactory('MockFlashLoanReceiver');
      const receiver = await MockReceiver.deploy();
      await receiver.waitForDeployment();

      const assets = [await mockTokenA.getAddress()];
      const amounts = [0];
      const modes = [0];

      await expect(
        mockPool.flashLoan(
          await receiver.getAddress(),
          assets,
          amounts,
          modes,
          owner.address,
          '0x',
          0
        )
      ).to.be.revertedWith('Invalid amount');
    });

    it('should handle multiple flash loans in the same transaction', async () => {
      const MockReceiver = await ethers.getContractFactory('MockFlashLoanReceiver');
      const receiver = await MockReceiver.deploy();
      await receiver.waitForDeployment();

      // Fund the receiver
      await mockTokenA.mint(await receiver.getAddress(), FLASH_LOAN_AMOUNT * 4n);
      await mockTokenB.mint(await receiver.getAddress(), FLASH_LOAN_AMOUNT * 4n);

      const assets = [await mockTokenA.getAddress(), await mockTokenB.getAddress()];
      const amounts = [FLASH_LOAN_AMOUNT, FLASH_LOAN_AMOUNT];
      const modes = [0, 0];

      await expect(
        mockPool.flashLoan(
          await receiver.getAddress(),
          assets,
          amounts,
          modes,
          owner.address,
          '0x',
          0
        )
      ).to.be.revertedWith('Only single asset flash loans supported in mock');
    });

    it('should validate input parameters', async () => {
      const MockReceiver = await ethers.getContractFactory('MockFlashLoanReceiver');
      const receiver = await MockReceiver.deploy();
      await receiver.waitForDeployment();

      // Mismatched arrays length
      const assets = [await mockTokenA.getAddress()];
      const amounts = [FLASH_LOAN_AMOUNT, FLASH_LOAN_AMOUNT];
      const modes = [0];

      await expect(
        mockPool.flashLoan(
          await receiver.getAddress(),
          assets,
          amounts,
          modes,
          owner.address,
          '0x',
          0
        )
      ).to.be.revertedWith('Array lengths must match');
    });
  });
});
