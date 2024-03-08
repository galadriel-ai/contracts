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

    struct Message {
        string role;
        string content;
    }

    struct ChatRun {
        address owner;
        Message[] messages;
        uint messagesCount;
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
        Message memory newMessage;
        newMessage.content = message;
        newMessage.role = "user";
        run.messages.push(newMessage);
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
        ChatRun storage run = chatRuns[msg.sender][runId];
        require(
            keccak256(abi.encodePacked(run.messages[run.messagesCount - 1].role)) == keccak256(abi.encodePacked("assistant")),
            "No response to previous message"
        );

        Message memory newMessage;
        newMessage.content = message;
        newMessage.role = "user";
        run.messages.push(newMessage);
        run.messagesCount++;
        IOracle(oracleAddress).addPrompt(msg.sender, "chat", runId);
    }

    function getMessages(address owner, uint chatId) public view returns (string[] memory) {
        string[] memory messages = new string[](chatRuns[owner][chatId].messages.length);
        for (uint i = 0; i < chatRuns[owner][chatId].messages.length; i++) {
            messages[i] = chatRuns[owner][chatId].messages[i].content;
        }
        return messages;
    }

    function getRoles(address owner, uint chatId) public view returns (string[] memory) {
        string[] memory roles = new string[](chatRuns[owner][chatId].messages.length);
        for (uint i = 0; i < chatRuns[owner][chatId].messages.length; i++) {
            roles[i] = chatRuns[owner][chatId].messages[i].role;
        }
        return roles;
    }
}
