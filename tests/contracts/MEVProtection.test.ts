import { expect } from "chai";
import { ethers } from "hardhat";
import { time, loadFixture } from "@nomicfoundation/hardhat-network-helpers";

// Mainnet contract addresses
const AAVE_V3_POOL_ADDRESS = "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9";
const WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";
const USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";
const UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
const SUSHISWAP_V2_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F";

describe("MEV Protection", function () {
  // We define a fixture to reuse the same setup in every test
  async function deployMEVProtectionFixture() {
    const [owner, user1, user2, relayerSigner] = await ethers.getSigners();

    // Get real tokens from mainnet fork - using fully qualified name
    const weth = await ethers.getContractAt("@openzeppelin/contracts/token/ERC20/IERC20.sol:IERC20", WETH_ADDRESS) as any;
    const usdc = await ethers.getContractAt("@openzeppelin/contracts/token/ERC20/IERC20.sol:IERC20", USDC_ADDRESS) as any;

    // Deploy mock Flashbots relayer (still needed as we can't test real Flashbots)
    const mockFlashbotsRelayerFactory = await ethers.getContractFactory("MockFlashbotsRelayer");
    const mockFlashbotsRelayer = await mockFlashbotsRelayerFactory.deploy() as any;

    // Deploy MEV Protection
    const mevProtectionFactory = await ethers.getContractFactory("MEVProtection");
    const mevProtection = await mevProtectionFactory.deploy(await mockFlashbotsRelayer.getAddress()) as any;

    // Deploy real ArbitrageExecutor with required constructor arguments
    const arbitrageExecutorFactory = await ethers.getContractFactory("ArbitrageExecutor");
    const arbitrageExecutor = await arbitrageExecutorFactory.deploy(
      UNISWAP_V2_ROUTER,
      SUSHISWAP_V2_ROUTER,
      ethers.parseEther("0.01"), // minProfitAmount
      await mevProtection.getAddress()
    ) as any;

    // Get the real Aave V3 Pool from mainnet fork - using fully qualified name
    const aavePool = await ethers.getContractAt("contracts/interfaces/aave/IPool.sol:IPool", AAVE_V3_POOL_ADDRESS) as any;

    // Deploy FlashLoanService with real contracts
    const flashLoanServiceFactory = await ethers.getContractFactory("FlashLoanService");
    const flashLoanService = await flashLoanServiceFactory.deploy(
      await aavePool.getAddress(),
      await arbitrageExecutor.getAddress(),
      ethers.parseEther("0.1"),  // minAmount
      ethers.parseEther("10"),   // maxAmount
      await mevProtection.getAddress()
    ) as any;

    // Set up initial state
    await flashLoanService.updateTokenSupport(await weth.getAddress(), true);
    await flashLoanService.updateTokenSupport(await usdc.getAddress(), true);
    await flashLoanService.setFlashbotsRelayer(await mockFlashbotsRelayer.getAddress());

    // Fund the user with some ETH to pay for gas
    await owner.sendTransaction({
      to: user1.address,
      value: ethers.parseEther("1.0")
    });

    return { 
      flashLoanService, 
      mevProtection, 
      aavePool, 
      arbitrageExecutor, 
      weth, 
      usdc, 
      mockFlashbotsRelayer,
      owner, 
      user1, 
      user2, 
      relayerSigner 
    };
  }

  describe("Commit-Reveal Scheme", function () {
    it("Should allow creating a commitment", async function () {
      const { flashLoanService, weth, user1 } = await loadFixture(deployMEVProtectionFixture);
      
      const amount = ethers.parseEther("1");
      const secret = ethers.keccak256(ethers.toUtf8Bytes("my secret"));
      
      // Create commitment
      const tx = await flashLoanService.connect(user1).commitFlashLoanTransaction(
        await weth.getAddress(),
        amount,
        secret
      );
      
      const receipt = await tx.wait();
      const event = receipt?.logs.find((log: any) => {
        try {
          const parsedLog = flashLoanService.interface.parseLog(log);
          return parsedLog?.name === "TransactionCommitted";
        } catch (e) {
          return false;
        }
      });
      
      expect(event).to.not.be.undefined;
      const parsedEvent = flashLoanService.interface.parseLog(event);
      expect(parsedEvent?.args.commitmentHash).to.not.be.undefined;
      expect(parsedEvent?.args.blockNumber).to.not.be.undefined;
    });

    it("Should reject execution if commitment is too recent", async function () {
      const { flashLoanService, weth, user1 } = await loadFixture(deployMEVProtectionFixture);
      
      // Set commitment age parameters
      await flashLoanService.setCommitmentAgeParams(3, 10); // Min age: 3 blocks, Max age: 10 blocks
      
      const amount = ethers.parseEther("1");
      const secret = ethers.keccak256(ethers.toUtf8Bytes("my secret"));
      
      // Create commitment
      const tx = await flashLoanService.connect(user1).commitFlashLoanTransaction(
        await weth.getAddress(),
        amount,
        secret
      );
      
      const receipt = await tx.wait();
      const event = receipt?.logs.find((log: any) => {
        try {
          const parsedLog = flashLoanService.interface.parseLog(log);
          return parsedLog?.name === "TransactionCommitted";
        } catch (e) {
          return false;
        }
      });
      
      const parsedEvent = flashLoanService.interface.parseLog(event);
      const commitmentHash = parsedEvent?.args.commitmentHash;
      
      // Enable test mode to avoid actual flash loan execution
      await flashLoanService.toggleTestMode(true);
      
      // Try to execute immediately (should fail)
      await expect(
        flashLoanService.connect(user1).executeFlashLoanWithMEVProtection(
          await weth.getAddress(),
          amount,
          secret,
          commitmentHash
        )
      ).to.be.revertedWithCustomError(flashLoanService, "CommitmentNotReady");
    });

    it("Should allow execution after minimum blocks have passed", async function () {
      const { flashLoanService, weth, user1 } = await loadFixture(deployMEVProtectionFixture);
      
      const amount = ethers.parseEther("1");
      const secret = ethers.keccak256(ethers.toUtf8Bytes("my secret"));
      
      // Create commitment
      const tx = await flashLoanService.connect(user1).commitFlashLoanTransaction(
        await weth.getAddress(),
        amount,
        secret
      );
      
      const receipt = await tx.wait();
      const event = receipt?.logs.find((log: any) => {
        try {
          const parsedLog = flashLoanService.interface.parseLog(log);
          return parsedLog?.name === "TransactionCommitted";
        } catch (e) {
          return false;
        }
      });
      
      const parsedEvent = flashLoanService.interface.parseLog(event);
      const commitmentHash = parsedEvent?.args.commitmentHash;
      
      // Mine blocks to pass the minimum age
      await time.increase(2); // Advance time
      await time.advanceBlock(); // Mine a block
      await time.advanceBlock(); // Mine another block
      
      // Mock the flash loan execution to avoid actual execution
      await flashLoanService.toggleMEVProtection(false);
      await flashLoanService.toggleMEVProtection(true);
      await flashLoanService.toggleTestMode(true);
      
      // Execute with valid commitment
      const execTx = await flashLoanService.connect(user1).executeFlashLoanWithMEVProtection(
        await weth.getAddress(),
        amount,
        secret,
        commitmentHash
      );
      
      const execReceipt = await execTx.wait();
      const revealEvent = execReceipt?.logs.find((log: any) => {
        try {
          const parsedLog = flashLoanService.interface.parseLog(log);
          return parsedLog?.name === "CommitmentRevealed";
        } catch (e) {
          return false;
        }
      });
      
      expect(revealEvent).to.not.be.undefined;
      const parsedRevealEvent = flashLoanService.interface.parseLog(revealEvent);
      expect(parsedRevealEvent?.args.commitmentHash).to.equal(commitmentHash);
      expect(parsedRevealEvent?.args.user).to.equal(user1.address);
    });

    it("Should reject execution if commitment has expired", async function () {
      const { flashLoanService, weth, user1 } = await loadFixture(deployMEVProtectionFixture);
      
      const amount = ethers.parseEther("1");
      const secret = ethers.keccak256(ethers.toUtf8Bytes("my secret"));
      
      // Create commitment
      const tx = await flashLoanService.connect(user1).commitFlashLoanTransaction(
        await weth.getAddress(),
        amount,
        secret
      );
      
      const receipt = await tx.wait();
      const event = receipt?.logs.find((log: any) => {
        try {
          const parsedLog = flashLoanService.interface.parseLog(log);
          return parsedLog?.name === "TransactionCommitted";
        } catch (e) {
          return false;
        }
      });
      
      const parsedEvent = flashLoanService.interface.parseLog(event);
      const commitmentHash = parsedEvent?.args.commitmentHash;
      
      // Mine blocks to exceed the maximum age
      for (let i = 0; i < 51; i++) {
        await time.advanceBlock();
      }
      
      // Try to execute (should fail)
      await expect(
        flashLoanService.connect(user1).executeFlashLoanWithMEVProtection(
          await weth.getAddress(),
          amount,
          secret,
          commitmentHash
        )
      ).to.be.revertedWithCustomError(flashLoanService, "CommitmentExpired");
    });

    it("Should reject execution with invalid commitment hash", async function () {
      const { flashLoanService, weth, user1 } = await loadFixture(deployMEVProtectionFixture);
      
      const amount = ethers.parseEther("1");
      const secret = ethers.keccak256(ethers.toUtf8Bytes("my secret"));
      const wrongSecret = ethers.keccak256(ethers.toUtf8Bytes("wrong secret"));
      
      // Create commitment
      const tx = await flashLoanService.connect(user1).commitFlashLoanTransaction(
        await weth.getAddress(),
        amount,
        secret
      );
      
      const receipt = await tx.wait();
      const event = receipt?.logs.find((log: any) => {
        try {
          const parsedLog = flashLoanService.interface.parseLog(log);
          return parsedLog?.name === "TransactionCommitted";
        } catch (e) {
          return false;
        }
      });
      
      const parsedEvent = flashLoanService.interface.parseLog(event);
      const commitmentHash = parsedEvent?.args.commitmentHash;
      
      // Mine blocks to pass the minimum age
      await time.increase(2);
      await time.advanceBlock();
      await time.advanceBlock();
      
      // Try to execute with wrong secret (should fail)
      await expect(
        flashLoanService.connect(user1).executeFlashLoanWithMEVProtection(
          await weth.getAddress(),
          amount,
          wrongSecret,
          commitmentHash
        )
      ).to.be.revertedWithCustomError(flashLoanService, "InvalidCommitment");
    });

    it("Should prevent reusing the same commitment", async function () {
      const { flashLoanService, weth, user1 } = await loadFixture(deployMEVProtectionFixture);
      
      const amount = ethers.parseEther("1");
      const secret = ethers.keccak256(ethers.toUtf8Bytes("my secret"));
      
      // Create commitment
      const tx = await flashLoanService.connect(user1).commitFlashLoanTransaction(
        await weth.getAddress(),
        amount,
        secret
      );
      
      const receipt = await tx.wait();
      const event = receipt?.logs.find((log: any) => {
        try {
          const parsedLog = flashLoanService.interface.parseLog(log);
          return parsedLog?.name === "TransactionCommitted";
        } catch (e) {
          return false;
        }
      });
      
      const parsedEvent = flashLoanService.interface.parseLog(event);
      const commitmentHash = parsedEvent?.args.commitmentHash;
      
      // Mine blocks to pass the minimum age
      await time.increase(2);
      await time.advanceBlock();
      await time.advanceBlock();
      
      // Enable test mode to avoid actual flash loan execution
      await flashLoanService.toggleTestMode(true);
      
      // Execute with valid commitment
      await flashLoanService.connect(user1).executeFlashLoanWithMEVProtection(
        await weth.getAddress(),
        amount,
        secret,
        commitmentHash
      );
      
      // Try to execute again with the same commitment (should fail)
      await expect(
        flashLoanService.connect(user1).executeFlashLoanWithMEVProtection(
          await weth.getAddress(),
          amount,
          secret,
          commitmentHash
        )
      ).to.be.revertedWithCustomError(flashLoanService, "CommitmentRequired");
    });
  });

  describe("Flashbots Integration", function () {
    it("Should set the Flashbots relayer", async function () {
      const { flashLoanService, mockFlashbotsRelayer, owner } = await loadFixture(deployMEVProtectionFixture);
      
      // Check current relayer
      const currentRelayer = await flashLoanService.flashbotsRelayer();
      expect(currentRelayer).to.equal(await mockFlashbotsRelayer.getAddress());
      
      // Set a new relayer
      await flashLoanService.connect(owner).setFlashbotsRelayer(owner.address);
      
      // Check updated relayer
      const newRelayer = await flashLoanService.flashbotsRelayer();
      expect(newRelayer).to.equal(owner.address);
    });

    it("Should toggle Flashbots usage", async function () {
      const { flashLoanService, owner } = await loadFixture(deployMEVProtectionFixture);
      
      // Check initial state
      const initialState = await flashLoanService.useFlashbots();
      
      // Toggle state
      await flashLoanService.connect(owner).toggleFlashbots(!initialState);
      
      // Check updated state
      const newState = await flashLoanService.useFlashbots();
      expect(newState).to.equal(!initialState);
    });

    it("Should update commitment age parameters", async function () {
      const { flashLoanService, owner } = await loadFixture(deployMEVProtectionFixture);
      
      // Check initial values
      const initialMinAge = await flashLoanService.commitmentMinAge();
      const initialMaxAge = await flashLoanService.commitmentMaxAge();
      expect(initialMinAge).to.equal(1);
      expect(initialMaxAge).to.equal(50);
      
      // Update parameters
      await flashLoanService.connect(owner).setCommitmentAgeParams(3, 100);
      
      // Check updated values
      const updatedMinAge = await flashLoanService.commitmentMinAge();
      const updatedMaxAge = await flashLoanService.commitmentMaxAge();
      expect(updatedMinAge).to.equal(3);
      expect(updatedMaxAge).to.equal(100);
    });

    it("Should use Flashbots relayer when enabled", async function () {
      const { flashLoanService, weth, user1, mockFlashbotsRelayer, owner } = await loadFixture(deployMEVProtectionFixture);
      
      // Enable Flashbots
      const initialState = await flashLoanService.useFlashbots();
      await flashLoanService.connect(owner).toggleFlashbots(!initialState);
      
      const amount = ethers.parseEther("1");
      const secret = ethers.keccak256(ethers.toUtf8Bytes("my secret"));
      
      // Create commitment
      const tx = await flashLoanService.connect(user1).commitFlashLoanTransaction(
        await weth.getAddress(),
        amount,
        secret
      );
      
      const receipt = await tx.wait();
      const event = receipt?.logs.find((log: any) => {
        try {
          const parsedLog = flashLoanService.interface.parseLog(log);
          return parsedLog?.name === "TransactionCommitted";
        } catch (e) {
          return false;
        }
      });
      
      const parsedEvent = flashLoanService.interface.parseLog(event);
      const commitmentHash = parsedEvent?.args.commitmentHash;
      
      // Mine blocks to pass the minimum age
      await time.increase(2);
      await time.advanceBlock();
      await time.advanceBlock();
      
      // Reset the mock relayer's state
      await mockFlashbotsRelayer.reset();
      
      // Enable test mode to avoid actual flash loan execution
      await flashLoanService.toggleTestMode(true);
      
      // Execute with valid commitment
      await flashLoanService.connect(user1).executeFlashLoanWithMEVProtection(
        await weth.getAddress(),
        amount,
        secret,
        commitmentHash
      );
      
      // Check that the relayer was called
      expect(await mockFlashbotsRelayer.callCount()).to.be.gt(0);
      expect(await mockFlashbotsRelayer.lastCalledContract()).to.equal(await flashLoanService.getAddress());
    });
  });
}); 