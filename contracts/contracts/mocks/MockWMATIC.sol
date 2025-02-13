// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockWMATIC is ERC20 {
    constructor() ERC20("Wrapped MATIC", "WMATIC") {
        _mint(msg.sender, 1000000 * 10 ** 18); // Mint 1M tokens
    }

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}
