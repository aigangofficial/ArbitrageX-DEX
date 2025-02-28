import { BigNumber } from '@ethersproject/bignumber';
import { Contract } from '@ethersproject/contracts';
import { JsonRpcProvider } from '@ethersproject/providers';
import { config } from 'dotenv';
import { resolve } from 'path';
import { DEXRouterFactory } from '../execution/interfaces/IDEXRouter';
import { logger } from '../utils/logger';

// Load environment variables from the config directory
const envPath = resolve(__dirname, '../../config/.env.sepolia');
logger.info(`Loading environment variables from: ${envPath}`);
const result = config({ path: envPath });

if (result.error) {
    logger.error(`Failed to load .env file: ${result.error}`);
    process.exit(1);
}

if (!result.parsed) {
    logger.error('No environment variables were loaded');
    process.exit(1);
}

// Log loaded environment variables
logger.info(`Loaded environment variables: ${JSON.stringify(result.parsed, null, 2)}`);

// Extract required variables from parsed result
const {
    NETWORK_RPC,
    UNISWAP_ROUTER_ADDRESS,
    SUSHISWAP_ROUTER_ADDRESS,
    WETH_ADDRESS,
    USDC_ADDRESS
} = result.parsed;

// Validate required environment variables
if (!NETWORK_RPC || !UNISWAP_ROUTER_ADDRESS || !SUSHISWAP_ROUTER_ADDRESS || !WETH_ADDRESS || !USDC_ADDRESS) {
    const missing = [
        !NETWORK_RPC && 'NETWORK_RPC',
        !UNISWAP_ROUTER_ADDRESS && 'UNISWAP_ROUTER_ADDRESS',
        !SUSHISWAP_ROUTER_ADDRESS && 'SUSHISWAP_ROUTER_ADDRESS',
        !WETH_ADDRESS && 'WETH_ADDRESS',
        !USDC_ADDRESS && 'USDC_ADDRESS'
    ].filter(Boolean);
    logger.error(`Missing required environment variables: ${missing.join(', ')}`);
    process.exit(1);
}

const ERC20_ABI = [
    'function name() view returns (string)',
    'function symbol() view returns (string)',
    'function decimals() view returns (uint8)'
];

async function verifyContract(provider: JsonRpcProvider, address: string, name: string): Promise<boolean> {
    try {
        logger.info(`Verifying ${name} at address: ${address}`);
        const code = await provider.getCode(address);
        if (code === '0x') {
            logger.error(`${name} contract not deployed at ${address}`);
            return false;
        }
        logger.info(`✓ ${name} contract verified at ${address}`);
        return true;
    } catch (error) {
        logger.error(`Failed to verify ${name} contract: ${error instanceof Error ? error.message : 'Unknown error'}`);
        return false;
    }
}

async function verifyToken(provider: JsonRpcProvider, address: string): Promise<boolean> {
    try {
        const token = new Contract(address, ERC20_ABI, provider);
        const [name, symbol, decimals] = await Promise.all([
            token.name(),
            token.symbol(),
            token.decimals()
        ]);
        logger.info(`✓ Token verified: ${name} (${symbol}) with ${decimals} decimals at ${address}`);
        return true;
    } catch (error) {
        logger.error(`Failed to verify token at ${address}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        return false;
    }
}

async function main() {
    try {
        logger.info('Using contract addresses:');
        logger.info(`Network RPC: ${NETWORK_RPC}`);
        logger.info(`Uniswap Router: ${UNISWAP_ROUTER_ADDRESS}`);
        logger.info(`SushiSwap Router: ${SUSHISWAP_ROUTER_ADDRESS}`);
        logger.info(`WETH Address: ${WETH_ADDRESS}`);
        logger.info(`USDC Address: ${USDC_ADDRESS}`);

        // Initialize provider
        const provider = new JsonRpcProvider(NETWORK_RPC);

        // Get current block
        const block = await provider.getBlock('latest');
        if (!block) throw new Error('Could not get latest block');
        logger.info(`\nCurrent block: ${block.number} (${new Date(block.timestamp * 1000).toISOString()})`);

        // Verify contracts
        logger.info('\nVerifying contracts...');

        // Verify each contract individually for better error tracking
        const uniswapValid = await verifyContract(provider, UNISWAP_ROUTER_ADDRESS, 'Uniswap Router');
        const sushiswapValid = await verifyContract(provider, SUSHISWAP_ROUTER_ADDRESS, 'SushiSwap Router');
        const wethValid = await verifyToken(provider, WETH_ADDRESS);
        const usdcValid = await verifyToken(provider, USDC_ADDRESS);

        if (!uniswapValid || !sushiswapValid || !wethValid || !usdcValid) {
            throw new Error('Contract verification failed');
        }

        // Initialize routers
        const uniswapRouter = DEXRouterFactory.connect(UNISWAP_ROUTER_ADDRESS, provider);
        const sushiswapRouter = DEXRouterFactory.connect(SUSHISWAP_ROUTER_ADDRESS, provider);

        // Test amount: 1 ETH
        const amount = BigNumber.from('1000000000000000000');

        // Fetch WETH/USDC prices
        logger.info('\nFetching WETH/USDC prices...');
        const [uniWethUsdc, sushiWethUsdc] = await Promise.all([
            uniswapRouter.getAmountsOut(amount, [WETH_ADDRESS, USDC_ADDRESS]),
            sushiswapRouter.getAmountsOut(amount, [WETH_ADDRESS, USDC_ADDRESS])
        ]);

        logger.info(`Uniswap WETH/USDC: ${uniWethUsdc[1].toString()} USDC per WETH`);
        logger.info(`SushiSwap WETH/USDC: ${sushiWethUsdc[1].toString()} USDC per WETH`);

        // Calculate and log price difference
        const priceDiff = uniWethUsdc[1].sub(sushiWethUsdc[1]).abs();
        const minPrice = BigNumber.from(
            uniWethUsdc[1].lt(sushiWethUsdc[1]) ? uniWethUsdc[1] : sushiWethUsdc[1]
        );
        const spreadPercentage = priceDiff.mul(100).div(minPrice);

        logger.info(`\nPrice difference: ${priceDiff.toString()} USDC`);
        logger.info(`Spread percentage: ${spreadPercentage.toString()}%`);

    } catch (error: unknown) {
        if (error instanceof Error) {
            logger.error(`Script failed: ${error.message}`);
        } else {
            logger.error('Script failed with unknown error');
        }
        process.exit(1);
    }
}

main();
