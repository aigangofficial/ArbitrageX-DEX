// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IFrontRunningProtection
 * @dev Interface for front-running protection contract
 */
interface IFrontRunningProtection {
    // Events
    event CommitmentSubmitted(bytes32 indexed commitmentHash, uint256 timestamp);
    event CommitmentRevealed(bytes32 indexed commitmentHash, address indexed sender);
    event CommitmentExecuted(bytes32 indexed commitmentHash, bool success);
    event BundleExecuted(bytes32 indexed bundleId, uint256 size);
    event MaxGasPriceUpdated(uint256 oldPrice, uint256 newPrice);
    event CommitRevealWindowUpdated(uint256 oldWindow, uint256 newWindow);
    event MinCommitAgeUpdated(uint256 oldAge, uint256 newAge);
    event FlashbotsRelayerUpdated(address indexed oldRelayer, address indexed newRelayer);
    event PrivateMempoolToggled(bool enabled);
    event GasPriceEnforcementToggled(bool enforced);
    
    /**
     * @dev Submit a commitment hash
     * @param commitmentHash Hash of the commitment
     */
    function submitCommitment(bytes32 commitmentHash) external;
    
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
    ) external;
    
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
    ) external;
    
    /**
     * @dev Set the maximum gas price
     * @param _maxGasPrice New maximum gas price
     */
    function setMaxGasPrice(uint256 _maxGasPrice) external;
    
    /**
     * @dev Set the commit-reveal window
     * @param _window New window duration in seconds
     */
    function setCommitRevealWindow(uint256 _window) external;
    
    /**
     * @dev Set the minimum commitment age
     * @param _minAge New minimum age in seconds
     */
    function setMinCommitAge(uint256 _minAge) external;
    
    /**
     * @dev Set the Flashbots relayer address
     * @param _relayer New relayer address
     */
    function setFlashbotsRelayer(address _relayer) external;
    
    /**
     * @dev Toggle the use of private mempool
     * @param _enabled Whether to use private mempool
     */
    function togglePrivateMempool(bool _enabled) external;
    
    /**
     * @dev Toggle gas price enforcement
     * @param _enforced Whether to enforce gas price limits
     */
    function toggleGasPriceEnforcement(bool _enforced) external;
    
    /**
     * @dev Get a time-based nonce for commitments
     * @return Time-based nonce
     */
    function getTimeBasedNonce() external view returns (uint256);
    
    /**
     * @dev Check if a commitment exists
     * @param commitmentHash Hash of the commitment
     * @return Whether the commitment exists
     */
    function commitmentExists(bytes32 commitmentHash) external view returns (bool);
    
    /**
     * @dev Check if a commitment has been used
     * @param commitmentHash Hash of the commitment
     * @return Whether the commitment has been used
     */
    function isCommitmentUsed(bytes32 commitmentHash) external view returns (bool);
    
    /**
     * @dev Get the timestamp of a commitment
     * @param commitmentHash Hash of the commitment
     * @return Timestamp when the commitment was submitted
     */
    function getCommitmentTimestamp(bytes32 commitmentHash) external view returns (uint256);
} 