// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

// Uncomment this line to use console.log
// import "hardhat/console.sol";
import "./interfaces/IChatGpt.sol";
import "./interfaces/IOracle.sol";

contract ChatOracle is IOracle {

    struct PromptTypes {
        string defaultType;
        string openAi;
        string groq;
    }

    PromptTypes public promptTypes;

    mapping(address => bool) whitelistedAddresses;

    mapping(address => string) public attestations;
    address public latestAttestationOwner;
    mapping(address => string) public pcr0Hashes;
    address public latestPcr0HashOwner;


    // LLM calls
    mapping(uint => address) public callbackAddresses;
    mapping(uint => uint) public promptCallbackIds;
    mapping(uint => bool) public isPromptProcessed;
    // "default", "OpenAI"
    mapping(uint => string) public promptType;

    mapping(uint => IOracle.OpenAiRequest) public openAiConfigurations;
    mapping(uint => IOracle.GroqRequest) public groqConfigurations;


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

    mapping(uint => IOracle.KnowledgeBaseQueryRequest) public kbQueries;
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

    function addPcr0Hash(string memory pcr0Hash) public onlyOwner {
        pcr0Hashes[msg.sender] = pcr0Hash;
        latestPcr0HashOwner = msg.sender;
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
        isPromptProcessed[promptId] = true;
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

   function getMessagesAndRoles(
        uint promptId,
        uint promptCallBackId
    ) public view returns (IOracle.Message[] memory) {
        return IChatGpt(callbackAddresses[promptId]).getMessageHistory(promptCallBackId);
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

    function markFunctionAsProcessed(uint functionId) public onlyWhitelisted {
        isFunctionProcessed[functionId] = true;
    }

    function createOpenAiLlmCall(uint promptCallbackId, IOracle.OpenAiRequest memory config) public returns (uint i) {
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
        IOracle.OpenAiResponse memory response,
        string memory errorMessage
    ) public onlyWhitelisted {
        require(!isPromptProcessed[promptId], "Prompt already processed");
        isPromptProcessed[promptId] = true;
        IChatGpt(callbackAddresses[promptId]).onOracleOpenAiLlmResponse(
            promptCallBackId,
            response,
            errorMessage
        );
    }

    function markOpenAiPromptAsProcessed(uint promptId) public onlyWhitelisted {
        isPromptProcessed[promptId] = true;
    }

    function createGroqLlmCall(uint promptCallbackId, IOracle.GroqRequest memory config) public returns (uint i) {
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
        IOracle.GroqResponse memory response,
        string memory errorMessage
    ) public onlyWhitelisted {
        require(!isPromptProcessed[promptId], "Prompt already processed");
        isPromptProcessed[promptId] = true;
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
        string memory query,
        uint32 num_documents
    ) public returns (uint i) {
        require(bytes(kbIndexes[cid]).length > 0, "Index not available for this CID");
        require(bytes(query).length > 0, "Query cannot be empty");
        require(num_documents > 0, "Number of documents should be greater than 0");
        uint kbQueryId = kbQueryCount;
        kbQueries[kbQueryId].cid = cid;
        kbQueries[kbQueryId].query = query;
        kbQueries[kbQueryId].num_documents = num_documents;
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
