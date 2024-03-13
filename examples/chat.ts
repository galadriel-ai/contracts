import {Contract, ethers, Wallet} from "ethers";
import ABI from "./abis/ChatGpt.json";
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
  const contractAddress = process.env.CHAT_ADDRESS
  if (!contractAddress) throw Error("Missing CHAT_ADDRESS in .env")

  const provider = new ethers.JsonRpcProvider(rpcUrl)
  const wallet = new Wallet(
    privateKey, provider
  )
  const contract = new Contract(contractAddress, ABI, wallet)

  // The message you want to start the chat with
  const message = await getUserInput()

  // Call the startChat function
  const transactionResponse = await contract.startChat(message)
  const receipt = await transactionResponse.wait()
  console.log(`Message sent, tx hash: ${receipt.hash}`)

  console.log(`Chat started with message: "${message}"`)

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
      console.log("Could not parse log:", log)
    }
  }
  console.log(`Created chat ID: ${chatId}`)
  if (!chatId && chatId !== 0) {
    return
  }

  let allMessages: Message[] = []
  while (true) {
    const messages = await contract.getMessageHistoryContents(wallet.address, chatId)
    const roles = await contract.getMessageHistoryRoles(wallet.address, chatId)

    const newMessages: Message[] = []
    messages.forEach((message: any, i: number) => {
      if (i >= allMessages.length) {
        newMessages.push({
          role: roles[i],
          content: messages[i]
        })
      }
    })
    if (newMessages) {
      for (let message of newMessages) {
        console.log(`${message.role}: ${message.content}`)
        allMessages.push(message)
        if (allMessages.at(-1)?.role == "assistant") {
          const message = getUserInput()
          const transactionResponse = await contract.startChat(message)
          const receipt = await transactionResponse.wait()
          console.log(`Message sent, tx hash: ${receipt.hash}`)
        }
      }
    }
    await new Promise(resolve => setTimeout(resolve, 2000))
  }

}

async function getUserInput(): Promise<string | undefined> {
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
    const input = await question("Message ChatGPT: ")
    rl.close()
    return input
  } catch (err) {
    console.error('Error getting user input:', err)
    rl.close()
  }
}

main()
  .then(() => console.log("Done"))