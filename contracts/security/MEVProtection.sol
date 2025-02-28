// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title MEVProtection
 * @dev Implements protection mechanisms against MEV (Miner Extractable Value) attacks
 * including front-running, sandwich attacks, and other transaction ordering exploits
 */
contract MEVProtection is Ownable, ReentrancyGuard {
    // Commit-reveal scheme parameters
    uint256 public commitRevealDelay = 1; // blocks
    mapping(bytes32 => bool) public pendingCommitments;
    mapping(bytes32 => uint256) public commitmentTimestamps;
    mapping(bytes32 => bool) public usedCommitments;
    
    // Private mempool integration
    address public flashbotsRelayer;
    bool public usePrivateMempool = true;
    
    // Transaction bundling parameters
    uint256 public minBundleSize = 1;
    uint256 public maxBundleSize = 10;
    mapping(bytes32 => uint256) public bundleNonces;
    
    // Events
    event CommitmentSubmitted(bytes32 indexed commitmentHash, uint256 revealBlock);
    event CommitmentRevealed(bytes32 indexed commitmentHash, address indexed sender);
    event PrivateMempoolToggled(bool enabled);
    event FlashbotsRelayerUpdated(address indexed newRelayer);
    event BundleExecuted(bytes32 indexed bundleId, uint256 size);
    
    // Custom errors
    error InvalidCommitment();
    error CommitmentAlreadyUsed();
    error CommitmentNotReady();
    error InvalidRelayer();
    error UnauthorizedRelayer();
    error InvalidBundleSize();
    error BundleExecutionFailed();
    
    constructor(address _flashbotsRelayer) {
        if (_flashbotsRelayer != address(0)) {
            flashbotsRelayer = _flashbotsRelayer;
        }
    }
    
    /**
     * @dev Submit a commitment hash for a future transaction to prevent front-running
     * @param commitmentHash Hash of the transaction parameters and a secret
     */
    function submitCommitment(bytes32 commitmentHash) external {
        if (pendingCommitments[commitmentHash]) revert InvalidCommitment();
        if (usedCommitments[commitmentHash]) revert CommitmentAlreadyUsed();
        
        pendingCommitments[commitmentHash] = true;
        commitmentTimestamps[commitmentHash] = block.number;
        
        emit CommitmentSubmitted(commitmentHash, block.number + commitRevealDelay);
    }
    
    /**
     * @dev Reveal and execute a previously committed transaction
     * @param secret The secret used in the commitment
     * @param transactionData The original transaction data
     */
    function revealAndExecute(
        bytes32 secret,
        bytes calldata transactionData
    ) external nonReentrant returns (bool) {
        bytes32 commitmentHash = keccak256(abi.encodePacked(secret, transactionData, msg.sender));
        
        if (!pendingCommitments[commitmentHash]) revert InvalidCommitment();
        if (block.number < commitmentTimestamps[commitmentHash] + commitRevealDelay) revert CommitmentNotReady();
        
        // Mark commitment as used
        pendingCommitments[commitmentHash] = false;
        usedCommitments[commitmentHash] = true;
        
        emit CommitmentRevealed(commitmentHash, msg.sender);
        
        // Execute the transaction
        (bool success, ) = address(this).call(transactionData);
        return success;
    }
    
    /**
     * @dev Verify if a transaction is coming from the authorized Flashbots relayer
     */
    modifier onlyFlashbotsRelayer() {
        if (usePrivateMempool && msg.sender != flashbotsRelayer) revert UnauthorizedRelayer();
        _;
    }
    
    /**
     * @dev Update the Flashbots relayer address
     * @param _newRelayer New relayer address
     */
    function setFlashbotsRelayer(address _newRelayer) external onlyOwner {
        if (_newRelayer == address(0)) revert InvalidRelayer();
        flashbotsRelayer = _newRelayer;
        emit FlashbotsRelayerUpdated(_newRelayer);
    }
    
    /**
     * @dev Toggle the use of private mempool
     * @param _enabled Whether to use private mempool
     */
    function togglePrivateMempool(bool _enabled) external onlyOwner {
        usePrivateMempool = _enabled;
        emit PrivateMempoolToggled(_enabled);
    }
    
    /**
     * @dev Set the commit-reveal delay in blocks
     * @param _blocks Number of blocks to wait
     */
    function setCommitRevealDelay(uint256 _blocks) external onlyOwner {
        commitRevealDelay = _blocks;
    }
    
    /**
     * @dev Execute a bundle of transactions atomically to prevent sandwich attacks
     * @param targets Array of target addresses
     * @param values Array of ETH values to send
     * @param datas Array of transaction data
     */
    function executeBundle(
        address[] calldata targets,
        uint256[] calldata values,
        bytes[] calldata datas
    ) external onlyFlashbotsRelayer nonReentrant returns (bool) {
        uint256 bundleSize = targets.length;
        
        if (bundleSize < minBundleSize || bundleSize > maxBundleSize) revert InvalidBundleSize();
        if (bundleSize != values.length || bundleSize != datas.length) revert InvalidBundleSize();
        
        bytes32 bundleId = keccak256(abi.encode(targets, values, block.number));
        bundleNonces[bundleId] = block.number;
        
        bool allSuccess = true;
        for (uint256 i = 0; i < bundleSize; i++) {
            (bool success, ) = targets[i].call{value: values[i]}(datas[i]);
            allSuccess = allSuccess && success;
        }
        
        if (!allSuccess) revert BundleExecutionFailed();
        
        emit BundleExecuted(bundleId, bundleSize);
        return true;
    }
    
    /**
     * @dev Calculate a time-based nonce to prevent transaction reordering
     */
    function getTimeBasedNonce() public view returns (uint256) {
        return block.timestamp * 1000 + block.number;
    }
} 