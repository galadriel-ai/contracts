// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.9;

// Uncomment this line to use console.log
// import "hardhat/console.sol";

interface IOracle {
    function addPrompt(string memory prompt, uint promptId) external returns (uint);
}

contract Agent {

    struct AgentRun {
        address owner;
        string[] prompts;
        string[] responses;
        uint responsesCount;
        uint8 max_iterations;
        bool is_finished;
    }

    mapping(uint => AgentRun) public agentRuns;
    uint private agentRunCount;

    event AgentRunCreated(uint indexed runId);

    address private owner;
    address public oracleAddress;

    event OracleAddressUpdated(address indexed newOracleAddress);

    constructor(address initialOracleAddress) {
        agentRunCount = 0;
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
    }

    function setOracleAddress(address newOracleAddress) public {
        require(msg.sender == owner, "Caller is not the owner");
        oracleAddress = newOracleAddress;
        emit OracleAddressUpdated(newOracleAddress);
    }

    function runAgent(string memory prompt, uint8 max_iterations) public returns (uint i) {
        AgentRun storage run = agentRuns[agentRunCount];

        run.owner = msg.sender;
        run.is_finished = false;
        run.responsesCount = 0;
        run.max_iterations = max_iterations;
        run.prompts.push(prompt);

        uint currentId = agentRunCount;
        agentRunCount++;

        IOracle(oracleAddress).addPrompt(prompt, currentId);
        emit AgentRunCreated(currentId);

        return currentId;
    }

    function addResponse(string memory response, uint promptId) public {
        require(msg.sender == oracleAddress, "Caller is not oracle");
        require(agentRuns[promptId].is_finished == false, "Run is already finished");

        agentRuns[promptId].responses.push(response);
        agentRuns[promptId].responsesCount++;

        // TODO: some actual prompting logic for next request etc
        uint currentIndex = agentRuns[promptId].responsesCount;
        string memory newPrompt = string.concat(agentRuns[promptId].prompts[currentIndex - 1]);
        newPrompt = string.concat(newPrompt, response);
        if (agentRuns[promptId].responsesCount >= agentRuns[promptId].max_iterations) {
            agentRuns[promptId].prompts.push(newPrompt);
            agentRuns[promptId].is_finished = true;
        } else {
            newPrompt = string.concat(newPrompt, "\nUser: Please elaborate!");
            newPrompt = string.concat(newPrompt, "\nAssistant: ");
            agentRuns[promptId].prompts.push(newPrompt);
            IOracle(oracleAddress).addPrompt(newPrompt, promptId);
        }
    }

    function getPrompts(uint agentRunId) public view returns (string[] memory) {
        return agentRuns[agentRunId].prompts;
    }

    function getResponses(uint agentRunId) public view returns (string[] memory) {
        return agentRuns[agentRunId].responses;
    }
}
