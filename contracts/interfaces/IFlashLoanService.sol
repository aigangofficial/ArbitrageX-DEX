// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

interface IFlashLoanService {
    error UnprofitableTrade();
    error InsufficientFundsForRepayment();
    error InvalidPath();
    error InvalidTokenAddresses();
    error InvalidAmount();
    error InvalidMinProfit();

    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amount,
        bytes calldata params
    ) external;

    function executeOperation(
        address asset,
        uint256 amount,
        uint256 fee,
        address initiator,
        bytes calldata params
    ) external returns (bool);

    function setArbitrageExecutor(address _arbitrageExecutor) external;

    function setMinProfitBps(uint16 _minProfitBps) external;

    function withdrawToken(address token, uint256 amount) external;

    function approveTokens(address[] calldata tokens, address[] calldata spenders) external;
}
