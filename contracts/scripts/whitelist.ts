// Import ethers from Hardhat package
const { ethers } = require("hardhat");

async function main() {
    const contractABI = [
        "function updateWhitelist(address _addressToWhitelist, bool isWhitelisted)"
    ];
    const contractAddress = "0x0165878A594ca255338adfa4d48449f69242Eb8F";
    const [signer] = await ethers.getSigners();

    // Create a contract instance
    const contract = new ethers.Contract(contractAddress, contractABI, signer);

    // Call the updateWhitelist function
    const transactionResponse = await contract.updateWhitelist(signer, true);
    await transactionResponse.wait();

    console.log(`Address whitelisted: "${signer}"`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });