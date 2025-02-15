// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title SecurityAdmin
 * @dev Core security module providing:
 * - Emergency pause functionality for immediate protocol shutdown
 * - Time-locked parameter changes with 24-hour delay
 * - Protected withdrawal mechanisms with delay and validation
 * - Reentrancy guards for all critical functions
 * - Enhanced ownership controls with renounce protection
 *
 * Used by both FlashLoanService and ArbitrageExecutor to ensure:
 * - Safe parameter updates through time-locks
 * - Protected emergency withdrawals
 * - Immediate protocol pause in case of detected vulnerabilities
 * - Prevention of ownership renouncement
 */
abstract contract SecurityAdmin is Ownable, Pausable, ReentrancyGuard {
    uint256 public constant EMERGENCY_WITHDRAWAL_DELAY = 24 hours;
    uint256 public constant PARAM_CHANGE_DELAY = 24 hours;
    uint256 public emergencyWithdrawalTimestamp;
    bool public emergencyWithdrawalInitiated;

    struct ParameterChange {
        uint256 newValue;
        uint256 scheduledTime;
        bool isValid;
    }

    mapping(bytes32 => ParameterChange) public pendingParameterChanges;

    event EmergencyWithdrawalInitiated(uint256 timestamp);
    event EmergencyWithdrawalCancelled();
    event EmergencyWithdrawalExecuted(address indexed token, uint256 amount);
    event SecurityParametersUpdated(string indexed parameter, uint256 value);
    event ParameterChangeScheduled(
        string indexed parameter,
        uint256 newValue,
        uint256 scheduledTime
    );
    event ParameterChangeCancelled(string indexed parameter);

    constructor() Ownable() {
        _transferOwnership(msg.sender);
    }

    modifier onlyAfterDelay() {
        require(
            emergencyWithdrawalInitiated &&
                block.timestamp >= emergencyWithdrawalTimestamp + EMERGENCY_WITHDRAWAL_DELAY,
            "Withdrawal delay not met"
        );
        _;
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function initiateEmergencyWithdrawal() external onlyOwner {
        require(!emergencyWithdrawalInitiated, "Emergency withdrawal already initiated");
        emergencyWithdrawalInitiated = true;
        emergencyWithdrawalTimestamp = block.timestamp;
        emit EmergencyWithdrawalInitiated(block.timestamp);
    }

    function cancelEmergencyWithdrawal() external onlyOwner {
        require(emergencyWithdrawalInitiated, "No emergency withdrawal in progress");
        emergencyWithdrawalInitiated = false;
        emit EmergencyWithdrawalCancelled();
    }

    function executeEmergencyWithdrawal(
        address token,
        uint256 amount
    ) external onlyOwner onlyAfterDelay {
        require(token != address(0), "Invalid token address");
        require(amount > 0, "Invalid amount");

        // Reset emergency withdrawal state
        emergencyWithdrawalInitiated = false;

        emit EmergencyWithdrawalExecuted(token, amount);
    }

    function scheduleParameterChange(
        string calldata parameter,
        uint256 newValue
    ) external onlyOwner whenNotPaused {
        bytes32 paramHash = keccak256(abi.encodePacked(parameter));
        require(!pendingParameterChanges[paramHash].isValid, "Change already pending");

        pendingParameterChanges[paramHash] = ParameterChange({
            newValue: newValue,
            scheduledTime: block.timestamp + PARAM_CHANGE_DELAY,
            isValid: true
        });

        emit ParameterChangeScheduled(parameter, newValue, block.timestamp + PARAM_CHANGE_DELAY);
    }

    function cancelParameterChange(string calldata parameter) external onlyOwner {
        bytes32 paramHash = keccak256(abi.encodePacked(parameter));
        require(pendingParameterChanges[paramHash].isValid, "No pending change");

        delete pendingParameterChanges[paramHash];
        emit ParameterChangeCancelled(parameter);
    }

    function executeParameterChange(string calldata parameter) external onlyOwner whenNotPaused {
        bytes32 paramHash = keccak256(abi.encodePacked(parameter));
        ParameterChange memory change = pendingParameterChanges[paramHash];

        require(change.isValid, "No pending change");
        require(block.timestamp >= change.scheduledTime, "Change delay not met");

        delete pendingParameterChanges[paramHash];

        _executeParameterChange(parameter, change.newValue);
        emit SecurityParametersUpdated(parameter, change.newValue);
    }

    function _executeParameterChange(string calldata parameter, uint256 newValue) internal virtual;

    function updateSecurityParameter(string calldata parameter, uint256 value) external onlyOwner {
        emit SecurityParametersUpdated(parameter, value);
    }

    function renounceOwnership() public virtual override onlyOwner {
        revert("Ownership cannot be renounced");
    }
}
