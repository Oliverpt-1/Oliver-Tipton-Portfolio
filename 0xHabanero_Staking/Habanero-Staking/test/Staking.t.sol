// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console} from "forge-std/Test.sol";
//import Tokens
//import my actual staking contradct
//import NFT

contract CounterTest is Test {

    function setUp() public {
        counter = new Counter();
        counter.setNumber(0);
        //set up user

    }

    function test_Increment() public {
        counter.increment();
        assertEq(counter.number(), 1);
    }

    function testFuzz_SetNumber(uint256 x) public {
        counter.setNumber(x);
        assertEq(counter.number(), x);
    }
}
