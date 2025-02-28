// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./IPool.sol";
import "./IPoolAddressesProvider.sol";
import "../IERC20.sol";

/**
 * @title FlashLoanSimpleReceiverBase
 * @notice Base contract for flash loan receivers
 */
abstract contract FlashLoanSimpleReceiverBase {
    IPoolAddressesProvider public immutable ADDRESSES_PROVIDER;
    IPool public immutable POOL;

    constructor(IPoolAddressesProvider provider) {
        ADDRESSES_PROVIDER = provider;
        POOL = IPool(provider.getPool());
    }

    /**
     * @notice Executes an operation after receiving the flash-borrowed asset
     * @param asset The address of the flash-borrowed asset
     * @param amount The amount of the flash-borrowed asset
     * @param premium The fee of the flash-borrowed asset
     * @param initiator The address of the flashloan initiator
     * @param params The byte-encoded params passed when initiating the flashloan
     * @return boolean The status of the operation
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external virtual returns (bool);

    /**
     * @notice Allows the pool to transfer tokens from this contract
     * @param token The address of the token
     * @param to The destination of the transfer
     * @param amount The amount to transfer
     */
    function _transferToken(address token, address to, uint256 amount) internal {
        IERC20(token).transfer(to, amount);
    }
}
