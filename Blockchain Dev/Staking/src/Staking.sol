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

/**
 * @title Staking Protocol
 * @author Oliver Tipton
 * @notice A staking platform for ERC20 tokens with NFT-based account management
 * @dev Implements advanced staking mechanics with built-in security features
 *
 * This contract allows users to stake ERC20 tokens, represented by unique NFTs,
 * and earn rewards based on their staking amount and duration. It includes
 * features for creating accounts, staking, withdrawing, and claiming rewards.
 */
 
contract Staking is Ownable, ReentrancyGuard {
    using SafeERC20 for ERC20Mock;

    // Events
    event AccountCreated(address user, uint256 tokenId);
    event Staked(address user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);

    // State Variables
    ERC20Mock public immutable stakingToken;
    ERC20Mock public immutable rewardToken;
    AccountNFT public immutable accountNFT;

    uint256 private nextTokenId = 1;
    uint256 public stakingEndTime;
    uint256 public rewardPool;
    uint256 public totalStaked;
    uint256 public lastUpdateTime;
    uint256 public stakingStartTime;

    // Constants
    uint256 public constant PRECISION = 1e18;

    struct AccountBalance {
        uint256 stakeBalance;
        uint256 lastRewardTime;
        uint256 stakedAt;
    }

    mapping(uint256 tokenId => AccountBalance) public users;

    /**
     * @notice Contract constructor
     * @param _stakingToken Address of the ERC20 token used for staking
     * @param _rewardToken Address of the ERC20 token used for rewards
     * @param _accountNFT Address of the NFT contract used for account representation
     * @param _owner Address of the contract owner
     */
    constructor(address _stakingToken, address _rewardToken, address _accountNFT, address _owner)
        Ownable(_owner)
    {
        stakingToken = ERC20Mock(_stakingToken);
        rewardToken = ERC20Mock(_rewardToken);
        accountNFT = AccountNFT(_accountNFT);
    }

    /**
     * @notice Creates a new staking account for a user
     * @dev Mints a new NFT to represent the user's account
     * @return tokenId The ID of the newly minted NFT
     */
    function createStakerAccount() public returns (uint256 tokenId) {
        require(accountNFT.getStakingTokenId(msg.sender) == 0, "Can't create multiple accounts");

        accountNFT.mint(msg.sender, nextTokenId);
        tokenId = nextTokenId;
        nextTokenId++;

        emit AccountCreated(msg.sender, tokenId);
    }

    /**
     * @notice Allows a user to stake tokens
     * @dev Creates a new account if the user doesn't have one
     * @param amount The amount of tokens to stake
     */
    function stake(uint256 amount) external nonReentrant {
        uint256 userTokenId = accountNFT.getStakingTokenId(msg.sender);

        require(userTokenId != 0, "User must have account to stake");
        require(block.timestamp < stakingEndTime, "Staking period has ended");

        AccountBalance storage userAccount = users[userTokenId];
        uint256 pendingRewards = getPendingRewards(userTokenId);

        if (pendingRewards > 0) {
            rewardToken.safeTransfer(msg.sender, pendingRewards);
            emit RewardPaid(msg.sender, pendingRewards);
        }

        userAccount.stakeBalance += amount;
        totalStaked += amount;
        userAccount.lastRewardTime = block.timestamp;
        userAccount.stakedAt = block.timestamp;

        stakingToken.safeTransferFrom(msg.sender, address(this), amount);
        emit Staked(msg.sender, amount);
    }

    /**
     * @notice Allows a user to withdraw staked tokens
     * @dev Transfers staked tokens and any accrued rewards to the user
     * @param tokenId The NFT token ID representing the user's account
     * @param amount Amount of tokens to withdraw
     */
    function withdrawUnderlying(uint256 tokenId, uint256 amount) external nonReentrant {
        require(amount > 0, "Can't withdraw 0");
        require(msg.sender == accountNFT.ownerOf(tokenId), "Can't withdraw from someone else's account");
        require(users[tokenId].stakeBalance >= amount, "You may not unstake more than you have in your account");

        AccountBalance storage userAccount = users[tokenId];
        uint256 userRewards = getPendingRewards(tokenId);

        userAccount.stakeBalance -= amount;
        totalStaked -= amount;

        if (userRewards > 0) {
            rewardToken.safeTransfer(msg.sender, userRewards);
        }

        userAccount.lastRewardTime = block.timestamp;
        stakingToken.safeTransfer(msg.sender, amount);

        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @notice Allows a user to emergency withdraw while forfeiting available rewards
     * @dev Transfers staked tokens to the user and updates the last reward time
     * @param tokenId The NFT token ID representing the user's account
     */
    function emergencyWithdraw(uint256 tokenId) external nonReentrant {
        require(msg.sender == accountNFT.ownerOf(tokenId), "Not owner");

        AccountBalance storage userAccount = users[tokenId];
        uint256 amount = userAccount.stakeBalance;
        userAccount.stakeBalance = 0;
        totalStaked -= amount;
        stakingToken.safeTransfer(msg.sender, amount);
        userAccount.lastRewardTime = block.timestamp;

        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @notice Allows a user to claim accrued rewards
     * @dev Transfers accrued rewards to the user and updates the last reward time
     * @param tokenId The NFT token ID representing the user's account
     */
    function claimRewards(uint256 tokenId) external nonReentrant {
        require(msg.sender == accountNFT.ownerOf(tokenId), "Not owner");

        AccountBalance storage userAccount = users[tokenId];

        uint256 userRewards = getPendingRewards(tokenId);
        require(userRewards > 0, "No rewards to claim");

        userAccount.lastRewardTime = block.timestamp;

        rewardToken.safeTransfer(msg.sender, userRewards);
        emit RewardPaid(msg.sender, userRewards);
    }


    //VIEW FUNCTIONS


    /**
     * @notice Calculates the pending rewards for a given account
     * @dev Uses the reward rate and staking duration to calculate rewards
     * @param tokenId The NFT token ID representing the user's account
     * @return The amount of pending rewards
     */
    function getPendingRewards(uint256 tokenId) public view returns (uint256) {
        AccountBalance storage user = users[tokenId];
        if (totalStaked == 0) return 0;

        uint256 userStakingDuration = block.timestamp - user.lastRewardTime;
        uint256 totalUserRewards = (getRewardRate(tokenId) * userStakingDuration) / PRECISION;

        return totalUserRewards;
    }

    /**
     * @notice Calculates the reward rate based on user amount staked and start time
     * @dev Takes into account the user's stake amount and duration
     * @param tokenId The NFT token ID representing the user's account
     * @return The calculated reward rate for the user
     */
    function getRewardRate(uint256 tokenId) public view returns (uint256) {
        AccountBalance storage user = users[tokenId];

        uint256 totalStakingDuration = stakingEndTime - stakingStartTime;
        if (totalStakingDuration == 0 || totalStaked == 0) {
            return 0;
        }

        uint256 userStakingDuration = block.timestamp - user.stakedAt;
        if (userStakingDuration > totalStakingDuration) {
            userStakingDuration = totalStakingDuration;
        }

        uint256 userShareOfStake = (user.stakeBalance * PRECISION) / totalStaked;
        uint256 userShareOfDuration = (userStakingDuration * PRECISION) / totalStakingDuration;
        uint256 rewardRate = (rewardPool * userShareOfStake * userShareOfDuration) / (totalStakingDuration * PRECISION * PRECISION);

        return rewardRate;
    }


    // ADMIN CONTROLS



    /**
     * @notice Sets the end time for the staking period
     * @dev Can only be called by the contract owner
     * @param _totalTime The total duration of the staking period in seconds
     */
    function setStakingEndTime(uint256 _totalTime) external onlyOwner {
        stakingEndTime = block.timestamp + _totalTime;
        stakingStartTime = block.timestamp;
    }

    /**
     * @notice Sets the total reward pool for the staking period
     * @dev Can only be called by the contract owner
     * @param _rewardPool The total amount of tokens to be distributed as rewards
     */
    function setRewardPool(uint256 _rewardPool) external onlyOwner {
        rewardPool = _rewardPool;
    }
}