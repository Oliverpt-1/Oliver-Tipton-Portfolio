# Yield-Generating Staking Protocol

## Overview

This staking protocol allows users to stake ERC20 tokens and earn rewards over time. It's designed to provide a 15% annual yield for users while maintaining precision and security.

## Key Features

- **ERC20 Token Staking**: Users can stake any compatible ERC20 token.
- **15% Annual Yield**: Stakers earn a competitive 15% annual return on their staked tokens.
- **Non-Custodial**: Users retain control of their assets through a unique NFT representing their stake.
- **Flexible Withdrawals**: Stakers can withdraw their funds partially or fully at any time.
- **Reward Claiming**: Users can claim their accumulated rewards separately from their stake.

## Technical Implementation

### Smart Contracts

The protocol consists of several interconnected smart contracts:

1. **Staking Contract**: The core contract managing stakes, rewards, and withdrawals.
2. **AccountNFT**: An ERC721 contract representing user stakes.
3. **ERC20Mock**: Mock tokens for staking and rewards (for testing purposes).

### Staking Mechanism

- Users create a staking account, receiving an NFT that represents their stake.
- The Staking contract tracks user balances and reward accumulation times.
- Rewards are calculated using a per-second rate derived from the annual yield.

### Reward Calculation

Rewards are calculated using high-precision fixed-point arithmetic:

```solidity
rewardRate = (ANNUAL_INTEREST_RATE * PRECISION) / (100 * SECONDS_PER_YEAR);
rewards = (timeElapsed * rewardRate * userStakeBalance) / PRECISION;
```

# Setup Instructions
### 1. Clone Repository
```
git clone [repo-url]
```
### 2. Install Dependencies
```
forge install
```
```
forge install OpenZeppelin/openzeppelin-contracts
```
### 3. Compile / Build
```
forge build
```
### 4. Run tests
```
forge test
```

