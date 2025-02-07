// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";

contract MockDEX is IUniswapV2Router02, Ownable {
    // Mapping of token pairs to their liquidity
    mapping(address => mapping(address => uint256)) public liquidity;
    
    // Mapping of token pairs to their exchange rates (1e18 = 1:1)
    mapping(address => mapping(address => uint256)) public rates;

    constructor() Ownable(msg.sender) {}

    function setRate(
        address tokenIn,
        address tokenOut,
        uint256 rate
    ) external onlyOwner {
        require(rate > 0, "Invalid rate");
        rates[tokenIn][tokenOut] = rate;
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

        amounts = new uint256[](path.length);
        amounts[0] = amountIn;

        // Execute swaps along the path
        for (uint i = 0; i < path.length - 1; i++) {
            address tokenIn = path[i];
            address tokenOut = path[i + 1];

            // Get exchange rate (default to 1:1 if not set)
            uint256 rate = rates[tokenIn][tokenOut];
            if (rate == 0) {
                rate = 1e18;
            }

            // Calculate amount out based on exchange rate
            uint256 amountOut = (amounts[i] * rate) / 1e18;
            amounts[i + 1] = amountOut;

            // Transfer tokens
            require(
                IERC20(tokenIn).transferFrom(i == 0 ? msg.sender : address(this), address(this), amounts[i]),
                "Transfer in failed"
            );
            require(
                IERC20(tokenOut).transfer(i == path.length - 2 ? to : address(this), amountOut),
                "Transfer out failed"
            );

            // Update liquidity
            liquidity[tokenIn][tokenOut] += amounts[i];
            liquidity[tokenOut][tokenIn] -= amountOut;
        }

        require(amounts[amounts.length - 1] >= amountOutMin, "Insufficient output amount");
        return amounts;
    }

    function addLiquidity(
        address tokenA,
        address tokenB,
        uint256 amountA,
        uint256 amountB
    ) external returns (uint256) {
        require(amountA > 0 && amountB > 0, "Invalid amounts");
        require(tokenA != tokenB, "Same token");

        // Check if tokens are already in the contract
        uint256 balanceA = IERC20(tokenA).balanceOf(address(this));
        uint256 balanceB = IERC20(tokenB).balanceOf(address(this));

        // Transfer only if needed
        if (balanceA < amountA) {
            require(
                IERC20(tokenA).transferFrom(msg.sender, address(this), amountA - balanceA),
                "Transfer A failed"
            );
        }
        if (balanceB < amountB) {
            require(
                IERC20(tokenB).transferFrom(msg.sender, address(this), amountB - balanceB),
                "Transfer B failed"
            );
        }

        // Update liquidity
        liquidity[tokenA][tokenB] += amountA;
        liquidity[tokenB][tokenA] += amountB;

        return amountA; // Return liquidity tokens (simplified)
    }

    // Required interface functions with minimal implementations
    function WETH() external pure override returns (address) {
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
        require(deadline >= block.timestamp, "Expired");
        return (0, 0, 0);
    }

    function addLiquidityETH(
        address token,
        uint256 amountTokenDesired,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline
    ) external payable override returns (uint256 amountToken, uint256 amountETH, uint256 liquidity) {
        require(deadline >= block.timestamp, "Expired");
        return (0, 0, 0);
    }

    function factory() external pure override returns (address) {
        return address(0);
    }

    function getAmountIn(uint256 amountOut, uint256 reserveIn, uint256 reserveOut) external pure override returns (uint256 amountIn) {
        return 0;
    }

    function getAmountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut) external pure override returns (uint256 amountOut) {
        return 0;
    }

    function getAmountsIn(uint256 amountOut, address[] calldata path) external view override returns (uint256[] memory amounts) {
        return new uint256[](0);
    }

    function getAmountsOut(uint256 amountIn, address[] calldata path) external view override returns (uint256[] memory amounts) {
        require(path.length >= 2, "Invalid path");

        amounts = new uint256[](path.length);
        amounts[0] = amountIn;

        for (uint i = 0; i < path.length - 1; i++) {
            address tokenIn = path[i];
            address tokenOut = path[i + 1];

            uint256 rate = rates[tokenIn][tokenOut];
            if (rate == 0) {
                rate = 1e18;
            }

            // Calculate amount out based on exchange rate and apply 0.3% fee
            amounts[i + 1] = (amounts[i] * rate * 997) / (1e18 * 1000);
        }

        return amounts;
    }

    function quote(uint256 amountA, uint256 reserveA, uint256 reserveB) external pure override returns (uint256 amountB) {
        return 0;
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
        require(deadline >= block.timestamp, "Expired");
        return (0, 0);
    }

    function removeLiquidityETH(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline
    ) external override returns (uint256 amountToken, uint256 amountETH) {
        require(deadline >= block.timestamp, "Expired");
        return (0, 0);
    }

    function removeLiquidityETHSupportingFeeOnTransferTokens(
        address token,
        uint256 liquidity,
        uint256 amountTokenMin,
        uint256 amountETHMin,
        address to,
        uint256 deadline
    ) external override returns (uint256 amountETH) {
        require(deadline >= block.timestamp, "Expired");
        return 0;
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
        require(deadline >= block.timestamp, "Expired");
        return (0, 0);
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
        require(deadline >= block.timestamp, "Expired");
        return 0;
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
        require(deadline >= block.timestamp, "Expired");
        return (0, 0);
    }

    function swapETHForExactTokens(uint256 amountOut, address[] calldata path, address to, uint256 deadline)
        external
        payable
        override
        returns (uint256[] memory amounts)
    {
        require(deadline >= block.timestamp, "Expired");
        return new uint256[](0);
    }

    function swapExactETHForTokens(uint256 amountOutMin, address[] calldata path, address to, uint256 deadline)
        external
        payable
        override
        returns (uint256[] memory amounts)
    {
        require(deadline >= block.timestamp, "Expired");
        return new uint256[](0);
    }

    function swapExactETHForTokensSupportingFeeOnTransferTokens(
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable override {
        require(deadline >= block.timestamp, "Expired");
    }

    function swapExactTokensForETH(uint256 amountIn, uint256 amountOutMin, address[] calldata path, address to, uint256 deadline)
        external
        override
        returns (uint256[] memory amounts)
    {
        require(deadline >= block.timestamp, "Expired");
        return new uint256[](0);
    }

    function swapExactTokensForETHSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override {
        require(deadline >= block.timestamp, "Expired");
    }

    function swapExactTokensForTokensSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override {
        require(deadline >= block.timestamp, "Expired");
    }

    function swapTokensForExactETH(uint256 amountOut, uint256 amountInMax, address[] calldata path, address to, uint256 deadline)
        external
        override
        returns (uint256[] memory amounts)
    {
        require(deadline >= block.timestamp, "Expired");
        return new uint256[](0);
    }

    function swapTokensForExactTokens(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "Expired");
        return new uint256[](0);
    }
} 