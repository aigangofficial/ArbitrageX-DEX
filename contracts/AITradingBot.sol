// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./interfaces/IArbitrageExecutor.sol";
import "./SecurityAdmin.sol";

/**
 * @title AITradingBot
 * @dev AI-powered trading bot that interfaces with the ArbitrageExecutor
 */
contract AITradingBot is Ownable, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    IArbitrageExecutor public arbitrageExecutor;
    SecurityAdmin public securityAdmin;

    // Trading parameters
    uint256 public minTradeAmount;
    uint256 public maxTradeAmount;
    uint256 public minProfitBps;

    // Custom errors
    error InvalidAmount(uint256 amount, uint256 min, uint256 max);
    error InsufficientProfit(uint256 expected, uint256 minimum);
    error TokenNotWhitelisted(address token);
    error InvalidParameters(string reason);
    error TradeExecutionFailed(string reason);

    // Events
    event TradeExecuted(
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amount,
        uint256 profit
    );
    event ParametersUpdated(uint256 minTradeAmount, uint256 maxTradeAmount, uint256 minProfitBps);
    event TokensApproved(address[] tokens, address spender);

    constructor(
        address _arbitrageExecutor,
        address _securityAdmin,
        uint256 _minTradeAmount,
        uint256 _maxTradeAmount,
        uint256 _minProfitBps
    ) Ownable() ReentrancyGuard() Pausable() {
        if (_minTradeAmount > _maxTradeAmount) revert InvalidParameters("min > max");
        if (_minProfitBps == 0) revert InvalidParameters("zero profit threshold");

        arbitrageExecutor = IArbitrageExecutor(_arbitrageExecutor);
        securityAdmin = SecurityAdmin(_securityAdmin);
        minTradeAmount = _minTradeAmount;
        maxTradeAmount = _maxTradeAmount;
        minProfitBps = _minProfitBps;
    }

    /**
     * @dev Approve multiple tokens for the ArbitrageExecutor to spend
     * @param tokens Array of token addresses to approve
     * @param spender Address that will be approved to spend the tokens
     */
    function approveTokens(address[] calldata tokens, address spender) external onlyOwner {
        for (uint256 i = 0; i < tokens.length; i++) {
            IERC20(tokens[i]).forceApprove(spender, type(uint256).max);
        }
        emit TokensApproved(tokens, spender);
    }

    /**
     * @dev Execute a trade based on AI strategy signals
     * @param tokenIn Address of input token
     * @param tokenOut Address of output token
     * @param amount Amount of tokenIn to trade
     * @param expectedProfit Expected profit in basis points
     */
    function executeTrade(
        address tokenIn,
        address tokenOut,
        uint256 amount,
        uint256 expectedProfit
    ) external onlyOwner nonReentrant whenNotPaused {
        // Validate parameters
        if (amount < minTradeAmount || amount > maxTradeAmount) {
            revert InvalidAmount(amount, minTradeAmount, maxTradeAmount);
        }
        if (expectedProfit < minProfitBps) {
            revert InsufficientProfit(expectedProfit, minProfitBps);
        }
        if (!securityAdmin.isTokenWhitelisted(tokenIn)) {
            revert TokenNotWhitelisted(tokenIn);
        }
        if (!securityAdmin.isTokenWhitelisted(tokenOut)) {
            revert TokenNotWhitelisted(tokenOut);
        }

        // Transfer tokens from sender to this contract
        IERC20(tokenIn).safeTransferFrom(msg.sender, address(this), amount);

        // Approve ArbitrageExecutor to spend tokens
        IERC20(tokenIn).forceApprove(address(arbitrageExecutor), amount);

        // Create path for the trade
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        try
            arbitrageExecutor.executeArbitrage(
                tokenIn,
                tokenOut,
                amount,
                arbitrageExecutor.UNISWAP_V2_ROUTER()
            )
        returns (uint256 actualProfit) {
            // Reset approval
            IERC20(tokenIn).forceApprove(address(arbitrageExecutor), 0);

            emit TradeExecuted(tokenIn, tokenOut, amount, actualProfit);
        } catch Error(string memory reason) {
            // Reset approval on failure
            IERC20(tokenIn).forceApprove(address(arbitrageExecutor), 0);
            revert TradeExecutionFailed(reason);
        }
    }

    /**
     * @dev Update trading parameters
     * @param _minTradeAmount New minimum trade amount
     * @param _maxTradeAmount New maximum trade amount
     * @param _minProfitBps New minimum profit in basis points
     */
    function updateParameters(
        uint256 _minTradeAmount,
        uint256 _maxTradeAmount,
        uint256 _minProfitBps
    ) external onlyOwner {
        if (_minTradeAmount > _maxTradeAmount) {
            revert InvalidParameters("min > max");
        }
        if (_minProfitBps == 0) {
            revert InvalidParameters("zero profit threshold");
        }

        minTradeAmount = _minTradeAmount;
        maxTradeAmount = _maxTradeAmount;
        minProfitBps = _minProfitBps;

        emit ParametersUpdated(_minTradeAmount, _maxTradeAmount, _minProfitBps);
    }

    /**
     * @dev Emergency pause trading
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @dev Resume trading
     */
    function unpause() external onlyOwner {
        _unpause();
    }
}
