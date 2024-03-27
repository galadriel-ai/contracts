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
        // JSON string or empty string
        string logitBias;
        // 0 for null
        uint32 maxTokens;
        // int -20 - 20? Mapped to float -2.0 - 2.0? If bigger than 20 then null?
        int8 presencePenalty;
        // JSON string or empty string
        string responseFormat;
        // 0 for null
        uint seed;
        // empty str for null
        string stop;
        // 0-20, > 20 for null
        uint temperature;
        // 0-100  percentage, > 100 for null
        uint topP;
        // JSON list for tools in OpenAI format, empty for null, names have to match the supported tools
        string tools;
        // "none", "auto" or empty str which defaults to auto on OpenAI side
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

    struct GroqRequest {
        // "llama2-70b-4096", "mixtral-8x7b-32768" or "gemma-7b-it"
        string model;
        // int -20 - 20? Mapped to float -2.0 - 2.0? If bigger than 20 then null?
        int8 frequencyPenalty;
        // JSON string or empty string
        string logitBias;
        // 0 for null
        uint32 maxTokens;
        // int -20 - 20? Mapped to float -2.0 - 2.0? If bigger than 20 then null?
        int8 presencePenalty;
        // JSON string or empty string
        string responseFormat;
        // 0 for null
        uint seed;
        // empty str for null
        string stop;
        // 0-20, > 20 for null
        uint temperature;
        // 0-100  percentage, > 100 for null
        uint topP;
        string user;
    }

    struct GroqResponse {
        string id;

        string content;

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

    function onOracleKnowledgeBaseQueryResponse(
        uint callbackId,
        string [] memory documents,
        string memory errorMessage
    ) external;

    function getMessageHistoryContents(
        uint callbackId
    ) external view returns (string[] memory);

    function getMessageHistoryRoles(
        uint callbackId
    ) external view returns (string[] memory);

    function onOracleOpenAiLlmResponse(
        uint callbackId,
        IOracleTypes.OpenAiResponse memory response,
        string memory errorMessage
    ) external;

    function onOracleGroqLlmResponse(
        uint callbackId,
        IOracleTypes.GroqResponse memory response,
        string memory errorMessage
    ) external;
}

