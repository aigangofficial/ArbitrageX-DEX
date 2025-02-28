import { Provider, Wallet, ethers } from 'ethers';
import { Logger } from 'winston';
import { FlashbotsBundleProvider, FlashbotsBundleResolution } from '@flashbots/ethers-provider-bundle';
import { BigNumber, formatEther, parseEther } from 'ethers/lib/utils';
import { getConfig } from '../api/config';

interface FlashbotsTransaction {
    to: string;
    data: string;
    value?: bigint;
    gasLimit?: number;
}

interface BundleOptions {
    revertingTxHashes?: string[];
}

interface BundleResult {
    success: boolean;
    resolution?: FlashbotsBundleResolution;
    error?: string;
}

export class FlashbotsRelay {
    private provider: Provider;
    private signer: Wallet;
    private flashbotsProvider?: FlashbotsBundleProvider;
    private logger: Logger;
    private config = getConfig();

    constructor(provider: Provider, signingKey: string, logger: Logger) {
        this.provider = provider;
        this.signer = new Wallet(signingKey);
        this.logger = logger;
    }

    async initialize() {
        const network = await this.provider.getNetwork();
        const relayUrl = network.chainId === 1n 
            ? 'https://relay.flashbots.net'
            : 'https://relay-goerli.flashbots.net';

        this.flashbotsProvider = await FlashbotsBundleProvider.create(
            this.provider,
            this.signer,
            relayUrl
        );
        this.logger.info('Flashbots provider initialized');
    }

    async signTransaction(tx: FlashbotsTransaction): Promise<string> {
        const transaction = {
            ...tx,
            nonce: await this.provider.getTransactionCount(await this.signer.getAddress()),
            gasPrice: await this.provider.getFeeData().then(data => data.gasPrice),
            chainId: await this.provider.getNetwork().then(network => network.chainId)
        };

        const signedTx = await this.signer.signTransaction(transaction);
        return signedTx;
    }

    async submitBundle(
        signedTransactions: string[],
        targetBlock: number,
        options: BundleOptions = {}
    ): Promise<BundleResult> {
        if (!this.flashbotsProvider) {
            throw new Error('Flashbots provider not initialized');
        }

        try {
            const simulation = await this.flashbotsProvider.simulate(
                signedTransactions,
                targetBlock
            );

            if ('error' in simulation) {
                return {
                    success: false,
                    error: simulation.error.message
                };
            }

            const bundleSubmission = await this.flashbotsProvider.sendBundle(
                signedTransactions,
                targetBlock
            );

            const resolution = await bundleSubmission.wait();
            
            return {
                success: resolution === FlashbotsBundleResolution.BundleIncluded,
                resolution
            };
        } catch (error) {
            this.logger.error('Bundle submission failed:', error);
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    async calculateOptimalBribe(gasUsed: number, fee: bigint): Promise<bigint> {
        const baseFee = await this.provider.getFeeData()
            .then(data => data.gasPrice || BigInt(0));
        
        // Calculate optimal bribe based on current market conditions
        // This is a simplified version - you would want to implement more sophisticated logic
        const bribeMultiplier = BigInt(120); // 20% higher than base fee
        const bribe = (baseFee * BigInt(gasUsed) * bribeMultiplier) / BigInt(100);
        
        // Ensure bribe doesn't exceed provided fee
        return bribe > fee ? fee : bribe;
    }

    async prepareBundle(
        transactions: Array<{
            to: string;
            data: string;
            value?: BigNumber;
            gasLimit?: number;
        }>,
        targetBlock: number
    ) {
        const nonce = await this.provider.getTransactionCount();
        const signedTransactions: string[] = [];

        for (let i = 0; i < transactions.length; i++) {
            const tx = transactions[i];
            const gasLimit = tx.gasLimit || 500000;
            const value = tx.value || BigNumber.from(0);

            const signedTx = await this.signer.signTransaction({
                to: tx.to,
                data: tx.data,
                value,
                nonce: nonce + i,
                gasLimit,
                gasPrice: 0, // Flashbots bundles use 0 gas price
                chainId: this.config.network.chainId
            });

            signedTransactions.push(signedTx);
        }

        return signedTransactions;
    }

    async monitorBundleInclusion(
        bundleHash: string,
        maxBlocks: number = 5
    ): Promise<boolean> {
        let blocksWaited = 0;
        const startBlock = await this.provider.getBlockNumber();

        return new Promise((resolve) => {
            const checkInterval = setInterval(async () => {
                const currentBlock = await this.provider.getBlockNumber();
                blocksWaited = currentBlock - startBlock;

                const bundleStats = await this.flashbotsProvider.getBundleStats(
                    bundleHash,
                    startBlock + blocksWaited
                );

                if (bundleStats?.isIncluded) {
                    clearInterval(checkInterval);
                    resolve(true);
                }

                if (blocksWaited >= maxBlocks) {
                    clearInterval(checkInterval);
                    resolve(false);
                }
            }, 12000); // Check every 12 seconds (approximate block time)
        });
    }

    async estimateBundleGas(signedTransactions: string[]): Promise<number> {
        const simulation = await this.flashbotsProvider.simulate(
            signedTransactions,
            await this.provider.getBlockNumber()
        );

        if ('error' in simulation) {
            throw new Error(`Gas estimation failed: ${simulation.error.message}`);
        }

        return simulation.totalGasUsed;
    }
} 