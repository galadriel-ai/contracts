// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

// Uncomment this line to use console.log
// import "hardhat/console.sol";

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

    function onOracleKbQueryResponse(
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
}

contract ChatOracle {

    mapping(address => bool) whitelistedAddresses;

    mapping(address => string) public attestations;
    address public latestAttestationOwner;

    mapping(uint => address) public callbackAddresses;
    mapping(uint => uint) public promptCallbackIds;
    mapping(uint => bool) public isPromptProcessed;
    uint public promptsCount;

    mapping(uint => string) public functionInputs;
    mapping(uint => string) public functionTypes;
    mapping(uint => address) public functionCallbackAddresses;
    mapping(uint => uint) public functionCallbackIds;
    mapping(uint => bool) public isFunctionProcessed;
    uint public functionsCount;

    mapping(uint => string) public kbIndexingRequests;
    mapping(string => string) public kbIndexes;
    uint public kbIndexingRequestCount;

    mapping(uint => string) public kbQueryCids;
    mapping(uint => string) public kbQueries;
    mapping(uint => address) public kbQueryCallbackAddresses;
    mapping(uint => uint) public kbQueryCallbackIds;
    mapping(uint => bool) public isKbQueryProcessed;
    uint public kbQueryCount;

    address private owner;

    event PromptAdded(
        uint indexed promptId,
        uint indexed promptCallbackId,
        address sender
    );

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

    function addKnowledgeBase(string memory cid) public {
        require(bytes(kbIndexes[cid]).length == 0, "Index already set for this CID");
        uint kbIndexingRequestId = kbIndexingRequestCount;
        kbIndexingRequests[kbIndexingRequestId] = cid;
        kbIndexingRequestCount++;
        emit KnowledgeBaseIndexRequestAdded(kbIndexingRequestId, msg.sender);
    }

    function addKnowledgeBaseIndex(uint kbIndexingRequestId, string memory indexCid) public onlyWhitelisted {
        require(bytes(kbIndexes[kbIndexingRequests[kbIndexingRequestId]]).length == 0, "Index already set for this CID");
        kbIndexes[kbIndexingRequests[kbIndexingRequestId]] = indexCid;
        emit KnowledgeBaseIndexed(kbIndexingRequests[kbIndexingRequestId], indexCid);
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
        IChatGpt(kbQueryCallbackAddresses[kbQueryId]).onOracleKbQueryResponse(
            kbQueryCallbackId,
            documents,
            errorMessage
        );
    }
}
