// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";
import "../interfaces/IFlashLoanService.sol";

error InvalidAddress();
error InvalidAmount();
error UnprofitableTrade();
error TransferFailed();
error InsufficientBalance();
error ApprovalFailed();

contract ArbitrageExecutor is Ownable {
    uint256 public constant BPS = 10000;
    uint256 public constant MIN_PROFIT_BPS = 10; // 0.1% minimum profit
    uint256 public constant PRECISION = 1e18;

    IUniswapV2Router02 public immutable uniswapRouter;
    IUniswapV2Router02 public immutable sushiswapRouter;
    IFlashLoanService public immutable flashLoanService;
    address public immutable WETH;

    event ArbitrageExecuted(
        address indexed tokenA,
        address indexed tokenB,
        uint256 amountIn,
        uint256 amountOut,
        uint256 profit,
        uint256 timestamp
    );

    event DebugProfitCalculation(
        uint256 amountIn,
        uint256 firstSwapOut,
        uint256 secondSwapOut,
        uint256 profit,
        uint256 minProfit
    );

    constructor(
        address _flashLoanService,
        address _uniswapRouter,
        address _sushiswapRouter,
        address _weth
    ) Ownable() {
        if (
            _uniswapRouter == address(0) ||
            _sushiswapRouter == address(0) ||
            _flashLoanService == address(0) ||
            _weth == address(0)
        ) {
            revert InvalidAddress();
        }

        uniswapRouter = IUniswapV2Router02(_uniswapRouter);
        sushiswapRouter = IUniswapV2Router02(_sushiswapRouter);
        flashLoanService = IFlashLoanService(_flashLoanService);
        WETH = _weth;

        _transferOwnership(msg.sender);
    }

    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        bool startWithUniswap
    ) external onlyOwner {
        if (tokenA == address(0) || tokenB == address(0)) {
            revert InvalidAddress();
        }
        if (amountIn == 0) {
            revert InvalidAmount();
        }

        // Calculate expected profit
        (uint256 expectedProfit, uint256 minRequiredProfit) = _calculateExpectedProfit(
            tokenA,
            tokenB,
            amountIn,
            startWithUniswap
        );

        if (expectedProfit < minRequiredProfit) {
            revert UnprofitableTrade();
        }

        // Emit debug info
        _emitDebugProfitCalculation(
            amountIn,
            0, // We don't have firstSwapOut yet
            0, // We don't have secondSwapOut yet
            expectedProfit,
            minRequiredProfit
        );

        // Execute flash loan and swaps
        flashLoanService.executeArbitrage(
            tokenA,
            tokenB,
            amountIn,
            abi.encode(tokenA, tokenB, amountIn, startWithUniswap)
        );
    }

    function _calculateExpectedProfit(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        bool startWithUniswap
    ) internal view returns (uint256 expectedProfit, uint256 minRequiredProfit) {
        // Setup path for swaps
        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        // Get amounts out from first swap
        uint256[] memory firstSwapAmounts = startWithUniswap
            ? uniswapRouter.getAmountsOut(amountIn, path)
            : sushiswapRouter.getAmountsOut(amountIn, path);

        // Reverse path for second swap
        address[] memory reversePath = new address[](2);
        reversePath[0] = tokenB;
        reversePath[1] = tokenA;

        // Get amounts out from second swap
        uint256[] memory secondSwapAmounts = startWithUniswap
            ? sushiswapRouter.getAmountsOut(firstSwapAmounts[1], reversePath)
            : uniswapRouter.getAmountsOut(firstSwapAmounts[1], reversePath);

        // Calculate profit
        if (secondSwapAmounts[1] <= amountIn) {
            expectedProfit = 0;
        } else {
            expectedProfit = secondSwapAmounts[1] - amountIn;
        }

        // Calculate minimum required profit (0.1% of input amount)
        minRequiredProfit = (amountIn * MIN_PROFIT_BPS) / BPS;

        return (expectedProfit, minRequiredProfit);
    }

    function _emitDebugProfitCalculation(
        uint256 amountIn,
        uint256 firstSwapOut,
        uint256 secondSwapOut,
        uint256 profit,
        uint256 minProfit
    ) internal {
        emit DebugProfitCalculation(amountIn, firstSwapOut, secondSwapOut, profit, minProfit);
    }

    function _executeSwaps(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        bool startWithUniswap
    ) internal returns (uint256) {
        // Approve first router
        IUniswapV2Router02 firstRouter = startWithUniswap ? uniswapRouter : sushiswapRouter;
        if (!IERC20(tokenA).approve(address(firstRouter), amountIn)) {
            revert ApprovalFailed();
        }

        // Setup path for first swap
        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        // Execute first swap
        uint256[] memory firstSwapAmounts = firstRouter.swapExactTokensForTokens(
            amountIn,
            0, // Accept any amount of tokenB
            path,
            address(this),
            block.timestamp
        );

        // Approve second router
        IUniswapV2Router02 secondRouter = startWithUniswap ? sushiswapRouter : uniswapRouter;
        if (!IERC20(tokenB).approve(address(secondRouter), firstSwapAmounts[1])) {
            revert ApprovalFailed();
        }

        // Setup path for second swap
        address[] memory reversePath = new address[](2);
        reversePath[0] = tokenB;
        reversePath[1] = tokenA;

        // Execute second swap
        uint256[] memory secondSwapAmounts = secondRouter.swapExactTokensForTokens(
            firstSwapAmounts[1],
            0, // Accept any amount of tokenA
            reversePath,
            address(this),
            block.timestamp
        );

        // Calculate and emit profit
        uint256 profit = secondSwapAmounts[1] > amountIn ? secondSwapAmounts[1] - amountIn : 0;

        emit ArbitrageExecuted(
            tokenA,
            tokenB,
            amountIn,
            secondSwapAmounts[1],
            profit,
            block.timestamp
        );

        return secondSwapAmounts[1];
    }

    function onFlashLoan(bytes calldata data) external returns (bool) {
        require(msg.sender == address(flashLoanService), "Unauthorized");

        // Decode parameters
        (address tokenA, address tokenB, uint256 amountIn, bool startWithUniswap) = abi.decode(
            data,
            (address, address, uint256, bool)
        );

        // Execute swaps
        uint256 finalAmount = _executeSwaps(tokenA, tokenB, amountIn, startWithUniswap);

        // Approve flash loan service to take repayment
        if (!IERC20(tokenA).approve(address(flashLoanService), finalAmount)) {
            revert ApprovalFailed();
        }

        return true;
    }

    // Emergency token recovery
    function recoverToken(address token, uint256 amount) external onlyOwner {
        if (!IERC20(token).transfer(msg.sender, amount)) {
            revert TransferFailed();
        }
    }
}
