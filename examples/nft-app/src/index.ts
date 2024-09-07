import { ethers, Contract } from "ethers";
import DalleImageGenerator from "../../../contracts/artifacts/contracts/DalleImageGenerator.sol/DalleImageGenerator.json" assert { type: "json" };
import dotenv from "dotenv";

dotenv.config({
  path: ".env",
});

console.log("RPC URL", process.env.RPC_URL);
const provider = new ethers.JsonRpcProvider(
  process.env.RPC_URL as string,
  undefined,
  {
    polling: true,
    pollingInterval: 2000,
  }
);

const privateKey: string = process.env.PRIVATE_KEY as string;

console.log("private key", privateKey);
const signer = new ethers.Wallet(privateKey, provider);

const signerAddress = await signer.getAddress();
console.log("signer address", signerAddress);

const DalleImageGeneratorAbi = DalleImageGenerator.abi;
const DALLE_CONTRACT_ADDRESS: string = process.env.CONTRACT_ADDRESS as string;
console.log("contract address", DALLE_CONTRACT_ADDRESS);

const contract = new Contract(
  DALLE_CONTRACT_ADDRESS,
  DalleImageGeneratorAbi,
  signer
);

const promptTx = await contract.addPrompt("A cat on an airplan");
const tx = await promptTx.wait();
console.log("tx reciept", tx);

contract.once("PromptAdded", (promptId: number) => {
  console.log("PromptAdded", promptId);
});

contract.once("PromptReplied", async (promptId: number) => {
  console.log("PromptReplied", promptId);
  const image = await contract.getImage(0);
  console.log("image", image);
});
