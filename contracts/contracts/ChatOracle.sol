// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

// Uncomment this line to use console.log
// import "hardhat/console.sol";

interface IChatGpt {
    function addResponse(
        string memory response,
        // chat || function_call || function_result
        string memory responseType,
        address runOwner,
        uint promptId
    ) external;
}

contract ChatOracle {

    mapping(address => bool) whitelistedAddresses;

    // chat || image_generation
    mapping(uint => string) public promptType;
    mapping(uint => address) public callbackAddresses;
    mapping(uint => address) public runOwners;
    mapping(uint => uint) public promptCallbackIds;
    mapping(uint => bool) public isPromptProcessed;
    uint private promptsCount;

    address private owner;

    event PromptAdded(
        uint indexed promptId,
        uint indexed promptCallbackId,
        address sender,
        address indexed runOwner
    );

    constructor() {
        owner = msg.sender;
        promptsCount = 0;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not owner");
        _;
    }

    modifier onlyWhitelisted() {
        require(whitelistedAddresses[msg.sender], "Caller is not whitelisted");
        _;
    }

    function updateWhitelist(address _addressToWhitelist, bool isWhitelisted) public onlyOwner {
        whitelistedAddresses[_addressToWhitelist] = isWhitelisted;
    }


    function addPrompt(address runOwner, string memory _promptType, uint promptCallbackId) public returns (uint i) {
        uint promptId = promptsCount;
        callbackAddresses[promptId] = msg.sender;
        promptType[promptId] = _promptType;
        runOwners[promptId] = runOwner;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;

        promptsCount++;

        emit PromptAdded(promptId, promptCallbackId, msg.sender, runOwner);

        return promptId;
    }

    function addResponse(
        uint promptId,
        string memory response,
        string memory responseType,
        uint promptCallBackId
    ) public onlyWhitelisted {
        require(!isPromptProcessed[promptId], "Prompt already processed");
        isPromptProcessed[promptId] = true;
        address runOwner = runOwners[promptId];
        IChatGpt(callbackAddresses[promptId]).addResponse(response, responseType, runOwner, promptCallBackId);
    }

}
