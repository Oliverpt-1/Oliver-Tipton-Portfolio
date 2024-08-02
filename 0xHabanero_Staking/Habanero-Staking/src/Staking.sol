// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

//imports

import {ERC20Mock} from "./Mock Tokens/ERC20Mock.sol";
import {ERC721Mock} from "./Mock Tokens/ERC721Mock.sol";
import {Ownable} from ;


//needs to inherit
// from stakingUtils

contract Staking is Ownable, ReentrancyGuard{
    

    //need events here

    //initalize variables
    //Staking Tokens: Eth, USDT, USDC, DAI (this good?)
    ERC20Mock public immutable stakingToken; 
    ERC721Mock public immutable userNFT;
    
    uint256 immutable private nextTokenId;
    uint256 public rewardFactor;

    constructor(address owner) Ownable(owner){

    }


    /**
    * user - 
    * amount - 
    */

    function stake(address user, uint256 amount) external nonReentrant{
        if (positions[user].balance > 0){
            require(user = msg.sender, "This is not your account");
            userPosition[user] += amount;
            updateUserRewards(user);
        }

        else{
            userPosition[user].amount = amount;
            _mint(user, nextTokenId);
            nextTokenId++;
        }

        stakingToken.safeTransferFrom(user, address(this), amount);
        emit Staked(user, amount)
    }

    function withdrawUnderlying(address user, uint256 amount) external nonReentrant{
        require(user == msg.sender, "No Bitch");
        require(amount == 0, "Must Initialize")
        require(amount <= user.amount, "No your poor");


        if(amount == user.amount){
            user.amount = 0;
            user.rewards = 0;
            stakingToken.safeTransferFrom(address(this), user, amount);
            rewardToken.safeTransferFrom(address(this), amount);
        }
        else{
            user.amount -= amount;
            //need to do something about reward calculations here
            //If the amount is changing, their rewards will be less
            //Maybe like rebalance rewards calculation function or something like that
                //how do I do this?
                //Maybe user.cachedRewards.... so everytime the amount in the vault changes, recalculate cached rewards
            stakingToken.safeTransferFrom(address(this), user, amount);
        }

    }

    function withdrawRewards(address user, uint256 amount, bool maxRewardClaim)external nonReentrant{
        require(user == msg.sender, "No bitch");

        if maxRewardClaim{
            user.rewards = 0;
            rewardToken.safeTransferFrom(address(this), amount);


        }
        else if (amount > userPosition[user].rewardsAvailable){
            revert("InsufficentRewards");
        }
        else{
            //transfer user the rewards
            //
        }

        //updatePool
    }


    function updateUserRewards(address user) internal {
        uint256 timeStaked = block.timestamp - user.startTime;
        user.rewards = user.position * timeStaked;
        //safemath?
    }
}