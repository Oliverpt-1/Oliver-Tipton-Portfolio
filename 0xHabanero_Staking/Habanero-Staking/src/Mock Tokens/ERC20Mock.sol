// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract ERC20Mock{
    uint constant _initial_supply = 100 * (10**18);
    //100 is arbitrary but whatever I want supply to be.  This could be important
    //for making sure numbers / rewards calculation is accurate... good math opportunity

    constructor() ERC20("StakeToken", "ST") public {
        _mint(msg.sender, _initial_supply);
    }

}