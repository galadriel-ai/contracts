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

    struct Document {
        string text;
        address owner;
        uint score;
    }

    // Available prompt types
    PromptTypes public promptTypes;

    // Mapping of whitelisted addresses
    mapping(address => bool) private whitelistedAddresses;

    // Mapping of attestations made by addresses
    mapping(address => string) public attestations;
    address public latestAttestationOwner;

    // Mapping of PCR0 hashes by addresses
    mapping(address => string) public pcr0Hashes;
    address public latestPcr0HashOwner;

    // Mapping of prompt ID to the address of the contract that called the LLM
    mapping(uint => address) public callbackAddresses;

    // Mapping of prompt ID to the callback ID of the contract that called the LLM
    mapping(uint => uint) public promptCallbackIds;

    // Mapping of prompt ID to whether the prompt has been processed
    mapping(uint => bool) public isPromptProcessed;

    //  Mapping of prompt ID to the type of prompt
    mapping(uint => string) public promptType;

    // Mapping of prompt ID to the LLM configuration
    mapping(uint => IOracle.LlmRequest) public llmConfigurations;

    // Mapping of prompt ID to the OpenAI configuration
    mapping(uint => IOracle.OpenAiRequest) public openAiConfigurations;

    // Mapping of prompt ID to the Groq configuration
    mapping(uint => IOracle.GroqRequest) public groqConfigurations;

    // Total number of prompts
    uint public promptsCount;

    // Event emitted when a prompt is added
    event PromptAdded(
        uint indexed promptId,
        uint indexed promptCallbackId,
        address sender
    );

    // Mapping of function ID to the input of the function
    mapping(uint => string) public functionInputs;

    // Mapping of function ID to the type of the function
    mapping(uint => string) public functionTypes;

    // Mapping of function ID to the address of the contract that called the function
    mapping(uint => address) public functionCallbackAddresses;

    // Mapping of function ID to the callback ID of the contract that called the function
    mapping(uint => uint) public functionCallbackIds;

    // Mapping of function ID to whether the function has been processed
    mapping(uint => bool) public isFunctionProcessed;

    // Total number of functions
    uint public functionsCount;

    // Mapping of langchain knowledge base indexing request ID to the s3 key
    mapping(uint => string) public langchainkbIndexingRequests;

    // Mapping of langchain knowledge base indexing request ID to the address of the EOA that called the request
    mapping(uint => address) public langchainkbIndexingOwnerAddress;

    // Mapping of langchain knowledge base indexing request ID to the error message
    mapping(uint => string) public langchainkbIndexingRequestErrors;

    // Mapping of langchain knowledge base indexing request ID to whether the request has been processed
    mapping(uint => bool) public langchainisKbIndexingRequestProcessed;

    // Total number of langchain knowledge base indexing requests
    uint public langchainkbIndexingRequestCount;

    // Mapping of langchain knowledge base query ID to the the query request
    mapping(uint => IOracle.LangchainKnowledgeBaseQueryRequest)
        public langchainkbQueries;
    
    // Mapping of langchain knowledge base query ID to the address of the contract that called the query
    mapping(uint => address) public langchainkbQueryCallbackAddresses;

    // Mapping of langchain knowledge base query ID to the callback ID of the contract that called the query
    mapping(uint => uint) public langchainkbQueryCallbackIds;

    // Mapping of langchain knowledge base query ID to whether the query has been processed
    mapping(uint => bool) public langchainisKbQueryProcessed;

    // Total number of knowledge base queries
    uint public langchainkbQueryCount;

    address private owner;
    
    // Event emitted when a function call is added
    event FunctionAdded(
        uint indexed functionId,
        string indexed functionInput,
        uint functionCallbackId,
        address sender
    );

    // Event emitted when a langchain knowledge base query is added
    event LangchainKnowledgeIndexRequestAdded(
        uint indexed kbQueryId,
        address sender
    );

    // Event emitted when a knowledge base is indexed
    event LangchainKnowledgeBaseIndexed(uint indexed kbQueryId, string key, string errorMessage);

    // Event emitted when a langchain knowledge base query is added
    event LangchainKnowledgeBaseQueryAdded(
        uint indexed kbQueryId,
        address sender
    );

    event LangchainKnowledgeBaseQueryResponseAdded(
        uint indexed kbQueryId,
        Document[] documents,
        string errorMessage
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

    // Adds a knowledge base with the given s3 key
    // @param key: s3 key of the knowledge base
    function addLangchainKnowledgeBase(string memory key) public {
        uint langchainkbIndexingRequestId = langchainkbIndexingRequestCount;
        langchainkbIndexingRequests[langchainkbIndexingRequestId] = key;
        langchainkbIndexingOwnerAddress[langchainkbIndexingRequestId] = msg.sender;
        
        langchainkbIndexingRequestCount++;
        emit LangchainKnowledgeIndexRequestAdded(
            langchainkbIndexingRequestId,
            msg.sender
        );
    }

    // Adds an index to a knowledge base
    // @param langchainkbIndexingRequestId The ID of the indexing request
    // @param error Any error message
    function addLangchainKnowledgeBaseIndex(
        uint langchainkbIndexingRequestId,
        string memory errorMessage
    ) public onlyWhitelisted {
        require(
            !langchainisKbIndexingRequestProcessed[
                langchainkbIndexingRequestId
            ],
            "Langchain indexing request already processed"
        );
        langchainkbIndexingRequestErrors[langchainkbIndexingRequestId] = errorMessage;
        langchainisKbIndexingRequestProcessed[
            langchainkbIndexingRequestId
        ] = true;
        emit LangchainKnowledgeBaseIndexed(
            langchainkbIndexingRequestId, 
            langchainkbIndexingRequests[langchainkbIndexingRequestId],
            errorMessage
        );
    }

    // Marks a knowledge base indexing request as processed
    // @param langchainkbIndexingRequestId The ID of the indexing request
    function markLangchainKnowledgeBaseAsProcessed(
        uint langchainkbIndexingRequestId
    ) public onlyWhitelisted {
        langchainisKbIndexingRequestProcessed[
            langchainkbIndexingRequestId
        ] = true;
    }

    // Creates a new knowledge base query
    // @param langchainkbQueryCallbackId The callback ID for the query
    // @param query The query text
    // @param num_documents The number of documents to retrieve
    // @return The ID of the created query
    function createLangchainKnowledgeBaseQuery(
        uint langchainkbQueryCallbackId,
        string memory query,
        uint32 num_documents
    ) public returns (uint) {
        require(bytes(query).length > 0, "Query cannot be empty");
        require(
            num_documents > 0,
            "Number of documents should be greater than 0"
        );
        uint kbQueryId = langchainkbQueryCount;
        langchainkbQueries[kbQueryId].query = query;
        langchainkbQueries[kbQueryId].num_documents = num_documents;
        langchainkbQueryCallbackIds[kbQueryId] = langchainkbQueryCallbackId;

        langchainkbQueryCallbackAddresses[kbQueryId] = msg.sender;
        langchainisKbQueryProcessed[kbQueryId] = false;

        langchainkbQueryCount++;

        emit LangchainKnowledgeBaseQueryAdded(kbQueryId, msg.sender);

        return kbQueryId;
    }

    // Adds a response to a knowledge base query
    // @param langchainkbQueryId The ID of the query
    // @param langchainkbQueryCallbackId The callback ID for the query
    // @param documents The array of retrieved documents
    // @param errorMessage Any error message
    function addLangchainKnowledgeBaseQueryResponse(
        uint langchainkbQueryId,
        uint langchainkbQueryCallbackId,
        Document[] memory documents,
        string memory errorMessage
    ) public onlyWhitelisted {
        require(
            !langchainisKbQueryProcessed[langchainkbQueryId],
            "Knowledge base query already processed"
        );
        langchainisKbQueryProcessed[langchainkbQueryId] = true;
        emit LangchainKnowledgeBaseQueryResponseAdded(
            langchainkbQueryCallbackId,
            documents,
            errorMessage
        );
    }

    // Marks a knowledge base query as processed
    // @param langchainkbQueryId The ID of the query
    function markLangchainKnowledgeBaseQueryAsProcessed(
        uint langchainkbQueryId
    ) public onlyWhitelisted {
        langchainisKbQueryProcessed[langchainkbQueryId] = true;
    }
}
