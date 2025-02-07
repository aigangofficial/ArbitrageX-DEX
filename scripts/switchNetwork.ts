import fs from 'fs';
import dotenv from 'dotenv';
import path from 'path';

export async function updateNetwork(network: 'testnet' | 'mainnet') {
  const envPath = path.resolve(__dirname, '../.env');
  const envConfig = dotenv.parse(fs.readFileSync(envPath));

  // Update environment variables
  envConfig.NODE_ENV = network;
  envConfig.RPC_URL = network === 'testnet' ? envConfig.SEPOLIA_RPC_URL : envConfig.MAINNET_RPC_URL;
  envConfig.CURRENT_NETWORK = network;

  // Update contract addresses based on network
  if (network === 'testnet') {
    envConfig.AAVE_POOL_ADDRESS = envConfig.SEPOLIA_AAVE_POOL;
    envConfig.UNISWAP_ROUTER = envConfig.SEPOLIA_UNISWAP_ROUTER;
    envConfig.SUSHISWAP_ROUTER = envConfig.SEPOLIA_SUSHISWAP_ROUTER;
    envConfig.WETH_ADDRESS = envConfig.SEPOLIA_WETH;
  } else {
    // Restore mainnet addresses
    envConfig.AAVE_POOL_ADDRESS = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2';
    envConfig.UNISWAP_ROUTER = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D';
    envConfig.SUSHISWAP_ROUTER = '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F';
    envConfig.WETH_ADDRESS = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
  }

  // Write back to .env file
  fs.writeFileSync(
    envPath,
    Object.entries(envConfig)
      .map(([key, val]) => `${key}=${val}`)
      .join('\n')
  );

  console.log(`✅ Switched to ${network.toUpperCase()}`);
  console.log(`Network RPC: ${envConfig.RPC_URL}`);
  console.log(`AAVE Pool: ${envConfig.AAVE_POOL_ADDRESS}`);
  console.log(`Uniswap Router: ${envConfig.UNISWAP_ROUTER}`);
  console.log(`SushiSwap Router: ${envConfig.SUSHISWAP_ROUTER}`);
  console.log(`WETH: ${envConfig.WETH_ADDRESS}`);
}

// Allow command line usage
if (require.main === module) {
  const network = process.argv[2] as 'testnet' | 'mainnet';
  if (!network || !['testnet', 'mainnet'].includes(network)) {
    console.error('Please specify network: testnet or mainnet');
    process.exit(1);
  }
  updateNetwork(network)
    .then(() => process.exit(0))
    .catch((error) => {
      console.error('Error switching network:', error);
      process.exit(1);
    });
} 