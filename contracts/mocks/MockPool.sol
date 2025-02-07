// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@aave/core-v3/contracts/interfaces/IPool.sol";

// Simplified Flash Loan Receiver Interface
interface IFlashLoanReceiver {
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}

contract MockPool is IPool, Ownable {
    address public token0;
    address public token1;
    uint256 public reserve0;
    uint256 public reserve1;
    uint256 public constant MINIMUM_LIQUIDITY = 1000;
    uint256 private unlocked = 1;

    constructor(address _token0, address _token1) Ownable(msg.sender) {
        require(_token0 != address(0), "Invalid token0");
        require(_token1 != address(0), "Invalid token1");
        token0 = _token0;
        token1 = _token1;
    }

    // Flash loan fee expressed in bps (0.05% = 5)
    uint256 public constant FLASH_LOAN_PREMIUM_TOTAL = 5;

    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata,
        address onBehalfOf,
        bytes calldata params,
        uint16
    ) external override {
        require(assets.length == 1 && amounts.length == 1, "Only single asset flash loans supported");
        
        // Transfer requested amount to receiver
        require(
            IERC20(assets[0]).transfer(receiverAddress, amounts[0]),
            "Flash loan transfer failed"
        );

        // Calculate premium
        uint256 premium = (amounts[0] * FLASH_LOAN_PREMIUM_TOTAL) / 10000;

        // Execute operation on receiver contract
        require(
            IFlashLoanReceiver(receiverAddress).executeOperation(
                assets[0],
                amounts[0],
                premium,
                onBehalfOf,
                params
            ),
            "Flash loan execution failed"
        );

        // Ensure flash loan is repaid with premium
        require(
            IERC20(assets[0]).transferFrom(
                receiverAddress,
                address(this),
                amounts[0] + premium
            ),
            "Flash loan repayment failed"
        );
    }

    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16
    ) external override {
        // Transfer requested amount to receiver
        require(
            IERC20(asset).transfer(receiverAddress, amount),
            "Flash loan transfer failed"
        );

        // Create arrays for executeOperation
        address[] memory assets = new address[](1);
        assets[0] = asset;
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        uint256[] memory premiums = new uint256[](1);
        premiums[0] = (amount * FLASH_LOAN_PREMIUM_TOTAL) / 10000;

        // Execute operation on receiver contract
        require(
            IFlashLoanReceiver(receiverAddress).executeOperation(
                assets[0],
                amounts[0],
                premiums[0],
                msg.sender,
                params
            ),
            "Flash loan execution failed"
        );

        // Ensure flash loan is repaid with premium
        require(
            IERC20(asset).transferFrom(
                receiverAddress,
                address(this),
                amount + premiums[0]
            ),
            "Flash loan repayment failed"
        );
    }

    // Implement missing interface functions with placeholder returns
    function BRIDGE_PROTOCOL_FEE() external pure override returns (uint256) {
        return 0;
    }

    function FLASHLOAN_PREMIUM_TO_PROTOCOL() external pure override returns (uint128) {
        return 0;
    }

    function MAX_NUMBER_RESERVES() external pure override returns (uint16) {
        return 0;
    }

    function MAX_STABLE_RATE_BORROW_SIZE_PERCENT() external pure override returns (uint256) {
        return 0;
    }

    function backUnbacked(address asset, uint256 amount, uint256 fee) external override returns (uint256) {
        return 0;
    }

    function deposit(address asset, uint256 amount, address onBehalfOf, uint16 referralCode) external override {}

    function getReserveAddressById(uint16 id) external pure override returns (address) {
        return address(0);
    }

    function mintUnbacked(address asset, uint256 amount, address onBehalfOf, uint16 referralCode) external override {}

    function repayWithPermit(
        address asset,
        uint256 amount,
        uint256 interestRateMode,
        address onBehalfOf,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external override returns (uint256) {
        return 0;
    }

    function supplyWithPermit(
        address asset,
        uint256 amount,
        address onBehalfOf,
        uint16 referralCode,
        uint256 deadline,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external override {}

    // Function to add liquidity to the mock pool
    function addLiquidity(address token, uint256 amount) external {
        require(
            IERC20(token).transferFrom(msg.sender, address(this), amount),
            "Transfer failed"
        );
    }

    // Function to get the flash loan premium
    function FLASHLOAN_PREMIUM_TOTAL() external pure returns (uint128) {
        return uint128(FLASH_LOAN_PREMIUM_TOTAL);
    }

    // Required interface implementations with empty bodies
    function supply(address asset, uint256 amount, address onBehalfOf, uint16 referralCode) external override {}
    function withdraw(address asset, uint256 amount, address to) external override returns (uint256) { return 0; }
    function borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf) external override {}
    function repay(address asset, uint256 amount, uint256 interestRateMode, address onBehalfOf) external override returns (uint256) { return 0; }
    function repayWithATokens(address asset, uint256 amount, uint256 interestRateMode) external override returns (uint256) { return 0; }
    function swapBorrowRateMode(address asset, uint256 interestRateMode) external override {}
    function rebalanceStableBorrowRate(address asset, address user) external override {}
    function setUserUseReserveAsCollateral(address asset, bool useAsCollateral) external override {}
    function liquidationCall(address collateralAsset, address debtAsset, address user, uint256 debtToCover, bool receiveAToken) external override {}
    function mintToTreasury(address[] calldata assets) external override {}
    function getReserveData(address asset) external view override returns (DataTypes.ReserveData memory) {}
    function getUserAccountData(address user) external view override returns (uint256 totalCollateralBase, uint256 totalDebtBase, uint256 availableBorrowsBase, uint256 currentLiquidationThreshold, uint256 ltv, uint256 healthFactor) {}
    function getConfiguration(address asset) external view override returns (DataTypes.ReserveConfigurationMap memory) {}
    function getUserConfiguration(address user) external view override returns (DataTypes.UserConfigurationMap memory) {}
    function getReserveNormalizedIncome(address asset) external view override returns (uint256) { return 0; }
    function getReserveNormalizedVariableDebt(address asset) external view override returns (uint256) { return 0; }
    function getReservesList() external view override returns (address[] memory) {}
    function ADDRESSES_PROVIDER() external view override returns (IPoolAddressesProvider) {}
    function finalizeTransfer(address asset, address from, address to, uint256 amount, uint256 balanceFromBefore, uint256 balanceToBefore) external override {}
    function initReserve(address asset, address aTokenAddress, address stableDebtAddress, address variableDebtAddress, address interestRateStrategyAddress) external override {}
    function dropReserve(address asset) external override {}
    function setReserveInterestRateStrategyAddress(address asset, address rateStrategyAddress) external override {}
    function setConfiguration(address asset, DataTypes.ReserveConfigurationMap calldata configuration) external override {}
    function updateBridgeProtocolFee(uint256 protocolFee) external override {}
    function updateFlashloanPremiums(uint128 flashLoanPremiumTotal, uint128 flashLoanPremiumToProtocol) external override {}
    function configureEModeCategory(uint8 id, DataTypes.EModeCategory memory category) external override {}
    function getEModeCategoryData(uint8 id) external view override returns (DataTypes.EModeCategory memory) {}
    function setUserEMode(uint8 categoryId) external override {}
    function getUserEMode(address user) external view override returns (uint256) { return 0; }
    function resetIsolationModeTotalDebt(address asset) external override {}
    function rescueTokens(address token, address to, uint256 amount) external override {}
} 