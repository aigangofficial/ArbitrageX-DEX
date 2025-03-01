import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";
import { spawn, ChildProcess } from "child_process";

/**
 * This script sets up a mainnet fork environment and runs the ArbitrageX AI system
 * to verify its profitability in real-world liquidity conditions.
 */

// Configuration
const AI_SYSTEM_PATH = path.join(__dirname, "../backend/ai");
const RESULTS_PATH = path.join(__dirname, "../results");
const RUN_DURATION = 300; // 5 minutes
const MODULES = "strategy_optimizer,backtesting,trade_analyzer,network_adaptation,integration";

// Ensure results directory exists
if (!fs.existsSync(RESULTS_PATH)) {
  fs.mkdirSync(RESULTS_PATH, { recursive: true });
}

// Log file paths
const LOG_FILE = path.join(RESULTS_PATH, `mainnet_fork_test_${Date.now()}.log`);
const logStream = fs.createWriteStream(LOG_FILE, { flags: "a" });

// Helper function to log messages
function log(message: string) {
  const timestamp = new Date().toISOString();
  const formattedMessage = `[${timestamp}] ${message}`;
  console.log(formattedMessage);
  logStream.write(formattedMessage + "\n");
}

// Helper function to run a shell command
async function runCommand(command: string, args: string[], cwd: string): Promise<string> {
  return new Promise((resolve, reject) => {
    log(`Running command: ${command} ${args.join(" ")}`);
    
    const childProcess = spawn(command, args, {
      cwd,
      env: { ...process.env, FORK_MODE: "true" },
      stdio: ["ignore", "pipe", "pipe"]
    });
    
    let stdout = "";
    let stderr = "";
    
    childProcess.stdout.on("data", (data) => {
      const output = data.toString();
      stdout += output;
      log(`[STDOUT] ${output.trim()}`);
    });
    
    childProcess.stderr.on("data", (data) => {
      const output = data.toString();
      stderr += output;
      log(`[STDERR] ${output.trim()}`);
    });
    
    childProcess.on("close", (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(`Command failed with exit code ${code}: ${stderr}`));
      }
    });
  });
}

// Main function to run the AI system in mainnet fork
async function main() {
  try {
    log("Starting ArbitrageX AI system in mainnet fork environment");
    
    // Get network information
    const provider = ethers.provider;
    const network = await provider.getNetwork();
    const blockNumber = await provider.getBlockNumber();
    
    log(`Connected to network: ${network.name} (chainId: ${network.chainId})`);
    log(`Current block number: ${blockNumber}`);
    
    // Deploy contracts if needed
    log("Deploying contracts to mainnet fork...");
    await runCommand("npx", ["hardhat", "run", "scripts/deploy.ts", "--network", "hardhat"], __dirname + "/..");
    
    // Create a configuration file for the AI system with contract addresses
    const contractAddressesPath = path.join(__dirname, "../backend/config/contractAddresses.json");
    log(`Reading contract addresses from ${contractAddressesPath}`);
    
    let contractAddresses = {};
    if (fs.existsSync(contractAddressesPath)) {
      contractAddresses = JSON.parse(fs.readFileSync(contractAddressesPath, "utf8"));
      log(`Contract addresses: ${JSON.stringify(contractAddresses, null, 2)}`);
    } else {
      log("Warning: Contract addresses file not found. Using default addresses.");
    }
    
    // Run the AI system
    log(`Running AI system with modules: ${MODULES}`);
    log(`Run duration: ${RUN_DURATION} seconds`);
    
    // Create a temporary configuration file for the mainnet fork test
    const forkConfigPath = path.join(AI_SYSTEM_PATH, "fork_config.json");
    const forkConfig = {
      mode: "mainnet_fork",
      blockNumber,
      chainId: network.chainId.toString(),
      contractAddresses,
      runDuration: RUN_DURATION
    };
    
    fs.writeFileSync(forkConfigPath, JSON.stringify(forkConfig, null, 2));
    log(`Created fork configuration at ${forkConfigPath}`);
    
    // Run the AI system with the mainnet fork configuration
    await runCommand(
      "./run_ai_system.sh",
      [
        "--modules", MODULES,
        "--run-time", RUN_DURATION.toString(),
        "--visualize",
        "--save-results",
        "--fork-config", "fork_config.json"
      ],
      AI_SYSTEM_PATH
    );
    
    // Analyze results
    log("AI system execution completed. Analyzing results...");
    
    // Read the results
    const resultsFiles = fs.readdirSync(path.join(AI_SYSTEM_PATH, "results"))
      .filter(file => file.startsWith("ai_results_"))
      .sort()
      .reverse();
    
    if (resultsFiles.length > 0) {
      const latestResultsFile = path.join(AI_SYSTEM_PATH, "results", resultsFiles[0]);
      log(`Reading latest results from ${latestResultsFile}`);
      
      const results = JSON.parse(fs.readFileSync(latestResultsFile, "utf8"));
      
      // Calculate profitability metrics
      let totalPredictions = results.length;
      let profitablePredictions = results.filter((r: any) => r.prediction.is_profitable).length;
      let totalExpectedProfit = results.reduce((sum: number, r: any) => sum + r.prediction.net_profit_usd, 0);
      let averageConfidence = results.reduce((sum: number, r: any) => sum + r.prediction.confidence_score, 0) / totalPredictions;
      
      log("\n=== MAINNET FORK TEST RESULTS ===");
      log(`Total predictions: ${totalPredictions}`);
      log(`Profitable predictions: ${profitablePredictions} (${(profitablePredictions / totalPredictions * 100).toFixed(2)}%)`);
      log(`Total expected profit: $${totalExpectedProfit.toFixed(2)}`);
      log(`Average confidence score: ${averageConfidence.toFixed(4)}`);
      
      // Copy the results to the main results directory
      const destinationFile = path.join(RESULTS_PATH, `mainnet_fork_results_${Date.now()}.json`);
      fs.copyFileSync(latestResultsFile, destinationFile);
      log(`Results copied to ${destinationFile}`);
    } else {
      log("No results found. Check the AI system logs for errors.");
    }
    
    log("Mainnet fork test completed successfully.");
  } catch (error) {
    log(`Error: ${error}`);
    process.exit(1);
  } finally {
    logStream.end();
  }
}

// Run the main function
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  }); 