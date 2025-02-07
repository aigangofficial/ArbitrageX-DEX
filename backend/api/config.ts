interface Config {
    port: number;
    wsPort: number;
    mongoUri: string;
    contractAddresses: {
        flashLoanService: string;
        arbitrageExecutor: string;
    };
    networks: {
        sepolia: {
            rpcUrl: string;
            chainId: number;
        };
        mainnet: {
            rpcUrl: string;
            chainId: number;
        };
    };
}

export const config: Config = {
    port: parseInt(process.env.API_PORT || '3000'),
    wsPort: parseInt(process.env.WS_PORT || '3001'),
    mongoUri: process.env.MONGO_URI || 'mongodb://localhost:27017/arbitragex',
    contractAddresses: {
        flashLoanService: process.env.FLASH_LOAN_ADDRESS || '',
        arbitrageExecutor: process.env.ARBITRAGE_EXECUTOR_ADDRESS || ''
    },
    networks: {
        sepolia: {
            rpcUrl: process.env.SEPOLIA_RPC || 'https://sepolia.infura.io/v3/YOUR-PROJECT-ID',
            chainId: 11155111
        },
        mainnet: {
            rpcUrl: process.env.MAINNET_RPC || 'https://mainnet.infura.io/v3/YOUR-PROJECT-ID',
            chainId: 1
        }
    }
}; 