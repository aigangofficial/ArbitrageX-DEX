"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MockFlashLoanService = void 0;
class MockFlashLoanService {
    constructor(_address, _provider) {
        // Mock implementation
    }
    async executeArbitrage(_tokenA, _tokenB, _exchangeA, _exchangeB, _amount) {
        // Mock implementation
        return Promise.resolve({});
    }
}
exports.MockFlashLoanService = MockFlashLoanService;
