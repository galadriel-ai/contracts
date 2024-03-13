// Import ethers from Hardhat package
const { ethers } = require("hardhat");

async function main() {
    const contractABI = [
        "function initializeDalleCall(string memory message) public returns (uint)"
    ];

    if (!process.env.QUICKSTART_CONTRACT_ADDRESS) {
        throw new Error("QUICKSTART_CONTRACT_ADDRESS env variable is not set.");
    }

    const contractAddress = process.env.QUICKSTART_CONTRACT_ADDRESS;
    const [signer] = await ethers.getSigners();

    // Create a contract instance
    const contract = new ethers.Contract(contractAddress, contractABI, signer);

    // The content of the image you want to generate
    const message = "a cat with two heads";

    // Call the startChat function
    const transactionResponse = await contract.initializeDalleCall(message);
    await transactionResponse.wait();

    console.log(`Image generation started with message: "${message}"`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });