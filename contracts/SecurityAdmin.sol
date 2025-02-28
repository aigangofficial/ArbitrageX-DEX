// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "./interfaces/ISecurityAdmin.sol";

/**
 * @title SecurityAdmin
 * @dev Provides security features for arbitrage contracts
 */
abstract contract SecurityAdmin is ISecurityAdmin, Ownable, ReentrancyGuard, Pausable {
    uint256 public constant TIMELOCK_DURATION = 24 hours;
    mapping(bytes32 => uint256) public pendingChanges;
    mapping(bytes32 => uint256) public pendingDelayedOperations;
    mapping(address => bool) public whitelistedTokens;

    event ChangeRequested(bytes32 indexed changeId, uint256 executionTime);
    event ChangeExecuted(bytes32 indexed changeId);
    event ChangeCancelled(bytes32 indexed changeId);
    event DelayedOperationScheduled(bytes32 indexed operationId, uint256 executionTime);
    event TokenWhitelisted(address indexed token);
    event TokenRemovedFromWhitelist(address indexed token);

    constructor() {
        _transferOwnership(msg.sender);
    }

    modifier timelocked(bytes32 changeId) {
        require(pendingChanges[changeId] != 0, "Change not requested");
        require(pendingChanges[changeId] <= block.timestamp, "Timelock not expired");
        delete pendingChanges[changeId];
        emit ChangeExecuted(changeId);
        _;
    }

    modifier onlyAfterDelay() {
        bytes32 operationId = keccak256(abi.encodePacked(msg.sig, msg.sender));
        require(pendingDelayedOperations[operationId] != 0, "Operation not scheduled");
        require(pendingDelayedOperations[operationId] <= block.timestamp, "Delay not expired");
        delete pendingDelayedOperations[operationId];
        _;
    }

    function scheduleDelayedOperation() external onlyOwner {
        bytes32 operationId = keccak256(abi.encodePacked(msg.sig, msg.sender));
        require(pendingDelayedOperations[operationId] == 0, "Operation already scheduled");
        pendingDelayedOperations[operationId] = block.timestamp + TIMELOCK_DURATION;
        emit DelayedOperationScheduled(operationId, pendingDelayedOperations[operationId]);
    }

    function requestChange(bytes32 changeId) external onlyOwner {
        require(pendingChanges[changeId] == 0, "Change already requested");
        pendingChanges[changeId] = block.timestamp + TIMELOCK_DURATION;
        emit ChangeRequested(changeId, pendingChanges[changeId]);
    }

    function cancelChange(bytes32 changeId) external onlyOwner {
        require(pendingChanges[changeId] != 0, "Change not requested");
        delete pendingChanges[changeId];
        emit ChangeCancelled(changeId);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function _executeParameterChange(string calldata parameter, uint256 newValue) internal virtual {
        revert("Not implemented");
    }

    /**
     * @dev Check if a token is whitelisted
     * @param token Address of the token to check
     */
    function isTokenWhitelisted(address token) external view returns (bool) {
        return whitelistedTokens[token];
    }

    /**
     * @dev Whitelist a token for trading
     * @param token Address of the token to whitelist
     */
    function whitelistToken(address token) external onlyOwner {
        require(token != address(0), "Invalid token address");
        require(!whitelistedTokens[token], "Token already whitelisted");
        whitelistedTokens[token] = true;
        emit TokenWhitelisted(token);
    }

    /**
     * @dev Remove a token from the whitelist
     * @param token Address of the token to remove
     */
    function removeTokenFromWhitelist(address token) external onlyOwner {
        require(whitelistedTokens[token], "Token not whitelisted");
        whitelistedTokens[token] = false;
        emit TokenRemovedFromWhitelist(token);
    }
}
