// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IArbitrageExecutor {
    error UnprofitableTrade();

    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amount,
        bool useUniswapFirst
    ) external returns (uint256);
} 