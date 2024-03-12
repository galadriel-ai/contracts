// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.9;

// Uncomment this line to use console.log
// import "hardhat/console.sol";

interface IOracle {
    function createLlmCall(
        uint promptId
    ) external returns (uint);
}

contract ChatGpt {

    struct Message {
        string role;
        string content;
    }

    struct ChatRun {
        address owner;
        Message[] messages;
        uint messagesCount;
    }

    mapping(uint => ChatRun) public chatRuns;
    uint private chatRunsCount;

    event ChatCreated(address indexed owner, uint indexed chatId);

    address private owner;
    address public oracleAddress;

    event OracleAddressUpdated(address indexed newOracleAddress);

    constructor(address initialOracleAddress) {
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
        chatRunsCount = 0;
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
        ChatRun storage run = chatRuns[chatRunsCount];

        run.owner = msg.sender;
        Message memory newMessage;
        newMessage.content = message;
        newMessage.role = "user";
        run.messages.push(newMessage);
        run.messagesCount = 1;

        uint currentId = chatRunsCount;
        chatRunsCount = chatRunsCount + 1;

        IOracle(oracleAddress).createLlmCall(currentId);
        emit ChatCreated(msg.sender, currentId);

        return currentId;
    }

    function onOracleLlmResponse(
        uint runId,
        string memory response
    ) public onlyOracle {
        ChatRun storage run = chatRuns[runId];
        require(
            keccak256(abi.encodePacked(run.messages[run.messagesCount - 1].role)) == keccak256(abi.encodePacked("user")),
            "No message to respond to"
        );

        Message memory newMessage;
        newMessage.content = response;
        newMessage.role = "assistant";
        run.messages.push(newMessage);
        run.messagesCount++;
    }

    function addMessage(string memory message, uint runId) public {
        ChatRun storage run = chatRuns[runId];
        require(
            keccak256(abi.encodePacked(run.messages[run.messagesCount - 1].role)) == keccak256(abi.encodePacked("assistant")),
            "No response to previous message"
        );
        require(
            run.owner == msg.sender, "Only chat owner can add messages"
        );

        Message memory newMessage;
        newMessage.content = message;
        newMessage.role = "user";
        run.messages.push(newMessage);
        run.messagesCount++;
        IOracle(oracleAddress).createLlmCall(runId);
    }

    function getMessageHistoryContents(uint chatId) public view returns (string[] memory) {
        string[] memory messages = new string[](chatRuns[chatId].messages.length);
        for (uint i = 0; i < chatRuns[chatId].messages.length; i++) {
            messages[i] = chatRuns[chatId].messages[i].content;
        }
        return messages;
    }

    function getMessageHistoryRoles(uint chatId) public view returns (string[] memory) {
        string[] memory roles = new string[](chatRuns[chatId].messages.length);
        for (uint i = 0; i < chatRuns[chatId].messages.length; i++) {
            roles[i] = chatRuns[chatId].messages[i].role;
        }
        return roles;
    }
}
