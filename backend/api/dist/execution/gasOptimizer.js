"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ethers_1 = require("ethers");
const config_1 = require("../api/config");
const logger_1 = require("../api/utils/logger");
class GasOptimizer {
    constructor() {
        this.MAX_GAS_PRICE = ethers_1.ethers.parseUnits('100', 'gwei');
        this.MIN_GAS_PRICE = ethers_1.ethers.parseUnits('5', 'gwei');
        this.provider = new ethers_1.ethers.JsonRpcProvider(config_1.config.network.rpc);
        this.gasPriceHistory = [];
        this.maxHistorySize = 100;
    }
    async getOptimalGasPrice() {
        try {
            const currentGasPrice = await this.provider.getFeeData();
            if (!currentGasPrice.gasPrice) {
                throw new Error('Failed to get current gas price');
            }
            this.gasPriceHistory.push(Number(currentGasPrice.gasPrice));
            if (this.gasPriceHistory.length > this.maxHistorySize) {
                this.gasPriceHistory.shift();
            }
            const optimalPrice = this.calculateOptimalPrice(currentGasPrice.gasPrice);
            logger_1.logger.info('Calculated optimal gas price:', {
                current: currentGasPrice.gasPrice.toString(),
                optimal: optimalPrice.toString(),
            });
            return optimalPrice;
        }
        catch (error) {
            logger_1.logger.error('Error getting optimal gas price:', error);
            throw error;
        }
    }
    calculateOptimalPrice(currentPrice) {
        if (this.gasPriceHistory.length < 10) {
            return currentPrice;
        }
        const avg = this.calculateAverage();
        const std = this.calculateStandardDeviation(avg);
        if (Number(currentPrice) < avg - std) {
            return currentPrice;
        }
        if (Number(currentPrice) > avg + std) {
            return BigInt(Math.floor(avg * 1.1));
        }
        return currentPrice;
    }
    calculateAverage() {
        const sum = this.gasPriceHistory.reduce((a, b) => a + b, 0);
        return sum / this.gasPriceHistory.length;
    }
    calculateStandardDeviation(avg) {
        const squareDiffs = this.gasPriceHistory.map(price => {
            const diff = price - avg;
            return diff * diff;
        });
        const avgSquareDiff = squareDiffs.reduce((a, b) => a + b, 0) / squareDiffs.length;
        return Math.sqrt(avgSquareDiff);
    }
    async estimateGasLimit(to, data, value = BigInt(0)) {
        try {
            const gasEstimate = await this.provider.estimateGas({
                to,
                data,
                value,
            });
            const gasBuffer = (gasEstimate * BigInt(120)) / BigInt(100);
            logger_1.logger.info('Estimated gas limit:', {
                estimate: gasEstimate.toString(),
                withBuffer: gasBuffer.toString(),
            });
            return gasBuffer;
        }
        catch (error) {
            logger_1.logger.error('Error estimating gas limit:', error);
            throw error;
        }
    }
    async waitForOptimalGas(maxWaitTime = 300000) {
        const startTime = Date.now();
        let optimalPrice;
        while (true) {
            optimalPrice = await this.getOptimalGasPrice();
            if (Number(optimalPrice) < this.calculateAverage() || Date.now() - startTime > maxWaitTime) {
                return optimalPrice;
            }
            await new Promise(resolve => setTimeout(resolve, 15000));
        }
    }
    async calculateOptimalGas(provider) {
        try {
            const feeData = await provider.getFeeData();
            const gasPrice = feeData.gasPrice;
            if (!gasPrice) {
                throw new Error('Failed to get gas price');
            }
            if (gasPrice > this.MAX_GAS_PRICE) {
                return BigInt(0);
            }
            if (gasPrice < this.MIN_GAS_PRICE) {
                return this.MIN_GAS_PRICE;
            }
            return gasPrice + (gasPrice * BigInt(10) / BigInt(100));
        }
        catch (error) {
            console.error('Error calculating optimal gas:', error);
            return this.MAX_GAS_PRICE;
        }
    }
    async isGasPriceFavorable(provider) {
        const feeData = await provider.getFeeData();
        const gasPrice = feeData.gasPrice;
        return gasPrice ? gasPrice <= this.MAX_GAS_PRICE : false;
    }
    getMaxGasPrice() {
        return this.MAX_GAS_PRICE;
    }
    getMinGasPrice() {
        return this.MIN_GAS_PRICE;
    }
}
exports.default = GasOptimizer;
//# sourceMappingURL=gasOptimizer.js.map