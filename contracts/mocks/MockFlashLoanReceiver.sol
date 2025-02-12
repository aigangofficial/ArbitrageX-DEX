// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IFlashLoanReceiver.sol";

contract MockFlashLoanReceiver is IFlashLoanReceiver {
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 fee,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        // Calculate total amount to repay
        uint256 amountToRepay = amount + fee;

        // Clear any existing allowance and approve the pool to pull the repayment amount
        IERC20(asset).approve(msg.sender, 0);
        require(IERC20(asset).approve(msg.sender, amountToRepay), "Approval failed");

        // Transfer the repayment amount back to the pool
        require(IERC20(asset).transfer(msg.sender, amountToRepay), "Repayment transfer failed");

        return true;
    }
}
