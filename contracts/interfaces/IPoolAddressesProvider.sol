// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IPoolAddressesProvider {
    function getPool() external view returns (address);
    function getPoolDataProvider() external view returns (address);
    function getAddress(bytes32 id) external view returns (address);
    function setAddress(bytes32 id, address newAddress) external;
    function getMarketId() external view returns (string memory);
}
