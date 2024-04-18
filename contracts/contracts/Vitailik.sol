// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.9;

// Uncomment this line to use console.log
// import "hardhat/console.sol";
import "./interfaces/IOracle.sol";

contract Vitailik {

    string public prompt;

    struct Message {
        string role;
        string content;
    }

    struct Game {
        address player;
        uint messagesCount;
        Message[] messages;
        string[] imageUrls;
        uint imagesCount;
        bool isFinished;
    }

    mapping(uint => Game) public games;
    uint private gamesCount;

    event GameCreated(address indexed owner, uint indexed gameId);

    address private owner;
    address public oracleAddress;

    IOracle.GroqRequest private config;

    event OracleAddressUpdated(address indexed newOracleAddress);

    constructor(
        address initialOracleAddress,
        string memory initialPrompt
    ) {
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
        prompt = initialPrompt;
        gamesCount = 0;

        config = IOracle.GroqRequest({
        model : "mixtral-8x7b-32768",
        frequencyPenalty : 21, // > 20 for null
        logitBias : "", // empty str for null
        maxTokens : 1000, // 0 for null
        presencePenalty : 21, // > 20 for null
        responseFormat : "",
        seed : 0, // null
        stop : "", // null
        temperature : 21, // Example temperature (scaled up, 10 means 1.0), > 20 means null
        topP : 101, // Percentage 0-100, > 100 means null
        user : "" // null
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

    function setOracleAddress(address newOracleAddress) public onlyOwner {
        oracleAddress = newOracleAddress;
        emit OracleAddressUpdated(newOracleAddress);
    }

    function startGame() public returns (uint i) {
        Game storage game = games[gamesCount];

        game.player = msg.sender;

        Message memory systemMessage;
        systemMessage.content = prompt;
        systemMessage.role = "system";
        game.messages.push(systemMessage);
        game.messagesCount++;

        Message memory userMessage;
        userMessage.content = "Start now!";
        userMessage.role = "user";
        game.messages.push(userMessage);
        game.messagesCount++;

        Message memory assistantMessage;
        assistantMessage.content = "I'll first describe the scene and then give 4 options (a,b,c,d) for player to choose what character to play as. I'll come up with animals to select from, and add 2 adjectives to combine as the character name. I'll keep it short. I'll structure it as following:\n\n<short scene description>\n\n<4 character choices>\n\n<image description>\n\n<HPs>";
        assistantMessage.role = "assistant";
        game.messages.push(assistantMessage);
        game.messagesCount++;

        uint currentId = gamesCount;
        gamesCount = currentId + 1;

        IOracle(oracleAddress).createGroqLlmCall(currentId, config);
        emit GameCreated(msg.sender, currentId);

        return currentId;
    }


    function onOracleFunctionResponse(
        uint runId,
        string memory response,
        string memory errorMessage
    ) public onlyOracle {
        Game storage game = games[runId];
        require(
            !game.isFinished, "Game is finished"
        );
        if (!compareStrings(errorMessage, "")) {
            game.imageUrls.push("error");
        } else {
            game.imageUrls.push(response);
        }
        game.imagesCount++;
    }

    function onOracleGroqLlmResponse(
        uint runId,
        IOracle.GroqResponse memory response,
        string memory /*errorMessage*/
    ) public onlyOracle {
        Game storage game = games[runId];
        require(
            !game.isFinished, "Game is finished"
        );
        require(
            compareStrings(game.messages[game.messagesCount - 1].role, "user") || game.messagesCount == 3,
            "No message to respond to"
        );

        Message memory assistantMessage;
        assistantMessage.content = response.content;
        assistantMessage.role = "assistant";
        game.messages.push(assistantMessage);
        game.messagesCount++;

        string[2] memory hpValues = findHPInstances(response.content);

        if (compareStrings(hpValues[0], "0") || compareStrings(hpValues[1], "0")) {
            game.isFinished = true;
        }

        string memory imageDescription = findImageLine(response.content);
        if (!compareStrings(imageDescription, "")) {
            IOracle(oracleAddress).createFunctionCall(
                runId,
                "image_generation",
                imageDescription
            );
        }
    }

    function addSelection(uint8 selection, uint gameId) public {
        Game storage game = games[gameId];
        require(selection <= 3, "Selection needs to be 0-3");
        require(
            !game.isFinished, "Game is finished"
        );
        require(
            compareStrings(game.messages[game.messagesCount - 1].role, "assistant"),
            "No message to respond to"
        );

        Message memory userMessage;
        userMessage.role = "user";
        if (selection == 0) {
            userMessage.content = "A";
        } else if (selection == 1) {
            userMessage.content = "B";
        } else if (selection == 2) {
            userMessage.content = "C";
        } else if (selection == 3) {
            userMessage.content = "D";
        }
        game.messages.push(userMessage);
        game.messagesCount++;

        IOracle(oracleAddress).createGroqLlmCall(gameId, config);
    }

    function getSystemPrompt() public view returns (string memory) {
        return prompt;
    }

    function getMessageHistoryContents(uint chatId) public view returns (string[] memory) {
        string[] memory messages = new string[](games[chatId].messages.length);
        for (uint i = 0; i < games[chatId].messages.length; i++) {
            messages[i] = games[chatId].messages[i].content;
        }
        return messages;
    }

    function getMessageHistoryRoles(uint chatId) public view returns (string[] memory) {
        string[] memory roles = new string[](games[chatId].messages.length);
        for (uint i = 0; i < games[chatId].messages.length; i++) {
            roles[i] = games[chatId].messages[i].role;
        }
        return roles;
    }

    function getImages(uint chatId) public view returns (string[] memory) {
        return games[chatId].imageUrls;
    }

    function findImageLine(string memory input) public pure returns (string memory) {
        bytes memory inputBytes = bytes(input);
        bytes memory imagePrefix1 = bytes("<IMAGE");
        bytes memory imagePrefix2 = bytes("[IMAGE");
        uint prefixLength1 = imagePrefix1.length;
        uint prefixLength2 = imagePrefix2.length;

        bool found = false;
        uint startIndex = 0;

        for (uint i = 0; i <= inputBytes.length - prefixLength1; i++) {
            bool isMatch1 = true;
            bool isMatch2 = true;

            for (uint j = 0; j < prefixLength1 && (isMatch1 || isMatch2); j++) {
                if (i + j < inputBytes.length) {// Prevent out-of-bounds access
                    if (isMatch1 && inputBytes[i + j] != imagePrefix1[j]) {
                        isMatch1 = false;
                    }
                    if (j < prefixLength2 && isMatch2 && inputBytes[i + j] != imagePrefix2[j]) {
                        isMatch2 = false;
                    }
                } else {
                    // If the current index goes beyond the inputBytes length, no match is possible
                    isMatch1 = false;
                    isMatch2 = false;
                }
            }

            if (isMatch1 || isMatch2) {
                found = true;
                startIndex = i;
                break;
            }
        }

        if (!found) {
            return "";
        }

        // Find the end of the line
        uint endIndex = startIndex;
        for (uint i = startIndex; i < inputBytes.length; i++) {
            if (inputBytes[i] == '\n' || inputBytes[i] == '\r') {
                endIndex = i;
                break;
            }
        }

        bytes memory line = new bytes(endIndex - startIndex);
        for (uint i = startIndex; i < endIndex; i++) {
            line[i - startIndex] = inputBytes[i];
        }

        return string(line);
    }


    function findHPInstances(string memory input) public pure returns (string[2] memory) {
        bytes memory inputBytes = bytes(input);
        string[2] memory hpValues;
        uint hpCount = 0;

        for (uint i = 0; i < inputBytes.length; i++) {
            // Look for "HP: " pattern
            if (inputBytes[i] == 'H' && i + 4 < inputBytes.length && inputBytes[i + 1] == 'P' && inputBytes[i + 2] == ':' && inputBytes[i + 3] == ' ') {
                uint startIndex = i + 4;
                // Start of the number
                uint endIndex = startIndex;

                // Find the end of the number
                while (endIndex < inputBytes.length && ((inputBytes[endIndex] >= '0' && inputBytes[endIndex] <= '9') || inputBytes[endIndex] == ',')) {
                    endIndex++;
                }

                // Extract the number
                bytes memory hpValue = new bytes(endIndex - startIndex);
                for (uint j = startIndex; j < endIndex; j++) {
                    hpValue[j - startIndex] = inputBytes[j];
                }

                // Store the extracted number
                hpValues[hpCount] = string(hpValue);
                hpCount++;

                // Move the index past this number
                i = endIndex;

                // Check if we've found two instances
                if (hpCount >= 2) {
                    break;
                }
            }
        }

        return hpValues;
    }

    function compareStrings(string memory a, string memory b) private pure returns (bool) {
        return (keccak256(abi.encodePacked((a))) == keccak256(abi.encodePacked((b))));
    }
}
