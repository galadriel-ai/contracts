// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.9;

// Uncomment this line to use console.log
// import "hardhat/console.sol";

interface IOracle {
    function addPrompt(
        address runOwner,
        string memory promptType,
        uint promptId
    ) external returns (uint);
}

contract ChatGpt {

    struct ChatRun {
        address owner;
        string[] messages;
        uint messagesCount;
        string[] responses;
        uint responsesCount;
    }

    mapping(address => mapping(uint => ChatRun)) public chatRuns;
    mapping(address => uint) private chatRunsCount;

    event ChatCreated(address indexed owner, uint indexed chatId);

    address private owner;
    address public oracleAddress;

    event OracleAddressUpdated(address indexed newOracleAddress);

    constructor(address initialOracleAddress) {
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

    function startChat(string memory message) public returns (uint i) {
        uint runsCount = chatRunsCount[msg.sender];
        ChatRun storage run = chatRuns[msg.sender][runsCount];

        run.owner = msg.sender;
        run.responsesCount = 0;
        run.messages.push(message);
        run.messagesCount = 1;

        uint currentId = chatRunsCount[msg.sender];
        chatRunsCount[msg.sender] = currentId + 1;

        IOracle(oracleAddress).addPrompt(msg.sender, "chat", currentId);
        emit ChatCreated(msg.sender, currentId);

        return currentId;
    }

    function addResponse(
        string memory response,
        string memory responseType,
        address chatOwner,
        uint runId
    ) public onlyOracle {
        ChatRun storage run = chatRuns[chatOwner][runId];
        require(run.messagesCount > run.responsesCount, "No message to respond to");
        run.responses.push(response);
        run.responsesCount++;
    }

    function addMessage(string memory message, uint runId) public {
        ChatRun storage run = chatRuns[msg.sender][runId];
        require(run.messagesCount == run.responsesCount, "No response to previous message");
        run.messages.push(message);
        run.messagesCount++;
        IOracle(oracleAddress).addPrompt(msg.sender, "chat", runId);
    }

    function getMessages(address owner, uint chatId) public view returns (string[] memory) {
        return chatRuns[owner][chatId].messages;
    }

    function getResponses(address owner, uint chatId) public view returns (string[] memory) {
        return chatRuns[owner][chatId].responses;
    }
}
