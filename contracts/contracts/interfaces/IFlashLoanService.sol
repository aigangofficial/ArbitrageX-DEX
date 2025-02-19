// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

interface IFlashLoanService {
    error UnprofitableTrade();
    error InsufficientFundsForRepayment();
    error InvalidPath();
    error InvalidTokenAddresses();
    error InvalidAmount();
    error InvalidMinProfit();
    error TransferFailed();
    error InvalidFlashLoanProvider();
    error InvalidArbitrageExecutor();
    error InvalidTokenApproval();
    error InvalidFlashLoanAmount();
    error FlashLoanFailed();
    error InvalidParameter();

    function executeFlashLoan(
        address[] calldata assets,
        uint256[] calldata amounts,
        bytes calldata tradeData
    ) external;

    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external returns (bool);

    function executeArbitrage(
        address token,
        uint256 amount,
        bytes calldata data
    ) external returns (uint256);

    function setArbitrageExecutor(address _arbitrageExecutor) external;

    function setMinProfitBps(uint16 _minProfitBps) external;

    function withdrawToken(address token, uint256 amount) external;

    function approveTokens(address[] calldata tokens, address[] calldata spenders) external;

    function addFlashLoanProvider(address provider) external;

    function removeFlashLoanProvider(address provider) external;
}
