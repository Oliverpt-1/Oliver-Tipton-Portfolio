// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;

//imports

import {ERC20Mock} from "./Mock Tokens/ERC20Mock.sol";
import {AccountNFT} from "./AccountNFT.sol";
import {Test, console} from "forge-std/Test.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {IERC20, SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";


/**
 * @title Staking Protocol
 * @author Oliver Tipton
 * @notice A sophisticated staking platform for ERC20 tokens with NFT-based account management
 * @dev Implements advanced staking mechanics with built-in security features
 *
 * ░██████╗████████╗░█████╗░██╗░░██╗██╗███╗░░██╗░██████╗░
 * ██╔════╝╚══██╔══╝██╔══██╗██║░██╔╝██║████╗░██║██╔════╝░
 * ╚█████╗░░░░██║░░░███████║█████═╝░██║██╔██╗██║██║░░██╗░
 * ░╚═══██╗░░░██║░░░██╔══██║██╔═██╗░██║██║╚████║██║░░╚██╗
 * ██████╔╝░░░██║░░░██║░░██║██║░╚██╗██║██║░╚███║╚██████╔╝
 * ╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝╚═╝░░╚══╝░╚═════╝░
 *
 * ┌─────────────────────────────────────────────────────────────────────────┐
 * │ This contract combines:                                                  │
 * │ • ERC20 token staking                                                    │
 * │ • NFT-based account representation                                       │
 * │ • Dynamic reward calculation                                             │
 * │ • Robust security measures                                               │
 * └─────────────────────────────────────────────────────────────────────────┘
 *
 * Key Features:
 * ✓ Create unique staking accounts represented by NFTs
 * ✓ Stake and withdraw ERC20 tokens seamlessly
 * ✓ Earn rewards based on staking duration and amount
 * ✓ Claim rewards at any time
 * ✓ Built-in protection against common vulnerabilities
 *
 * Technical Highlights:
 * • Leverages OpenZeppelin's security contracts
 * • Utilizes SafeERC20 for foolproof token transfers
 * • Precision-focused calculations to ensure accuracy
 */
