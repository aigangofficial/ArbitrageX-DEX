// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@aave/core-v3/contracts/interfaces/IPool.sol";
import "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import "../interfaces/IFlashLoanService.sol";
import "../interfaces/IFlashLoanReceiver.sol";
import "../interfaces/IArbitrageExecutor.sol";
import "../SecurityAdmin.sol";

error InvalidPath();
error InsufficientFundsForRepayment();
error InvalidTokenAddresses();
error InvalidAmount();
error InvalidMinProfit();
error UnprofitableTrade();
error TransferFailed();
error InvalidFlashLoanProvider();
error InvalidArbitrageExecutor();
error InvalidTokenApproval();
error InvalidFlashLoanAmount();
error FlashLoanFailed();
error InvalidParameter();

contract FlashLoanService is
    IFlashLoanService,
    IFlashLoanReceiver,
    Ownable,
    ReentrancyGuard,
    SecurityAdmin
{
    uint256 private constant BPS = 10000;

    IPool public immutable pool;
    IArbitrageExecutor public arbitrageExecutor;
    uint16 public minProfitBps = 1;
    mapping(address => bool) public flashLoanProviders;
    uint256 public constant FLASH_LOAN_FEE = 9;
    uint256 public minFlashLoanAmount;
    uint256 public maxFlashLoanAmount;

    event FlashLoanExecuted(
        address indexed token,
        uint256 amount,
        address indexed borrower,
        uint256 fee
    );
    event MinProfitBpsUpdated(uint16 oldValue, uint16 newValue);
    event FlashLoanProviderAdded(address indexed provider);
    event FlashLoanProviderRemoved(address indexed provider);
    event ArbitrageExecutorUpdated(address indexed oldExecutor, address indexed newExecutor);
    event TokenApprovalUpdated(address indexed token, address indexed spender, uint256 amount);

    constructor(address _pool) SecurityAdmin() {
        if (_pool == address(0)) revert InvalidPath();
        pool = IPool(_pool);
        flashLoanProviders[msg.sender] = true;
        emit FlashLoanProviderAdded(msg.sender);
    }

    function executeArbitrage(
        address tokenA,
        address tokenB,
        uint256 amount,
        bytes calldata params
    ) external override nonReentrant whenNotPaused {
        if (tokenA == address(0) || tokenB == address(0)) revert InvalidTokenAddresses();
        if (amount == 0) revert InvalidAmount();
        if (address(arbitrageExecutor) == address(0)) revert InvalidArbitrageExecutor();

        bytes memory flashLoanParams = abi.encode(params, tokenB);

        address[] memory assets = new address[](1);
        assets[0] = tokenA;
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = amount;
        uint256[] memory modes = new uint256[](1);
        modes[0] = 0;

        try
            pool.flashLoan(address(this), assets, amounts, modes, address(this), flashLoanParams, 0)
        {
            emit FlashLoanExecuted(tokenA, amount, msg.sender, FLASH_LOAN_FEE);
        } catch Error(string memory reason) {
            revert(bytes(reason).length > 0 ? reason : "UnprofitableTrade");
        } catch {
            revert UnprofitableTrade();
        }
    }

    function executeOperation(
        address token,
        uint256 amount,
        uint256 fee,
        address initiator,
        bytes calldata params
    ) external override(IFlashLoanReceiver, IFlashLoanService) returns (bool) {
        if (!flashLoanProviders[msg.sender]) revert InvalidFlashLoanProvider();

        // Decode the params to get tokenB and arbitrage parameters
        (bytes memory arbitrageParams, address tokenB) = abi.decode(params, (bytes, address));

        // Approve arbitrage executor to spend tokens
        bool success = IERC20(token).approve(address(arbitrageExecutor), amount);
        if (!success) revert InvalidTokenApproval();

        // Execute the arbitrage
        try
            arbitrageExecutor.executeArbitrage(
                token,
                tokenB,
                amount,
                abi.decode(arbitrageParams, (bool))
            )
        returns (uint256 finalBalance) {
            // Verify we have enough to repay the flash loan
            uint256 amountToRepay = amount + fee;
            if (finalBalance < amountToRepay) revert InsufficientFundsForRepayment();

            // Approve the pool to take the repayment
            success = IERC20(token).approve(msg.sender, amountToRepay);
            if (!success) revert InvalidTokenApproval();

            return true;
        } catch Error(string memory reason) {
            revert(bytes(reason).length > 0 ? reason : "UnprofitableTrade");
        } catch {
            revert UnprofitableTrade();
        }
    }

    function setMinProfitBps(uint16 _minProfitBps) external onlyOwner {
        if (_minProfitBps == 0) revert InvalidMinProfit();
        uint16 oldValue = minProfitBps;
        minProfitBps = _minProfitBps;
        emit MinProfitBpsUpdated(oldValue, _minProfitBps);
    }

    function setArbitrageExecutor(address _arbitrageExecutor) external onlyOwner {
        if (_arbitrageExecutor == address(0)) revert InvalidArbitrageExecutor();
        address oldExecutor = address(arbitrageExecutor);
        arbitrageExecutor = IArbitrageExecutor(_arbitrageExecutor);
        emit ArbitrageExecutorUpdated(oldExecutor, _arbitrageExecutor);
    }

    function approveTokens(
        address[] calldata tokens,
        address[] calldata spenders
    ) external onlyOwner {
        if (tokens.length != spenders.length) revert InvalidTokenApproval();
        for (uint i = 0; i < tokens.length; i++) {
            if (tokens[i] == address(0) || spenders[i] == address(0)) revert InvalidTokenApproval();
            bool success = IERC20(tokens[i]).approve(spenders[i], type(uint256).max);
            if (!success) revert InvalidTokenApproval();
            emit TokenApprovalUpdated(tokens[i], spenders[i], type(uint256).max);
        }
    }

    function withdrawToken(address token, uint256 amount) external onlyOwner {
        if (token == address(0)) revert InvalidTokenAddresses();
        if (amount == 0) revert InvalidAmount();
        bool success = IERC20(token).transfer(owner(), amount);
        if (!success) revert TransferFailed();
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

    function renounceOwnership() public virtual override(Ownable, SecurityAdmin) onlyOwner {
        revert("Ownership cannot be renounced");
    }

    function _executeParameterChange(
        string calldata parameter,
        uint256 newValue
    ) internal override {
        bytes32 paramHash = keccak256(abi.encodePacked(parameter));

        if (paramHash == keccak256(abi.encodePacked("minFlashLoanAmount"))) {
            require(newValue > 0, "Invalid minimum amount");
            minFlashLoanAmount = newValue;
        } else if (paramHash == keccak256(abi.encodePacked("maxFlashLoanAmount"))) {
            require(newValue > minFlashLoanAmount, "Invalid maximum amount");
            maxFlashLoanAmount = newValue;
        } else {
            revert InvalidParameter();
        }
    }
}
