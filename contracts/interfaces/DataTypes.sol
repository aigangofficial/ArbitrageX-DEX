// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

library DataTypes {
    struct ReserveData {
        uint256 liquidityIndex;
        uint256 currentLiquidityRate;
        uint256 variableBorrowIndex;
        uint256 currentVariableBorrowRate;
        uint256 currentStableBorrowRate;
        uint40 lastUpdateTimestamp;
        uint16 id;
        address aTokenAddress;
        address stableDebtTokenAddress;
        address variableDebtTokenAddress;
        address interestRateStrategyAddress;
        uint128 accruedToTreasury;
        uint128 unbacked;
        uint128 isolationModeTotalDebt;
    }

    struct ReserveConfigurationMap {
        uint256 data;
    }

    struct UserConfigurationMap {
        uint256 data;
    }

    struct EModeCategory {
        uint16 ltv;
        uint16 liquidationThreshold;
        uint16 liquidationBonus;
        address priceSource;
        string label;
    }
}