contract Staking is Ownable, ReentrancyGuard{
    using SafeERC20 for ERC20Mock;

    //Events
    event AccountCreated(address user, uint256 tokenId);
    event Staked(address user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);


    //State Variables

    ERC20Mock public immutable stakingToken; 
    ERC20Mock public immutable rewardToken;
    AccountNFT public immutable accountNFT;

    uint256 public rewardRate;
    uint256 private nextTokenId = 1;

    //Constants

    uint256 public constant ANNUAL_INTEREST_RATE = 15;
    uint256 public constant PRECISION = 1e18;
    uint256 public constant SECONDS_PER_YEAR = 365 * 86400;

    struct accountBalance{
        uint256 stakeBalance;
        uint256 lastRewardTime;
    }

    mapping(uint256 tokenId => accountBalance) public users;
    mapping(address user => bool ) public existingAccount;

    /**
     * @notice Contract constructor
     * @param _stakingToken Address of the ERC20 token used for staking
     * @param _rewardToken Address of the ERC20 token used for rewards
     * @param _accountNFT Address of the NFT contract used for account representation
     * @param _owner Address of the contract owner
     */
    constructor(address _stakingToken,
        address _rewardToken,
        address _accountNFT,
        address _owner) Ownable(_owner){

        stakingToken = ERC20Mock(_stakingToken);
        rewardToken = ERC20Mock(_rewardToken);
        accountNFT = AccountNFT(_accountNFT);
    
        rewardRate = (ANNUAL_INTEREST_RATE * PRECISION) / (100 * SECONDS_PER_YEAR);
    }

    /**
     * @notice Creates a new staking account for a user
     * @dev Mints a new NFT to represent the user's account
     * @param user Address of the user creating the account
     * @return tokenId The ID of the newly minted NFT
     */
    function createStakerAccount(address user) public nonReentrant returns (uint256 tokenId) {
        require(msg.sender == user, "Can't create accounts for other users");
        require(!existingAccount[user], "Can't create multiple accounts");

        accountNFT.mint(user, nextTokenId);
        uint256 tokenId = nextTokenId;
        users[tokenId].lastRewardTime = block.timestamp;
        nextTokenId++;
        emit AccountCreated(user, tokenId);

        return tokenId;
    }


   /**
     * @notice Allows a user to stake tokens
     * @dev Creates a new account if the user doesn't have one
     * @param amount The amount of tokens to stake
     */
    function stake(uint256 amount) external{
        address user = msg.sender;
        uint256 userTokenId;


        if (existingAccount[msg.sender]){
            userTokenId = accountNFT.getStakingTokenId(user);
            accountBalance storage userAccount = users[userTokenId];

            uint256 pendingRewards = getPendingRewards(userTokenId);
            if(pendingRewards > 0){
                rewardToken.safeTransfer(user, pendingRewards);
                emit RewardPaid(user, pendingRewards);
            }
            
            userAccount.stakeBalance += amount;
            userAccount.lastRewardTime = block.timestamp;
        }

        else{
            userTokenId = createStakerAccount(user);
            existingAccount[msg.sender] = true;
            users[userTokenId].stakeBalance = amount;
        }

        stakingToken.safeTransferFrom(user, address(this), amount);
        emit Staked(user, amount);
    }

    /**
     * @notice Allows a user to withdraw staked tokens
     * @dev Transfers staked tokens and any accrued rewards to the user
     * @param user Address of the user withdrawing tokens
     * @param amount Amount of tokens to withdraw
     */
    function withdrawUnderlying(address user, uint256 amount) external nonReentrant{
        require(user == msg.sender, "Access Denied: Only Owner of account can withdraw");
        require(amount > 0, "Can't withdraw 0");
        
        uint256 tokenId = accountNFT.getStakingTokenId(user);

        require(existingAccount[user], "Can only withdraw from existing account");
        require(users[tokenId].stakeBalance >= amount, "You may not unstake more than you have in your account");


        accountBalance storage userAccount = users[accountNFT.getStakingTokenId(user)];


        if(amount == userAccount.stakeBalance){
            userAccount.stakeBalance = 0;
            uint256 userRewards = getPendingRewards(tokenId);

            stakingToken.safeTransfer(user, amount);
            rewardToken.safeTransfer(user, userRewards);
            
        }
        else{
            userAccount.stakeBalance -= amount;
            
            uint256 pendingRewards = getPendingRewards(tokenId);

            if(pendingRewards > 0){
                rewardToken.safeTransfer(user, pendingRewards);
            }
            stakingToken.safeTransfer(user, amount);
        }
        userAccount.lastRewardTime = block.timestamp;
        emit Withdrawn(user, amount);
    }

    /**
     * @notice Allows a user to claim accrued rewards
     * @dev Transfers accrued rewards to the user and updates the last reward time
     * @param user Address of the user claiming rewards
     */
    function claimRewards(address user) external nonReentrant{
        require(user == msg.sender, "Access Denied: User must own account to claim rewards");
        require(existingAccount[user] != false, "Uninitialized Account");

        //get user token Id and account
        uint256 tokenId = accountNFT.getStakingTokenId(user);
        accountBalance storage userAccount = users[tokenId];
        
        //get user Rewards and update last reward claim
        uint256 userRewards = getPendingRewards(tokenId);
        userAccount.lastRewardTime = block.timestamp;


        rewardToken.safeTransfer(user, userRewards);
        emit RewardPaid(user, userRewards);
    }

    /**
     * @notice Calculates the pending rewards for a given account
     * @dev Uses the reward rate and staking duration to calculate rewards
     * @param tokenId The NFT token ID representing the user's account
     * @return The amount of pending rewards
     */
    function getPendingRewards(uint256 tokenId) public view returns (uint256) {
        accountBalance storage user = users[tokenId];

        
        uint256 timeElapsed = block.timestamp - user.lastRewardTime;
        uint256 rewardsPerToken = (timeElapsed * rewardRate * user.stakeBalance) / PRECISION;
        return rewardsPerToken;
    }
}