import { ethers, network, run } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  console.log(`🚀 Starting deployment on ${network.name}...`);

  // Deploy FlashLoanService
  console.log("📦 Deploying FlashLoanService...");
  const FlashLoanService = await ethers.getContractFactory("FlashLoanService");
  const flashLoanService = await FlashLoanService.deploy();
  await flashLoanService.waitForDeployment();
  console.log(`✅ FlashLoanService deployed to: ${await flashLoanService.getAddress()}`);

  // Deploy ArbitrageExecutor
  console.log("📦 Deploying ArbitrageExecutor...");
  const ArbitrageExecutor = await ethers.getContractFactory("ArbitrageExecutor");
  const arbitrageExecutor = await ArbitrageExecutor.deploy(await flashLoanService.getAddress());
  await arbitrageExecutor.waitForDeployment();
  console.log(`✅ ArbitrageExecutor deployed to: ${await arbitrageExecutor.getAddress()}`);

  // Save deployment addresses
  const deploymentInfo = {
    network: network.name,
    flashLoanService: await flashLoanService.getAddress(),
    arbitrageExecutor: await arbitrageExecutor.getAddress(),
    timestamp: new Date().toISOString()
  };

  // Ensure the config directory exists
  const configDir = path.join(__dirname, "../backend/config");
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }

  // Save deployment info
  const deploymentPath = path.join(configDir, "contractAddresses.json");
  fs.writeFileSync(
    deploymentPath,
    JSON.stringify(deploymentInfo, null, 2)
  );
  console.log(`📝 Deployment info saved to: ${deploymentPath}`);

  // Wait for etherscan to index the contracts
  if (network.name !== "hardhat" && network.name !== "localhost") {
    console.log("⏳ Waiting for Etherscan to index contracts...");
    await new Promise(resolve => setTimeout(resolve, 30000)); // 30 seconds

    // Verify contracts on Etherscan
    try {
      console.log("🔍 Verifying contracts on Etherscan...");
      await run("verify:verify", {
        address: await flashLoanService.getAddress(),
        constructorArguments: []
      });
      await run("verify:verify", {
        address: await arbitrageExecutor.getAddress(),
        constructorArguments: [await flashLoanService.getAddress()]
      });
      console.log("✅ Contract verification complete!");
    } catch (error) {
      console.error("❌ Error verifying contracts:", error);
    }
  }

  console.log("🎉 Deployment complete!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
