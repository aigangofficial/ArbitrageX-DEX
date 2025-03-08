/**
 * Script to check the execution mode of the FlashLoanService contract
 * 
 * Usage: npx hardhat run scripts/check_mode.js --network localhost
 */

const { ethers } = require("hardhat");

async function main() {
  try {
    console.log("Checking FlashLoanService execution mode...");
    
    // FlashLoanService contract address
    const contractAddress = "0xad203b3144f8c09a20532957174fc0366291643c";
    
    // Connect to the contract
    const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");
    const abi = [
      "function getExecutionMode() external view returns (uint8)"
    ];
    const contract = new ethers.Contract(contractAddress, abi, provider);
    
    // Get the execution mode
    const mode = await contract.getExecutionMode();
    console.log(`Raw execution mode value: ${mode} (${typeof mode})`);
    
    // Interpret the mode
    const modeString = mode.toString() === '0' ? 'MAINNET/production' : 'FORK/fork';
    console.log(`Execution mode: ${modeString}`);
    
    // Check API interpretation
    try {
      const response = await fetch("http://localhost:3002/api/v1/blockchain/contract-execution-mode");
      const data = await response.json();
      console.log(`API reports execution mode as: ${data.mode}`);
      
      // Check sync status
      const syncResponse = await fetch("http://localhost:3002/api/v1/execution-mode/sync-status");
      const syncData = await syncResponse.json();
      console.log(`Execution modes in sync: ${syncData.data.isInSync}`);
      console.log(`API execution mode: ${syncData.data.apiMode}`);
    } catch (error) {
      console.log("Could not check API execution mode. Is the API server running?");
    }
  } catch (error) {
    console.error("Error checking execution mode:", error.message);
    console.log("Make sure the Hardhat node is running and the contract is deployed.");
  }
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  }); 