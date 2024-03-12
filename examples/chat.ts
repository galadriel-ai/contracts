import {Contract, ethers, Wallet} from "ethers";
import ABI from "./abis/ChatGpt.json";

require("dotenv").config()

async function main() {
  const rpcUrl = process.env.RPC_URL
  if (!rpcUrl) throw Error("Missing RPC_URL in .env")
  const privateKey = process.env.PRIVATE_KEY
  if (!privateKey) throw Error("Missing PRIVATE_KEY in .env")
  const contractAddress = process.env.CHAT_ADDRESS
  if (!contractAddress) throw Error("Missing CHAT_ADDRESS in .env")

  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const wallet = new Wallet(
    privateKey, provider
  );
  const contract = new Contract(contractAddress, ABI, wallet);

  // The message you want to start the chat with
  const message = "Say 3 dog names!";

  // Call the startChat function
  const transactionResponse = await contract.startChat(message);
  const receipt = await transactionResponse.wait();

  console.log(`Chat started with message: "${message}"`);

  // Get the chat ID from receipt logs
  let chatId
  for (const log of receipt.logs) {
    try {
      const parsedLog = contract.interface.parseLog(log)
      if (parsedLog && parsedLog.name === "ChatCreated") {
        chatId = ethers.toNumber(parsedLog.args[1])
      }
    } catch (error) {
      // This log might not have been from your contract, or it might be an anonymous log
      console.log("Could not parse log:", log);
    }
  }
  console.log(`Created chat ID: ${chatId}`)
  if (!chatId) {
    return
  }

  let chatHistory = []
  while (true) {

    const messages = await contract.getMessages(wallet.address, chatId)
    const roles = await contract.getRoles(wallet.address, chatId)
    for (let i = 0; i < messages.length; i++) {
      // Skip system prompt and first user "start" message
      if (i > 1) {
        if (roles[i] !== "user") {
          const newMessage: Message = {
            role: roles[i],
            content: messages[i]
          }
          if (images.length > imageIndex && newMessage.content.includes("[IMAGE")) {
            newMessage.imageUrl = images[imageIndex]
            imageIndex++
          }
          formattedMessages.push(newMessage)
        } else if (formattedMessages.length) {
          formattedMessages[formattedMessages.length - 1].selection = messages[i]
        }
      }
    }

    await new Promise(resolve => setTimeout(resolve, 2000))
  }

}

main()
  .then(() => console.log("Done"))