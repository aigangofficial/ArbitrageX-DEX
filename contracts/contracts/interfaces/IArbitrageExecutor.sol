// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

interface IArbitrageExecutor {
    error UnprofitableTrade();
    error InvalidPath();
    error InvalidTokenAddresses();
    error InvalidAmount();
    error InvalidMinProfit();
    error TransferFailed();
    error InvalidTokenApproval();
    error InvalidParameter();

    function executeArbitrage(
        address loanToken,
        uint256 loanAmount,
        bytes calldata tradeData
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
}
