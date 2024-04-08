// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

// Uncomment this line to use console.log
// import "hardhat/console.sol";


interface IOracle {
    struct GroqRequest {
        string model;
        int8 frequencyPenalty;
        string logitBias;
        uint32 maxTokens;
        int8 presencePenalty;
        string responseFormat;
        uint seed;
        string stop;
        uint temperature;
        uint topP;
        string user;
    }

    struct GroqResponse {
        string id;

        string content;

        uint64 created;
        string model;
        string systemFingerprint;
        string object;

        uint32 completionTokens;
        uint32 promptTokens;
        uint32 totalTokens;
    }

    function createGroqLlmCall(
        uint promptId,
        GroqRequest memory request
    ) external returns (uint);

    struct OpenAiRequest {
        string model;
        int8 frequencyPenalty;
        string logitBias;
        uint32 maxTokens;
        int8 presencePenalty;
        string responseFormat;
        uint seed;
        string stop;
        uint temperature;
        uint topP;
        string tools;
        string toolChoice;
        string user;
    }

    struct OpenAiResponse {
        string id;

        string content;
        string functionName;
        string functionArguments;

        uint64 created;
        string model;
        string systemFingerprint;
        string object;

        uint32 completionTokens;
        uint32 promptTokens;
        uint32 totalTokens;
    }

    function createOpenAiLlmCall(
        uint promptId,
        OpenAiRequest memory request
    ) external returns (uint);

    function createFunctionCall(
        uint functionCallbackId,
        string memory functionType,
        string memory functionInput
    ) external returns (uint i);

    function createKnowledgeBaseQuery(
        uint kbQueryCallbackId,
        string memory cid,
        string memory query,
        uint32 num_documents
    ) external returns (uint i);
}

contract Test {
    address private owner;
    address public oracleAddress;
    string public llmMessage;
    string public lastResponse;
    string public lastError;
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

    function callFunction(string memory name, string memory message) public returns (uint i) {
        uint currentId = callsCount;
        callsCount = currentId + 1;

        lastResponse = "";
        lastError = "";

        IOracle(oracleAddress).createFunctionCall(
            currentId,
            name,
            message
        );

        return currentId;
    }

    function callOpenAiLLM(string memory model, string memory message) public returns (uint i) {
        uint currentId = callsCount;
        callsCount = currentId + 1;

        llmMessage = message;
        lastResponse = "";
        lastError = "";
    
        IOracle(oracleAddress).createOpenAiLlmCall(
            currentId,
            IOracle.OpenAiRequest({
                model: model,
                frequencyPenalty : 21, // > 20 for null
                logitBias : "", // empty str for null
                maxTokens : 1000, // 0 for null
                presencePenalty : 21, // > 20 for null
                responseFormat : "{\"type\":\"text\"}",
                seed : 0, // null
                stop : "", // null
                temperature : 10, // Example temperature (scaled up, 10 means 1.0), > 20 means null
                topP : 101, // Percentage 0-100, > 100 means null
                tools : "",
                toolChoice : "", // "none" or "auto"
                user : "" // null
            })
        );

        return currentId;
    }

    function callGroqLLM(string memory model, string memory message) public returns (uint i) {
        uint currentId = callsCount;
        callsCount = currentId + 1;

        llmMessage = message;
        lastResponse = "";
        lastError = "";

        IOracle(oracleAddress).createGroqLlmCall(
            currentId,
            IOracle.GroqRequest({
                model : model,
                frequencyPenalty : 21, // > 20 for null
                logitBias : "", // empty str for null
                maxTokens : 1000, // 0 for null
                presencePenalty : 21, // > 20 for null
                responseFormat : "{\"type\":\"text\"}",
                seed : 0, // null
                stop : "", // null
                temperature : 10, // Example temperature (scaled up, 10 means 1.0), > 20 means null
                topP : 101, // Percentage 0-100, > 100 means null
                user : "" // null
            })
        );

        return currentId;
    }

    function getMessageHistoryContents(uint chatId) public view returns (string[] memory) {
        string[] memory messages = new string[](1);
        messages[0] = llmMessage;
        return messages;
    }

    function getMessageHistoryRoles(uint chatId) public view returns (string[] memory) {
        string[] memory roles = new string[](1);
        roles[0] = "user";
        return roles;
    }

    function queryKnowledgeBase(string memory cid, string memory query) public returns (uint i) {
        uint currentId = callsCount;
        callsCount = currentId + 1;

        lastResponse = "";
        lastError = "";

        IOracle(oracleAddress).createKnowledgeBaseQuery(
            currentId,
            cid,
            query,
            3
        );
        return currentId;
    }

    function onOracleFunctionResponse(
        uint runId,
        string memory response,
        string memory errorMessage
    ) public onlyOracle {
        lastResponse = response;
        lastError = errorMessage;
    }

    function onOracleKnowledgeBaseQueryResponse(
            uint runId,
            string [] memory documents,
            string memory errorMessage
        ) public onlyOracle {
        string memory newContent = "";
        for (uint i = 0; i < documents.length; i++) {
            newContent = string(abi.encodePacked(newContent, documents[i], "\n"));
        }
        lastResponse = newContent;
        lastError = errorMessage;
    }

    function onOracleOpenAiLlmResponse(
        uint runId,
        IOracle.OpenAiResponse memory response,
        string memory errorMessage
    ) public onlyOracle {
        lastResponse = response.content;
        lastError = errorMessage;
    }

    function onOracleGroqLlmResponse(
        uint runId,
        IOracle.GroqResponse memory response,
        string memory errorMessage
    ) public onlyOracle {
        lastResponse = response.content;
        lastError = errorMessage;
    }
}
