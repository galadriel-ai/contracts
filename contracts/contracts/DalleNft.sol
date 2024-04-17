// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

// Uncomment this line to use console.log
// import "hardhat/console.sol";
import {ERC721URIStorage, ERC721} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import {ERC721Enumerable} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import {IOracle} from "./interfaces/IOracle.sol";

contract DalleNft is ERC721, ERC721Enumerable, ERC721URIStorage {
    uint256 private _nextTokenId;

    struct MintInput {
        address owner;
        string prompt;
        bool isMinted;
    }

    mapping(uint => MintInput) public mintInputs;

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

    function getMessageHistoryContents(uint chatId) public view returns (string[] memory) {
        string[] memory promptsArray = new string[](1);
        string memory fullPrompt = prompt;
        fullPrompt = string.concat(fullPrompt, mintInputs[chatId].prompt);
        fullPrompt = string.concat(fullPrompt, "\"");
        promptsArray[0] = fullPrompt;
        return promptsArray;
    }

    function getRoles(address /*_owner*/, uint /*_chatId*/) public pure returns (string[] memory) {
        string[] memory rolesArray = new string[](1);
        rolesArray[0] = "user";
        return rolesArray;
    }

    function _update(address to, uint256 tokenId, address auth)
        internal
        override(ERC721, ERC721Enumerable)
        returns (address)
    {
        return super._update(to, tokenId, auth);
    }

    function _increaseBalance(address account, uint128 value)
        internal
        override(ERC721, ERC721Enumerable)
    {
        super._increaseBalance(account, value);
    }

    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721, ERC721URIStorage)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721Enumerable, ERC721URIStorage)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
