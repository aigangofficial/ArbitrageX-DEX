// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@aave/core-v3/contracts/interfaces/IPool.sol";
import "./interfaces/IFlashLoanReceiver.sol";
import "./interfaces/IArbitrageExecutor.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";
import "hardhat/console.sol";

error InvalidPath();
error InsufficientFundsForRepayment();
error InvalidTokenAddresses();
error InvalidAmount();
error InvalidMinProfit();

contract FlashLoanService is Ownable, ReentrancyGuard, IFlashLoanReceiver {
    IPool public immutable pool;
    IUniswapV2Router02 public immutable uniswapRouter;
    IUniswapV2Router02 public immutable sushiswapRouter;
    uint16 public minProfitBps = 10; // 0.1% minimum profit

    event FlashLoanExecuted(
        address indexed token,
        uint256 amount,
        uint256 profit
    );

    event MinProfitBpsUpdated(uint16 oldValue, uint16 newValue);

    constructor(
        address _pool,
        address _uniswapRouter,
        address _sushiswapRouter
    ) Ownable(msg.sender) ReentrancyGuard() {
        pool = IPool(_pool);
        uniswapRouter = IUniswapV2Router02(_uniswapRouter);
        sushiswapRouter = IUniswapV2Router02(_sushiswapRouter);
        
        // Set initial minimum profit to 10 bps (0.1%)
        minProfitBps = 10;
        emit MinProfitBpsUpdated(0, 10);
    }

    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        console.log("executeOperation called with amount:", amount);
        console.log("premium:", premium);

        // Decode params
        (address[] memory path, bool isArbitrage) = abi.decode(params, (address[], bool));
        if (path.length < 2) revert InvalidPath();
        
        // Execute the arbitrage swaps
        uint256 finalBalance = _executeArbitrageSwaps(asset, amount, path[1]);
        
        // Verify profitability
        uint256 amountOwed = _calculateAmountOwed(amount, premium);
        if (finalBalance < amountOwed) revert InsufficientFundsForRepayment();
        
        uint256 profit = finalBalance - amountOwed;
        if (!_isProfitable(amount, profit)) revert IArbitrageExecutor.UnprofitableTrade();

        // Approve repayment
        IERC20(asset).approve(address(pool), amountOwed);
        console.log("Approved pool for repayment:", amountOwed);

        emit FlashLoanExecuted(asset, amount, profit);
        return true;
    }

    function _executeArbitrageSwaps(
        address tokenA,
        uint256 amountIn,
        address tokenB
    ) internal returns (uint256) {
        // First swap on Uniswap: TokenA -> TokenB
        IERC20(tokenA).approve(address(uniswapRouter), amountIn);
        console.log("Approved Uniswap for amount:", amountIn);

        uint256 amountOut = _swapExactTokensForTokens(
            uniswapRouter,
            amountIn,
            tokenA,
            tokenB
        );
        console.log("First swap completed, received:", amountOut);

        // Second swap on Sushiswap: TokenB -> TokenA
        IERC20(tokenB).approve(address(sushiswapRouter), amountOut);
        console.log("Approved Sushiswap for amount:", amountOut);

        uint256 finalAmount = _swapExactTokensForTokens(
            sushiswapRouter,
            amountOut,
            tokenB,
            tokenA
        );
        console.log("Second swap completed, received:", finalAmount);

        return IERC20(tokenA).balanceOf(address(this));
    }

    function _calculateAmountOwed(uint256 amount, uint256 premium) internal pure returns (uint256) {
        unchecked {
            // Safe because premium is always a small percentage of amount
            return amount + premium;
        }
    }

    function _isProfitable(uint256 amount, uint256 profit) internal view returns (bool) {
        return profit * 10000 >= amount * uint256(minProfitBps);
    }

    function executeFlashLoan(
        address asset,
        uint256 amount,
        address[] memory path,
        bool isArbitrage
    ) internal {
        if (path.length < 2) revert InvalidPath();
        if (path[0] != asset) revert InvalidPath();
        
        // Additional validation for each token in path
        for(uint i = 0; i < path.length; i++) {
            if (path[i] == address(0)) revert InvalidPath();
            if(i > 0 && path[i] == path[i-1]) revert InvalidPath();
        }

        // Prepare flash loan parameters
        address[] memory assets = new address[](1);
        assets[0] = asset;

        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;

        uint256[] memory modes = new uint256[](1);
        modes[0] = 0; // no debt, flash loan

        bytes memory params = abi.encode(path, isArbitrage);

        // Execute flash loan
        pool.flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            params,
            0
        );
    }

    function setMinProfitBps(uint16 _minProfitBps) external onlyOwner {
        if (_minProfitBps == 0) revert InvalidMinProfit();
        uint16 oldValue = minProfitBps;
        minProfitBps = _minProfitBps;
        emit MinProfitBpsUpdated(oldValue, _minProfitBps);
    }

    function withdrawToken(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner(), amount);
    }

    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amount
    ) external nonReentrant {
        if (amount == 0) revert InvalidAmount();
        if (tokenA == address(0) || tokenB == address(0)) revert InvalidTokenAddresses();

        // Create path array
        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;

        // Execute flash loan
        try pool.flashLoan(
            address(this),
            _createSingleAssetArray(tokenA),
            _createSingleAmountArray(amount),
            _createSingleModeArray(),
            address(this),
            abi.encode(path, true),
            0
        ) {
            emit FlashLoanExecuted(tokenA, amount, 0);
        } catch Error(string memory) {
            revert InsufficientFundsForRepayment();
        } catch {
            revert InsufficientFundsForRepayment();
        }
    }

    function _swapExactTokensForTokens(
        IUniswapV2Router02 router,
        uint256 amountIn,
        address tokenIn,
        address tokenOut
    ) internal returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        uint256[] memory amounts = router.swapExactTokensForTokens(
            amountIn,
            0, // Accept any amount of tokenOut
            path,
            address(this),
            block.timestamp
        );

        return amounts[1];
    }

    function _createSingleAssetArray(address asset) internal pure returns (address[] memory) {
        address[] memory assets = new address[](1);
        assets[0] = asset;
        return assets;
    }

    function _createSingleAmountArray(uint256 amount) internal pure returns (uint256[] memory) {
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        return amounts;
    }

    function _createSingleModeArray() internal pure returns (uint256[] memory) {
        uint256[] memory modes = new uint256[](1);
        modes[0] = 0;
        return modes;
    }
} 