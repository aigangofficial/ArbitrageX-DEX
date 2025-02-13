// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockUSDT is ERC20 {
    constructor() ERC20("Tether USD", "USDT") {
        _mint(msg.sender, 1000000 * 10 ** 6); // Mint 1M tokens with 6 decimals
    }

    function decimals() public pure override returns (uint8) {
        return 6; // USDT uses 6 decimals
    }

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}
