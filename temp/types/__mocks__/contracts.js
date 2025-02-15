"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MockFlashLoanContract = exports.mockFlashLoanService = exports.FlashLoanService = void 0;
class FlashLoanService {
    address;
    constructor(address) {
        this.address = address;
    }
    async executeArbitrage(tokenA, tokenB, amount) {
        // Mock implementation that uses all parameters
        console.log(`Mock arbitrage execution:
      Token A: ${tokenA}
      Token B: ${tokenB}
      Amount: ${amount}
      Contract Address: ${this.address}
    `);
        // Return deterministic mock data based on inputs
        const mockHash = Buffer.from(`${tokenA}-${tokenB}-${amount}-${this.address}`).toString('hex');
        return {
            to: this.address,
            data: '0x' + mockHash,
            wait: async () => ({
                hash: '0x' + mockHash.padEnd(64, '0'),
                gasUsed: BigInt(100000),
            }),
        };
    }
}
exports.FlashLoanService = FlashLoanService;
const mockFlashLoanService = (_address, _provider) => ({
    executeArbitrage: async (_tokenA, _tokenB, _exchangeA, _exchangeB, _amount) => {
        // Mock implementation
        return Promise.resolve({});
    },
});
exports.mockFlashLoanService = mockFlashLoanService;
class MockFlashLoanContract {
    address;
    constructor(address) {
        this.address = address;
    }
    async executeArbitrage(tokenA, tokenB, amount) {
        // Mock implementation that uses all parameters
        console.log(`Mock arbitrage execution:
      Token A: ${tokenA}
      Token B: ${tokenB}
      Amount: ${amount}
      Contract Address: ${this.address}
    `);
        // Return a deterministic mock transaction hash based on inputs
        const mockHash = Buffer.from(`${tokenA}-${tokenB}-${amount}-${this.address}`).toString('hex');
        return { hash: '0x' + mockHash.padEnd(64, '0') };
    }
}
exports.MockFlashLoanContract = MockFlashLoanContract;
