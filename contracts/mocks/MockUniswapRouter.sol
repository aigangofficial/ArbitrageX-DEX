// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MockUniswapRouter is IUniswapV2Router02 {
    uint256 public constant BPS = 10000;
    uint256 public constant IMPACT_BPS = 200;  // 2% impact for 10% of reserves
    uint256 public constant FEE_BPS = 30;     // 0.3% fee
    uint256 public constant PRECISION = 1e18;

    mapping(address => mapping(address => uint256)) public exchangeRates;
    mapping(address => mapping(address => uint256)) public reserves;
    mapping(address => uint8) public tokenDecimals;

    event RateUpdated(address tokenIn, address tokenOut, uint256 rate);
    event ReservesUpdated(address tokenIn, address tokenOut, uint256 reserveIn, uint256 reserveOut);

    address private immutable wethAddress;

    constructor(address _weth) {
        require(_weth != address(0), "Invalid WETH address");
        wethAddress = _weth;
        // Example: Initialize USDC with 6 decimals
        tokenDecimals[0x63fea6E447F120B8Faf85B53cdaD8348e645D80E] = 6;
    }

    function WETH() external pure override returns (address) { 
        return 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    }

    function getWETHAddress() external view returns (address) {
        return wethAddress;
    }

    function setTokenDecimals(address token, uint8 decimals) external {
        tokenDecimals[token] = decimals;
    }

    function setExchangeRate(address tokenIn, address tokenOut, uint256 rate) external {
        exchangeRates[tokenIn][tokenOut] = rate;
        // Calculate and set reverse rate
        uint8 decimalsIn = tokenDecimals[tokenIn];
        uint8 decimalsOut = tokenDecimals[tokenOut];
        uint256 reverseRate = _calculateReverseRate(rate, decimalsIn, decimalsOut);
        exchangeRates[tokenOut][tokenIn] = reverseRate;
        
        emit RateUpdated(tokenIn, tokenOut, rate);
        emit RateUpdated(tokenOut, tokenIn, reverseRate);
        
        // Update reserves to match rate
        reserves[tokenIn][tokenOut] = rate;
        reserves[tokenOut][tokenIn] = reverseRate;
        
        emit ReservesUpdated(tokenIn, tokenOut, rate, reverseRate);
    }

    function _calculateReverseRate(uint256 rate, uint8 decimalsIn, uint8 decimalsOut) internal pure returns (uint256) {
        uint256 baseUnit = 10**18;  // Use 18 decimals as base
        if (decimalsIn == decimalsOut) {
            return (baseUnit * baseUnit) / rate;
        }
        
        if (decimalsIn > decimalsOut) {
            uint256 scaledRate = rate * 10**(decimalsIn - decimalsOut);
            return (baseUnit * baseUnit) / scaledRate;
        } else {
            uint256 scaledRate = rate / 10**(decimalsOut - decimalsIn);
            return (baseUnit * baseUnit) / scaledRate;
        }
    }

    function getAmountsOut(uint256 amountIn, address[] memory path) public view returns (uint256[] memory amounts) {
        require(path.length >= 2, "Invalid path");
        amounts = new uint256[](path.length);
        amounts[0] = amountIn;

        for (uint i; i < path.length - 1; i++) {
            uint256 rate = exchangeRates[path[i]][path[i + 1]];
            require(rate > 0, "Rate not set");

            // Get token decimals
            uint8 decimalsIn = tokenDecimals[path[i]] == 0 ? 18 : tokenDecimals[path[i]];
            uint8 decimalsOut = tokenDecimals[path[i + 1]] == 0 ? 18 : tokenDecimals[path[i + 1]];

            // Calculate base amount out before price impact
            uint256 amountOut;
            if (decimalsIn == decimalsOut) {
                amountOut = (amountIn * rate) / PRECISION;
            } else if (decimalsIn > decimalsOut) {
                // Example: ETH (18) -> USDC (6)
                amountOut = (amountIn * rate) / (10 ** decimalsIn);
            } else {
                // Example: USDC (6) -> ETH (18)
                amountOut = (amountIn * rate * (10 ** (decimalsOut - decimalsIn))) / PRECISION;
            }

            // Calculate price impact based on trade size relative to reserves
            uint256 reserveIn = reserves[path[i]][path[i + 1]];
            uint256 priceImpactBps = IMPACT_BPS; // Base 2% impact
            if (reserveIn > 0) {
                uint256 tradeRatio = (amountIn * BPS) / reserveIn;
                if (tradeRatio > 500) { // If trade is > 5% of reserves
                    priceImpactBps = IMPACT_BPS + ((tradeRatio - 500) * 2) / 100;
                    if (priceImpactBps > 400) priceImpactBps = 400; // Cap at 4%
                }
            }

            // Apply price impact and trading fee
            uint256 priceImpact = (amountOut * priceImpactBps) / BPS;
            uint256 tradingFee = (amountOut * FEE_BPS) / BPS;
            amountOut = amountOut - priceImpact - tradingFee;

            amounts[i + 1] = amountOut;
            amountIn = amountOut; // For multi-hop trades
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
        amounts = getAmountsOut(amountIn, path);
        require(amounts[amounts.length - 1] >= amountOutMin, "Insufficient output amount");

        IERC20(path[0]).transferFrom(msg.sender, address(this), amountIn);
        IERC20(path[path.length - 1]).transfer(to, amounts[amounts.length - 1]);

        return amounts;
    }

    function swapTokensForExactTokens(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "Expired");
        
        uint256 baseAmountIn = (amountOut * PRECISION) / exchangeRates[path[0]][path[1]];
        
        // Account for trading fee
        baseAmountIn = (baseAmountIn * BPS) / (BPS - FEE_BPS);
        
        // Calculate price impact
        uint256 priceImpact = 0;
        if (baseAmountIn * BPS > reserves[path[0]][path[1]] * IMPACT_BPS) {
            priceImpact = (baseAmountIn * IMPACT_BPS * 2) / reserves[path[0]][path[1]];
            baseAmountIn = baseAmountIn * BPS / (BPS - priceImpact);
        }
        
        require(baseAmountIn <= amountInMax, "Excessive input amount");
        
        IERC20(path[0]).transferFrom(msg.sender, address(this), baseAmountIn);
        IERC20(path[path.length - 1]).transfer(to, amountOut);
        
        amounts = new uint256[](path.length);
        amounts[0] = baseAmountIn;
        amounts[amounts.length - 1] = amountOut;
    }

    function getAmountsIn(uint256 amountOut, address[] calldata path) public view override returns (uint256[] memory amounts) {
        require(path.length >= 2, "Invalid path");
        amounts = new uint256[](path.length);
        amounts[amounts.length - 1] = amountOut;
        
        for (uint i = path.length - 1; i > 0; i--) {
            address tokenIn = path[i-1];
            address tokenOut = path[i];
            uint256 baseRate = exchangeRates[tokenIn][tokenOut];
            require(baseRate > 0, "Rate not set");
            
            uint256 reserveIn = reserves[tokenIn][tokenOut];
            require(reserveIn > 0, "Insufficient liquidity");
            
            // Calculate base amount without impact
            uint256 baseAmountIn = (amounts[i] * PRECISION) / baseRate;
            
            // Account for trading fee
            baseAmountIn = (baseAmountIn * FEE_BPS) / BPS;
            
            // Calculate price impact
            uint256 impactRatio = (baseAmountIn * PRECISION) / reserveIn;
            uint256 priceImpact = (impactRatio * IMPACT_BPS) / BPS;
            if (priceImpact > IMPACT_BPS) {
                priceImpact = IMPACT_BPS;
            }
            
            // Apply price impact
            amounts[i-1] = (baseAmountIn * (BPS + priceImpact)) / BPS;
        }
        
        return amounts;
    }

    function factory() external pure override returns (address) { return address(0); }
    
    function quote(uint256 amountA, uint256 reserveA, uint256 reserveB) external pure override returns (uint256) {
        require(amountA > 0, "Insufficient amount");
        require(reserveA > 0 && reserveB > 0, "Insufficient liquidity");
        return (amountA * reserveB) / reserveA;
    }
    
    function getAmountOut(uint amountIn, uint reserveIn, uint reserveOut) public pure returns (uint amountOut) {
        require(amountIn > 0, 'INSUFFICIENT_INPUT_AMOUNT');
        require(reserveIn > 0 && reserveOut > 0, 'INSUFFICIENT_LIQUIDITY');
        
        // Calculate base amount with 0.3% fee
        uint amountInWithFee = amountIn * 997;
        
        // Calculate output with constant product formula
        uint numerator = amountInWithFee * reserveOut;
        uint denominator = (reserveIn * 1000) + amountInWithFee;
        
        // Calculate base output amount
        amountOut = numerator / denominator;
        
        // Apply slippage impact based on trade size relative to reserves
        uint slippageImpact = (amountIn * 1000) / reserveIn;  // In basis points (0.01%)
        if (slippageImpact > 100) {  // If trade size > 1% of reserves
            // Apply additional slippage (up to 2% for large trades)
            uint additionalSlippage = (slippageImpact - 100) * 2;  // 2 bps per 0.01% above threshold
            if (additionalSlippage > 200) additionalSlippage = 200;  // Cap at 2%
            amountOut = amountOut * (10000 - additionalSlippage) / 10000;
        }
    }
    
    function getAmountIn(uint amountOut, uint reserveIn, uint reserveOut) public pure returns (uint amountIn) {
        require(amountOut > 0, 'INSUFFICIENT_OUTPUT_AMOUNT');
        require(reserveIn > 0 && reserveOut > 0, 'INSUFFICIENT_LIQUIDITY');
        
        uint numerator = reserveIn * amountOut * 1000;
        uint denominator = (reserveOut - amountOut) * 997;
        amountIn = (numerator / denominator) + 1;
    }

    // Implement remaining interface functions with minimal functionality
    function addLiquidity(
        address,
        address,
        uint256,
        uint256,
        uint256,
        uint256,
        address,
        uint256
    ) external pure override returns (uint256, uint256, uint256) {
        return (0, 0, 0);
    }

    function addLiquidityETH(
        address,
        uint256,
        uint256,
        uint256,
        address,
        uint256
    ) external payable override returns (uint256, uint256, uint256) {
        return (0, 0, 0);
    }

    function removeLiquidity(
        address,
        address,
        uint256,
        uint256,
        uint256,
        address,
        uint256
    ) external pure override returns (uint256, uint256) {
        return (0, 0);
    }

    function removeLiquidityETH(
        address,
        uint256,
        uint256,
        uint256,
        address,
        uint256
    ) external pure override returns (uint256, uint256) {
        return (0, 0);
    }

    function removeLiquidityWithPermit(
        address,
        address,
        uint256,
        uint256,
        uint256,
        address,
        uint256,
        bool,
        uint8,
        bytes32,
        bytes32
    ) external pure override returns (uint256, uint256) {
        return (0, 0);
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
    ) external pure override returns (uint256, uint256) {
        return (0, 0);
    }

    function swapExactETHForTokens(
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable override returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "Expired");
        require(path[0] == this.WETH(), "Invalid path");

        amounts = getAmountsOut(msg.value, path);
        require(amounts[amounts.length - 1] >= amountOutMin, "Insufficient output amount");

        IERC20(path[path.length - 1]).transfer(to, amounts[amounts.length - 1]);
        return amounts;
    }

    function swapTokensForExactETH(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "Expired");
        require(path.length >= 2 && path[path.length-1] == this.WETH(), "Invalid path");
        
        amounts = this.getAmountsIn(amountOut, path);
        require(amounts[0] <= amountInMax, "Excessive input amount");
        
        IERC20(path[0]).transferFrom(msg.sender, address(this), amounts[0]);
        payable(to).transfer(amountOut);
        return amounts;
    }

    function swapExactTokensForETH(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "Expired");
        require(path.length >= 2 && path[path.length-1] == this.WETH(), "Invalid path");
        
        amounts = getAmountsOut(amountIn, path);
        require(amounts[amounts.length - 1] >= amountOutMin, "Insufficient output amount");
        
        IERC20(path[0]).transferFrom(msg.sender, address(this), amountIn);
        payable(to).transfer(amounts[amounts.length - 1]);
        return amounts;
    }

    function swapETHForExactTokens(
        uint256 amountOut,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable override returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "Expired");
        require(path[0] == this.WETH(), "Invalid path");
        
        amounts = this.getAmountsIn(amountOut, path);
        require(amounts[0] <= msg.value, "Excessive input amount");
        
        IERC20(path[path.length - 1]).transfer(to, amountOut);
        
        // Refund excess ETH
        if (msg.value > amounts[0]) {
            payable(msg.sender).transfer(msg.value - amounts[0]);
        }
        return amounts;
    }

    function swapExactTokensForTokensSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override {
        require(deadline >= block.timestamp, "Expired");
        IERC20(path[0]).transferFrom(msg.sender, address(this), amountIn);
        
        uint256 balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
        _swapSupportingFeeOnTransferTokens(path, to);
        
        require(
            IERC20(path[path.length - 1]).balanceOf(to) - balanceBefore >= amountOutMin,
            "Insufficient output amount"
        );
    }

    function swapExactETHForTokensSupportingFeeOnTransferTokens(
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable override {
        require(deadline >= block.timestamp, "Expired");
        require(path[0] == this.WETH(), "Invalid path");
        
        uint256 balanceBefore = IERC20(path[path.length - 1]).balanceOf(to);
        _swapSupportingFeeOnTransferTokens(path, to);
        
        require(
            IERC20(path[path.length - 1]).balanceOf(to) - balanceBefore >= amountOutMin,
            "Insufficient output amount"
        );
    }

    function swapExactTokensForETHSupportingFeeOnTransferTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override {
        require(deadline >= block.timestamp, "Expired");
        require(path.length >= 2 && path[path.length-1] == this.WETH(), "Invalid path");
        
        IERC20(path[0]).transferFrom(msg.sender, address(this), amountIn);
        _swapSupportingFeeOnTransferTokens(path, address(this));
        
        uint256 amountOut = address(this).balance;
        require(amountOut >= amountOutMin, "Insufficient output amount");
        
        payable(to).transfer(amountOut);
    }

    function _swapSupportingFeeOnTransferTokens(address[] memory path, address _to) internal {
        for (uint i; i < path.length - 1; i++) {
            (address input, address output) = (path[i], path[i + 1]);
            uint256 amountInput = IERC20(input).balanceOf(address(this));
            _swap(amountInput, input, output, _to);
        }
    }

    function _swap(uint256 amount, address tokenIn, address tokenOut, address to) internal {
        address[] memory path = _getPath(tokenIn, tokenOut);
        uint256[] memory amounts = this.getAmountsOut(amount, path);
        IERC20(tokenOut).transfer(to, amounts[1]);
    }

    function _getPath(address tokenIn, address tokenOut) internal pure returns (address[] memory) {
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;
        return path;
    }

    function removeLiquidityETHSupportingFeeOnTransferTokens(
        address,
        uint256,
        uint256,
        uint256,
        address,
        uint256
    ) external pure override returns (uint256) {
        return 0;
    }

    function removeLiquidityETHWithPermitSupportingFeeOnTransferTokens(
        address,
        uint256,
        uint256,
        uint256,
        address,
        uint256,
        bool,
        uint8,
        bytes32,
        bytes32
    ) external pure override returns (uint256) {
        return 0;
    }

    receive() external payable {}
}