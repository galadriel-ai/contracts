// Import ethers from Hardhat package
const { ethers } = require("hardhat");

async function main() {
    const contractABI = [
        "function startChat(string memory message) public returns (uint)"
    ];
    const contractAddress = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";
    const [signer] = await ethers.getSigners();

    // Create a contract instance
    const contract = new ethers.Contract(contractAddress, contractABI, signer);

    // The message you want to start the chat with
    const message = "Say 3 dog names!";

    // Call the startChat function
    const transactionResponse = await contract.startChat(message);
    await transactionResponse.wait();

    console.log(`Chat started with message: "${message}"`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });