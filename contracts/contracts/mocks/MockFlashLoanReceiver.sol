// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/IFlashLoanReceiver.sol";

contract MockFlashLoanReceiver is IFlashLoanReceiver {
    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(
            assets.length == amounts.length && amounts.length == premiums.length,
            "Length mismatch"
        );

        // Approve and repay each asset
        for (uint256 i = 0; i < assets.length; i++) {
            uint256 amountToRepay = amounts[i] + premiums[i];

            // Clear any existing allowance and approve the pool to pull the repayment amount
            IERC20(assets[i]).approve(msg.sender, 0);
            require(IERC20(assets[i]).approve(msg.sender, amountToRepay), "Approval failed");

            // Transfer the repayment amount back to the pool
            require(
                IERC20(assets[i]).transfer(msg.sender, amountToRepay),
                "Repayment transfer failed"
            );
        }

        return true;
    }
}
