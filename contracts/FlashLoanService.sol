// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@aave/core-v3/contracts/interfaces/IPool.sol";
import "./interfaces/IFlashLoanReceiver.sol";
import "@uniswap/v2-periphery/contracts/interfaces/IUniswapV2Router02.sol";

contract FlashLoanService is Ownable, ReentrancyGuard, IFlashLoanReceiver {
    IPool public immutable aavePool;
    IUniswapV2Router02 public immutable uniswapRouter;
    IUniswapV2Router02 public immutable sushiswapRouter;
    uint16 public minProfitBps = 1; // 0.01% minimum profit by default

    event FlashLoanExecuted(
        address indexed token,
        uint256 amount,
        uint256 profit
    );

    event MinProfitBpsUpdated(uint16 oldValue, uint16 newValue);

    constructor(
        address _aavePool,
        address _uniswapRouter,
        address _sushiswapRouter
    ) Ownable(msg.sender) ReentrancyGuard() {
        require(_aavePool != address(0), "Invalid Aave pool address");
        require(_uniswapRouter != address(0), "Invalid Uniswap router address");
        require(_sushiswapRouter != address(0), "Invalid SushiSwap router address");

        aavePool = IPool(_aavePool);
        uniswapRouter = IUniswapV2Router02(_uniswapRouter);
        sushiswapRouter = IUniswapV2Router02(_sushiswapRouter);
        
        // Set initial minimum profit to 1 bps (0.01%)
        minProfitBps = 1;
        emit MinProfitBpsUpdated(0, 1);
    }

    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(aavePool), "Callback only from Aave pool");
        require(assets.length == 1 && amounts.length == 1, "Only single asset flash loans supported");
        require(amounts[0] > 0, "Flash loan amount must be greater than 0");

        // Decode arbitrage parameters
        (
            address[] memory path,
            bool isUniToSushi
        ) = abi.decode(params, (address[], bool));

        require(path.length >= 2, "Invalid path length");
        require(path[0] == assets[0], "First token in path must match flash loan asset");

        // Get the flash loaned token and calculate amount owed
        IERC20 token = IERC20(assets[0]);
        uint256 amountOwed = amounts[0] + premiums[0];
        require(amountOwed > amounts[0], "Invalid premium calculation");

        // Create reverse path for second swap
        address[] memory reversePath = new address[](path.length);
        for (uint i = 0; i < path.length; i++) {
            reversePath[i] = path[path.length - 1 - i];
        }

        // Check initial token balance
        uint256 initialBalance = token.balanceOf(address(this));
        require(initialBalance >= amounts[0], "Flash loan amount not received");

        // Reset approvals to 0 first
        require(token.approve(address(uniswapRouter), 0), "Failed to reset Uniswap approval");
        require(token.approve(address(sushiswapRouter), 0), "Failed to reset SushiSwap approval");

        // Approve routers with exact amounts
        require(
            token.approve(address(uniswapRouter), amounts[0]),
            "Uniswap approval failed"
        );
        require(
            token.approve(address(sushiswapRouter), amounts[0]),
            "SushiSwap approval failed"
        );

        // Execute arbitrage
        uint256 receivedAmount;
        if (isUniToSushi) {
            // Swap on Uniswap first
            try uniswapRouter.swapExactTokensForTokens(
                amounts[0],
                0, // Accept any amount
                path,
                address(this),
                block.timestamp
            ) returns (uint256[] memory uniAmounts) {
                require(uniAmounts[uniAmounts.length - 1] > 0, "Uniswap swap failed");

                // Reset approval for intermediate token
                IERC20 intermediateToken = IERC20(path[path.length - 1]);
                require(intermediateToken.approve(address(sushiswapRouter), 0), "Failed to reset intermediate token approval");
                
                // Approve intermediate token for second swap
                require(
                    intermediateToken.approve(address(sushiswapRouter), uniAmounts[uniAmounts.length - 1]),
                    "SushiSwap intermediate approval failed"
                );

                // Then swap on SushiSwap with reverse path
                try sushiswapRouter.swapExactTokensForTokens(
                    uniAmounts[uniAmounts.length - 1],
                    0, // Accept any amount
                    reversePath,
                    address(this),
                    block.timestamp
                ) returns (uint256[] memory sushiAmounts) {
                    require(sushiAmounts[sushiAmounts.length - 1] > 0, "SushiSwap swap failed");
                    receivedAmount = sushiAmounts[sushiAmounts.length - 1];
                } catch Error(string memory reason) {
                    revert(string(abi.encodePacked("SushiSwap swap failed: ", reason)));
                } catch {
                    revert("SushiSwap swap failed with unknown error");
                }
            } catch Error(string memory reason) {
                revert(string(abi.encodePacked("Uniswap swap failed: ", reason)));
            } catch {
                revert("Uniswap swap failed with unknown error");
            }
        } else {
            // Swap on SushiSwap first
            try sushiswapRouter.swapExactTokensForTokens(
                amounts[0],
                0, // Accept any amount
                path,
                address(this),
                block.timestamp
            ) returns (uint256[] memory sushiAmounts) {
                require(sushiAmounts[sushiAmounts.length - 1] > 0, "SushiSwap swap failed");

                // Reset approval for intermediate token
                IERC20 intermediateToken = IERC20(path[path.length - 1]);
                require(intermediateToken.approve(address(uniswapRouter), 0), "Failed to reset intermediate token approval");
                
                // Approve intermediate token for second swap
                require(
                    intermediateToken.approve(address(uniswapRouter), sushiAmounts[sushiAmounts.length - 1]),
                    "Uniswap intermediate approval failed"
                );

                // Then swap on Uniswap with reverse path
                try uniswapRouter.swapExactTokensForTokens(
                    sushiAmounts[sushiAmounts.length - 1],
                    0, // Accept any amount
                    reversePath,
                    address(this),
                    block.timestamp
                ) returns (uint256[] memory uniAmounts) {
                    require(uniAmounts[uniAmounts.length - 1] > 0, "Uniswap swap failed");
                    receivedAmount = uniAmounts[uniAmounts.length - 1];
                } catch Error(string memory reason) {
                    revert(string(abi.encodePacked("Uniswap swap failed: ", reason)));
                } catch {
                    revert("Uniswap swap failed with unknown error");
                }
            } catch Error(string memory reason) {
                revert(string(abi.encodePacked("SushiSwap swap failed: ", reason)));
            } catch {
                revert("SushiSwap swap failed with unknown error");
            }
        }

        // Verify profit
        require(receivedAmount >= amountOwed, "Insufficient funds to repay flash loan");
        uint256 profit = receivedAmount - amountOwed;
        if (profit * 10000 < amounts[0] * uint256(minProfitBps)) {
            revert UnprofitableTrade();
        }

        // Reset approval for Aave pool
        require(token.approve(address(aavePool), 0), "Failed to reset Aave approval");
        
        // Approve repayment with exact amount
        require(
            token.approve(address(aavePool), amountOwed),
            "Aave repayment approval failed"
        );

        // Transfer any excess profit to owner
        if (profit > 0) {
            require(
                token.transfer(owner(), profit),
                "Profit transfer failed"
            );
        }

        emit FlashLoanExecuted(assets[0], amounts[0], profit);

        return true;
    }

    function executeFlashLoan(
        address asset,
        uint256 amount,
        address[] memory path,
        bool isArbitrage
    ) internal {
        require(path.length >= 2, "Invalid path length");
        require(path[0] == asset, "First token must match asset");
        
        // Additional validation for each token in path
        for(uint i = 0; i < path.length; i++) {
            require(path[i] != address(0), "Invalid token in path");
            if(i > 0) {
                require(path[i] != path[i-1], "Consecutive tokens must be different");
            }
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
        aavePool.flashLoan(
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
        require(_minProfitBps > 0, "Min profit must be greater than 0");
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
    ) external onlyOwner {
        require(tokenA != address(0) && tokenB != address(0), "Invalid token addresses");
        require(tokenA != tokenB, "Tokens must be different");
        require(amount > 0, "Amount must be greater than 0");

        address[] memory path = new address[](2);
        path[0] = tokenA;
        path[1] = tokenB;
        
        executeFlashLoan(tokenA, amount, path, true);
    }
} 