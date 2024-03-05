// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Test, console} from "forge-std/Test.sol";
import {Agent} from "../src/Agent.sol";

contract CounterTest is Test {
    Agent public agent;

    // TODO:
    function setUp() public {
        agent = new Agent(0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266);
//        counter.setNumber(0);
    }

//    function test_Increment() public {
//        counter.increment();
//        assertEq(counter.number(), 1);
//    }

//    function testFuzz_SetNumber(uint256 x) public {
//        counter.setNumber(x);
//        assertEq(counter.number(), x);
//    }
}
