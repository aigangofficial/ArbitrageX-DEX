// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";
import "./FlashLoanService.sol";

contract FlashLoanArbitrage is Ownable {
    IUniswapV2Router02 public immutable uniswapRouter;
    IUniswapV2Router02 public immutable sushiswapRouter;
    FlashLoanService public immutable flashLoanService;
    uint16 public maxSlippage = 100; // 1% default max slippage

    event ArbitrageExecuted(
        address indexed tokenA,
        address indexed tokenB,
        uint256 amountIn,
        uint256 profit
    );

    constructor(
        address _uniswapRouter,
        address _sushiswapRouter,
        address _flashLoanService
    ) Ownable(msg.sender) {
        require(_uniswapRouter != address(0), "Invalid Uniswap router address");
        require(_sushiswapRouter != address(0), "Invalid SushiSwap router address");
        require(_flashLoanService != address(0), "Invalid FlashLoan service address");

        uniswapRouter = IUniswapV2Router02(_uniswapRouter);
        sushiswapRouter = IUniswapV2Router02(_sushiswapRouter);
        flashLoanService = FlashLoanService(_flashLoanService);
    }

    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        bool isUniToSushi
    ) external onlyOwner {
        require(tokenA != address(0) && tokenB != address(0), "Invalid token addresses");
        require(amountIn > 0, "Amount must be greater than 0");

        // Create path for swaps
        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        // Get expected returns from both DEXes
        uint256[] memory uniAmounts = uniswapRouter.getAmountsOut(amountIn, path);
        uint256[] memory sushiAmounts = sushiswapRouter.getAmountsOut(amountIn, path);

        // Calculate expected returns for the complete arbitrage
        uint256 uniReturn = uniAmounts[1];
        uint256 sushiReturn = sushiAmounts[1];

        require(uniReturn > 0 && sushiReturn > 0, "Invalid exchange rates");

        // Calculate minimum amount out with slippage protection
        uint256 minAmountOut = (isUniToSushi ? sushiReturn : uniReturn) * (10000 - maxSlippage) / 10000;
        require(minAmountOut > 0, "Minimum output amount is too low");

        // Get tokens from sender
        IERC20 tokenAContract = IERC20(tokenA);
        IERC20 tokenBContract = IERC20(tokenB);
        
        require(
            tokenAContract.transferFrom(msg.sender, address(this), amountIn),
            "Initial transfer failed"
        );

        // Reset approvals first
        tokenAContract.approve(address(uniswapRouter), 0);
        tokenAContract.approve(address(sushiswapRouter), 0);

        // Approve routers with exact amounts
        require(
            tokenAContract.approve(address(uniswapRouter), amountIn),
            "Uniswap approval failed"
        );
        require(
            tokenAContract.approve(address(sushiswapRouter), amountIn),
            "SushiSwap approval failed"
        );

        uint256 initialBalance = tokenAContract.balanceOf(address(this));
        require(initialBalance >= amountIn, "Insufficient initial balance");

        uint256[] memory amounts;
        if (isUniToSushi) {
            // Swap on Uniswap first
            amounts = uniswapRouter.swapExactTokensForTokens(
                amountIn,
                0, // Accept any amount of TokenB
                path,
                address(this),
                block.timestamp
            );
            require(amounts[1] > 0, "Uniswap swap failed");

            // Reset approval for TokenB
            tokenBContract.approve(address(sushiswapRouter), 0);

            // Approve SushiSwap for the received TokenB
            require(
                tokenBContract.approve(address(sushiswapRouter), amounts[1]),
                "SushiSwap second approval failed"
            );

            // Create reverse path for second swap
            address[] memory reversePath = new address[](2);
            reversePath[0] = tokenB;
            reversePath[1] = tokenA;

            // Swap back on SushiSwap
            amounts = sushiswapRouter.swapExactTokensForTokens(
                amounts[1],
                minAmountOut,
                reversePath,
                address(this),
                block.timestamp
            );
            require(amounts[1] >= minAmountOut, "SushiSwap swap failed");
        } else {
            // Same process but starting with SushiSwap
            amounts = sushiswapRouter.swapExactTokensForTokens(
                amountIn,
                0,
                path,
                address(this),
                block.timestamp
            );
            require(amounts[1] > 0, "SushiSwap swap failed");

            // Reset approval for TokenB
            tokenBContract.approve(address(uniswapRouter), 0);

            require(
                tokenBContract.approve(address(uniswapRouter), amounts[1]),
                "Uniswap second approval failed"
            );

            address[] memory reversePath = new address[](2);
            reversePath[0] = tokenB;
            reversePath[1] = tokenA;

            amounts = uniswapRouter.swapExactTokensForTokens(
                amounts[1],
                minAmountOut,
                reversePath,
                address(this),
                block.timestamp
            );
            require(amounts[1] >= minAmountOut, "Uniswap swap failed");
        }

        // Calculate profit and transfer back to sender
        uint256 finalBalance = tokenAContract.balanceOf(address(this));
        require(finalBalance > initialBalance, "Trade not profitable");

        uint256 profit = finalBalance - initialBalance;
        require(
            tokenAContract.transfer(msg.sender, finalBalance),
            "Final transfer failed"
        );

        emit ArbitrageExecuted(tokenA, tokenB, amountIn, profit);
    }

    function setMaxSlippage(uint16 _maxSlippage) external onlyOwner {
        require(_maxSlippage <= 1000, "Max slippage cannot exceed 10%");
        maxSlippage = _maxSlippage;
    }
} 