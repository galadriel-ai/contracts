// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

// Uncomment this line to use console.log
// import "hardhat/console.sol";
import {IOracle} from "./interfaces/IOracle.sol";

// DalleNft
contract DalleImageGenerator {
    uint256 private _promptId;

    // Address of the contract owner
    address private owner;

    // Address of the oracle contract
    address public oracleAddress;

    // Event emitted when the prompt is updated
    event PromptAdded(string indexed taskId);

    // Event emitted when the prompt is replied
    event PromptReplied(uint indexed promptId);

    mapping(uint => string) public prompts;
    mapping (uint => string) public promptResponses;
    mapping(string => uint) public tasks;

    // Event emitted when the oracle address is updated
    event OracleAddressUpdated(address indexed newOracleAddress);

    // initialOracleAddress Initial address of the oracle contract
    constructor(
        address initialOracleAddress
    ) {
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
    }

    // Ensures the caller is the contract owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not owner");
        _;
    }

    // Ensures the caller is the oracle contract
    modifier onlyOracle() {
        require(msg.sender == oracleAddress, "Caller is not oracle");
        _;
    }

    // Updates the oracle address
    function setOracleAddress(address newOracleAddress) public onlyOwner {
        oracleAddress = newOracleAddress;
        emit OracleAddressUpdated(newOracleAddress);
    }

    // Add prompt to the oracle
    function addPrompt(string memory prompt, string memory taskId) public {
        uint promptId = _promptId;
        tasks[taskId] = _promptId;
        prompts[promptId] = prompt;
        IOracle(oracleAddress).createFunctionCall(
            _promptId,
            "image_generation",
            prompt
        );
        _promptId++;
        emit PromptAdded(taskId);
    }

    // Handles the response from the oracle for the function call
    function onOracleFunctionResponse(
        uint promptId,
        string memory response,
        string memory /*errorMessage*/
    ) public onlyOracle {
        promptResponses[promptId] = response;
        emit PromptReplied(promptId);
    }


    function getImage(uint promptId) public view returns (string memory) {
        return promptResponses[promptId];
    }

}
