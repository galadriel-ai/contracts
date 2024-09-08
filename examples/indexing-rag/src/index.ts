import { ethers, Contract } from "ethers";
import ChatOracle from "../../../contracts/artifacts/contracts/ChatOracle.sol/ChatOracle.json" assert { type: "json" };
import dotenv from "dotenv";
import * as readline from "readline";

dotenv.config({
  path: ".env",
});

console.log("RPC URL", process.env.RPC_URL);
const provider = new ethers.JsonRpcProvider(process.env.RPC_URL);

const privateKey: string = process.env.PRIVATE_KEY as string;

console.log("private key", privateKey);
const signer = new ethers.Wallet(privateKey, provider);

const signerAddress = await signer.getAddress();
console.log("signer address", signerAddress);

const chatOracleAbi = ChatOracle.abi;
const CHATORACLE_CONTRACT_ADDRESS: string = process.env
  .CONTRACT_ADDRESS as string;
console.log("contract address", CHATORACLE_CONTRACT_ADDRESS);

const contract = new Contract(
  CHATORACLE_CONTRACT_ADDRESS,
  chatOracleAbi,
  signer
);

const ioInterface = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

const prompt = (query: string) =>
  new Promise((resolve) => ioInterface.question(query, resolve));

let continue_indexing = false;
do {
  const key = await prompt("Enter key of document to index: ");
  const startTx = await contract.addLangchainKnowledgeBase(key);

  const promptContinue = await prompt("Continue indexing? (y/n): ");
  continue_indexing = promptContinue === "y" ? true : false;
} while (continue_indexing);

contract.on("LangchainKnowledgeIndexRequestAdded", async (id, sender) => {
  console.log("Index request added", id, sender);
});

contract.on("LangchainKnowledgeBaseIndexed", async (id, key, errorMessage) => {
  console.log("file indexed added", key, errorMessage);
});
