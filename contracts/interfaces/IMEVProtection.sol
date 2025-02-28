// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IMEVProtection
 * @dev Interface for the MEVProtection contract
 */
interface IMEVProtection {
    // Events
    event CommitmentSubmitted(bytes32 indexed commitmentHash, uint256 revealBlock);
    event CommitmentRevealed(bytes32 indexed commitmentHash, address indexed sender);
    event PrivateMempoolToggled(bool enabled);
    event FlashbotsRelayerUpdated(address indexed newRelayer);
    event BundleExecuted(bytes32 indexed bundleId, uint256 size);
    
    // Functions
    function submitCommitment(bytes32 commitmentHash) external;
    
    function revealAndExecute(
        bytes32 secret,
        bytes calldata transactionData
    ) external returns (bool);
    
    function setFlashbotsRelayer(address _newRelayer) external;
    
    function togglePrivateMempool(bool _enabled) external;
    
    function setCommitRevealDelay(uint256 _blocks) external;
    
    function executeBundle(
        address[] calldata targets,
        uint256[] calldata values,
        bytes[] calldata datas
    ) external returns (bool);
    
    function getTimeBasedNonce() external view returns (uint256);
    
    // View functions
    function commitRevealDelay() external view returns (uint256);
    function pendingCommitments(bytes32 commitmentHash) external view returns (bool);
    function commitmentTimestamps(bytes32 commitmentHash) external view returns (uint256);
    function usedCommitments(bytes32 commitmentHash) external view returns (bool);
    function flashbotsRelayer() external view returns (address);
    function usePrivateMempool() external view returns (bool);
    function minBundleSize() external view returns (uint256);
    function maxBundleSize() external view returns (uint256);
    function bundleNonces(bytes32 bundleId) external view returns (uint256);
} 