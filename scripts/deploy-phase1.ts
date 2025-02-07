import { ethers, network, run } from "hardhat";
import * as fs from "fs";
import * as dotenv from "dotenv";

dotenv.config();

interface DeploymentInfo {
  network: {
    name: string;
    chainId: number;
  };
  contracts: {
    flashLoanService: {
      address: string;
      constructorArgs: string[];
    };
    arbitrageExecutor: {
      address: string;
      constructorArgs: string[];
    };
  };
  transactions: {
    flashLoanService: {
      hash: string;
      gasUsed: string;
      gasPrice: string;
      cost: string;
    };
    arbitrageExecutor: {
      hash: string;
      gasUsed: string;
      gasPrice: string;
      cost: string;
    };
  };
  verification: {
    flashLoanService: boolean;
    arbitrageExecutor: boolean;
  };
  timestamp: string;
  deployer: string;
}

async function verifyContract(
  name: string,
  address: string,
  constructorArguments: any[]
) {
  console.log(`\nVerifying ${name}...`);
  try {
    await run("verify:verify", {
      address,
      constructorArguments,
    });
    return true;
  } catch (error) {
    console.log(`Error verifying ${name}:`, error);
    return false;
  }
}

async function main() {
  console.log("Starting deployment of Phase 1 contracts...");
  console.log(`Network: ${network.name} (${network.config.chainId})`);

  // Get network-specific addresses
  const AAVE_POOL = network.name === "sepolia" 
    ? process.env.SEPOLIA_AAVE_POOL
    : process.env.AAVE_POOL_ADDRESS;
  
  const UNISWAP = network.name === "sepolia"
    ? process.env.SEPOLIA_UNISWAP_ROUTER
    : process.env.UNISWAP_ROUTER;
  
  const SUSHISWAP = network.name === "sepolia"
    ? process.env.SEPOLIA_SUSHISWAP_ROUTER
    : process.env.SUSHISWAP_ROUTER;

  // Validate environment variables
  if (!AAVE_POOL || !UNISWAP || !SUSHISWAP) {
    throw new Error("Missing required environment variables");
  }

  // Get deployer
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", ethers.formatEther(await deployer.provider.getBalance(deployer.address)), "ETH");

  // Deploy FlashLoanService
  console.log("\nDeploying FlashLoanService...");
  const FlashLoanService = await ethers.getContractFactory("FlashLoanService");
  const flashLoanService = await FlashLoanService.deploy(AAVE_POOL, UNISWAP, SUSHISWAP);
  const flashLoanReceipt = await flashLoanService.deploymentTransaction()?.wait();
  console.log("FlashLoanService deployed to:", await flashLoanService.getAddress());

  // Deploy ArbitrageExecutor
  console.log("\nDeploying ArbitrageExecutor...");
  const ArbitrageExecutor = await ethers.getContractFactory("ArbitrageExecutor");
  const arbitrageExecutor = await ArbitrageExecutor.deploy(
    UNISWAP,
    SUSHISWAP,
    await flashLoanService.getAddress()
  );
  const arbitrageReceipt = await arbitrageExecutor.deploymentTransaction()?.wait();
  console.log("ArbitrageExecutor deployed to:", await arbitrageExecutor.getAddress());

  // Verify contracts on Etherscan
  let verificationResults = {
    flashLoanService: false,
    arbitrageExecutor: false
  };

  if (network.name !== "hardhat") {
    // Wait for contracts to be deployed fully
    await new Promise(resolve => setTimeout(resolve, 30000));

    verificationResults.flashLoanService = await verifyContract(
      "FlashLoanService",
      await flashLoanService.getAddress(),
      [AAVE_POOL, UNISWAP, SUSHISWAP]
    );

    verificationResults.arbitrageExecutor = await verifyContract(
      "ArbitrageExecutor",
      await arbitrageExecutor.getAddress(),
      [UNISWAP, SUSHISWAP, await flashLoanService.getAddress()]
    );
  }

  // Prepare deployment info
  const deploymentInfo: DeploymentInfo = {
    network: {
      name: network.name,
      chainId: network.config.chainId || 0,
    },
    contracts: {
      flashLoanService: {
        address: await flashLoanService.getAddress(),
        constructorArgs: [AAVE_POOL, UNISWAP, SUSHISWAP],
      },
      arbitrageExecutor: {
        address: await arbitrageExecutor.getAddress(),
        constructorArgs: [UNISWAP, SUSHISWAP, await flashLoanService.getAddress()],
      },
    },
    transactions: {
      flashLoanService: {
        hash: flashLoanReceipt?.hash || "unknown",
        gasUsed: flashLoanReceipt?.gasUsed.toString() || "unknown",
        gasPrice: flashLoanReceipt?.gasPrice?.toString() || "unknown",
        cost: ((flashLoanReceipt?.gasUsed || 0n) * (flashLoanReceipt?.gasPrice || 0n)).toString(),
      },
      arbitrageExecutor: {
        hash: arbitrageReceipt?.hash || "unknown",
        gasUsed: arbitrageReceipt?.gasUsed.toString() || "unknown",
        gasPrice: arbitrageReceipt?.gasPrice?.toString() || "unknown",
        cost: ((arbitrageReceipt?.gasUsed || 0n) * (arbitrageReceipt?.gasPrice || 0n)).toString(),
      },
    },
    verification: verificationResults,
    timestamp: new Date().toISOString(),
    deployer: deployer.address,
  };

  // Save deployment info
  const deploymentPath = `deployments/${network.name}`;
  if (!fs.existsSync(deploymentPath)) {
    fs.mkdirSync(deploymentPath, { recursive: true });
  }
  
  fs.writeFileSync(
    `${deploymentPath}/deployment-phase1.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );

  // Print deployment summary
  console.log("\n=== Deployment Summary ===");
  console.log(`Network: ${network.name} (Chain ID: ${network.config.chainId})`);
  console.log(`Deployer: ${deployer.address}`);
  console.log("\nContracts:");
  console.log(`- FlashLoanService: ${await flashLoanService.getAddress()}`);
  console.log(`- ArbitrageExecutor: ${await arbitrageExecutor.getAddress()}`);
  console.log("\nVerification Status:");
  console.log(`- FlashLoanService: ${verificationResults.flashLoanService ? "✅" : "❌"}`);
  console.log(`- ArbitrageExecutor: ${verificationResults.arbitrageExecutor ? "✅" : "❌"}`);
  
  const totalGasUsed = (BigInt(flashLoanReceipt?.gasUsed || 0) + BigInt(arbitrageReceipt?.gasUsed || 0)).toString();
  console.log("\nTotal Gas Used:", totalGasUsed);

  return deploymentInfo;
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  }); 