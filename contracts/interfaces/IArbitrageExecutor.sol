// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

interface IArbitrageExecutor {
    error UnprofitableTrade();

    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amount,
        bool useUniswapFirst
    ) external returns (uint256);

    function getExpectedReturn(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        bool useUniswapFirst
    ) external view returns (uint256);
}
