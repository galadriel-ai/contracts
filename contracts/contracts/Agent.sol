// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.9;

// Uncomment this line to use console.log
// import "hardhat/console.sol";

interface IOracle {
    function createLlmCall(
        uint promptId
    ) external returns (uint);

    function createFunctionCall(
        uint functionCallbackId,
        string memory functionType,
        string memory functionInput
    ) external returns (uint i);
}

contract Agent {

    string public prompt;

    struct Message {
        string role;
        string content;
    }

    struct AgentRun {
        address owner;
        Message[] messages;
        uint responsesCount;
        uint8 max_iterations;
        bool is_finished;
    }

    mapping(uint => AgentRun) public agentRuns;
    uint private agentRunCount;

    event AgentRunCreated(address indexed owner, uint indexed runId);

    address private owner;
    address public oracleAddress;

    event OracleAddressUpdated(address indexed newOracleAddress);

    constructor(
        address initialOracleAddress,         
        string memory systemPrompt
    ) {
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
        prompt = systemPrompt;
        agentRunCount = 0;
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
        require(msg.sender == owner, "Caller is not the owner");
        oracleAddress = newOracleAddress;
        emit OracleAddressUpdated(newOracleAddress);
    }

    function runAgent(string memory query, uint8 max_iterations) public returns (uint i) {
        AgentRun storage run = agentRuns[agentRunCount];

        run.owner = msg.sender;
        run.is_finished = false;
        run.responsesCount = 0;
        run.max_iterations = max_iterations;

        Message memory systemMessage;
        systemMessage.content = prompt;
        systemMessage.role = "system";
        run.messages.push(systemMessage);

        Message memory newMessage;
        newMessage.content = query;
        newMessage.role = "user";
        run.messages.push(newMessage);

        uint currentId = agentRunCount;
        agentRunCount = agentRunCount + 1;

        IOracle(oracleAddress).createLlmCall(currentId);
        emit AgentRunCreated(run.owner, currentId);

        return currentId;
    }

    function onOracleLlmResponse(
        uint runId,
        string memory response,
        string memory errorMessage
    ) public onlyOracle {
        AgentRun storage run = agentRuns[runId];

        Message memory assistantMessage;
        assistantMessage.content = response;
        assistantMessage.role = "assistant";
        run.messages.push(assistantMessage);
        run.responsesCount++;

        if (run.responsesCount >= run.max_iterations) {
            run.is_finished = true;
        } else {
            (string memory action, string memory actionInput) = findActionAndInput(response);
            if (compareStrings(action, "web_search")) {
                IOracle(oracleAddress).createFunctionCall(
                    runId,
                    "web_search",
                    actionInput
                );
            }
            else if (containsFinalAnswer(response)) {
                run.is_finished = true;
            }
        }
    }

    function onOracleFunctionResponse(
        uint runId,
        string memory response,
        string memory errorMessage
    ) public onlyOracle {
        AgentRun storage run = agentRuns[runId];
        require(
            !run.is_finished, "Run is finished"
        );
        Message memory newMessage;
        newMessage.content = makeObservation(response);
        newMessage.role = "user";
        run.messages.push(newMessage);
        IOracle(oracleAddress).createLlmCall(runId);
    }

    function getMessageHistoryContents(uint agentId) public view returns (string[] memory) {
        string[] memory messages = new string[](agentRuns[agentId].messages.length);
        for (uint i = 0; i < agentRuns[agentId].messages.length; i++) {
            messages[i] = agentRuns[agentId].messages[i].content;
        }
        return messages;
    }

    function getMessageHistoryRoles(uint agentId) public view returns (string[] memory) {
        string[] memory roles = new string[](agentRuns[agentId].messages.length);
        for (uint i = 0; i < agentRuns[agentId].messages.length; i++) {
            roles[i] = agentRuns[agentId].messages[i].role;
        }
        return roles;
    }

    function isRunFinished(uint runId) public view returns (bool) {
        return agentRuns[runId].is_finished;
    }

    function findActionAndInput(string memory input) public pure returns (string memory action, string memory actionInput) {
        bytes memory inputBytes = bytes(input);
        uint inputLength = inputBytes.length;
        uint i = 0;

        // Temporary storage for byte segments
        bytes memory tempBytes;

        while (i < inputLength) {
            // Reset tempBytes for each iteration
            tempBytes = "";

            // Look for "Action: " pattern
            if (i + 7 < inputLength && inputBytes[i] == 'A' && inputBytes[i + 1] == 'c' && inputBytes[i + 2] == 't' && inputBytes[i + 3] == 'i' && inputBytes[i + 4] == 'o' && inputBytes[i + 5] == 'n' && inputBytes[i + 6] == ':' && inputBytes[i + 7] == ' ') {
                i += 8; // Move past the "Action: " part
                while (i < inputLength && inputBytes[i] != '\n') {
                    tempBytes = abi.encodePacked(tempBytes, inputBytes[i]);
                    i++;
                }
                action = string(tempBytes);
            }
            // Look for "Action Input: " pattern
            else if (i + 13 < inputLength && inputBytes[i] == 'A' && inputBytes[i + 1] == 'c' && inputBytes[i + 2] == 't' && inputBytes[i + 3] == 'i' && inputBytes[i + 4] == 'o' && inputBytes[i + 5] == 'n' && inputBytes[i + 6] == ' ' && inputBytes[i + 7] == 'I' && inputBytes[i + 8] == 'n' && inputBytes[i + 9] == 'p' && inputBytes[i + 10] == 'u' && inputBytes[i + 11] == 't' && inputBytes[i + 12] == ':' && inputBytes[i + 13] == ' ') {
                i += 14; // Move past the "Action Input: " part
                while (i < inputLength && inputBytes[i] != '\n') {
                    tempBytes = abi.encodePacked(tempBytes, inputBytes[i]);
                    i++;
                }
                actionInput = string(tempBytes);
            } else {
                i++; // Move to the next character if no pattern is matched
            }
        }

        return (action, actionInput);
    }

    function containsFinalAnswer(string memory input) public pure returns (bool) {
        bytes memory inputBytes = bytes(input);
        bytes memory target = bytes("Final Answer:");

        if (inputBytes.length < target.length) {
            return false;
        }
        for (uint i = 0; i <= inputBytes.length - target.length; i++) {
            bool found = true;
            for (uint j = 0; j < target.length; j++) {
                if (inputBytes[i + j] != target[j]) {
                    found = false;
                    break;
                }
            }
            if (found) {
                return true;
            }
        }
        return false;
    }

    function compareStrings(string memory a, string memory b) private pure returns (bool) {
        return (keccak256(abi.encodePacked((a))) == keccak256(abi.encodePacked((b))));
    }

    function makeObservation(string memory response) public pure returns (string memory) {
        return string(abi.encodePacked("Observation: ", response));
    }
}