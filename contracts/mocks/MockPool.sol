// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@aave/core-v3/contracts/interfaces/IPool.sol";
import "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import "@aave/core-v3/contracts/protocol/libraries/types/DataTypes.sol";
import "../interfaces/IFlashLoanService.sol";

error InvalidAddress();
error InvalidAmount();
error InsufficientFundsForRepayment();
error TransferFailed();
error ApprovalFailed();
error NotImplemented();

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

contract MockPool is IFlashLoanService, IPool, Ownable, ReentrancyGuard {
    address public immutable tokenA;
    address public immutable tokenB;
    address public immutable poolProvider;

    uint256 public constant BPS = 10000;
    uint256 public constant FLASH_LOAN_FEE_BPS = 9; // 0.09% fee
    address public arbitrageExecutor;
    uint16 public minProfitBps;

    event FlashLoan(
        address indexed borrower,
        address indexed token,
        uint256 amount,
        uint256 fee,
        uint256 timestamp
    );

    mapping(address => uint256) public balances;
    mapping(address => bool) public isFlashLoanProvider;
    IPoolAddressesProvider private immutable _addressesProvider;

    constructor(address _tokenA, address _tokenB, address _provider) Ownable(msg.sender) {
        if (_tokenA == address(0) || _tokenB == address(0) || _provider == address(0)) {
            revert InvalidAddress();
        }

        tokenA = _tokenA;
        tokenB = _tokenB;
        poolProvider = _provider;

        _addressesProvider = IPoolAddressesProvider(_provider);
        _transferOwnership(msg.sender);
    }

    function ADDRESSES_PROVIDER() external view override returns (IPoolAddressesProvider) {
        return _addressesProvider;
    }

    function flashLoan(
        address receiverAddress,
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata modes,
        address onBehalfOf,
        bytes calldata params,
        uint16 referralCode
    ) external override {
        require(assets.length == amounts.length, "Array lengths must match");
        require(assets.length == modes.length, "Array lengths must match");
        require(assets.length == 1, "Only single asset flash loans supported in mock");
        require(assets[0] == tokenA || assets[0] == tokenB, "Unsupported asset");
        require(amounts[0] > 0, "Invalid amount");

        // Store initial balance
        uint256 initialBalance = IERC20(assets[0]).balanceOf(address(this));

        // Calculate fee
        uint256 amount = amounts[0];
        uint256 fee = (amount * FLASH_LOAN_FEE_BPS) / BPS;
        uint256 amountToRepay = amount + fee;

        // Transfer tokens to receiver
        bool success = IERC20(assets[0]).transfer(receiverAddress, amount);
        require(success, "Transfer to receiver failed");

        // Call executeOperation on receiver
        bool executed = IFlashLoanReceiver(receiverAddress).executeOperation(
            assets[0],
            amount,
            fee,
            onBehalfOf,
            params
        );
        require(executed, "Flash loan execution failed");

        // Verify final balance after receiver's repayment
        uint256 finalBalance = IERC20(assets[0]).balanceOf(address(this));
        if (finalBalance < initialBalance + fee) {
            revert InsufficientFundsForRepayment();
        }
    }

    function supply(
        address asset,
        uint256 amount,
        address onBehalfOf,
        uint16 referralCode
    ) external override {
        require(asset != address(0), "Invalid asset");
        require(amount > 0, "Invalid amount");
        balances[onBehalfOf] += amount;
    }

    function withdraw(
        address asset,
        uint256 amount,
        address to
    ) external override returns (uint256) {
        require(asset != address(0), "Invalid asset");
        require(amount > 0, "Invalid amount");
        require(balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;
        return amount;
    }

    function borrow(
        address asset,
        uint256 amount,
        uint256 interestRateMode,
        uint16 referralCode,
        address onBehalfOf
    ) external override {
        require(asset != address(0), "Invalid asset");
        require(amount > 0, "Invalid amount");
        balances[onBehalfOf] += amount;
    }

    function repay(
        address asset,
        uint256 amount,
        uint256 interestRateMode,
        address onBehalfOf
    ) external override returns (uint256) {
        require(asset != address(0), "Invalid asset");
        require(amount > 0, "Invalid amount");
        require(balances[onBehalfOf] >= amount, "Insufficient balance");

        balances[onBehalfOf] -= amount;
        return amount;
    }

    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external override {
        require(receiverAddress != address(0), "Invalid receiver");
        require(asset != address(0), "Invalid asset");
        require(amount > 0, "Invalid amount");

        // Calculate fee
        uint256 fee = (amount * FLASH_LOAN_FEE_BPS) / BPS;

        // Transfer tokens to receiver
        balances[receiverAddress] += amount;

        // Execute operation
        IFlashLoanReceiver(receiverAddress).executeOperation(
            asset,
            amount,
            fee,
            msg.sender,
            params
        );

        // Verify repayment
        require(balances[receiverAddress] >= amount + fee, "Flash loan not repaid");
        balances[receiverAddress] -= (amount + fee);
    }

    function setUserUseReserveAsCollateral(address asset, bool useAsCollateral) external override {
        // Not implemented for mock
    }

    function liquidationCall(
        address collateralAsset,
        address debtAsset,
        address user,
        uint256 debtToCover,
        bool receiveAToken
    ) external override {
        // Mock implementation - no actual liquidation
    }

    function getReserveData(
        address asset
    ) external view override returns (DataTypes.ReserveData memory) {
        return
            DataTypes.ReserveData({
                configuration: DataTypes.ReserveConfigurationMap(0),
                liquidityIndex: 0,
                currentLiquidityRate: 0,
                variableBorrowIndex: 0,
                currentVariableBorrowRate: 0,
                currentStableBorrowRate: 0,
                lastUpdateTimestamp: 0,
                id: 0,
                aTokenAddress: address(0),
                stableDebtTokenAddress: address(0),
                variableDebtTokenAddress: address(0),
                interestRateStrategyAddress: address(0),
                accruedToTreasury: 0,
                unbacked: 0,
                isolationModeTotalDebt: 0
            });
    }

    function getUserAccountData(
        address user
    )
        external
        view
        override
        returns (
            uint256 totalCollateralBase,
            uint256 totalDebtBase,
            uint256 availableBorrowsBase,
            uint256 currentLiquidationThreshold,
            uint256 ltv,
            uint256 healthFactor
        )
    {
        return (0, 0, 0, 0, 0, type(uint256).max);
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

    function backUnbacked(
        address asset,
        uint256 amount,
        uint256 fee
    ) external override returns (uint256) {
        return 0;
    }

    function deposit(
        address asset,
        uint256 amount,
        address onBehalfOf,
        uint16 referralCode
    ) external override {}

    function getReserveAddressById(uint16 id) external pure override returns (address) {
        return address(0);
    }

    function mintUnbacked(
        address asset,
        uint256 amount,
        address onBehalfOf,
        uint16 referralCode
    ) external override {}

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
        require(IERC20(token).transferFrom(msg.sender, address(this), amount), "Transfer failed");
    }

    // Function to get the flash loan premium
    function FLASHLOAN_PREMIUM_TOTAL() external pure returns (uint128) {
        return uint128(FLASH_LOAN_FEE_BPS);
    }

    // Additional helper functions for testing
    function setBalance(address user, uint256 amount) external onlyOwner {
        balances[user] = amount;
    }

    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }

    function repayWithATokens(
        address asset,
        uint256 amount,
        uint256 interestRateMode
    ) external override returns (uint256) {
        return 0;
    }

    function swapBorrowRateMode(address asset, uint256 interestRateMode) external override {}

    function rebalanceStableBorrowRate(address asset, address user) external override {}

    function mintToTreasury(address[] calldata assets) external override {}

    function getConfiguration(
        address asset
    ) external view override returns (DataTypes.ReserveConfigurationMap memory) {
        return DataTypes.ReserveConfigurationMap(0);
    }

    function getUserConfiguration(
        address user
    ) external view override returns (DataTypes.UserConfigurationMap memory) {
        return DataTypes.UserConfigurationMap(0);
    }

    function getReserveNormalizedIncome(address asset) external view override returns (uint256) {
        return 1e27;
    }

    function getReserveNormalizedVariableDebt(
        address asset
    ) external view override returns (uint256) {
        return 0;
    }

    function getReservesList() external view override returns (address[] memory) {
        return new address[](0);
    }

    function finalizeTransfer(
        address asset,
        address from,
        address to,
        uint256 amount,
        uint256 balanceFromBefore,
        uint256 balanceToBefore
    ) external override {}

    function initReserve(
        address asset,
        address aTokenAddress,
        address stableDebtAddress,
        address variableDebtAddress,
        address interestRateStrategyAddress
    ) external override {}

    function dropReserve(address asset) external override {}

    function setReserveInterestRateStrategyAddress(
        address asset,
        address rateStrategyAddress
    ) external override {}

    function setConfiguration(
        address asset,
        DataTypes.ReserveConfigurationMap calldata configuration
    ) external override {}

    function updateBridgeProtocolFee(uint256 protocolFee) external override {}

    function updateFlashloanPremiums(
        uint128 flashLoanPremiumTotal,
        uint128 flashLoanPremiumToProtocol
    ) external override {}

    function configureEModeCategory(
        uint8 id,
        DataTypes.EModeCategory memory category
    ) external override {}

    function getEModeCategoryData(
        uint8 id
    ) external view override returns (DataTypes.EModeCategory memory) {
        return
            DataTypes.EModeCategory({
                ltv: 0,
                liquidationThreshold: 0,
                liquidationBonus: 0,
                priceSource: address(0),
                label: ""
            });
    }

    function setUserEMode(uint8 categoryId) external override {}

    function getUserEMode(address user) external view override returns (uint256) {
        return 0;
    }

    function resetIsolationModeTotalDebt(address asset) external override {}

    function rescueTokens(address token, address to, uint256 amount) external override {}

    function executeArbitrage(
        address _tokenA,
        address _tokenB,
        uint256 amount,
        bytes calldata data
    ) external override {
        // Mock implementation
    }

    function executeOperation(
        address asset,
        uint256 amount,
        uint256 fee,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        // Mock implementation
        return true;
    }

    function setArbitrageExecutor(address _arbitrageExecutor) external override onlyOwner {
        if (_arbitrageExecutor == address(0)) revert InvalidAddress();
        arbitrageExecutor = _arbitrageExecutor;
    }

    function setMinProfitBps(uint16 _minProfitBps) external override onlyOwner {
        minProfitBps = _minProfitBps;
    }

    function withdrawToken(address token, uint256 amount) external override onlyOwner {
        if (token == address(0)) revert InvalidAddress();
        if (amount == 0) revert InvalidAmount();
        if (!IERC20(token).transfer(msg.sender, amount)) revert TransferFailed();
    }

    function approveTokens(
        address[] calldata tokens,
        address[] calldata spenders
    ) external override onlyOwner {
        if (tokens.length != spenders.length) revert InvalidAmount();
        for (uint256 i = 0; i < tokens.length; i++) {
            if (!IERC20(tokens[i]).approve(spenders[i], type(uint256).max)) revert ApprovalFailed();
        }
    }
}
