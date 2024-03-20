// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

// Uncomment this line to use console.log
// import "hardhat/console.sol";

interface IOracleTypes {

    struct OpenAiRequest {
        // "gpt-4-turbo-preview" or "gpt-3.5-turbo-1106"
        string model;
        // int -20 - 20? Mapped to float -2.0 - 2.0? If bigger than 20 then null?
        int8 frequencyPenalty;
        string logitBias;
        // 0 for null
        uint32 maxTokens;
        // int -20 - 20? Mapped to float -2.0 - 2.0? If bigger than 20 then null?
        int8 presencePenalty;
        // "" ,"text" or "json_object". In docs its actually '{"type": "json_object"}'
        string responseFormat;
        // 0 for null
        uint seed;
        // string / array / null - Up to 4 sequences where the API will stop generating further tokens.
        string stop;
        // 0-20 >20 for null
        uint temperature;
        // Not supported here? or list of str maybe of our supported tools?
        // tools
        string toolChoice;
        string user;
    }

    struct OpenAiResponse {
        string id;

        // either content is an empty srt or functionName and functionArguments
        string content;
        string functionName;
        string functionArguments;

        uint64 created;
        string model;
        string systemFingerprint;
        // kind of pointless since its always "chat.completion"?
        string object;

        uint32 completionTokens;
        uint32 promptTokens;
        uint32 totalTokens;
    }
}

interface IChatGpt {
    function onOracleFunctionResponse(
        uint callbackId,
        string memory response,
        string memory errorMessage
    ) external;

    function onOracleLlmResponse(
        uint callbackId,
        string memory response,
        string memory errorMessage
    ) external;

    function getMessageHistoryContents(
        uint callbackId
    ) external view returns (string[] memory);

    function getMessageHistoryRoles(
        uint callbackId
    ) external view returns (string[] memory);


    function onOpenAiOracleLlmResponse(
        uint callbackId,
        IOracleTypes.OpenAiResponse memory response,
        string memory errorMessage
    ) external;
}

contract ChatOracle {

    mapping(address => bool) whitelistedAddresses;

    mapping(address => string) public attestations;
    address public latestAttestationOwner;


    // LLM calls
    mapping(uint => address) public callbackAddresses;
    mapping(uint => uint) public promptCallbackIds;
    mapping(uint => bool) public isPromptProcessed;
    // "default", "OpenAI"
    mapping(uint => string) public promptType;

    mapping(uint => IOracleTypes.OpenAiRequest) public openAiConfigurations;


    uint public promptsCount;

    event PromptAdded(
        uint indexed promptId,
        uint indexed promptCallbackId,
        address sender
    );

    mapping(uint => string) public functionInputs;
    mapping(uint => string) public functionTypes;
    mapping(uint => address) public functionCallbackAddresses;
    mapping(uint => uint) public functionCallbackIds;
    mapping(uint => bool) public isFunctionProcessed;
    uint public functionsCount;


    address private owner;

    event FunctionAdded(
        uint indexed functionId,
        string indexed functionInput,
        uint functionCallbackId,
        address sender
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

    function addAttestation(address owner, string memory attestation) public onlyOwner {
        attestations[owner] = attestation;
        latestAttestationOwner = owner;
    }

    function createLlmCall(uint promptCallbackId) public returns (uint i) {
        uint promptId = promptsCount;
        callbackAddresses[promptId] = msg.sender;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;
        promptType[promptId] = "default";

        promptsCount++;

        emit PromptAdded(promptId, promptCallbackId, msg.sender);

        return promptId;
    }

    function addResponse(
        uint promptId,
        uint promptCallBackId,
        string memory response,
        string memory errorMessage
    ) public onlyWhitelisted {
        require(!isPromptProcessed[promptId], "Prompt already processed");
        isPromptProcessed[promptId] = true;
        IChatGpt(callbackAddresses[promptId]).onOracleLlmResponse(
            promptCallBackId,
            response,
            errorMessage
        );
    }

    function getMessages(
        uint promptId,
        uint promptCallBackId
    ) public view returns (string[] memory) {
        return IChatGpt(callbackAddresses[promptId]).getMessageHistoryContents(promptCallBackId);
    }

    function getRoles(
        uint promptId,
        uint promptCallBackId
    ) public view returns (string[] memory) {
        return IChatGpt(callbackAddresses[promptId]).getMessageHistoryRoles(promptCallBackId);
    }

    function createFunctionCall(
        uint functionCallbackId,
        string memory functionType,
        string memory functionInput
    ) public returns (uint i) {
        uint functionId = functionsCount;
        functionTypes[functionId] = functionType;
        functionInputs[functionId] = functionInput;
        functionCallbackIds[functionId] = functionCallbackId;

        functionCallbackAddresses[functionId] = msg.sender;
        isFunctionProcessed[functionId] = false;

        functionsCount++;

        emit FunctionAdded(functionId, functionInput, functionCallbackId, msg.sender);

        return functionId;
    }

    function addFunctionResponse(
        uint functionId,
        uint functionCallBackId,
        string memory response,
        string memory errorMessage
    ) public onlyWhitelisted {
        require(!isFunctionProcessed[functionId], "Function already processed");
        isFunctionProcessed[functionId] = true;
        IChatGpt(functionCallbackAddresses[functionId]).onOracleFunctionResponse(
            functionCallBackId,
            response,
            errorMessage
        );
    }

    function createOpenAiLlmCall(uint promptCallbackId, IOracleTypes.OpenAiRequest memory config) public returns (uint i) {
        uint promptId = promptsCount;
        callbackAddresses[promptId] = msg.sender;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;
        promptType[promptId] = "OpenAI";

        promptsCount++;

        openAiConfigurations[promptId] = config;
        emit PromptAdded(promptId, promptCallbackId, msg.sender);

        return promptId;
    }

    function addOpenAiResponse(
        uint promptId,
        uint promptCallBackId,
        IOracleTypes.OpenAiResponse memory response,
        string memory errorMessage
    ) public onlyWhitelisted {
        require(!isPromptProcessed[promptId], "Prompt already processed");
        isPromptProcessed[promptId] = true;
        IChatGpt(callbackAddresses[promptId]).onOpenAiOracleLlmResponse(
            promptCallBackId,
            response,
            errorMessage
        );
    }
}
