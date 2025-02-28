// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IPoolConfigurator {
    function configureReserveAsCollateral(
        address asset,
        uint256 ltv,
        uint256 liquidationThreshold,
        uint256 liquidationBonus
    ) external;

    function enableBorrowingOnReserve(address asset, bool stableBorrowRateEnabled) external;

    function setReserveFactor(address asset, uint256 reserveFactor) external;

    function setReserveInterestRateStrategyAddress(
        address asset,
        address rateStrategyAddress
    ) external;

    function setPoolPause(bool paused) external;
}
