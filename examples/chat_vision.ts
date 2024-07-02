import {Contract, ethers, TransactionReceipt, Wallet} from "ethers";
import ABI from "./abis/ChatGptVision.json";
import * as readline from 'readline';

require("dotenv").config()

interface Message {
  role: string,
  content: string,
}

async function main() {
  const rpcUrl = process.env.RPC_URL
  if (!rpcUrl) throw Error("Missing RPC_URL in .env")
  const privateKey = process.env.PRIVATE_KEY
  if (!privateKey) throw Error("Missing PRIVATE_KEY in .env")
  const contractAddress = process.env.CHAT_VISION_CONTRACT_ADDRESS
  if (!contractAddress) throw Error("Missing CHAT_VISION_CONTRACT_ADDRESS in .env")

  const provider = new ethers.JsonRpcProvider(rpcUrl)
  const wallet = new Wallet(
    privateKey, provider
  )
  const contract = new Contract(contractAddress, ABI, wallet)

  // The message you want to start the chat with
  let imageUrls = [];
  while (true) {
      const imageUrl = await getUserInput("Paste the URL of an image (or leave blank to proceed to the question): ");
      if (imageUrl === "") {
          break;
      }
      imageUrls.push(imageUrl);
  }
  const message = await getUserInput("Question: ");

  // Call the startChat function
  const transactionResponse = await contract.startChat(message, imageUrls)
  const receipt = await transactionResponse.wait()
  console.log(`Message sent, tx hash: ${receipt.hash}`)
  console.log(`Chat started with message: "${message}"`)

  // Get the chat ID from transaction receipt logs
  let chatId = getChatId(receipt, contract);
  console.log(`Created chat ID: ${chatId}`)
  if (!chatId && chatId !== 0) {
    return
  }

  let allMessages: Message[] = []
  // Run the chat loop: read messages and send messages
  while (true) {
    const newMessages: Message[] = await getNewMessages(contract, chatId, allMessages.length);
    if (newMessages) {
      for (let message of newMessages) {
        console.log(`${message.role}: ${message.content}`)
        allMessages.push(message)
        if (allMessages.at(-1)?.role == "assistant") {
          const message = getUserInput("Question: ")
          const transactionResponse = await contract.addMessage(message, chatId)
          const receipt = await transactionResponse.wait()
          console.log(`Message sent, tx hash: ${receipt.hash}`)
        }
      }
    }
    await new Promise(resolve => setTimeout(resolve, 2000))
  }

}

async function getUserInput(prompt: string): Promise<string | undefined> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  })

  const question = (query: string): Promise<string> => {
    return new Promise((resolve) => {
      rl.question(query, (answer) => {
        resolve(answer)
      })
    })
  }

  try {
    const input = await question(prompt)
    rl.close()
    return input
  } catch (err) {
    console.error('Error getting user input:', err)
    rl.close()
  }
}


function getChatId(receipt: TransactionReceipt, contract: Contract) {
  let chatId
  for (const log of receipt.logs) {
    try {
      const parsedLog = contract.interface.parseLog(log)
      if (parsedLog && parsedLog.name === "ChatCreated") {
        // Second event argument
        chatId = ethers.toNumber(parsedLog.args[1])
      }
    } catch (error) {
      // This log might not have been from your contract, or it might be an anonymous log
      console.log("Could not parse log:", log)
    }
  }
  return chatId;
}

async function getNewMessages(
  contract: Contract,
  chatId: number,
  currentMessagesCount: number
): Promise<Message[]> {
  const messages = await contract.getMessageHistory(chatId)

  const newMessages: Message[] = []
  messages.forEach((message: any, i: number) => {
    if (i >= currentMessagesCount) {
      newMessages.push(
        {
          role: message.role,
          content: message.content[0].value,
        }
      );
    }
  })
  return newMessages;
}

main()
  .then(() => console.log("Done"))