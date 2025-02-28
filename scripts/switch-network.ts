import fs from 'fs';
import path from 'path';

interface NetworkConfig {
  name: string;
  rpc: string;
  chainId: number;
  contracts: {
    dex1Router: string;
    dex2Router: string;
    weth: string;
  }
}

interface Networks {
  mainnet: NetworkConfig;
}

const networks: Networks = {
  mainnet: {
    name: 'mainnet',
    rpc: 'https://mainnet.infura.io/v3/59de174d2d904c1980b975abae2ef0ec',
    chainId: 1,
    contracts: {
      dex1Router: '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', // Uniswap V2 Router
      dex2Router: '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F', // Sushiswap Router
      weth: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    }
  }
};

async function switchNetwork(network: keyof Networks) {
  if (!networks[network]) {
    console.log('Invalid network specified');
    console.log('Usage: npm run switch-network [mainnet]');
    process.exit(1);
  }

  const networkConfig = networks[network];
  const envContent = `NETWORK=${network}
NETWORK_RPC=${networkConfig.rpc}
CHAIN_ID=${networkConfig.chainId}
DEPLOY_NETWORK=${network}
DEPLOY_CONFIRMATIONS=2

# Contract Addresses
UNISWAP_ROUTER_ADDRESS=${networkConfig.contracts.dex1Router}
SUSHISWAP_ROUTER_ADDRESS=${networkConfig.contracts.dex2Router}
WETH_ADDRESS=${networkConfig.contracts.weth}
`;

  fs.writeFileSync(path.join(__dirname, '../.env'), envContent);
  console.log(`Switched to ${network} network`);
}

const network = process.argv[2] as keyof Networks;
if (!network) {
  console.log('Usage: npm run switch-network [mainnet]');
  process.exit(1);
}

switchNetwork(network).catch(console.error);
