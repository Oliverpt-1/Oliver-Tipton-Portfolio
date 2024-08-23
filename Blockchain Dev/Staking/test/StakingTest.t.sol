// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import {Test, console} from "forge-std/Test.sol";
import {ERC20Mock} from "../src/Mock Tokens/ERC20Mock.sol";
import {AccountNFT} from "../src/AccountNFT.sol";
import {Staking} from "../src/Staking.sol";

contract StakingTest is Test {
    ERC20Mock stakingToken;
    ERC20Mock rewardToken;
    AccountNFT accountNFT;
    Staking staking;

    address owner = address(this);
    address oliver = address(0x123);

    function setUp() public {
        // Deploy mock tokens
        stakingToken = new ERC20Mock();
        rewardToken = new ERC20Mock();

        // Deploy AccountNFT
        accountNFT = new AccountNFT("Account NFT", "ANFT", owner);

        // Deploy staking contract
        staking = new Staking(address(stakingToken), address(rewardToken), address(accountNFT), owner);

        vm.startPrank(oliver);
        // Mint tokens to Oliver
        stakingToken.mint(1000 ether);
        
        // Approve staking contract to spend Oliver's tokens
        stakingToken.approve(address(staking), 1000 ether);
        
        vm.stopPrank();

        vm.startPrank(address(staking));
        rewardToken.mint(1000 ether);
        rewardToken.approve(address(staking), 1000 ether);
        stakingToken.approve(address(staking), 1000 ether);
        vm.stopPrank();

        // Log initial balances
        console.log("Oliver's initial staking token balance:", stakingToken.balanceOf(oliver));
        console.log("Oliver's initial reward token balance:", rewardToken.balanceOf(oliver));
    }


    // Invariant Tests

    function test_RewardCalculationAccuracy() public{
         uint256 initialTimeStamp = block.timestamp;

        vm.startPrank(oliver);
        staking.stake(1000 ether);
        vm.stopPrank();

        uint256 tokenID = accountNFT.getStakingTokenId(oliver);
        (uint256 stakeBalance, ) = staking.users(tokenID);

        // Fast forward 365 days
        vm.warp(initialTimeStamp + 365 days);

        uint256 oliverRewards = staking.getPendingRewards(tokenID);
        console.log("Oliver's Rewards:", oliverRewards);

        uint256 expectedReward = (1000 ether * 15) / 100; // 15% of 1000 ether
        uint256 rewardDifference = expectedReward > oliverRewards ? 
            expectedReward - oliverRewards : 
            oliverRewards - expectedReward;
        uint256 percentageDifference = (rewardDifference * 1e18) / expectedReward;


        uint256 maxAllowedDifference = 1e14; // 0.0001% expressed in 1e18 scale
        assert(percentageDifference < maxAllowedDifference);


        //The staking protocol is currently returning a 14.9999999999% interest rate as opposed to the desired 15%.  
        //This test case aims to show the accuracy closeness.
    }

    function test_RevertWhenOverWithdraw() public {
        uint256 initialTimeStamp = block.timestamp;

        vm.startPrank(oliver);
        staking.stake(1000 ether);
        vm.stopPrank();

        uint256 tokenID = accountNFT.getStakingTokenId(oliver);
        (uint256 stakeBalance, ) = staking.users(tokenID);
        
        vm.roll(block.number + 6307200);
        
        vm.expectRevert("Access Denied: Only Owner of account can withdraw");
        staking.withdrawUnderlying(oliver, 1001);
    }

    function test_ClaimMaxRewards() public{
        uint256 initialTimeStamp = block.timestamp;

        vm.startPrank(oliver);
        staking.stake(1000 ether);
        vm.stopPrank();

        uint256 tokenID = accountNFT.getStakingTokenId(oliver);
        (uint256 stakeBalance, ) = staking.users(tokenID);

        vm.warp(block.timestamp + 365 days);
        

        uint256 expectedRewards = staking.getPendingRewards(tokenID);
        vm.startPrank(oliver);
        staking.claimRewards(oliver);
        vm.stopPrank();

        assert(expectedRewards == rewardToken.balanceOf(oliver));
    }
    function test_withdrawUnderlying() public{
        uint256 initialTimeStamp = block.timestamp;
        uint256 initBalance = stakingToken.balanceOf(address(oliver));

        
        vm.startPrank(oliver);
        staking.stake(1000 ether);
        vm.stopPrank();

        uint256 tokenID = accountNFT.getStakingTokenId(oliver);
        (uint256 stakeBalance, ) = staking.users(tokenID);
        
        vm.roll(block.number + 6307200);
        
        vm.startPrank(oliver);
        staking.withdrawUnderlying(address(oliver), 1000 ether);
        vm.stopPrank();

        uint256 withdrawnBalance = stakingToken.balanceOf(address(oliver));

        assert(initBalance == withdrawnBalance);
    }
    



}