import { Provider } from '@ethersproject/abstract-provider';
import { JsonRpcProvider } from '@ethersproject/providers';
import { getConfig } from '../api/config';
import { ArbitrageScanner } from './arbitrageScanner';
import { logger } from '../utils/logger';

const config = getConfig();
const provider = new JsonRpcProvider(config.web3Provider) as unknown as Provider;

const scanner = new ArbitrageScanner(
    provider,
    config.contracts.uniswapRouter,
    config.contracts.sushiswapRouter,
    {
        minProfitThreshold: config.security.minProfitThreshold,
        minNetProfit: 0.001, // 0.1% minimum net profit
        gasLimit: 500000,    // 500k gas limit
        scanInterval: 5000,  // 5 second interval
        maxGasPrice: 100000000000n, // 100 gwei
        gasMultiplier: 1.1   // 10% buffer
    },
    [
        {
            tokenA: config.contracts.weth,
            tokenB: config.contracts.usdc
        },
        {
            tokenA: config.contracts.weth,
            tokenB: config.contracts.usdt
        }
    ],
    logger
);

export { scanner };
