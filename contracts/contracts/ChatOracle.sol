// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

// Uncomment this line to use console.log
// import "hardhat/console.sol";

interface IChatGpt {
    function addResponse(
        string memory response,
    // chat || function_call || function_result || error(?)
        string memory responseType,
        address runOwner,
        uint promptId
    ) external;

    function getMessages(
        address owner,
        uint chatId
    ) external view returns (string[] memory);

    function getRoles(
        address owner,
        uint chatId
    ) external view returns (string[] memory);

}

contract ChatOracle {

    mapping(address => bool) whitelistedAddresses;

    mapping(uint => address) public callbackAddresses;
    mapping(uint => address) public runOwners;
    mapping(uint => uint) public promptCallbackIds;
    mapping(uint => bool) public isPromptProcessed;
    uint public promptsCount;

    mapping(uint => string) public functionInputs;
    mapping(uint => string) public functionType;
    mapping(uint => address) public functionOwners;
    mapping(uint => address) public functionCallbackAddresses;
    mapping(uint => uint) public functionCallbackIds;
    mapping(uint => bool) public isFunctionProcessed;
    uint private functionsCount;


    address private owner;

    event PromptAdded(
        uint indexed promptId,
        uint indexed promptCallbackId,
        address sender,
        address indexed runOwner
    );


    event FunctionAdded(
        uint indexed functionId,
        string indexed functionInput,
        uint functionCallbackId,
        address sender,
        address indexed runOwner
    );

    constructor() {
        owner = msg.sender;
        promptsCount = 0;
        functionsCount = 0;
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
        runOwners[promptId] = runOwner;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;

        promptsCount++;

        emit PromptAdded(promptId, promptCallbackId, msg.sender, runOwner);

        return promptId;
    }

    function addResponse(
        uint promptId,
        uint promptCallBackId,
        string memory response,
        string memory responseType
    ) public onlyWhitelisted {
        require(!isPromptProcessed[promptId], "Prompt already processed");
        isPromptProcessed[promptId] = true;
        address runOwner = runOwners[promptId];
        IChatGpt(callbackAddresses[promptId]).addResponse(response, responseType, runOwner, promptCallBackId);
    }

    function getMessages(
        uint promptId,
        uint promptCallBackId
    ) public view returns (string[] memory) {
        address runOwner = runOwners[promptId];
        return IChatGpt(callbackAddresses[promptId]).getMessages(runOwner, promptCallBackId);
    }

    function getRoles(
        uint promptId,
        uint promptCallBackId
    ) public view returns (string[] memory) {
        address runOwner = runOwners[promptId];
        return IChatGpt(callbackAddresses[promptId]).getRoles(runOwner, promptCallBackId);
    }

    function addFunctionCall(
        address runOwner,
        string memory functionType,
        string memory functionInput,
        uint functionCallbackId
    ) public returns (uint i) {
        uint functionId = functionsCount;
        functionOwners[functionId] = runOwner;
        functionInputs[functionId] = functionType;
        functionInputs[functionId] = functionInput;
        functionCallbackIds[functionId] = functionCallbackId;

        functionCallbackAddresses[functionId] = msg.sender;
        isFunctionProcessed[functionId] = false;

        functionsCount++;

        emit FunctionAdded(functionId, functionInput, functionCallbackId, msg.sender, runOwner);

        return functionId;
    }

    function addFunctionResponse(
        uint functionId,
        uint functionCallBackId,
        string memory response,
        string memory responseType
    ) public onlyWhitelisted {
        require(!isFunctionProcessed[functionId], "Function already processed");
        isFunctionProcessed[functionId] = true;
        address runOwner = functionOwners[functionId];
        IChatGpt(functionCallbackAddresses[functionId]).addResponse(
            response,
            responseType,
            runOwner,
            functionCallBackId
        );
    }
}
