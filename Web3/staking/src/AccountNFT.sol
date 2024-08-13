// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

import { ERC721, ERC721Enumerable } from "@openzeppelin/token/ERC721/extensions/ERC721Enumerable.sol";
import { Ownable } from "@openzeppelin/access/Ownable.sol";
import { SafeCast } from "@openzeppelin/utils/math/SafeCast.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {AccountNFT} from "./AccountNFT.sol";

contract AccountNFT is ERC721Enumerable, Ownable{

    mapping(address => uint256) userTokenPair;

    constructor(string memory name, string memory symbol, address owner) ERC721(name, symbol) Ownable(owner) { 
        transferOwnership(owner);
    }


    function mint(address to, uint256 tokenId) external {
        _mint(to, tokenId);
        userTokenPair[to] = tokenId;
    }
    
    function getStakingTokenId(address user) external returns (uint256){
        return userTokenPair[user];
    }
}