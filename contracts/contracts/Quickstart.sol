// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

// Uncomment this line to use console.log
// import "hardhat/console.sol";
import "./interfaces/IOracle.sol";

contract Quickstart {
    address private owner;
    address public oracleAddress;
    string public lastResponse;
    uint private callsCount;

    event OracleAddressUpdated(address indexed newOracleAddress);

    constructor(
        address initialOracleAddress
    ) {
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not owner");
        _;
    }

    modifier onlyOracle() {
        require(msg.sender == oracleAddress, "Caller is not oracle");
        _;
    }

    function setOracleAddress(address newOracleAddress) public onlyOwner {
        oracleAddress = newOracleAddress;
        emit OracleAddressUpdated(newOracleAddress);
    }

    function initializeDalleCall(string memory message) public returns (uint i) {
        uint currentId = callsCount;
        callsCount = currentId + 1;

        IOracle(oracleAddress).createFunctionCall(
            currentId,
            "image_generation",
            message
        );

        return currentId;
    }

    function onOracleFunctionResponse(
        uint /*runId*/,
        string memory response,
        string memory errorMessage
    ) public onlyOracle {
        if (keccak256(abi.encodePacked(errorMessage)) != keccak256(abi.encodePacked(""))) {
            lastResponse = errorMessage;
        } else {
            lastResponse = response;
        }
    }
}
