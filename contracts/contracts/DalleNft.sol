// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

// Uncomment this line to use console.log
// import "hardhat/console.sol";
import {ERC721URIStorage, ERC721} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import {ERC721Enumerable} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import {IOracle} from "./interfaces/IOracle.sol";

// @title DalleNft
// @notice This contract integrates with teeML oracle to generate and mint NFTs based on user inputs.
contract DalleNft is ERC721, ERC721Enumerable, ERC721URIStorage {
    uint256 private _nextTokenId;

    struct MintInput {
        address owner;
        string prompt;
        bool isMinted;
    }

    // @notice Mapping from token ID to mint input data
    mapping(uint => MintInput) public mintInputs;

    // @notice Event emitted when a new mint input is created
    event MintInputCreated(address indexed owner, uint indexed chatId);

    // @notice Address of the contract owner
    address private owner;

    // @notice Address of the oracle contract
    address public oracleAddress;

    // @notice Prompt used for generating the NFTs
    string public prompt;

    // @notice Event emitted when the prompt is updated
    event PromptUpdated(string indexed newPrompt);

    // @notice Event emitted when the oracle address is updated
    event OracleAddressUpdated(address indexed newOracleAddress);

    // @param initialOracleAddress Initial address of the oracle contract
    // @param initialPrompt Initial prompt for generating the NFTs
    constructor(
        address initialOracleAddress,
        string memory initialPrompt
    ) ERC721("DALL-E", "DLE") {
        owner = msg.sender;
        oracleAddress = initialOracleAddress;
        prompt = initialPrompt;
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

    // @notice Updates the prompt used for generating the NFTs
    // @param newPrompt The new prompt to set
    function setPrompt(string memory newPrompt) public onlyOwner {
        prompt = newPrompt;
        emit PromptUpdated(newPrompt);
    }

    // @notice Updates the oracle address
    // @param newOracleAddress The new oracle address to set
    function setOracleAddress(address newOracleAddress) public onlyOwner {
        oracleAddress = newOracleAddress;
        emit OracleAddressUpdated(newOracleAddress);
    }

    // @notice Initializes the minting process for a new NFT
    // @param message The user input to generate the NFT
    // @return The ID of the created mint input
    function initializeMint(string memory message) public returns (uint) {
        uint256 currentId = _nextTokenId++;
        MintInput storage mintInput = mintInputs[currentId];

        mintInput.owner = msg.sender;
        mintInput.prompt = message;

        mintInput.isMinted = false;


        string memory fullPrompt = prompt;
        fullPrompt = string.concat(fullPrompt, message);
        fullPrompt = string.concat(fullPrompt, "\"");
        IOracle(oracleAddress).createFunctionCall(
            currentId,
            "image_generation",
            fullPrompt
        );
        emit MintInputCreated(msg.sender, currentId);

        return currentId;
    }

    // @notice Handles the response from the oracle for the function call
    // @param runId The ID of the mint input
    // @param response The response from the oracle (token URI)
    // @dev Called by teeML oracle
    function onOracleFunctionResponse(
        uint runId,
        string memory response,
        string memory /*errorMessage*/
    ) public onlyOracle {
        MintInput storage mintInput = mintInputs[runId];
        require(!mintInput.isMinted, "NFT already minted");

        mintInput.isMinted = true;

        _mint(mintInput.owner, runId);
        _setTokenURI(runId, response);
    }

    // @notice Retrieves the message history contents for a given chat ID
    // @param chatId The ID of the chat
    // @return An array of message contents
    // @dev Called by teeML oracle
    function getMessageHistoryContents(uint chatId) public view returns (string[] memory) {
        string[] memory promptsArray = new string[](1);
        string memory fullPrompt = prompt;
        fullPrompt = string.concat(fullPrompt, mintInputs[chatId].prompt);
        fullPrompt = string.concat(fullPrompt, "\"");
        promptsArray[0] = fullPrompt;
        return promptsArray;
    }

    // @notice Retrieves the roles for a given chat
    // @return An array with a single role "user"
    // @dev Called by teeML oracle
    function getRoles(address /*_owner*/, uint /*_chatId*/) public pure returns (string[] memory) {
        string[] memory rolesArray = new string[](1);
        rolesArray[0] = "user";
        return rolesArray;
    }

    // @notice Updates internal state when a token is transferred
    function _update(address to, uint256 tokenId, address auth)
        internal
        override(ERC721, ERC721Enumerable)
        returns (address)
    {
        return super._update(to, tokenId, auth);
    }

    // @notice Increases the balance of an account
    function _increaseBalance(address account, uint128 value)
        internal
        override(ERC721, ERC721Enumerable)
    {
        super._increaseBalance(account, value);
    }

    // @notice Retrieves the token URI for a given token ID
    // @param tokenId The ID of the token
    // @return The token URI
    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    // @notice Checks if the contract supports a given interface
    // @param interfaceId The interface ID to check
    // @return True if the interface is supported, false otherwise
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721Enumerable, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
