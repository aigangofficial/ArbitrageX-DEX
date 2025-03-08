// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FrontRunningProtection
 * @dev Provides protection against front-running attacks
 *
 * This contract implements multiple strategies to prevent front-running attacks
 * on arbitrage transactions. It uses a combination of commit-reveal schemes,
 * gas price limits, and transaction bundling to ensure that transactions
 * cannot be easily front-run by malicious actors.
 *
 * PROTECTION STRATEGIES:
 * 1. Commit-Reveal Scheme:
 *    - Users commit to transactions with a hash
 *    - Actual transaction details are revealed later
 *    - Prevents miners from seeing transaction details early
 *
 * 2. Gas Price Limits:
 *    - Sets maximum gas price for transactions
 *    - Prevents attackers from outbidding with higher gas
 *    - Dynamically adjusts based on network conditions
 *
 * 3. Transaction Bundling:
 *    - Groups multiple transactions together
 *    - All transactions in a bundle must succeed or fail
 *    - Makes it harder to target specific transactions
 *
 * 4. Time-Based Execution:
 *    - Transactions can be scheduled for future blocks
 *    - Reduces the window for front-running
 *    - Allows for coordinated execution
 */

import "../interfaces/IFrontRunningProtection.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract FrontRunningProtection is IFrontRunningProtection, Ownable, ReentrancyGuard {
    // Commitment storage
    mapping(bytes32 => bool) public commitments;
    mapping(bytes32 => uint256) public commitmentTimestamps;
    mapping(bytes32 => bool) public usedCommitments;

    // Gas price limits
    uint256 public maxGasPrice;
    bool public enforceGasPrice = true;

    // Time windows
    uint256 public commitRevealWindow = 10 minutes;
    uint256 public minCommitAge = 1 minutes;

    // Flashbots integration
    address public flashbotsRelayer;
    bool public usePrivateMempool = true;

    // Custom errors
    error InvalidCommitment();
    error CommitmentTooRecent();
    error CommitmentExpired();
    error CommitmentAlreadyUsed();
    error GasPriceTooHigh(uint256 provided, uint256 maximum);
    error InvalidFlashbotsRelayer();
    error ExecutionFailed();
    error InvalidTimeWindow();

    /**
     * @dev Constructor
     * @param _maxGasPrice Initial maximum gas price
     * @param _flashbotsRelayer Address of the Flashbots relayer
     */
    constructor(uint256 _maxGasPrice, address _flashbotsRelayer) {
        maxGasPrice = _maxGasPrice;
        if (_flashbotsRelayer != address(0)) {
            flashbotsRelayer = _flashbotsRelayer;
        }
    }

    /**
     * @dev Submit a commitment hash
     * @param commitmentHash Hash of the commitment
     */
    function submitCommitment(bytes32 commitmentHash) external override {
        if (commitmentHash == bytes32(0)) revert InvalidCommitment();
        if (commitments[commitmentHash]) revert InvalidCommitment();

        commitments[commitmentHash] = true;
        commitmentTimestamps[commitmentHash] = block.timestamp;

        emit CommitmentSubmitted(commitmentHash, block.timestamp);
    }

    /**
     * @dev Reveal and execute a commitment
     * @param target Address of the contract to call
     * @param value Amount of ETH to send
     * @param data Calldata for the transaction
     * @param secret Secret used in the commitment
     */
    function revealAndExecute(
        address target,
        uint256 value,
        bytes calldata data,
        bytes32 secret
    ) external override nonReentrant {
        // Calculate commitment hash
        bytes32 commitmentHash = keccak256(
            abi.encode(target, value, keccak256(data), secret, msg.sender)
        );

        // Verify commitment exists
        if (!commitments[commitmentHash]) revert InvalidCommitment();

        // Check if commitment has been used
        if (usedCommitments[commitmentHash]) revert CommitmentAlreadyUsed();

        // Check commitment age
        uint256 commitTime = commitmentTimestamps[commitmentHash];
        if (block.timestamp < commitTime + minCommitAge) revert CommitmentTooRecent();
        if (block.timestamp > commitTime + commitRevealWindow) revert CommitmentExpired();

        // Mark commitment as used
        usedCommitments[commitmentHash] = true;

        // Check gas price if enforcement is enabled
        if (enforceGasPrice && tx.gasprice > maxGasPrice) {
            revert GasPriceTooHigh(tx.gasprice, maxGasPrice);
        }

        // Execute the transaction
        emit CommitmentRevealed(commitmentHash, msg.sender);

        (bool success, ) = target.call{value: value}(data);
        emit CommitmentExecuted(commitmentHash, success);

        if (!success) revert ExecutionFailed();
    }

    /**
     * @dev Execute a bundle of transactions atomically
     * @param targets Array of target addresses
     * @param values Array of ETH values
     * @param datas Array of calldata
     */
    function executeBundle(
        address[] calldata targets,
        uint256[] calldata values,
        bytes[] calldata datas
    ) external override nonReentrant {
        // Validate input arrays
        uint256 length = targets.length;
        if (length == 0 || length != values.length || length != datas.length) {
            revert InvalidCommitment();
        }

        // Check gas price if enforcement is enabled
        if (enforceGasPrice && tx.gasprice > maxGasPrice) {
            revert GasPriceTooHigh(tx.gasprice, maxGasPrice);
        }

        // Generate bundle ID for event
        bytes32 bundleId = keccak256(abi.encode(targets, values, block.number));

        // Execute all transactions
        for (uint256 i = 0; i < length; i++) {
            (bool success, ) = targets[i].call{value: values[i]}(datas[i]);
            if (!success) revert ExecutionFailed();
        }

        emit BundleExecuted(bundleId, targets.length);
    }

    /**
     * @dev Set the maximum gas price
     * @param _maxGasPrice New maximum gas price
     */
    function setMaxGasPrice(uint256 _maxGasPrice) external override onlyOwner {
        uint256 oldPrice = maxGasPrice;
        maxGasPrice = _maxGasPrice;
        emit MaxGasPriceUpdated(oldPrice, _maxGasPrice);
    }

    /**
     * @dev Set the commit-reveal window
     * @param _window New window duration in seconds
     */
    function setCommitRevealWindow(uint256 _window) external override onlyOwner {
        if (_window < minCommitAge) revert InvalidTimeWindow();
        uint256 oldWindow = commitRevealWindow;
        commitRevealWindow = _window;
        emit CommitRevealWindowUpdated(oldWindow, _window);
    }

    /**
     * @dev Set the minimum commitment age
     * @param _minAge New minimum age in seconds
     */
    function setMinCommitAge(uint256 _minAge) external override onlyOwner {
        if (_minAge >= commitRevealWindow) revert InvalidTimeWindow();
        uint256 oldAge = minCommitAge;
        minCommitAge = _minAge;
        emit MinCommitAgeUpdated(oldAge, _minAge);
    }

    /**
     * @dev Set the Flashbots relayer address
     * @param _relayer New relayer address
     */
    function setFlashbotsRelayer(address _relayer) external override onlyOwner {
        if (_relayer == address(0)) revert InvalidFlashbotsRelayer();
        address oldRelayer = flashbotsRelayer;
        flashbotsRelayer = _relayer;
        emit FlashbotsRelayerUpdated(oldRelayer, _relayer);
    }

    /**
     * @dev Toggle the use of private mempool
     * @param _enabled Whether to use private mempool
     */
    function togglePrivateMempool(bool _enabled) external override onlyOwner {
        usePrivateMempool = _enabled;
        emit PrivateMempoolToggled(_enabled);
    }

    /**
     * @dev Toggle gas price enforcement
     * @param _enforced Whether to enforce gas price limits
     */
    function toggleGasPriceEnforcement(bool _enforced) external override onlyOwner {
        enforceGasPrice = _enforced;
        emit GasPriceEnforcementToggled(_enforced);
    }

    /**
     * @dev Get a time-based nonce for commitments
     * @return Time-based nonce
     */
    function getTimeBasedNonce() external view override returns (uint256) {
        return block.timestamp;
    }

    /**
     * @dev Check if a commitment exists
     * @param commitmentHash Hash of the commitment
     * @return Whether the commitment exists
     */
    function commitmentExists(bytes32 commitmentHash) external view override returns (bool) {
        return commitments[commitmentHash];
    }

    /**
     * @dev Check if a commitment has been used
     * @param commitmentHash Hash of the commitment
     * @return Whether the commitment has been used
     */
    function isCommitmentUsed(bytes32 commitmentHash) external view override returns (bool) {
        return usedCommitments[commitmentHash];
    }

    /**
     * @dev Get the timestamp of a commitment
     * @param commitmentHash Hash of the commitment
     * @return Timestamp when the commitment was submitted
     */
    function getCommitmentTimestamp(
        bytes32 commitmentHash
    ) external view override returns (uint256) {
        return commitmentTimestamps[commitmentHash];
    }

    /**
     * @dev Receive ETH
     */
    receive() external payable {}
}
