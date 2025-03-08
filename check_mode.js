const { ethers } = require("hardhat");

async function main() {
  // FlashLoanService ABI for getExecutionMode
  const abi = [
    "function getExecutionMode() external view returns (uint8)"
  ];
  
  // FlashLoanService contract address
  const contractAddress = "0xad203b3144f8c09a20532957174fc0366291643c";
  
  // Connect to the contract
  const provider = new ethers.JsonRpcProvider("http://127.0.0.1:8545");
  const contract = new ethers.Contract(contractAddress, abi, provider);
  
  // Get the execution mode
  const mode = await contract.getExecutionMode();
  console.log("Execution mode:", mode);
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
