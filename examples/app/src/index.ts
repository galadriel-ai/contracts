import { ethers, Contract } from "ethers";
import ChatGpt from "../../../contracts/artifacts/contracts/GroqChatGpt.sol/GroqChatGpt.json" assert { type: "json" };
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

const chatGptAbi = ChatGpt.abi;
const CHATGPT_CONTRACT_ADDRESS: string = process.env.CONTRACT_ADDRESS as string;
console.log("contract address", CHATGPT_CONTRACT_ADDRESS);

const contract = new Contract(CHATGPT_CONTRACT_ADDRESS, chatGptAbi, signer);

const ioInterface = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

const prompt = (query: string) =>
  new Promise((resolve) => ioInterface.question(query, resolve));

const ask = async (id: number) => {
  const message = await prompt("Enter message: ");
  const documentCount = await prompt("Enter number of document: ");
  const askTx = await contract.addMessage(message, documentCount, id);
};

const recieve = async (id: number) => {
  const results = await contract.getMessageHistory(id);
  console.log("Reply: ", results.slice(-1)[0][1][0][1]);
};

const message = await prompt("Enter message: ");
const documentCount = await prompt("Enter number of document: ");
const startTx = await contract.startChat(message, documentCount);

contract.on("ChatCreated", async (_, __) => {});

contract.on("MessageAdded", async (_, __) => {});

contract.on("MessageReceived", async (_, id) => {
  await recieve(id);
  await ask(id);
});
