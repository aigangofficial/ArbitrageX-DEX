// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";

error NotImplemented();
error InsufficientFundsForRepayment();
error InvalidPath();
error Expired();
error InsufficientOutputAmount();
error TransferFailed();

contract MockDEX is IUniswapV2Router02, Ownable {
    uint256 public constant BPS = 10000;
    uint256 public constant IMPACT_BPS = 20; // 0.2% impact for 10% of reserves
    uint256 public constant FEE_BPS = 30; // 0.3% fee (standard Uniswap v2 fee)
    uint256 public constant PRECISION = 1e18;

    mapping(address => mapping(address => uint256)) public exchangeRates;
    mapping(address => uint256) public reserves;
    mapping(address => uint8) public tokenDecimals;
    bool public revertOnSwap;

    event DebugSwapCalculation(
        uint256 amountIn,
        uint256 rate,
        uint256 baseAmountOut,
        uint256 afterFee,
        uint256 afterImpact,
        uint256 impactRatio,
        uint256 impact
    );

    constructor(address weth) Ownable() {
        _transferOwnership(msg.sender);
    }

    function setExchangeRate(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOut
    ) external onlyOwner {
        require(tokenIn != address(0) && tokenOut != address(0), "Invalid token");
        require(amountIn > 0, "Invalid amountIn");
        require(amountOut > 0, "Invalid amountOut");

        // Set exchange rate
        exchangeRates[tokenIn][tokenOut] = (amountOut * PRECISION) / amountIn;
        exchangeRates[tokenOut][tokenIn] = (amountIn * PRECISION) / amountOut;

        // Update reserves
        reserves[tokenIn] = amountIn;
        reserves[tokenOut] = amountOut;
    }

    function setReserves(address token, uint256 amount) external onlyOwner {
        reserves[token] = amount;
    }

    function setTokenDecimals(address token, uint8 decimals) external onlyOwner {
        tokenDecimals[token] = decimals;
    }

    function getAmountsOut(
        uint256 amountIn,
        address[] calldata path
    ) external view override returns (uint256[] memory amounts) {
        require(path.length >= 2, "Invalid path");
        amounts = new uint256[](path.length);
        amounts[0] = amountIn;

        for (uint i = 0; i < path.length - 1; i++) {
            amounts[i + 1] = _calculateAmountOut(path[i], path[i + 1], amounts[i]);
        }

        return amounts;
    }

    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "Expired");
        require(path.length >= 2, "Invalid path");

        // Calculate amounts
        amounts = new uint256[](path.length);
        amounts[0] = amountIn;

        // Execute transfers and calculate amounts
        for (uint i = 0; i < path.length - 1; i++) {
            // Calculate output amount
            amounts[i + 1] = _calculateAmountOut(path[i], path[i + 1], amounts[i]);

            // Verify minimum output amount
            if (i == path.length - 2) {
                require(amounts[i + 1] >= amountOutMin, "Insufficient output amount");
            }

            // Transfer tokens
            require(
                IERC20(path[i]).transferFrom(
                    i == 0 ? msg.sender : address(this),
                    address(this),
                    amounts[i]
                ),
                "Transfer in failed"
            );
        }

        // Transfer final token to recipient
        require(
            IERC20(path[path.length - 1]).transfer(to, amounts[path.length - 1]),
            "Transfer out failed"
        );

        return amounts;
    }

    function _calculateAmountOut(
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) internal view returns (uint256) {
        require(exchangeRates[tokenIn][tokenOut] > 0, "Rate not set");

        // Calculate base amount using exchange rate
        uint256 baseAmountOut = (amountIn * exchangeRates[tokenIn][tokenOut]) / PRECISION;

        // Apply trading fee (0.3%)
        uint256 afterFee = (baseAmountOut * (BPS - FEE_BPS)) / BPS;

        // Calculate price impact
        uint256 impactRatio = (amountIn * PRECISION) / reserves[tokenIn];
        uint256 impact = 0;

        if (impactRatio > PRECISION / 10) {
            // If trade is > 10% of reserves
            impact = ((impactRatio - PRECISION / 10) * IMPACT_BPS) / PRECISION;
            afterFee = (afterFee * (BPS - impact)) / BPS;
        }

        return afterFee;
    }

    // Required interface implementations
    function WETH() external pure override returns (address) {
        return address(0);
    }

    function factory() external pure override returns (address) {
        return address(0);
    }

    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountADesired,
        uint256 amountBDesired,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline
    ) external override returns (uint256 amountA, uint256 amountB, uint256 liquidity) {
        revert NotImplemented();
    }

    function addLiquidityETH(
        address token,
        uint256 amountTokenDesired,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline
    )
        external
        payable
        override
        returns (uint256 amountToken, uint256 amountETH, uint256 liquidity)
    {
        revert NotImplemented();
    }

    function removeLiquidity(
        address tokenA,
        address tokenB,
        uint256 liquidity,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline
    ) external override returns (uint256 amountA, uint256 amountB) {
        revert NotImplemented();
    }

    function removeLiquidityETH(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline
    ) external override returns (uint256 amountToken, uint256 amountETH) {
        revert NotImplemented();
    }

    function removeLiquidityWithPermit(
        address tokenA,
        address tokenB,
        uint256 liquidity,
        uint256 amountAMin,
        uint256 amountBMin,
        address to,
        uint256 deadline,
        bool approveMax,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external override returns (uint256 amountA, uint256 amountB) {
        revert NotImplemented();
    }

    function removeLiquidityETHWithPermit(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline,
        bool approveMax,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external override returns (uint256 amountToken, uint256 amountETH) {
        revert NotImplemented();
    }

    function swapExactETHForTokens(
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable override returns (uint256[] memory amounts) {
        revert NotImplemented();
    }

    function swapTokensForExactTokens(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        revert NotImplemented();
    }

    function swapExactTokensForETH(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        revert NotImplemented();
    }

    function swapTokensForExactETH(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        revert NotImplemented();
    }

    function swapETHForExactTokens(
        uint256 amountOut,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable override returns (uint256[] memory amounts) {
        revert NotImplemented();
    }

    function quote(
        uint256 amountA,
        uint256 reserveA,
        uint256 reserveB
    ) external pure override returns (uint256 amountB) {
        revert NotImplemented();
    }

    function getAmountOut(
        uint256 amountIn,
        uint256 reserveIn,
        uint256 reserveOut
    ) external pure override returns (uint256 amountOut) {
        revert NotImplemented();
    }

    function getAmountIn(
        uint256 amountOut,
        uint256 reserveIn,
        uint256 reserveOut
    ) external pure override returns (uint256 amountIn) {
        revert NotImplemented();
    }

    function getAmountsIn(
        uint256 amountOut,
        address[] calldata path
    ) external view override returns (uint256[] memory amounts) {
        revert NotImplemented();
    }

    function removeLiquidityETHSupportingFeeOnTransferTokens(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline
    ) external override returns (uint256 amountETH) {
        revert NotImplemented();
    }

    function removeLiquidityETHWithPermitSupportingFeeOnTransferTokens(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline,
        bool approveMax,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external override returns (uint256 amountETH) {
        revert NotImplemented();
    }

    function swapExactTokensForTokensSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override {
        revert NotImplemented();
    }

    function swapExactETHForTokensSupportingFeeOnTransferTokens(
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable override {
        revert NotImplemented();
    }

    function swapExactTokensForETHSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override {
        revert NotImplemented();
    }

    receive() external payable {}
}
