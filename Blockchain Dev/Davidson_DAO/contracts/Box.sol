// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";

contract Box is Ownable {
  uint256 private value;

  // Emitted when the stored value changes
  event ValueChanged(uint256 newValue);

  constructor(address initialOwner) Ownable(initialOwner) {}
  //q: need to decide who this shoudl be..... probably should be the governance contract

  // Stores a new value in the contract
  function store(uint256 newValue) public onlyOwner {
    value = newValue;
    emit ValueChanged(newValue);
  }

  // Reads the last stored value
  function retrieve() public view returns (uint256) {
    return value;
  }

  //THIS HANDLES WHAT THE GOVERNANCE IS FOR.  Make this Davidson specific.   
    //Ideas:
      //1.Get funding from somewhere / Vote on where the funding goes ie. Group trip, etc.
      //2. Vote on president, vice president, treasurer, and other officer positions.
      //3. Project Selection
      //4. Partnerships

}