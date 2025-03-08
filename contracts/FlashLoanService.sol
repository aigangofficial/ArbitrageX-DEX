// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FlashLoanService
 * @notice Handles flash loan operations for arbitrage execution
 * @dev Inherits from FlashLoanSimpleReceiverBase for Aave V3 flash loans
 */

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./interfaces/aave/IPool.sol";
import "./interfaces/IFlashLoanSimpleReceiver.sol";
import "./interfaces/IArbitrageExecutor.sol";
import "./interfaces/IUniswapV2Router02.sol";
import "./interfaces/IMEVProtection.sol";
import "./SecurityAdmin.sol";

error ExecutionFailed();
error UnsupportedToken();
error InvalidExecutor();
error InvalidPath();
error InsufficientFundsForRepayment();
error InvalidTokenAddresses();
error InvalidAmount(uint256 amount, uint256 limit);
error InsufficientProfit(uint256 received, uint256 required);
error UnprofitableTrade();
error TransferFailed();
error InvalidFlashLoanProvider();
error InvalidTokenApproval();
error InvalidFlashLoanAmount(uint256 amount, uint256 minAmount, uint256 maxAmount);
error FlashLoanFailed();
error InvalidParameter(string reason);
error UnauthorizedInitiator(address initiator);
error MEVProtectionFailed();
error CommitmentRequired();
error CommitmentNotReady();
error CommitmentExpired();
error InvalidCommitment();
error FlashbotsRelayerRequired();
error InvalidExecutionMode();

