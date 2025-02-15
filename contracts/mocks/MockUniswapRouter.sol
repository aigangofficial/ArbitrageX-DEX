// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.19;

import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./MockERC20.sol";

error InsufficientFundsForRepayment();
error InvalidPath();
error Expired();
error InsufficientOutputAmount();
error TransferFailed();
error NotImplemented();

contract MockUniswapRouter is IUniswapV2Router02 {
    uint256 public constant BPS = 10000;
    uint256 public constant IMPACT_BPS = 20; // 0.2% impact for 10% of reserves
    uint256 public constant FEE_BPS = 30; // 0.3% fee (standard Uniswap v2 fee)
    uint256 public constant PRECISION = 1e18;

    mapping(address => mapping(address => uint256)) public exchangeRates;
    mapping(address => mapping(address => uint256)) public reserves;
    mapping(address => uint8) public tokenDecimals;
    bool public revertOnSwap;

    struct SwapCalculation {
        uint256 amountIn;
        uint256 rate;
        uint256 baseAmountOut;
        uint256 afterFee;
        uint256 afterImpact;
        uint256 impactRatio;
        uint256 impact;
    }

    // Debug storage variables
    uint256 public lastAmountIn;
    uint256 public lastRate;
    uint256 public lastBaseAmountOut;
    uint256 public lastAfterFee;
    uint256 public lastAfterImpact;
    uint256 public lastImpactRatio;
    uint256 public lastImpact;

    event RateUpdated(address tokenIn, address tokenOut, uint256 rate);
    event ReservesUpdated(address tokenIn, address tokenOut, uint256 reserveIn, uint256 reserveOut);
    event DebugSwapCalculation(
        uint256 amountIn,
        uint256 rate,
        uint256 baseAmountOut,
        uint256 afterFee,
        uint256 afterImpact,
        uint256 impactRatio,
        uint256 impact
    );

    address private immutable wethAddress;

    constructor(address _weth) {
        wethAddress = _weth == address(0) ? 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 : _weth;
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

        // Calculate and set reverse rate with proper precision
        uint256 reverseRate = (PRECISION * PRECISION) / rate;
        exchangeRates[tokenOut][tokenIn] = reverseRate;

        // Update reserves to match rate (using much higher liquidity)
        reserves[tokenIn][tokenOut] = PRECISION * 100000000; // 100M base liquidity
        reserves[tokenOut][tokenIn] = (PRECISION * 100000000 * rate) / PRECISION; // Scaled liquidity

        emit RateUpdated(tokenIn, tokenOut, rate);
        emit RateUpdated(tokenOut, tokenIn, reverseRate);
        emit ReservesUpdated(
            tokenIn,
            tokenOut,
            reserves[tokenIn][tokenOut],
            reserves[tokenOut][tokenIn]
        );
    }

    function _calculateReverseRate(address tokenA, address tokenB) internal view returns (uint256) {
        uint8 decimalsA = tokenDecimals[tokenA];
        uint8 decimalsB = tokenDecimals[tokenB];
        uint256 forwardRate = exchangeRates[tokenA][tokenB];
        require(forwardRate > 0, "No rate set");
        return (10 ** (decimalsA + decimalsB)) / forwardRate;
    }

    function getAmountsOut(
        uint256 amountIn,
        address[] calldata path
    ) external view override returns (uint256[] memory amounts) {
        require(path.length >= 2, "Invalid path");

        amounts = new uint256[](path.length);
        amounts[0] = amountIn;

        for (uint i = 0; i < path.length - 1; i++) {
            address tokenIn = path[i];
            address tokenOut = path[i + 1];

            // Get exchange rate
            uint256 rate = exchangeRates[tokenIn][tokenOut];
            require(rate > 0, "Rate not set");

            // Calculate amount out with proper precision and apply fee
            amounts[i + 1] = (amountIn * rate * (BPS - FEE_BPS)) / (BPS * PRECISION);
        }

        return amounts;
    }

    function _calculateOutputAmount(uint256 amount, uint256 rate) internal pure returns (uint256) {
        return (amount * rate) / 1e18;
    }

    function calculateSwapAmounts(
        uint256 amountIn,
        address tokenIn,
        address tokenOut
    ) public view returns (SwapCalculation memory calc) {
        // Get exchange rate
        uint256 rate = exchangeRates[tokenIn][tokenOut];
        require(rate > 0, "Rate not set");

        // Calculate base amount out
        uint256 baseAmountOut = (amountIn * rate) / PRECISION;

        // Apply trading fee (0.3%)
        uint256 afterFee = (baseAmountOut * (BPS - FEE_BPS)) / BPS;

        // Apply price impact based on trade size vs liquidity
        uint256 reserveIn = reserves[tokenIn][tokenOut];
        uint256 afterImpact = afterFee;
        uint256 impactRatio = 0;
        uint256 impact = 0;
        if (reserveIn > 0) {
            // Calculate impact ratio with better precision
            impactRatio = (amountIn * PRECISION) / reserveIn;
            if (impactRatio > PRECISION / 10) {
                // If trade is > 10% of liquidity
                // Calculate impact (0.5% for every 10% of liquidity)
                impact = (impactRatio * 50) / (PRECISION / BPS); // 0.5% per 10% of liquidity
                if (impact >= BPS) impact = BPS - 1; // Cap impact at 99.99%
                afterImpact = (afterFee * (BPS - impact)) / BPS;
            }
        }

        return
            SwapCalculation({
                amountIn: amountIn,
                rate: rate,
                baseAmountOut: baseAmountOut,
                afterFee: afterFee,
                afterImpact: afterImpact,
                impactRatio: impactRatio,
                impact: impact
            });
    }

    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        if (deadline < block.timestamp) revert Expired();
        require(!revertOnSwap, "Swap reverted");
        require(path.length >= 2, "Invalid path");

        amounts = new uint256[](path.length);
        amounts[0] = amountIn;

        for (uint i = 0; i < path.length - 1; i++) {
            SwapCalculation memory calc = calculateSwapAmounts(amounts[i], path[i], path[i + 1]);
            amounts[i + 1] = calc.afterImpact;

            emit DebugSwapCalculation(
                calc.amountIn,
                calc.rate,
                calc.baseAmountOut,
                calc.afterFee,
                calc.afterImpact,
                calc.impactRatio,
                calc.impact
            );
        }

        if (amounts[amounts.length - 1] < amountOutMin) revert InsufficientOutputAmount();

        if (!IERC20(path[0]).transferFrom(msg.sender, address(this), amountIn))
            revert TransferFailed();
        if (!IERC20(path[path.length - 1]).transfer(to, amounts[amounts.length - 1]))
            revert TransferFailed();

        return amounts;
    }

    function swapTokensForExactTokens(
        uint256 amountOut,
        uint256 amountInMax,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external override returns (uint256[] memory amounts) {
        if (deadline < block.timestamp) revert Expired();

        uint256 baseAmountIn = (amountOut * PRECISION) / exchangeRates[path[0]][path[1]];

        baseAmountIn = (baseAmountIn * BPS) / (BPS - FEE_BPS);

        uint256 priceImpact = 0;
        if (baseAmountIn * BPS > reserves[path[0]][path[1]] * IMPACT_BPS) {
            priceImpact = (baseAmountIn * IMPACT_BPS * 2) / reserves[path[0]][path[1]];
            baseAmountIn = (baseAmountIn * BPS) / (BPS - priceImpact);
        }

        if (baseAmountIn > amountInMax) revert InsufficientOutputAmount();

        if (!IERC20(path[0]).transferFrom(msg.sender, address(this), baseAmountIn))
            revert TransferFailed();
        if (!IERC20(path[path.length - 1]).transfer(to, amountOut)) revert TransferFailed();

        amounts = new uint256[](path.length);
        amounts[0] = baseAmountIn;
        amounts[amounts.length - 1] = amountOut;

        return amounts;
    }

    function getAmountsIn(
        uint256 amountOut,
        address[] calldata path
    ) public view override returns (uint256[] memory amounts) {
        require(path.length >= 2, "Invalid path");
        amounts = new uint256[](path.length);
        amounts[amounts.length - 1] = amountOut;

        for (uint i = path.length - 1; i > 0; i--) {
            address tokenIn = path[i - 1];
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
            amounts[i - 1] = (baseAmountIn * (BPS + priceImpact)) / BPS;
        }

        return amounts;
    }

    function factory() external pure override returns (address) {
        return address(0);
    }

    function quote(
        uint256 amountA,
        uint256 reserveA,
        uint256 reserveB
    ) external pure override returns (uint256) {
        require(amountA > 0, "Insufficient amount");
        require(reserveA > 0 && reserveB > 0, "Insufficient liquidity");
        return (amountA * reserveB) / reserveA;
    }

    function getAmountOut(
        uint256 amountIn,
        uint256 reserveIn,
        uint256 reserveOut
    ) public pure override returns (uint256 amountOut) {
        require(amountIn > 0, "Insufficient input amount");
        require(reserveIn > 0 && reserveOut > 0, "Insufficient liquidity");

        // Calculate base amount out using constant product formula
        uint256 amountInWithFee = amountIn * 997;
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = (reserveIn * 1000) + amountInWithFee;
        amountOut = numerator / denominator;

        // Apply slippage for large trades
        if (amountIn > reserveIn / 10) {
            uint256 slippage = (amountIn * 100) / reserveIn; // Percentage of reserve
            if (slippage > 10) {
                // If trade is > 10% of reserve
                uint256 slippageImpact = ((slippage - 10) * 10) / 100; // 10 bps per 1% above threshold
                amountOut = (amountOut * (1000 - slippageImpact)) / 1000;
            }
        }

        return amountOut;
    }

    function getAmountIn(
        uint amountOut,
        uint reserveIn,
        uint reserveOut
    ) public pure returns (uint amountIn) {
        require(amountOut > 0, "INSUFFICIENT_OUTPUT_AMOUNT");
        require(reserveIn > 0 && reserveOut > 0, "INSUFFICIENT_LIQUIDITY");

        uint numerator = reserveIn * amountOut * 1000;
        uint denominator = (reserveOut - amountOut) * 990;
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
        revert NotImplemented();
    }

    function removeLiquidityETHWithPermit(
        address /* token */,
        uint256 /* liquidity */,
        uint256 /* amountTokenMin */,
        uint256 /* amountETHMin */,
        address /* to */,
        uint256 /* deadline */,
        bool /* approveMax */,
        uint8 /* v */,
        bytes32 /* r */,
        bytes32 /* s */
    ) external pure override returns (uint256, uint256) {
        revert NotImplemented();
    }

    function swapExactETHForTokens(
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable override returns (uint256[] memory amounts) {
        require(deadline >= block.timestamp, "Expired");
        require(path[0] == this.WETH(), "Invalid path");

        amounts = this.getAmountsOut(msg.value, path);
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
        require(path.length >= 2 && path[path.length - 1] == this.WETH(), "Invalid path");

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
        require(path.length >= 2 && path[path.length - 1] == this.WETH(), "Invalid path");

        amounts = this.getAmountsOut(amountIn, path);
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
        require(path.length >= 2 && path[path.length - 1] == this.WETH(), "Invalid path");

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

    function _applyPriceImpact(
        address /* tokenIn */,
        address tokenOut,
        uint256 amount
    ) internal view returns (uint256) {
        // Fixed price impact calculation with proper decimal handling
        uint256 impact = (amount * 997) / 1000; // 0.3% fee
        return
            tokenOut == address(0)
                ? impact
                : (impact * (10 ** tokenDecimals[tokenOut])) / PRECISION;
    }

    function setRevertOnSwap(bool shouldRevert) external {
        revertOnSwap = shouldRevert;
    }

    receive() external payable {}
}
