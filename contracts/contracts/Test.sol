// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

// Uncomment this line to use console.log
// import "hardhat/console.sol";


interface IOracle {
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
    }