contract FlashLoanService is IFlashLoanSimpleReceiver, SecurityAdmin {
    using SafeERC20 for IERC20;

    // Execution Mode enum (must match ArbitrageExecutor's enum)
    enum ExecutionMode {
        MAINNET,
        FORK
    }

    uint256 private constant BPS = 10000;
    uint256 private constant MIN_PROFIT_BPS = 50; // 0.5% minimum profit

    IPool public immutable aavePool;
    address public arbitrageExecutor;
    uint16 public constant REFERRAL_CODE = 0;

    uint16 public minProfitBps = 1;
    uint256 public minTradeAmount;
    uint256 public maxTradeAmount;
    mapping(address => bool) public flashLoanProviders;
    uint256 public constant FLASH_LOAN_FEE = 9;
    uint256 public minFlashLoanAmount;
    uint256 public maxFlashLoanAmount;
    mapping(address => bool) public supportedTokens;

    // Mapping to track profits for each token
    mapping(address => uint256) public profits;

    // MEV Protection
    IMEVProtection public mevProtection;
    bool public useMEVProtection = true;
    mapping(bytes32 => bool) public pendingTransactions;

    // Enhanced MEV Protection
    uint256 public commitmentMinAge = 1; // Minimum blocks before a commitment can be revealed
    uint256 public commitmentMaxAge = 50; // Maximum blocks before a commitment expires
    mapping(bytes32 => uint256) public commitmentBlocks; // Block number when commitment was made
    mapping(bytes32 => bool) public usedCommitments; // Track used commitments to prevent replay
    address public flashbotsRelayer; // Address of the Flashbots relayer
    bool public useFlashbots = false; // Whether to use Flashbots for private transactions
    mapping(bytes32 => uint256) public commitmentTimestamps; // Timestamp when commitment was made
    mapping(bytes32 => uint256) public commitmentNonces; // Nonce used in the commitment

    // Execution Mode
    ExecutionMode public executionMode = ExecutionMode.MAINNET;
    // Test mode flag (will be aligned with FORK execution mode)
    bool public testMode = false;

    event FlashLoanExecuted(
        address indexed asset,
        uint256 amount,
        uint256 premium,
        address indexed initiator
    );
    event ProfitAccrued(address indexed token, uint256 amount, uint256 totalProfit);
    event ExecutorUpdated(address oldExecutor, address newExecutor);
    event MinProfitBpsUpdated(uint16 oldValue, uint16 newValue);
    event FlashLoanProviderAdded(address indexed provider);
    event FlashLoanProviderRemoved(address indexed provider);
    event ArbitrageExecutorUpdated(address indexed executor);
    event TokenSupportUpdated(address indexed token, bool supported);
    event ExecutionModeChanged(ExecutionMode mode);
    event EmergencyWithdrawal(address indexed token, uint256 amount, address indexed recipient);
    event ArbitrageExecuted(
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        uint256 profit
    );
    event ProfitWithdrawn(address indexed token, uint256 amount, address indexed recipient);
    event MEVProtectionEnabled(bool enabled);
    event MEVProtectionContractUpdated(address indexed newProtection);
    event TransactionCommitted(bytes32 indexed commitmentHash, uint256 blockNumber);
    event CommitmentRevealed(bytes32 indexed commitmentHash, address indexed user);
    event FlashbotsRelayerUpdated(address indexed newRelayer);
    event FlashbotsUsageToggled(bool enabled);
    event CommitmentAgeParamsUpdated(uint256 minAge, uint256 maxAge);

    constructor(
        address _aavePool,
        address _arbitrageExecutor,
        uint256 _minAmount,
        uint256 _maxAmount,
        address _mevProtection
    ) {
        require(_aavePool != address(0), "Invalid Aave pool address");
        require(_arbitrageExecutor != address(0), "Invalid arbitrage executor address");
        require(_maxAmount > _minAmount, "Invalid amount bounds");

        aavePool = IPool(_aavePool);
        arbitrageExecutor = _arbitrageExecutor;
        minFlashLoanAmount = _minAmount;
        maxFlashLoanAmount = _maxAmount;

        // Set up MEV protection if provided
        if (_mevProtection != address(0)) {
            mevProtection = IMEVProtection(_mevProtection);
        }

        // Add Aave as a flash loan provider
        flashLoanProviders[_aavePool] = true;
    }

    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        // Security check 1: Validate caller is Aave pool or this is a test
        if (msg.sender != address(aavePool) && msg.sender != owner())
            revert UnauthorizedInitiator(msg.sender);

        // Security check 2: Validate initiator is authorized
        if (initiator != address(this) && initiator != owner())
            revert UnauthorizedInitiator(initiator);

        // Decode and validate parameters first
        (address tokenIn, address tokenOut, address router) = abi.decode(
            params,
            (address, address, address)
        );

        // Security check 3: Validate router first
        if (!IArbitrageExecutor(arbitrageExecutor).isApprovedRouter(router)) revert InvalidPath();

        // Security check 4: Validate tokens
        if (!supportedTokens[tokenIn] || !supportedTokens[tokenOut]) revert UnsupportedToken();

        // Security check 5: Validate asset support
        if (!supportedTokens[asset]) revert UnsupportedToken();

        // Security check 6: Validate amount boundaries
        if (amount < minFlashLoanAmount || amount > maxFlashLoanAmount) {
            revert InvalidFlashLoanAmount(amount, minFlashLoanAmount, maxFlashLoanAmount);
        }

        // Security check 7: Validate contract has sufficient balance for repayment
        uint256 repaymentAmount = amount + premium;
        uint256 contractBalance = IERC20(asset).balanceOf(address(this));
        if (contractBalance < repaymentAmount) revert InsufficientFundsForRepayment();

        // Transfer tokens to ArbitrageExecutor
        IERC20(asset).safeTransfer(arbitrageExecutor, amount);

        try
            IArbitrageExecutor(arbitrageExecutor).executeArbitrage(
                tokenIn,
                tokenOut,
                amount,
                router
            )
        returns (uint256 profit) {
            // Security check 8: Minimum profit validation including flash loan fee
            uint256 minProfit = (amount * minProfitBps) / BPS + premium;
            if (profit < minProfit) revert InsufficientProfit(profit, minProfit);

            // Security check 9: Ensure profit covers repayment
            uint256 finalBalance = IERC20(asset).balanceOf(address(this));
            if (finalBalance < repaymentAmount) revert InsufficientFundsForRepayment();

            // Track remaining profit
            profits[asset] += finalBalance - repaymentAmount;

            // Approve repayment
            IERC20(asset).safeApprove(msg.sender, repaymentAmount);

            emit FlashLoanExecuted(asset, amount, premium, initiator);
            emit ProfitAccrued(asset, profit, profits[asset]);

            return true;
        } catch Error(string memory reason) {
            revert(reason);
        } catch {
            revert ExecutionFailed();
        }
    }

    function executeArbitrage(
        address tokenIn,
        address tokenOut,
        address router,
        uint256 amount,
        uint256 requiredAmount
    ) external returns (uint256 profit) {
        require(msg.sender == address(this), "Unauthorized");

        // Execute trade through router
        IERC20(tokenIn).safeApprove(router, amount);

        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;

        uint256 balanceBefore = IERC20(tokenOut).balanceOf(address(this));

        IUniswapV2Router02(router).swapExactTokensForTokens(
            amount,
            0, // Accept any amount of tokenOut
            path,
            address(this),
            block.timestamp
        );

        uint256 balanceAfter = IERC20(tokenOut).balanceOf(address(this));
        uint256 received = balanceAfter - balanceBefore;

        // Convert back to original token if needed
        if (tokenOut != tokenIn) {
            received = _convertToInputToken(tokenOut, tokenIn, router, received, requiredAmount);
        }

        // Calculate profit
        if (received <= requiredAmount) {
            revert InsufficientProfit(received, requiredAmount);
        }

        return received - requiredAmount;
    }

    function _convertToInputToken(
        address fromToken,
        address toToken,
        address router,
        uint256 amount,
        uint256 minReturn
    ) internal returns (uint256) {
        IERC20(fromToken).safeApprove(router, amount);

        address[] memory path = new address[](2);
        path[0] = fromToken;
        path[1] = toToken;

        uint256[] memory amounts = IUniswapV2Router02(router).swapExactTokensForTokens(
            amount,
            minReturn,
            path,
            address(this),
            block.timestamp
        );

        return amounts[amounts.length - 1];
    }

    function requestFlashLoan(
        address token,
        uint256 amount,
        address tokenIn,
        address tokenOut,
        address router
    ) external onlyOwner {
        if (token == address(0)) revert InvalidTokenAddresses();
        if (amount < minFlashLoanAmount || amount > maxFlashLoanAmount) {
            revert InvalidFlashLoanAmount(amount, minFlashLoanAmount, maxFlashLoanAmount);
        }

        address[] memory assets = new address[](1);
        assets[0] = token;

        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;

        uint256[] memory modes = new uint256[](1);
        modes[0] = 0; // No debt - flash loan

        bytes memory params = abi.encode(tokenIn, tokenOut, router);

        aavePool.flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            params,
            REFERRAL_CODE
        );
    }

    function withdraw(address token, uint256 amount) external onlyOwner {
        require(amount > 0, "Amount must be greater than 0");
        IERC20(token).safeTransfer(msg.sender, amount);
    }

    function withdrawProfit(address token, address recipient, uint256 amount) external onlyOwner {
        uint256 availableProfit = profits[token];
        require(amount <= availableProfit, "Insufficient profit");

        profits[token] -= amount;
        IERC20(token).safeTransfer(recipient, amount);
    }

    function emergencyWithdraw(
        address token,
        uint256 amount,
        address recipient
    ) external onlyOwner {
        require(token != address(0), "Invalid token address");
        require(amount > 0, "Amount must be greater than 0");
        require(recipient != address(0), "Invalid recipient address");

        IERC20(token).safeTransfer(recipient, amount);
    }

    function setMinProfitBps(uint16 _minProfitBps) external onlyOwner {
        if (_minProfitBps == 0) revert InsufficientProfit(0, 1);
        uint16 oldValue = minProfitBps;
        minProfitBps = _minProfitBps;
        emit MinProfitBpsUpdated(oldValue, _minProfitBps);
    }

    function addFlashLoanProvider(address provider) external onlyOwner {
        if (provider == address(0)) revert InvalidFlashLoanProvider();
        flashLoanProviders[provider] = true;
        emit FlashLoanProviderAdded(provider);
    }

    function removeFlashLoanProvider(address provider) external onlyOwner {
        if (provider == address(0)) revert InvalidFlashLoanProvider();
        flashLoanProviders[provider] = false;
        emit FlashLoanProviderRemoved(provider);
    }

    function updateTokenSupport(address token, bool supported) external onlyOwner {
        if (token == address(0)) revert InvalidExecutor();
        supportedTokens[token] = supported;
        emit TokenSupportUpdated(token, supported);
    }

    function executeParameterChange(
        string calldata parameter,
        uint256 newValue
    ) external override onlyOwner timelocked(keccak256(abi.encodePacked(parameter))) {
        _executeParameterChange(parameter, newValue);
    }

    function _executeParameterChange(
        string calldata parameter,
        uint256 newValue
    ) internal override {
        bytes32 paramHash = keccak256(abi.encodePacked(parameter));

        if (paramHash == keccak256(abi.encodePacked("minFlashLoanAmount"))) {
            if (newValue == 0) revert InvalidParameter("Invalid minimum amount");
            minFlashLoanAmount = newValue;
        } else if (paramHash == keccak256(abi.encodePacked("maxFlashLoanAmount"))) {
            if (newValue <= minFlashLoanAmount) revert InvalidParameter("Invalid maximum amount");
            maxFlashLoanAmount = newValue;
        } else if (paramHash == keccak256(abi.encodePacked("minTradeAmount"))) {
            if (newValue == 0) revert InvalidParameter("Invalid minimum trade amount");
            if (newValue >= maxTradeAmount) revert InvalidParameter("Trade amount exceeds maximum");
            minTradeAmount = newValue;
        } else if (paramHash == keccak256(abi.encodePacked("maxTradeAmount"))) {
            if (newValue <= minTradeAmount) revert InvalidParameter("Trade amount below minimum");
            maxTradeAmount = newValue;
        } else {
            revert InvalidParameter("Invalid parameter");
        }
    }

    function updateExecutor(address newExecutor) external onlyOwner {
        require(newExecutor != address(0), "Invalid executor address");
        address oldExecutor = arbitrageExecutor;
        arbitrageExecutor = newExecutor;
        emit ExecutorUpdated(oldExecutor, newExecutor);
    }

    function setMEVProtection(address _mevProtection) external onlyOwner {
        if (_mevProtection == address(0)) revert InvalidParameter("Invalid MEV protection address");
        mevProtection = IMEVProtection(_mevProtection);
        emit MEVProtectionContractUpdated(_mevProtection);
    }

    function toggleMEVProtection(bool _enabled) external onlyOwner {
        useMEVProtection = _enabled;
        emit MEVProtectionEnabled(_enabled);
    }

    /**
     * @dev Set the Flashbots relayer address
     * @param _relayer Address of the Flashbots relayer
     */
    function setFlashbotsRelayer(address _relayer) external onlyOwner {
        require(_relayer != address(0), "Invalid relayer address");
        flashbotsRelayer = _relayer;
        emit FlashbotsRelayerUpdated(_relayer);
    }

    /**
     * @dev Toggle the use of Flashbots for private transactions
     * @param _enabled Whether to use Flashbots
     */
    function toggleFlashbots(bool _enabled) external onlyOwner {
        useFlashbots = _enabled;
        emit FlashbotsUsageToggled(_enabled);
    }

    /**
     * @dev Toggle test mode for testing purposes
     * @param _enabled Whether to enable test mode
     */
    function toggleTestMode(bool _enabled) external onlyOwner {
        testMode = _enabled;
    }

    /**
     * @dev Set the commitment age parameters
     * @param _minAge Minimum blocks before a commitment can be revealed
     * @param _maxAge Maximum blocks before a commitment expires
     */
    function setCommitmentAgeParams(uint256 _minAge, uint256 _maxAge) external onlyOwner {
        require(_minAge > 0, "Min age must be positive");
        require(_maxAge > _minAge, "Max age must be greater than min age");
        commitmentMinAge = _minAge;
        commitmentMaxAge = _maxAge;
        emit CommitmentAgeParamsUpdated(_minAge, _maxAge);
    }

    /**
     * @dev Create a commitment for a flash loan transaction with enhanced protection
     * @param tokenAddress The token to borrow in the flash loan
     * @param amount The amount to borrow
     * @param secret A secret value to prevent front-running
     * @return commitmentHash The hash of the commitment
     */
    function commitFlashLoanTransaction(
        address tokenAddress,
        uint256 amount,
        bytes32 secret
    ) external whenNotPaused returns (bytes32) {
        if (!useMEVProtection || address(mevProtection) == address(0)) {
            revert MEVProtectionFailed();
        }

        // Store the current timestamp and nonce
        uint256 commitmentTimestamp = block.timestamp;
        uint256 timeBasedNonce = mevProtection.getTimeBasedNonce();

        // Create commitment hash with additional entropy
        bytes32 commitmentHash = keccak256(
            abi.encodePacked(
                msg.sender,
                tokenAddress,
                amount,
                secret,
                block.number,
                commitmentTimestamp,
                timeBasedNonce
            )
        );

        // Submit commitment to MEV protection contract
        mevProtection.submitCommitment(commitmentHash);

        // Store pending transaction and block number
        pendingTransactions[commitmentHash] = true;
        commitmentBlocks[commitmentHash] = block.number;
        commitmentTimestamps[commitmentHash] = commitmentTimestamp;
        commitmentNonces[commitmentHash] = timeBasedNonce;

        emit TransactionCommitted(commitmentHash, block.number);
        return commitmentHash;
    }

    /**
     * @dev Execute a flash loan with MEV protection using the commit-reveal scheme
     * @param tokenAddress The token to borrow in the flash loan
     * @param amount The amount to borrow
     * @param secret The secret used in the commitment
     * @param commitmentHash The hash of the commitment
     */
    function executeFlashLoanWithMEVProtection(
        address tokenAddress,
        uint256 amount,
        bytes32 secret,
        bytes32 commitmentHash
    ) external whenNotPaused nonReentrant {
        if (!useMEVProtection || address(mevProtection) == address(0)) {
            revert MEVProtectionFailed();
        }

        // Verify commitment exists
        if (!pendingTransactions[commitmentHash]) {
            revert CommitmentRequired();
        }

        // Verify commitment hasn't been used
        if (usedCommitments[commitmentHash]) {
            revert InvalidCommitment();
        }

        // Verify commitment age
        uint256 commitmentBlock = commitmentBlocks[commitmentHash];

        // Always check the commitment age, even in test mode
        if (block.number < commitmentBlock + commitmentMinAge) {
            revert CommitmentNotReady();
        }
        if (block.number > commitmentBlock + commitmentMaxAge) {
            revert CommitmentExpired();
        }

        // Verify the commitment hash matches
        bytes32 calculatedHash = keccak256(
            abi.encodePacked(
                msg.sender,
                tokenAddress,
                amount,
                secret,
                commitmentBlock,
                commitmentTimestamps[commitmentHash],
                commitmentNonces[commitmentHash]
            )
        );

        if (calculatedHash != commitmentHash) {
            revert InvalidCommitment();
        }

        // Mark commitment as used
        usedCommitments[commitmentHash] = true;

        // Clear pending transaction
        delete pendingTransactions[commitmentHash];

        emit CommitmentRevealed(commitmentHash, msg.sender);

        // Execute the flash loan
        if (useFlashbots && flashbotsRelayer != address(0)) {
            _executeFlashLoanViaFlashbots(tokenAddress, amount);
        } else {
            _executeFlashLoan(tokenAddress, amount);
        }
    }

    /**
     * @dev Execute a flash loan via Flashbots to prevent front-running
     * @param tokenAddress The token to borrow in the flash loan
     * @param amount The amount to borrow
     */
    function _executeFlashLoanViaFlashbots(address tokenAddress, uint256 amount) internal {
        if (flashbotsRelayer == address(0)) {
            revert FlashbotsRelayerRequired();
        }

        // Prepare the flash loan parameters
        bytes memory params = abi.encode(tokenAddress, amount, msg.sender);

        // Request the Flashbots relayer to execute the transaction
        (bool success, ) = flashbotsRelayer.call(
            abi.encodeWithSignature(
                "relayTransaction(address,bytes)",
                address(this),
                abi.encodeWithSignature("executeFlashLoan(address,uint256)", tokenAddress, amount)
            )
        );

        if (!success) {
            revert MEVProtectionFailed();
        }
    }

    function executeFlashLoan(
        address tokenAddress,
        uint256 amount
    ) external whenNotPaused nonReentrant {
        // If MEV protection is enabled, require a commitment
        if (useMEVProtection && address(mevProtection) != address(0)) {
            revert CommitmentRequired();
        }

        _executeFlashLoan(tokenAddress, amount);
    }

    function _executeFlashLoan(address tokenAddress, uint256 amount) internal {
        // Validate parameters
        if (tokenAddress == address(0)) revert InvalidParameter("Invalid token address");
        if (amount == 0) revert InvalidParameter("Amount must be greater than 0");
        if (amount < minTradeAmount) revert InvalidAmount(amount, minTradeAmount);
        if (maxTradeAmount > 0 && amount > maxTradeAmount)
            revert InvalidAmount(amount, maxTradeAmount);

        // Skip actual flash loan execution in FORK mode
        if (executionMode == ExecutionMode.FORK) {
            emit FlashLoanExecuted(tokenAddress, amount, 0, msg.sender);
            return;
        }

        // Execute flash loan
        bytes memory params = abi.encode(msg.sender);
        aavePool.flashLoanSimple(address(this), tokenAddress, amount, params, REFERRAL_CODE);
    }

    /**
     * @dev Set the execution mode (MAINNET or FORK)
     * @param _mode The execution mode to set
     */
    function setExecutionMode(ExecutionMode _mode) external onlyOwner {
        executionMode = _mode;

        // Align testMode with FORK execution mode
        testMode = (_mode == ExecutionMode.FORK);

        emit ExecutionModeChanged(_mode);
    }

    /**
     * @dev Get the current execution mode
     * @return The current execution mode
     */
    function getExecutionMode() external view returns (ExecutionMode) {
        return executionMode;
    }

    receive() external payable {}
}