contract ChatOracle {

    struct PromptTypes {
        string defaultType;
        string openAi;
        string groq;
    }

    PromptTypes public promptTypes;

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
    mapping(uint => IOracleTypes.GroqRequest) public groqConfigurations;


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

    mapping(uint => string) public kbIndexingRequests;
    mapping(uint => string) public kbIndexingRequestErrors;
    mapping(uint => bool) public isKbIndexingRequestProcessed;
    mapping(string => string) public kbIndexes;
    uint public kbIndexingRequestCount;

    mapping(uint => string) public kbQueryCids;
    mapping(uint => string) public kbQueries;
    mapping(uint => address) public kbQueryCallbackAddresses;
    mapping(uint => uint) public kbQueryCallbackIds;
    mapping(uint => bool) public isKbQueryProcessed;
    uint public kbQueryCount;

    address private owner;

    event FunctionAdded(
        uint indexed functionId,
        string indexed functionInput,
        uint functionCallbackId,
        address sender
    );

    event KnowledgeBaseIndexRequestAdded(
        uint indexed id,
        address sender
    );

    event KnowledgeBaseIndexed(
        string indexed cid,
        string indexed indexCid
    );

    event knowledgeBaseQueryAdded(
        uint indexed kbQueryId,
        address sender
    );

    constructor() {
        owner = msg.sender;
        promptsCount = 0;
        functionsCount = 0;

        promptTypes = PromptTypes("default", "OpenAI", "Groq");
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

    function addAttestation(string memory attestation) public onlyWhitelisted {
        attestations[msg.sender] = attestation;
        latestAttestationOwner = msg.sender;
    }

    function createLlmCall(uint promptCallbackId) public returns (uint i) {
        uint promptId = promptsCount;
        callbackAddresses[promptId] = msg.sender;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;
        promptType[promptId] = promptTypes.defaultType;

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
        IChatGpt(callbackAddresses[promptId]).onOracleLlmResponse(
            promptCallBackId,
            response,
            errorMessage
        );
    }

    function markPromptAsProcessed(uint promptId) public onlyWhitelisted {
        isPromptProcessed[promptId] = true;
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
        IChatGpt(functionCallbackAddresses[functionId]).onOracleFunctionResponse(
            functionCallBackId,
            response,
            errorMessage
        );
    }

    function markFunctionAsProcessed(uint functionId) public onlyWhitelisted {
        isFunctionProcessed[functionId] = true;
    }

    function createOpenAiLlmCall(uint promptCallbackId, IOracleTypes.OpenAiRequest memory config) public returns (uint i) {
        uint promptId = promptsCount;
        callbackAddresses[promptId] = msg.sender;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;
        promptType[promptId] = promptTypes.openAi;

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
        IChatGpt(callbackAddresses[promptId]).onOracleOpenAiLlmResponse(
            promptCallBackId,
            response,
            errorMessage
        );
    }

    function markOpenAiPromptAsProcessed(uint promptId) public onlyWhitelisted {
        isPromptProcessed[promptId] = true;
    }

    function createGroqLlmCall(uint promptCallbackId, IOracleTypes.GroqRequest memory config) public returns (uint i) {
        uint promptId = promptsCount;
        callbackAddresses[promptId] = msg.sender;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;
        promptType[promptId] = promptTypes.groq;

        promptsCount++;

        groqConfigurations[promptId] = config;
        emit PromptAdded(promptId, promptCallbackId, msg.sender);

        return promptId;
    }

    function addGroqResponse(
        uint promptId,
        uint promptCallBackId,
        IOracleTypes.GroqResponse memory response,
        string memory errorMessage
    ) public onlyWhitelisted {
        require(!isPromptProcessed[promptId], "Prompt already processed");
        IChatGpt(callbackAddresses[promptId]).onOracleGroqLlmResponse(
            promptCallBackId,
            response,
            errorMessage
        );
    }

    function markGroqPromptAsProcessed(uint promptId) public onlyWhitelisted {
        isPromptProcessed[promptId] = true;
    }

    function addKnowledgeBase(string memory cid) public {
        require(bytes(kbIndexes[cid]).length == 0, "Index already set for this CID");
        uint kbIndexingRequestId = kbIndexingRequestCount;
        kbIndexingRequests[kbIndexingRequestId] = cid;
        kbIndexingRequestCount++;
        emit KnowledgeBaseIndexRequestAdded(kbIndexingRequestId, msg.sender);
    }

    function addKnowledgeBaseIndex(uint kbIndexingRequestId, string memory indexCid, string memory error) public onlyWhitelisted {
        require(!isKbIndexingRequestProcessed[kbIndexingRequestId], "Indexing request already processed");
        kbIndexes[kbIndexingRequests[kbIndexingRequestId]] = indexCid;
        kbIndexingRequestErrors[kbIndexingRequestId] = error;
        isKbIndexingRequestProcessed[kbIndexingRequestId] = true;
        emit KnowledgeBaseIndexed(kbIndexingRequests[kbIndexingRequestId], indexCid);
    }

    function markKnowledgeBaseAsProcessed(uint kbIndexingRequestId) public onlyWhitelisted {
        isKbIndexingRequestProcessed[kbIndexingRequestId] = true;
    }

    function createKnowledgeBaseQuery(
        uint kbQueryCallbackId,
        string memory cid,
        string memory query
    ) public returns (uint i) {
        require(bytes(kbIndexes[cid]).length > 0, "Index not available for this CID");
        uint kbQueryId = kbQueryCount;
        kbQueryCids[kbQueryId] = cid;
        kbQueries[kbQueryId] = query;
        kbQueryCallbackIds[kbQueryId] = kbQueryCallbackId;

        kbQueryCallbackAddresses[kbQueryId] = msg.sender;
        isKbQueryProcessed[kbQueryId] = false;

        kbQueryCount++;

        emit knowledgeBaseQueryAdded(kbQueryId, msg.sender);

        return kbQueryId;
    }

    function addKnowledgeBaseQueryResponse(
        uint kbQueryId,
        uint kbQueryCallbackId,
        string [] memory documents,
        string memory errorMessage
    ) public onlyWhitelisted {
        require(!isKbQueryProcessed[kbQueryId], "Knowledge base query already processed");
        isKbQueryProcessed[kbQueryId] = true;
        IChatGpt(kbQueryCallbackAddresses[kbQueryId]).onOracleKnowledgeBaseQueryResponse(
            kbQueryCallbackId,
            documents,
            errorMessage
        );
    }

    function markKnowledgeBaseQueryAsProcessed(uint kbQueryId) public onlyWhitelisted {
        isKbQueryProcessed[kbQueryId] = true;
    }
}
