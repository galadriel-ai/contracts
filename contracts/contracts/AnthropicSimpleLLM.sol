// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

// import "https://github.com/galadriel-ai/contracts/blob/main/contracts/contracts/interfaces/IOracle.sol";
import "./interfaces/IOracle.sol";

contract SimpleLLM {
    address private oracleAddress = 0x68EC9556830AD097D661Df2557FBCeC166a0A075; // use latest: https://docs.galadriel.com/oracle-address
    uint private runId = 0;
    string public message;
    string public response;
    IOracle.LlmRequest private config;

    constructor() {
        config = IOracle.LlmRequest({
            model: "claude-3-5-sonnet-20240620", // "claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-2.1", "claude-2.0", "claude-instant-1.2"
            frequencyPenalty: 21, // > 20 for null
            logitBias: "", // empty str for null
            maxTokens: 1000, // 0 for null
            presencePenalty: 21, // > 20 for null
            responseFormat: '{"type":"text"}',
            seed: 0, // null
            stop: "", // null
            temperature: 10, // Example temperature (scaled up, 10 means 1.0), > 20 means null
            topP: 101, // Percentage 0-100, > 100 means null
            tools: "",
            toolChoice: "auto", // "none" or "auto"
            user: "" // null
        });
    }

    function sendMessage(string memory _message) public {
        IOracle.Message memory newMessage = IOracle.Message({
            role: "user",
            content: new IOracle.Content[](1)
        });
        newMessage.content[0] = IOracle.Content({
            contentType: "text",
            value: _message
        });
        message = _message;
        IOracle(oracleAddress).createLlmCall(runId, config);
    }

    // required for Oracle
    function onOracleLlmResponse(
        uint /*_runId*/,
        IOracle.LlmResponse memory _response,
        string memory _errorMessage
    ) public {
        require(msg.sender == oracleAddress, "Caller is not oracle");
        if (
            keccak256(abi.encodePacked(_errorMessage)) !=
            keccak256(abi.encodePacked(""))
        ) {
            response = _errorMessage;
        } else {
            response = _response.content;
        }
    }

    // required for Oracle
    function getMessageHistory(
        uint /*_runId*/
    ) public view returns (IOracle.Message[] memory) {
        IOracle.Message memory newMessage = IOracle.Message({
            role: "user",
            content: new IOracle.Content[](1)
        });
        newMessage.content[0] = IOracle.Content({
            contentType: "text",
            value: message
        });
        IOracle.Message[] memory newMessages = new IOracle.Message[](1);
        newMessages[0] = newMessage;
        return newMessages;
    }
}