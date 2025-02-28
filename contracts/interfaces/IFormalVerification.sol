// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IFormalVerification
 * @dev Interface for formal verification contract
 */
interface IFormalVerification {
    /**
     * @dev Struct to store verification results
     */
    struct VerificationResult {
        bool verified;
        string details;
        address verifier;
        bool invariantsSatisfied;
        bool temporalPropertiesSatisfied;
        bool securityPropertiesSatisfied;
    }
    
    /**
     * @dev Add a new authorized verifier
     * @param verifier Address of the verifier to add
     */
    function addVerifier(address verifier) external;
    
    /**
     * @dev Remove an authorized verifier
     * @param verifier Address of the verifier to remove
     */
    function removeVerifier(address verifier) external;
    
    /**
     * @dev Request verification for a contract
     * @param contractAddress Address of the contract to verify
     */
    function requestVerification(address contractAddress) external;
    
    /**
     * @dev Verify a contract and record the results
     * @param contractAddress Address of the contract to verify
     * @param bytecode Bytecode of the contract
     * @param success Whether verification was successful
     * @param details Details of the verification result
     */
    function verifyContract(
        address contractAddress,
        bytes calldata bytecode,
        bool success,
        string calldata details
    ) external;
    
    /**
     * @dev Verify specific invariants for a contract
     * @param contractAddress Address of the contract to verify
     * @param invariantHashes Array of keccak256 hashes of invariant descriptions
     * @param results Array of boolean results for each invariant
     */
    function verifyInvariants(
        address contractAddress,
        bytes32[] calldata invariantHashes,
        bool[] calldata results
    ) external;
    
    /**
     * @dev Verify temporal properties for a contract
     * @param contractAddress Address of the contract to verify
     * @param propertyHashes Array of keccak256 hashes of temporal property descriptions
     * @param results Array of boolean results for each property
     */
    function verifyTemporalProperties(
        address contractAddress,
        bytes32[] calldata propertyHashes,
        bool[] calldata results
    ) external;
    
    /**
     * @dev Verify security properties for a contract
     * @param contractAddress Address of the contract to verify
     * @param propertyHashes Array of keccak256 hashes of security property descriptions
     * @param results Array of boolean results for each property
     */
    function verifySecurityProperties(
        address contractAddress,
        bytes32[] calldata propertyHashes,
        bool[] calldata results
    ) external;
    
    /**
     * @dev Check if a contract is verified
     * @param contractAddress Address of the contract to check
     * @return Whether the contract is verified
     */
    function isContractVerified(address contractAddress) external view returns (bool);
    
    /**
     * @dev Get detailed verification results for a contract
     * @param contractAddress Address of the contract to check
     * @return Detailed verification results
     */
    function getVerificationDetails(address contractAddress) external view returns (VerificationResult memory);
} 