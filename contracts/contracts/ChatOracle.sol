// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

// Uncomment this line to use console.log
// import "hardhat/console.sol";
import "./interfaces/IChatGpt.sol";
import "./interfaces/IOracle.sol";

// @title ChatOracle
// @notice This contract exposes functionalities for interacting with large language models (LLMs), external tools, and a knowledge base.
contract ChatOracle is IOracle {

    struct PromptTypes {
        string defaultType;
        string openAi;
        string groq;
    }

    // @notice Available prompt types
    PromptTypes public promptTypes;

    // @notice Mapping of whitelisted addresses
    mapping(address => bool) private whitelistedAddresses;

    // @notice Mapping of attestations made by addresses
    mapping(address => string) public attestations;
    address public latestAttestationOwner;

    // @notice Mapping of PCR0 hashes by addresses
    mapping(address => string) public pcr0Hashes;
    address public latestPcr0HashOwner;

    // @notice Mapping of prompt ID to the address of the contract that called the LLM
    mapping(uint => address) public callbackAddresses;

    // @notice Mapping of prompt ID to the callback ID of the contract that called the LLM
    mapping(uint => uint) public promptCallbackIds;

    // @notice Mapping of prompt ID to whether the prompt has been processed
    mapping(uint => bool) public isPromptProcessed;

    // @notice Mapping of prompt ID to the type of prompt
    // @dev Default is OpenAI
    mapping(uint => string) public promptType;

    // @notice Mapping of prompt ID to the LLM configuration
    mapping(uint => IOracle.LlmRequest) public llmConfigurations;

    // @notice Mapping of prompt ID to the OpenAI configuration
    mapping(uint => IOracle.OpenAiRequest) public openAiConfigurations;

    // @notice Mapping of prompt ID to the Groq configuration
    mapping(uint => IOracle.GroqRequest) public groqConfigurations;

    // @notice Total number of prompts
    uint public promptsCount;

    // @notice Event emitted when a prompt is added
    event PromptAdded(
        uint indexed promptId,
        uint indexed promptCallbackId,
        address sender
    );

    // @notice Mapping of function ID to the input of the function
    mapping(uint => string) public functionInputs;

    // @notice Mapping of function ID to the type of the function
    mapping(uint => string) public functionTypes;

    // @notice Mapping of function ID to the address of the contract that called the function
    mapping(uint => address) public functionCallbackAddresses;

    // @notice Mapping of function ID to the callback ID of the contract that called the function
    mapping(uint => uint) public functionCallbackIds;

    // @notice Mapping of function ID to whether the function has been processed
    mapping(uint => bool) public isFunctionProcessed;

    // @notice Total number of functions
    uint public functionsCount;

    // @notice Mapping of knowledge base indexing request ID to the IPFS CID
    mapping(uint => string) public kbIndexingRequests;

    // @notice Mapping of knowledge base indexing request ID to the error message
    mapping(uint => string) public kbIndexingRequestErrors;

    // @notice Mapping of knowledge base indexing request ID to whether the request has been processed
    mapping(uint => bool) public isKbIndexingRequestProcessed;

    // @notice Mapping of knowledge base CID to the index CID
    mapping(string => string) public kbIndexes;

    // @notice Total number of knowledge base indexing requests
    uint public kbIndexingRequestCount;

    // @notice Mapping of knowledge base query ID to the query request
    mapping(uint => IOracle.KnowledgeBaseQueryRequest) public kbQueries;

    // @notice Mapping of knowledge base query ID to the address of the contract that called the query
    mapping(uint => address) public kbQueryCallbackAddresses;

    // @notice Mapping of knowledge base query ID to the callback ID of the contract that called the query
    mapping(uint => uint) public kbQueryCallbackIds;

    // @notice Mapping of knowledge base query ID to whether the query has been processed
    mapping(uint => bool) public isKbQueryProcessed;

    // @notice Total number of knowledge base queries
    uint public kbQueryCount;

    address private owner;
    
    // @notice Event emitted when a function call is added
    event FunctionAdded(
        uint indexed functionId,
        string indexed functionInput,
        uint functionCallbackId,
        address sender
    );

    // @notice Event emitted when a knowledge base indexing request is added
    event KnowledgeBaseIndexRequestAdded(
        uint indexed id,
        address sender
    );

    // @notice Event emitted when a knowledge base is indexed
    event KnowledgeBaseIndexed(
        string indexed cid,
        string indexed indexCid
    );

    // @notice Event emitted when a knowledge base query is added
    event KnowledgeBaseQueryAdded(
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

    // @notice Updates the whitelist status of an address
    // @param _addressToWhitelist Address to update
    // @param isWhitelisted Whitelist status
    function updateWhitelist(address _addressToWhitelist, bool isWhitelisted) public onlyOwner {
        whitelistedAddresses[_addressToWhitelist] = isWhitelisted;
    }

    // @notice Adds an attestation for the caller
    // @param attestation The attestation text
    // @dev Called by teeML oracle
    function addAttestation(string memory attestation) public onlyWhitelisted {
        attestations[msg.sender] = attestation;
        latestAttestationOwner = msg.sender;
    }

    // @notice Adds a PCR0 hash for the caller
    // @param pcr0Hash The PCR0 hash
    function addPcr0Hash(string memory pcr0Hash) public onlyOwner {
        pcr0Hashes[msg.sender] = pcr0Hash;
        latestPcr0HashOwner = msg.sender;
    }

    // @notice Creates a new LLM call
    // @param promptCallbackId The callback ID for the LLM call
    // @return The ID of the created prompt
    function createLlmCall(uint promptCallbackId) public returns (uint) {
        uint promptId = promptsCount;
        callbackAddresses[promptId] = msg.sender;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;
        promptType[promptId] = promptTypes.defaultType;

        promptsCount++;

        emit PromptAdded(promptId, promptCallbackId, msg.sender);

        return promptId;
    }

    // @notice Adds a response to a prompt
    // @param promptId The ID of the prompt
    // @param promptCallBackId The callback ID for the prompt
    // @param response The response text
    // @param errorMessage Any error message
    // @dev Called by teeML oracle
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

    // @notice Creates a new LLM call
    // @param promptCallbackId The callback ID for the LLM call
    // @return The ID of the created prompt
    function createLlmCall(uint promptCallbackId, IOracle.LlmRequest memory request) public returns (uint) {
        uint promptId = promptsCount;
        callbackAddresses[promptId] = msg.sender;
        promptCallbackIds[promptId] = promptCallbackId;
        isPromptProcessed[promptId] = false;
        promptType[promptId] = promptTypes.defaultType;

        promptsCount++;

        llmConfigurations[promptId] = request;
        emit PromptAdded(promptId, promptCallbackId, msg.sender);

        return promptId;
    }

    // @notice Adds a response to a prompt
    // @param promptId The ID of the prompt
    // @param promptCallBackId The callback ID for the prompt
    // @param response The LLM response
    // @param errorMessage Any error message
    // @dev Called by teeML oracle
    function addResponse(
        uint promptId,
        uint promptCallBackId,
        IOracle.LlmResponse memory response,
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

    // @notice Marks a prompt as processed
    // @param promptId The ID of the prompt
    // @dev Called by teeML oracle
    function markPromptAsProcessed(uint promptId) public onlyWhitelisted {
        isPromptProcessed[promptId] = true;
    }

    // @notice Retrieves message history for a prompt
    // @param promptId The ID of the prompt
    // @param promptCallBackId The callback ID for the prompt
    // @return An array of message history contents
    function getMessages(
        uint promptId,
        uint promptCallBackId
    ) public view returns (string[] memory) {
        return IChatGpt(callbackAddresses[promptId]).getMessageHistoryContents(promptCallBackId);
    }

    // @notice Retrieves message roles for a prompt
    // @param promptId The ID of the prompt
    // @param promptCallBackId The callback ID for the prompt
    // @return An array of message history roles
    function getRoles(
        uint promptId,
        uint promptCallBackId
    ) public view returns (string[] memory) {
        return IChatGpt(callbackAddresses[promptId]).getMessageHistoryRoles(promptCallBackId);
    }

    // @notice Retrieves messages and roles for a prompt
    // @param promptId The ID of the prompt
    // @param promptCallBackId The callback ID for the prompt
    // @return An array of messages and roles
    function getMessagesAndRoles(
        uint promptId,
        uint promptCallBackId
    ) public view returns (IOracle.Message[] memory) {
        return IChatGpt(callbackAddresses[promptId]).getMessageHistory(promptCallBackId);
    }

    // @notice Creates a new function call
    // @param functionCallbackId The callback ID for the function call
    // @param functionType The type of the function
    // @param functionInput The input for the function
    // @return The ID of the created function call
    function createFunctionCall(
        uint functionCallbackId,
        string memory functionType,
        string memory functionInput
    ) public returns (uint) {
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

    // @notice Adds a response to a function call
    // @param functionId The ID of the function call
    // @param functionCallBackId The callback ID for the function call
    // @param response The response text
    // @param errorMessage Any error message
    // @dev Called by teeML oracle
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

    // @notice Marks a function call as processed
    // @param functionId The ID of the function call
    // @dev Called by teeML oracle
    function markFunctionAsProcessed(uint functionId) public onlyWhitelisted {
        isFunctionProcessed[functionId] = true;
    }

    // @notice Creates a new OpenAI LLM call
    // @param promptCallbackId The callback ID for the LLM call
    // @param config The OpenAI request configuration
    // @return The ID of the created prompt
    function createOpenAiLlmCall(uint promptCallbackId, IOracle.OpenAiRequest memory config) public returns (uint) {
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

    // @notice Adds a response to an OpenAI LLM call
    // @param promptId The ID of the prompt
    // @param promptCallBackId The callback ID for the prompt
    // @param response The OpenAI response
    // @param errorMessage Any error message
    // @dev Called by teeML oracle
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

    // @notice Marks an OpenAI prompt as processed
    // @param promptId The ID of the prompt
    // @dev Called by teeML oracle
    function markOpenAiPromptAsProcessed(uint promptId) public onlyWhitelisted {
        isPromptProcessed[promptId] = true;
    }

    // @notice Creates a new Groq LLM call
    // @param promptCallbackId The callback ID for the LLM call
    // @param config The Groq request configuration
    // @return The ID of the created prompt
    function createGroqLlmCall(uint promptCallbackId, IOracle.GroqRequest memory config) public returns (uint) {
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

    // @notice Adds a response to a Groq LLM call
    // @param promptId The ID of the prompt
    // @param promptCallBackId The callback ID for the prompt
    // @param response The Groq response
    // @param errorMessage Any error message
    // @dev Called by teeML oracle
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

    // @notice Marks a Groq prompt as processed
    // @param promptId The ID of the prompt
    // @dev Called by teeML oracle
    function markGroqPromptAsProcessed(uint promptId) public onlyWhitelisted {
        isPromptProcessed[promptId] = true;
    }

    // @notice Adds a knowledge base with the given CID
    // @param cid The IPFS CID of the knowledge base
    function addKnowledgeBase(string memory cid) public {
        require(bytes(kbIndexes[cid]).length == 0, "Index already set for this CID");
        uint kbIndexingRequestId = kbIndexingRequestCount;
        kbIndexingRequests[kbIndexingRequestId] = cid;
        kbIndexingRequestCount++;
        emit KnowledgeBaseIndexRequestAdded(kbIndexingRequestId, msg.sender);
    }

    // @notice Adds an index to a knowledge base
    // @param kbIndexingRequestId The ID of the indexing request
    // @param indexCid The IPFS CID of the index
    // @param error Any error message
    // @dev Called by teeML oracle
    function addKnowledgeBaseIndex(uint kbIndexingRequestId, string memory indexCid, string memory error) public onlyWhitelisted {
        require(!isKbIndexingRequestProcessed[kbIndexingRequestId], "Indexing request already processed");
        kbIndexes[kbIndexingRequests[kbIndexingRequestId]] = indexCid;
        kbIndexingRequestErrors[kbIndexingRequestId] = error;
        isKbIndexingRequestProcessed[kbIndexingRequestId] = true;
        emit KnowledgeBaseIndexed(kbIndexingRequests[kbIndexingRequestId], indexCid);
    }

    // @notice Marks a knowledge base indexing request as processed
    // @param kbIndexingRequestId The ID of the indexing request
    // @dev Called by teeML oracle
    function markKnowledgeBaseAsProcessed(uint kbIndexingRequestId) public onlyWhitelisted {
        isKbIndexingRequestProcessed[kbIndexingRequestId] = true;
    }

    // @notice Creates a new knowledge base query
    // @param kbQueryCallbackId The callback ID for the query
    // @param cid The IPFS CID of the knowledge base
    // @param query The query text
    // @param num_documents The number of documents to retrieve
    // @return The ID of the created query
    function createKnowledgeBaseQuery(
        uint kbQueryCallbackId,
        string memory cid,
        string memory query,
        uint32 num_documents
    ) public returns (uint) {
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

        emit KnowledgeBaseQueryAdded(kbQueryId, msg.sender);

        return kbQueryId;
    }

    // @notice Adds a response to a knowledge base query
    // @param kbQueryId The ID of the query
    // @param kbQueryCallbackId The callback ID for the query
    // @param documents The array of retrieved documents
    // @param errorMessage Any error message
    // @dev Called by teeML oracle
    function addKnowledgeBaseQueryResponse(
        uint kbQueryId,
        uint kbQueryCallbackId,
        string[] memory documents,
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

    // @notice Marks a knowledge base query as processed
    // @param kbQueryId The ID of the query
    // @dev Called by teeML oracle
    function markKnowledgeBaseQueryAsProcessed(uint kbQueryId) public onlyWhitelisted {
        isKbQueryProcessed[kbQueryId] = true;
    }
}
