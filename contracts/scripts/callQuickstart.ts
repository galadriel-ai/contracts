// Import ethers from Hardhat package
const {ethers} = require("hardhat");

async function main() {
  const contractABI = [
    "function initializeDalleCall(string memory message) public returns (uint)",
    "function lastResponse() public view returns (string)"
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
  const receipt = await transactionResponse.wait();
  console.log(`Transaction status: ${receipt.status}`)
  console.log(`Image generation started with message: "${message}"`);

  // loop and sleep by 1000ms, and keep printing `lastResponse` in the contract.
  let lastResponse = await contract.lastResponse();
  let newResponse = lastResponse;

  // print w/o newline
  console.log("Waiting for response: ");
  while (newResponse === lastResponse) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    newResponse = await contract.lastResponse();
    console.log(".");
  }

  console.log(`Response: ${newResponse}`)

}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });