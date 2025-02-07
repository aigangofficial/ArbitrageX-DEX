// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";
import "./interfaces/IArbitrageExecutor.sol";
import "./FlashLoanService.sol";

contract ArbitrageExecutor is Ownable, IArbitrageExecutor {
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
    ) external onlyOwner returns (uint256) {
        require(tokenA != address(0) && tokenB != address(0), "Invalid token addresses");
        require(amountIn > 0, "Amount must be greater than 0");

        // Transfer tokens from sender
        IERC20(tokenA).transferFrom(msg.sender, address(this), amountIn);

        // Approve routers
        IERC20(tokenA).approve(address(uniswapRouter), amountIn);
        IERC20(tokenA).approve(address(sushiswapRouter), amountIn);

        uint256 initialBalance = IERC20(tokenA).balanceOf(address(this));
        uint256 finalBalance;

        if (isUniToSushi) {
            finalBalance = _executeUniToSushiSwap(tokenA, tokenB, amountIn);
        } else {
            finalBalance = _executeSushiToUniSwap(tokenA, tokenB, amountIn);
        }
        
        if (finalBalance <= amountIn) {
            revert UnprofitableTrade();
        }

        uint256 profit = finalBalance - amountIn;
        IERC20(tokenA).transfer(msg.sender, finalBalance);
        emit ArbitrageExecuted(tokenA, tokenB, amountIn, profit);
        return profit;
    }

    function _executeUniToSushiSwap(
        address tokenA,
        address tokenB,
        uint256 amountIn
    ) internal returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        // Swap on Uniswap first
        uniswapRouter.swapExactTokensForTokens(
            amountIn,
            0, // Accept any amount of TokenB
            path,
            address(this),
            block.timestamp
        );

        // Approve SushiSwap for the received TokenB
        uint256 tokenBBalance = IERC20(tokenB).balanceOf(address(this));
        IERC20(tokenB).approve(address(sushiswapRouter), tokenBBalance);

        // Create reverse path for second swap
        address[] memory reversePath = new address[](2);
        reversePath[0] = tokenB;
        reversePath[1] = tokenA;

        // Calculate minimum amount out
        uint256[] memory expectedAmounts = sushiswapRouter.getAmountsOut(tokenBBalance, reversePath);
        uint256 minAmountOut = expectedAmounts[1] * (10000 - maxSlippage) / 10000;

        // Swap back on SushiSwap
        uint256[] memory amounts = sushiswapRouter.swapExactTokensForTokens(
            tokenBBalance,
            minAmountOut,
            reversePath,
            address(this),
            block.timestamp
        );

        return IERC20(tokenA).balanceOf(address(this));
    }

    function _executeSushiToUniSwap(
        address tokenA,
        address tokenB,
        uint256 amountIn
    ) internal returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        // Swap on SushiSwap first
        sushiswapRouter.swapExactTokensForTokens(
            amountIn,
            0,
            path,
            address(this),
            block.timestamp
        );

        // Approve Uniswap for the received TokenB
        uint256 tokenBBalance = IERC20(tokenB).balanceOf(address(this));
        IERC20(tokenB).approve(address(uniswapRouter), tokenBBalance);

        // Create reverse path for second swap
        address[] memory reversePath = new address[](2);
        reversePath[0] = tokenB;
        reversePath[1] = tokenA;

        // Calculate minimum amount out
        uint256[] memory expectedAmounts = uniswapRouter.getAmountsOut(tokenBBalance, reversePath);
        uint256 minAmountOut = expectedAmounts[1] * (10000 - maxSlippage) / 10000;

        // Swap back on Uniswap
        uint256[] memory amounts = uniswapRouter.swapExactTokensForTokens(
            tokenBBalance,
            minAmountOut,
            reversePath,
            address(this),
            block.timestamp
        );

        return IERC20(tokenA).balanceOf(address(this));
    }

    function setMaxSlippage(uint16 _maxSlippage) external onlyOwner {
        require(_maxSlippage <= 1000, "Max slippage cannot exceed 10%");
        maxSlippage = _maxSlippage;
    }
}
