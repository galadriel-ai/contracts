// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.9;

// Uncomment this line to use console.log
// import "hardhat/console.sol";
import "./interfaces/IOracle.sol";

// @title AiTownAgent
contract AiTownAgent {

    struct ChatRun {
        address owner;
        IOracle.Message[] messages;
        uint messagesCount;
    }

    // @notice Mapping from chat ID to ChatRun
    mapping(uint => ChatRun) public chatRuns;
    uint private chatRunsCount;

    mapping(string => uint) public conversationIdToChatRun;

    // @notice Event emitted when a new chat is created
    event ChatCreated(address indexed owner, uint indexed chatId);

    // @notice Address of the contract owner
    address private owner;
    
    // @notice Address of the oracle contract
    address public oracleAddress;

    // @notice System prompt for the agent
    string public systemPrompt;

    // @notice Event emitted when the oracle address is updated
    event OracleAddressUpdated(address indexed newOracleAddress);

    // @param initialOracleAddress Initial address of the oracle contract
    // @param systemPrompt System prompt for the run
    constructor(address initialOracleAddress, string memory _systemPrompt) {
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
        systemPrompt = _systemPrompt;
    }

    // @notice Ensures the caller is the contract owner
    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not owner");
        _;
    }

    // @notice Ensures the caller is the oracle contract
    modifier onlyOracle() {
        require(msg.sender == oracleAddress, "Caller is not oracle");
        _;
    }

    function setOracleAddress(address newOracleAddress) public onlyOwner {
        oracleAddress = newOracleAddress;
        emit OracleAddressUpdated(newOracleAddress);
    }

    function startChat(string memory conversationId, string memory message) public returns (uint) {
        ChatRun storage run = chatRuns[chatRunsCount];
        conversationIdToChatRun[conversationId] = chatRunsCount;
        run.owner = msg.sender;

        IOracle.Message memory systemMessage = createTextMessage("system", systemPrompt);
        run.messages.push(systemMessage);

        IOracle.Message memory newMessage = createTextMessage("user", message);
        run.messages.push(newMessage);

        run.messagesCount = 2;

        uint currentId = chatRunsCount;
        chatRunsCount++;

        IOracle(oracleAddress).createLlmCall(currentId);
        emit ChatCreated(msg.sender, currentId);

        return currentId;
    }

    function onOracleLlmResponse(
        uint runId,
        string memory response,
        string memory /*errorMessage*/
    ) public onlyOracle {
        ChatRun storage run = chatRuns[runId];
        require(
            keccak256(abi.encodePacked(run.messages[run.messagesCount - 1].role)) == keccak256(abi.encodePacked("user")),
            "No message to respond to"
        );

        IOracle.Message memory newMessage = createTextMessage("assistant", response);
        run.messages.push(newMessage);
        run.messagesCount++;
    }

    function addMessage(string memory message, string memory conversationId) public {
        uint runId = conversationIdToChatRun[conversationId];
        ChatRun storage run = chatRuns[runId];
        require(
            keccak256(abi.encodePacked(run.messages[run.messagesCount - 1].role)) == keccak256(abi.encodePacked("assistant")),
            "No response to previous message"
        );
        require(
            run.owner == msg.sender, "Only chat owner can add messages"
        );

        IOracle.Message memory newMessage = createTextMessage("user", message);
        run.messages.push(newMessage);
        run.messagesCount++;

        IOracle(oracleAddress).createLlmCall(runId);
    }

    function getMessageHistory(uint chatId) public view returns (IOracle.Message[] memory) {
        return chatRuns[chatId].messages;
    }

    function getMessageHistory(string memory conversationId) public view returns (IOracle.Message[] memory) {
        uint chatId = conversationIdToChatRun[conversationId];
        return chatRuns[chatId].messages;
    }

    function createTextMessage(string memory role, string memory content) private pure returns (IOracle.Message memory) {
        IOracle.Message memory newMessage = IOracle.Message({
            role: role,
            content: new IOracle.Content[](1)
        });
        newMessage.content[0].contentType = "text";
        newMessage.content[0].value = content;
        return newMessage;
    }
}