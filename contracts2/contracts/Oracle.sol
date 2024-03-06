// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

// Uncomment this line to use console.log
// import "hardhat/console.sol";

interface IAgent {
    function addResponse(string memory response, uint promptId) external;
}

contract Oracle {

    mapping(uint => string) public prompts;
    mapping(uint => address) public callbackAddresses;
    mapping(uint => uint) public promptCallbackIds;
    mapping(uint => bool) public isPromptProcessed;
    uint private promptsCount;

    address private owner;

    event PromptAdded(uint indexed promptId, uint indexed promptCallbackId, address indexed sender, string prompt);

    constructor() {
        owner = msg.sender;
        promptsCount = 0;
    }

    function addPrompt(string memory prompt, uint promptCallbackId) public returns (uint i) {
        uint promptId = promptsCount;
        prompts[promptId] = prompt;
        callbackAddresses[promptId] = msg.sender;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;

        promptsCount++;

        emit PromptAdded(promptId, promptCallbackId, msg.sender, prompt);

        return promptId;
    }

    function addResponse(uint promptId, string memory response, uint promptCallBackId) public {
        require(msg.sender == owner, "Caller is not owner");

        isPromptProcessed[promptId] = true;
        IAgent(callbackAddresses[promptId]).addResponse(response, promptCallBackId);
    }

}
