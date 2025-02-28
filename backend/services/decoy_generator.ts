import { ethers } from 'ethers';
import { getConfig } from '../api/config';

interface FlashbotsTransaction {
    to: string;
    data: string;
    value: bigint;
    gasLimit: bigint;
}

export class DecoyGenerator {
    private config = getConfig();
    private knownSelectors: string[];
    private contracts: string[];

    constructor() {
        this.knownSelectors = this.config.flashbots.monitoring.knownSelectors;
        this.contracts = this.config.flashbots.decoy.contracts;
    }

    public generateDecoys(count: number): FlashbotsTransaction[] {
        const decoys: FlashbotsTransaction[] = [];
        
        for (let i = 0; i < count; i++) {
            decoys.push(this._generateSingleDecoy());
        }
        
        return decoys;
    }

    private _generateSingleDecoy(): FlashbotsTransaction {
        const targetContract = this._getRandomContract();
        const selector = this._getRandomSelector();
        const value = this._generateRandomValue();
        const gasLimit = this._estimateGasLimit();

        return {
            to: targetContract,
            data: this._generateCalldata(selector),
            value,
            gasLimit
        };
    }

    private _getRandomContract(): string {
        return this.contracts[Math.floor(Math.random() * this.contracts.length)];
    }

    private _getRandomSelector(): string {
        return this.knownSelectors[Math.floor(Math.random() * this.knownSelectors.length)];
    }

    private _generateRandomValue(): bigint {
        const baseValue = ethers.parseEther('0.01'); // 0.01 ETH base
        const variation = this.config.flashbots.decoy.valueVariation;
        const randomMultiplier = 1 + (Math.random() * variation);
        return BigInt(Math.floor(Number(baseValue) * randomMultiplier));
    }

    private _estimateGasLimit(): bigint {
        const baseGas = this.config.flashbots.gas.base;
        const variance = this.config.flashbots.gas.variance;
        const randomVariance = Math.floor(Math.random() * variance);
        return BigInt(baseGas + randomVariance);
    }

    private _generateCalldata(selector: string): string {
        // Generate random parameters based on common function signatures
        const randomParams = this._generateRandomParameters();
        return selector + randomParams.slice(2); // Remove 0x from params
    }

    private _generateRandomParameters(): string {
        // Generate random parameters that look legitimate
        // This is a simplified version - expand based on your needs
        const options = [
            () => ethers.AbiCoder.defaultAbiCoder().encode(['uint256'], [Math.floor(Math.random() * 1000000)]),
            () => ethers.AbiCoder.defaultAbiCoder().encode(['address'], [ethers.Wallet.createRandom().address]),
            () => ethers.AbiCoder.defaultAbiCoder().encode(
                ['uint256', 'uint256'],
                [Math.floor(Math.random() * 1000000), Math.floor(Math.random() * 1000000)]
            )
        ];

        const randomOption = options[Math.floor(Math.random() * options.length)];
        return randomOption();
    }
} 