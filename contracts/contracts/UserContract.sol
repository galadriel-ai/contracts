// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.23;

import "./interfaces/IOracle.sol";

contract UserContract {
    struct ChatRun {
        address owner;
        IOracle.Message[] messages;
        uint256 messagesCount;
    }

    struct Response {
        address owner;
        bool success;
        string response;
    }

    mapping(uint256 => ChatRun) public chatRuns;
    uint256 private chatRunsCount;

    event ChatCreated(address indexed owner, uint256 indexed chatId);

    mapping(uint256 => Response) public responses;

    event ResponseReceived(address owner, uint256 indexed chatId, bool indexed success, string response);

    address private owner;
    address public oracleAddress;
    address public oracleManager;

    event OracleAddressUpdated(address indexed newOracleAddress);
    event OracleManagerUpdated(address indexed newOracleManager);

    IOracle.OpenAiRequest private config;

    constructor(address initialOracleAddress, address manager) {
        owner = msg.sender;
        oracleManager = manager;
        oracleAddress = initialOracleAddress;
        chatRunsCount = 0;

        config = IOracle.OpenAiRequest({
            model: "gpt-4-turbo",
            frequencyPenalty: 21, // > 20 for null
            logitBias: "", // empty str for null
            maxTokens: 1000, // 0 for null
            presencePenalty: 21, // > 20 for null
            responseFormat: "{\"type\":\"text\"}",
            seed: 0, // null
            stop: "", // null
            temperature: 10, // Example temperature (scaled up, 10 means 1.0), > 20 means null
            topP: 101, // Percentage 0-100, > 100 means null
            tools: "",
            toolChoice: "", // "none" or "auto"
            user: "" // null
        });
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not owner");
        _;
    }

    modifier onlyOracle() {
        require(msg.sender == oracleAddress, "Caller is not oracle");
        _;
    }

    modifier onlyManager() {
        require(msg.sender == oracleManager, "Caller is not manager");
        _;
    }

    function setOracleAddress(address newOracleAddress) public onlyOwner {
        oracleAddress = newOracleAddress;
        emit OracleAddressUpdated(newOracleAddress);
    }

    function setOracleManager(address newOracleManager) public onlyOwner {
        oracleManager = newOracleManager;
        emit OracleManagerUpdated(newOracleManager);
    }

    function copyContentArray(IOracle.Content[] memory source) internal pure returns (IOracle.Content[] memory) {
        IOracle.Content[] memory result = new IOracle.Content[](source.length);

        for (uint256 i = 0; i < source.length; i++) {
            result[i] = source[i];
        }
        return result;
    }

    function startChat(address chatOwner, string memory systemMessage, string memory message, string[] memory imageUrls)
    public
    onlyManager
    returns (uint256)
    {
        ChatRun storage run = chatRuns[chatRunsCount];
        run.owner = chatOwner;

        // Set system message
        IOracle.Message memory sysMessage = IOracle.Message({role: "system", content: new IOracle.Content[](1)});
        sysMessage.content[0] = IOracle.Content({contentType: "text", value: systemMessage});
        run.messages.push(sysMessage);

        // Set user message
        IOracle.Message memory newMessage =
                            IOracle.Message({role: "user", content: new IOracle.Content[](imageUrls.length + 1)});
        newMessage.content[0] = IOracle.Content({contentType: "text", value: message});
        for (uint256 i = 1; i < imageUrls.length; i++) {
            newMessage.content[i] = IOracle.Content({contentType: "image_url", value: imageUrls[i - 1]});
        }
        run.messages.push(newMessage);

        run.messagesCount = 2;

        uint256 currentId = chatRunsCount;
        chatRunsCount = chatRunsCount + 1;

        IOracle(oracleAddress).createOpenAiLlmCall(currentId, config);
        emit ChatCreated(msg.sender, currentId);

        return currentId;
    }

    function onOracleOpenAiLlmResponse(
        uint256 runId,
        IOracle.OpenAiResponse memory response,
        string memory errorMessage
    ) public onlyOracle {
        ChatRun storage run = chatRuns[runId];
        require(
            keccak256(abi.encodePacked(run.messages[run.messagesCount - 1].role)) == keccak256(abi.encodePacked("user")),
            "No message to respond to"
        );

        address chatOwner = chatRuns[runId].owner;
        if (!compareStrings(errorMessage, "")) {
            IOracle.Message memory newMessage = IOracle.Message({role: "assistant", content: new IOracle.Content[](1)});
            newMessage.content[0].contentType = "text";
            newMessage.content[0].value = errorMessage;
            run.messages.push(newMessage);
            run.messagesCount++;

            responses[runId] = Response({owner: chatOwner, success: false, response: errorMessage});
            emit ResponseReceived(chatOwner, runId, false, errorMessage);
        } else {
            IOracle.Message memory newMessage = IOracle.Message({role: "assistant", content: new IOracle.Content[](1)});
            newMessage.content[0].contentType = "text";
            newMessage.content[0].value = response.content;
            run.messages.push(newMessage);
            run.messagesCount++;

            responses[runId] = Response({owner: chatOwner, success: true, response: response.content});
            emit ResponseReceived(chatOwner, runId, true, response.content);
        }
    }

    function addMessage(address chatOwner, string memory message, uint256 runId) public onlyManager {
        ChatRun storage run = chatRuns[runId];
        require(
            keccak256(abi.encodePacked(run.messages[run.messagesCount - 1].role))
            == keccak256(abi.encodePacked("assistant")),
            "No response to previous message"
        );
        require(run.owner == chatOwner, "Only chat owner can add messages");

        IOracle.Message memory newMessage = IOracle.Message({role: "user", content: new IOracle.Content[](1)});
        newMessage.content[0].contentType = "text";
        newMessage.content[0].value = message;
        run.messages.push(newMessage);
        run.messagesCount++;

        IOracle(oracleAddress).createOpenAiLlmCall(runId, config);
    }

    function getMessageHistory(uint256 chatId) public view returns (IOracle.Message[] memory) {
        return chatRuns[chatId].messages;
    }

    function compareStrings(string memory a, string memory b) private pure returns (bool) {
        return (keccak256(abi.encodePacked((a))) == keccak256(abi.encodePacked((b))));
    }
}