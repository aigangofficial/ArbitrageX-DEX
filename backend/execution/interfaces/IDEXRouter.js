"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DEXRouterFactory = exports.ROUTER_ABI = void 0;
const ethers_1 = require("ethers");
exports.ROUTER_ABI = [
    'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)',
    'function factory() external pure returns (address)',
    'function WETH() external pure returns (address)',
    'function swapExactTokensForTokens(uint amountIn, uint amountOutMin, address[] calldata path, address to, uint deadline) external returns (uint[] memory amounts)'
];
class DEXRouterFactory {
    static connect(address, provider) {
        return new ethers_1.BaseContract(address, exports.ROUTER_ABI, provider);
    }
}
exports.DEXRouterFactory = DEXRouterFactory;
//# sourceMappingURL=IDEXRouter.js.map