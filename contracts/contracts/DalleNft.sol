// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

// Uncomment this line to use console.log
// import "hardhat/console.sol";
import {ERC721URIStorage, ERC721} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";


interface IOracle {
    function addFunctionCall(
        address runOwner,
        string memory functionType,
        string memory functionInput,
        uint functionCallbackId
    ) external returns (uint i);
}

contract DalleNft is ERC721URIStorage {
    uint256 private _nextTokenId;

    struct MintInput {
        address owner;
        string prompt;
        bool isMinted;
    }

    mapping(address => mapping(uint => MintInput)) public mintInputs;
    mapping(address => uint) private mintInputsCount;

    event MintInputCreated(address indexed owner, uint indexed chatId);

    address private owner;
    address public oracleAddress;

    string public prompt;

    event PromptUpdated(string indexed newPrompt);
    event OracleAddressUpdated(address indexed newOracleAddress);

    constructor(
        address initialOracleAddress,
        string memory initialPrompt
    ) ERC721("DALL-E", "DLE") {
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
        prompt = initialPrompt;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not owner");
        _;
    }

    modifier onlyOracle() {
        require(msg.sender == oracleAddress, "Caller is not oracle");
        _;
    }

    function setPrompt(string memory newPrompt) public onlyOwner {
        prompt = newPrompt;
        emit PromptUpdated(newPrompt);
    }

    function setOracleAddress(address newOracleAddress) public onlyOwner {
        oracleAddress = newOracleAddress;
        emit OracleAddressUpdated(newOracleAddress);
    }

    function initializeMint(string memory message) public returns (uint i) {
        uint mintsCount = mintInputsCount[msg.sender];
        MintInput storage mintInput = mintInputs[msg.sender][mintsCount];

        mintInput.owner = msg.sender;
        mintInput.prompt = message;
        mintInput.isMinted = false;

        uint currentId = mintInputsCount[msg.sender];
        mintInputsCount[msg.sender] = currentId + 1;

        string memory fullPrompt = prompt;
        fullPrompt = string.concat(fullPrompt, message);
        fullPrompt = string.concat(fullPrompt, "\"");
        IOracle(oracleAddress).addFunctionCall(
            msg.sender,
            "image_generation",
            fullPrompt,
            currentId
        );
        emit MintInputCreated(msg.sender, currentId);

        return currentId;
    }

    function addResponse(
        string memory response,
        string memory responseType,
        address chatOwner,
        uint runId
    ) public onlyOracle {
        MintInput storage mintInput = mintInputs[chatOwner][runId];
        require(!mintInput.isMinted, "NFT already minted");
        require(
            keccak256(abi.encodePacked(responseType)) == keccak256(abi.encodePacked("function_result")),
            "Expecting function_result"
        );

        mintInput.isMinted = true;

        uint256 tokenId = _nextTokenId++;
        _mint(mintInput.owner, tokenId);
        _setTokenURI(tokenId, response);
    }

    function getMessages(address _owner, uint chatId) public view returns (string[] memory) {
        string[] memory promptsArray = new string[](1);
        string memory fullPrompt = prompt;
        fullPrompt = string.concat(fullPrompt, mintInputs[owner][chatId].prompt);
        fullPrompt = string.concat(fullPrompt, "\"");
        promptsArray[0] = fullPrompt;
        return promptsArray;
    }

    function getRoles(address _owner, uint _chatId) public pure returns (string[] memory) {
        string[] memory rolesArray = new string[](1);
        rolesArray[0] = "user";
        return rolesArray;
    }
}
