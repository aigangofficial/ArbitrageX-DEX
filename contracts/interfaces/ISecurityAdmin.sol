// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface ISecurityAdmin {
    function requestChange(bytes32 changeId) external;
    function cancelChange(bytes32 changeId) external;
    function pause() external;
    function unpause() external;
    function isTokenWhitelisted(address token) external view returns (bool);
    function whitelistToken(address token) external;
    function removeTokenFromWhitelist(address token) external;
    function executeParameterChange(string calldata parameter, uint256 newValue) external;
}
