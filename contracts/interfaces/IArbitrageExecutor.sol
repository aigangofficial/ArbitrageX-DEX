// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IArbitrageExecutor {
    function UNISWAP_V2_ROUTER() external view returns (address);
    function SUSHISWAP_V2_ROUTER() external view returns (address);

    function executeArbitrage(
        address tokenIn,
        address tokenOut,
        uint256 amount,
        address router
    ) external returns (uint256);

    function getExpectedReturn(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        bool useFirstDexFirst
    ) external view returns (uint256);

    function executeTrade(
        address router,
        address[] calldata path,
        uint256 amountIn,
        uint256 minAmountOut
    ) external returns (uint256);

    function executeUniswapSushiSwapArbitrage(
        address tokenA,
        address tokenB,
        uint256 amountIn
    ) external returns (uint256);

    function calculateCrossDEXArbitrageProfitEstimate(
        address tokenA,
        address tokenB,
        uint256 amountIn
    ) external view returns (uint256 potentialProfit, bool useUniswapFirst);

    function setMinProfitAmount(uint256 _minProfitAmount) external;

    function emergencyWithdraw(address token, uint256 amount, address recipient) external;

    function isApprovedRouter(address router) external view returns (bool);
}
