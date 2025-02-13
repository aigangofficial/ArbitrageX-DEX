import { ethers } from 'hardhat';

async function main() {
  console.log('\nConnecting to Polygon Amoy testnet...\n');

  try {
    // Get network information
    const network = await ethers.provider.getNetwork();
    console.log('Network:', {
      name: network.name,
      chainId: Number(network.chainId),
    });

    // Get latest block
    const latestBlock = await ethers.provider.getBlock('latest');
    console.log('\nLatest block number:', latestBlock?.number);

    if (latestBlock) {
      console.log('\nLatest block details:');
      console.log('Hash:', latestBlock.hash);
      console.log('Parent Hash:', latestBlock.parentHash);
      console.log('Number:', latestBlock.number);
      console.log('Timestamp:', new Date(Number(latestBlock.timestamp) * 1000).toISOString());
      console.log('Gas Limit:', latestBlock.gasLimit.toString());
      console.log('Gas Used:', latestBlock.gasUsed.toString());

      // Get gas price safely
      try {
        const feeData = await ethers.provider.getFeeData();
        if (feeData) {
          console.log('\nCurrent gas prices (in wei):');
          if (feeData.gasPrice) console.log('Gas Price:', feeData.gasPrice.toString());
          if (feeData.maxFeePerGas)
            console.log('Max Fee Per Gas:', feeData.maxFeePerGas.toString());
          if (feeData.maxPriorityFeePerGas)
            console.log('Max Priority Fee Per Gas:', feeData.maxPriorityFeePerGas.toString());
        }
      } catch (error: any) {
        console.log('Could not fetch gas prices:', error.message);
      }

      // Check deployer balance
      try {
        const [deployer] = await ethers.getSigners();
        if (deployer) {
          const balance = await ethers.provider.getBalance(deployer.address);
          console.log('\nDeployer address:', deployer.address);
          console.log('Balance (in wei):', balance.toString());
        } else {
          console.log('\nNo deployer account found. Please check your private key configuration.');
        }
      } catch (error: any) {
        console.log('Could not fetch deployer balance:', error.message);
      }

      // Check known contract addresses
      const knownAddresses = {
        WMATIC: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
        USDC: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
        QUICKSWAP_ROUTER: '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
      };

      console.log('\nChecking known contract addresses:');
      for (const [name, address] of Object.entries(knownAddresses)) {
        try {
          const code = await ethers.provider.getCode(address);
          console.log(
            `${name}: ${address} - ${code !== '0x' ? '✅ Contract deployed' : '❌ Not deployed'}`
          );
        } catch (error: any) {
          console.log(`${name}: ${address} - ❌ Error checking contract: ${error.message}`);
        }
      }
    }
  } catch (error) {
    console.error('Error connecting to Amoy testnet:', error);
    throw error;
  }
}

main()
  .then(() => process.exit(0))
  .catch(error => {
    console.error(error);
    process.exit(1);
  });
