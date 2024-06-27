// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "./IOracle.sol";

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

    function onOracleLlmResponse(
        uint callbackId,
        IOracle.LlmResponse memory response,
        string memory errorMessage
    ) external;

    function onOracleKnowledgeBaseQueryResponse(
        uint callbackId,
        string [] memory documents,
        string memory errorMessage
    ) external;

    function getMessageHistory(
        uint callbackId
    ) external view returns (IOracle.Message[] memory);

    function getMessageHistoryContents(
        uint callbackId
    ) external view returns (string[] memory);

    function getMessageHistoryRoles(
        uint callbackId
    ) external view returns (string[] memory);

    function onOracleOpenAiLlmResponse(
        uint callbackId,
        IOracle.OpenAiResponse memory response,
        string memory errorMessage
    ) external;

    function onOracleGroqLlmResponse(
        uint callbackId,
        IOracle.GroqResponse memory response,
        string memory errorMessage
    ) external;
}