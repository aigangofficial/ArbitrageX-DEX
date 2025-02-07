// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IArbitrageExecutor {
    error UnprofitableTrade();

    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        bool isUniToSushi
    ) external returns (uint256);
} 