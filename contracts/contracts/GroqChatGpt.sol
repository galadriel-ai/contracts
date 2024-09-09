// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.9;

// Uncomment this line to use console.log
import "hardhat/console.sol";
import "./interfaces/IOracle.sol";

contract GroqChatGpt {

    struct ChatRun {
        address owner;
        IOracle.Message[] messages;
        uint messagesCount;
    }

    // Mapping from chat ID to ChatRun
    mapping(uint => ChatRun) public chatRuns;
    uint private chatRunsCount;

    // Event emitted when a new chat is created
    event ChatCreated(address indexed owner, uint indexed chatId);
    event MessageAdded(address indexed owner, uint indexed chatId);
    event MessageReceived(address indexed owner, uint indexed chatId);

    // Address of the contract owner
    address private owner;

    // Address of the oracle contract
    address public oracleAddress;

    // Event emitted when the oracle address is updated
    event OracleAddressUpdated(address indexed newOracleAddress);

    // Configuration for the Groq request
    IOracle.GroqRequest private config;

    mapping(address => uint) public balances;
    mapping(uint => uint) public chatBalances;

    // initialOracleAddress Initial address of the oracle contract
    constructor(address initialOracleAddress) {
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
        chatRunsCount = 0;

        config = IOracle.GroqRequest({
            model : "llama-3.1-8b-instant",
            frequencyPenalty : 21, // > 20 for null
            logitBias : "", // empty str for null
            maxTokens : 1000, // 0 for null
            presencePenalty : 21, // > 20 for null
            responseFormat : "{\"type\":\"text\"}",
            seed : 0, // null
            stop : "", // null
            temperature : 10, // Example temperature (scaled up, 10 means 1.0), > 20 means null
            topP : 101, // Percentage 0-100, > 100 means null
            user : "", // null
            ragConfig : IOracle.RAGConfig({num_documents: 0})
        });

        console.log("balance", address(this).balance);
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

    function startChat(string memory message, uint num_documents) public payable returns (uint) {
        
        ChatRun storage run = chatRuns[chatRunsCount];

        run.owner = msg.sender;
        IOracle.Message memory newMessage = createTextMessage("user", message);
        run.messages.push(newMessage);
        run.messagesCount = 1;

        uint currentId = chatRunsCount;
        chatRunsCount = chatRunsCount + 1;

        IOracle.GroqRequest memory callConfig = config;
        callConfig.ragConfig.num_documents = num_documents;

        IOracle(oracleAddress).createGroqLlmCall(currentId, callConfig);
        emit ChatCreated(msg.sender, currentId);
        console.log("received", msg.value);
        chatBalances[currentId] = msg.value;
        console.log("balance", address(this).balance);
        return currentId;
    }

    function onOracleGroqLlmResponse(
        uint runId,
        IOracle.GroqResponse memory response,
        string memory errorMessage
    ) public onlyOracle {
        ChatRun storage run = chatRuns[runId];
        require(
            keccak256(abi.encodePacked(run.messages[run.messagesCount - 1].role)) == keccak256(abi.encodePacked("user")),
            "No message to respond to"
        );
        if (!compareStrings(errorMessage, "")) {
            IOracle.Message memory newMessage = createTextMessage("assistant", errorMessage);
            run.messages.push(newMessage);
            run.messagesCount++;
        } else {

            if (response.system_prompt.content.length > 0) {
                IOracle.Message memory systemMessage = response.system_prompt;
                run.messages.push(systemMessage);
                run.messagesCount++;
            }

            IOracle.Message memory newMessage = createTextMessage("assistant", response.content);
            run.messages.push(newMessage);
            run.messagesCount++;

            uint total = 0;
            for (uint i = 0; i < response.scores.length; i++) {
                IOracle.Score memory score = response.scores[i];
                total += score.score;   
            }
            console.log("total amount allocated for chat is ", total);
            for(uint i = 0; i < response.scores.length; i++) {
                IOracle.Score memory score = response.scores[i];
                console.log("score for ", score.owner, "is", score.score);
                console.log("chat balance", chatBalances[runId]);
                console.log("balance before", balances[score.owner]);
                balances[score.owner] += chatBalances[runId] * (score.score / total);
                console.log("balance after ", score.owner, "is", balances[score.owner]);
            }

        }
        emit MessageReceived(msg.sender, runId);
    }

    function widthdraw(uint amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }

    function addMessage(string memory message, uint num_documents, uint runId) public {
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

        IOracle.GroqRequest memory callConfig = config;
        callConfig.ragConfig.num_documents = num_documents;

        IOracle(oracleAddress).createGroqLlmCall(runId, callConfig);
        emit MessageAdded(msg.sender, runId);
    }

    function getMessageHistory(uint chatId) public view returns (IOracle.Message[] memory){
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

    function compareStrings(string memory a, string memory b) private pure returns (bool) {
        return (keccak256(abi.encodePacked((a))) == keccak256(abi.encodePacked((b))));
    }
}
