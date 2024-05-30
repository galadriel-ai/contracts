import {loadFixture,} from "@nomicfoundation/hardhat-toolbox/network-helpers";
import {expect} from "chai";
import {ethers} from "hardhat";
import {Contract} from "ethers";
import {HardhatEthersSigner} from "@nomicfoundation/hardhat-ethers/signers";

// These tests only work for chat contracts (default chat, OpenAI, Groq or OpenAi vision, or any similar custom chat contract)
// Might need to configure the constructor arguments with parameters and/or extra logic
//   and modify the "startChat" function to have the correct name and parameters and extra logic
//   the "addUserMessage" should be modified if your contract has any custom logic/parameters for adding user messages
// search for "CONFIGURATION" to find the relevant parts to modify

// CONFIGURATION: modify this value to match your contract name
const contractName: string = "OpenAiChatGpt"

// Any custom logic your contract constructor requires, eg some addresses
async function deployContract(
  contract: Contract | any,
  oracle: Contract | any,
  allSigners: HardhatEthersSigner[]
): Promise<Contract | null> {
  /*
  CONFIGURATION: modify these values to match your contract
  const constructorArgs = [...constructorArgsPrefixes, oracle.target, ...constructorArgsSuffixes]
  * oracle.target = the address of the oracle contract that needs to be whitelisted in most cases aka ´initialOracleAddress´
  * constructorArgsPrefixes = any extra parameters that need to be added before the oracle address
  * constructorArgsSuffixes = any extra parameters that need to be added after the oracle address

  For example:
  constructor(address initialOracleAddress, address someAddress)
  -> constructorArgsPrefixes = []
  -> constructorArgsSuffixes = ["0xsomeAddress"] or [allSigners[0]]

  For contractName use either "ChatGpt", "OpenAiChatGpt", "GroqChatGpt", "OpenAiChatGptVision" or your own Chat contract
  */
  const constructorArgsPrefixes: any[] = []
  const constructorArgsSuffixes: any[] = []

  const constructorArgs = [...constructorArgsPrefixes, oracle.target, ...constructorArgsSuffixes]
  try {
    return await contract.deploy(...constructorArgs);
  } catch (e) {
    throw Error(`Failed to deploy contract, please ensure the constructor parameters are correct: [${constructorArgs}]`)
  }
}

// Start chat function overwrite
async function startChat(contract: Contract | any, allSigners: HardhatEthersSigner[], message: string) {
  /*
  CONFIGURATION: modify these values to match your contract

  For example:
  function myFunctionForStart(address someAddress, string memory message, address someAddress2) public returns (uint i)
  -> startChatFunctionName = "myFunctionForStart"
  -> startChatArgsPrefixes = ["0xSomeAddress"] or [allSigners[0]]
  -> startChatArgsSuffixes = ["0xSomeAddress2"] or [allSigners[1]]
   */
  const startChatFunctionName = "startChat"
  const startChatArgsPrefixes: any[] = []
  const startChatArgsSuffixes: any[] = []

  const args = [...startChatArgsPrefixes, message, ...startChatArgsSuffixes]

  let error: any | null = null
  try {
    await contract.connect(allSigners[0])[startChatFunctionName](...args);
  } catch (e) {
    error = e
  }
  expect(error).to.equal(
    null,
    `Failed to call "${startChatFunctionName}" with args: "${args}, ensure this method is called correctly, or update it accordingly.`
  )
}

async function addUserMessage(chatGpt: Contract | any, message: string, runId: number, allSigners: HardhatEthersSigner[]) {
  /* CONFIGURE: modify these values to match your contract

  For example:
  function addMessage123(address someAddress, string memory message, uint256 runId) public onlyManager
  -> addMessageFunctionName = "addMessage123"
  -> addMessageArgsPrefixes = ["0xSomeAddress"] or [allSigners[0]]
  -> addMessageArgsSuffixes = [runId]
  */
  const addMessageFunctionName = "addMessage"
  const addMessageArgsPrefixes: any[] = []
  const addMessageArgsSuffixes: any[] = [runId]
  const args = [...addMessageArgsPrefixes, message, ...addMessageArgsSuffixes]
  let error = null
  try {
    await chatGpt.connect(allSigners[0])[addMessageFunctionName](...args);
  } catch (e) {
    error = e
  }
  expect(error).to.equal(
    null,
    `Failed to add a user message with args: "${args}", check the implementation and update it accordingly\n`
  )
}

// Tests! Should not require any changes

interface Message {
  message: string
  role: string
}

async function getMessages(
  oracle: Contract | any,
  promptId: number,
  promptCallbackId: number
): Promise<Message[]> {
  const messages: Message[] = []
  let contents: string[] = []
  let roles: string[] = []
  try {
    contents = await oracle.getMessages(promptId, promptCallbackId)
    roles = await oracle.getRoles(promptId, promptCallbackId)
    contents.map((c: string, i: number) => {
      messages.push({message: c, role: roles[i]})
    })
  } catch (e) {
  }
  if (!messages.length) {
    try {
      const newMessages = await oracle.getMessagesAndRoles(promptId, promptCallbackId)
      newMessages.forEach((m: any) => {
        messages.push({
          message: m.content[0][1],
          role: m.role,
        })
      })
    } catch (e) {
    }
  }
  expect(messages).length.above(0)
  return messages
}

async function addOracleResponse(
  oracle: Contract | any,
  oracleAccount: HardhatEthersSigner,
  response: string,
  promptId: number,
  promptCallbackId: number
) {
  let error = null
  try {
    await oracle.connect(oracleAccount).addResponse(promptId, promptCallbackId, response, "");
  } catch (e) {
    error = e
  }
  if (error) {
    try {
      const openAiResponse = {
        id: "responseId",
        content: response,
        functionName: "",
        functionArguments: "",
        created: 1618888901, // Example UNIX timestamp
        model: "gpt-4-turbo-preview",
        systemFingerprint: "systemFingerprintHere",
        object: "chat.completion",
        completionTokens: 10,
        promptTokens: 5,
        totalTokens: 15
      };
      await oracle.connect(oracleAccount).addOpenAiResponse(promptId, promptCallbackId, openAiResponse, "");
      error = null
    } catch (e) {
      error = e
    }
  }
  if (error) {
    try {
      const groqResponse = {
        id: "responseId",
        content: response,
        functionName: "functionNameHere",
        functionArguments: "functionArgumentsHere",
        created: 1618888901, // Example UNIX timestamp
        model: "mixtral-8x7b-32768",
        systemFingerprint: "systemFingerprintHere",
        object: "chat.completion",
        completionTokens: 10,
        promptTokens: 5,
        totalTokens: 15
      };
      await oracle.connect(oracleAccount).addGroqResponse(promptId, promptCallbackId, groqResponse, "");
      error = null
    } catch (e) {
      error = e
    }
  }

  // TODO: message text
  expect(error).to.equal(
    null,
    `Oracle failed to add response, make sure your contract implements the relevant interfaces\n
    https://docs.galadriel.com/reference/overview\n`
  )
}

describe("Contract", function () {
  async function deploy() {
    // Contracts are deployed using the first signer/account by default
    const allSigners = await ethers.getSigners();
    const owner = allSigners[0];

    const Oracle = await ethers.getContractFactory("ChatOracle");
    const oracle = await Oracle.deploy();

    const ChatGpt = await ethers.getContractFactory(contractName);

    const contract = await deployContract(ChatGpt, oracle, allSigners)
    return {chatGpt: contract, oracle, owner, allSigners};
  }

  describe("Basic usage", function () {
    it("Can start chat", async () => {
      const {chatGpt, oracle, allSigners} = await loadFixture(deploy);

      const message = "Hello"
      await startChat(chatGpt, allSigners, message);
      const messages = await getMessages(oracle, 0, 0);
      expect(messages.length).to.above(0)
      expect(messages[0].message).to.not.equal(null, `Expected the first message from the "getMessages" function not to be null`)
    });
    it("Oracle can add response", async () => {
      const {
        chatGpt,
        oracle,
        owner,
        allSigners
      } = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      const promptId: number = 0
      const promptCallbackId: number = 0
      await startChat(chatGpt, allSigners, "Hello");
      await addOracleResponse(oracle, oracleAccount, "Hi", promptId, promptCallbackId);
      const messages = await getMessages(oracle, promptId, promptCallbackId);
      expect(messages.length).to.above(1, "Expected message history to contain at least 2 messages")
      expect(messages[messages.length - 1].message).to.equal("Hi", "Expected the last message to be equal to the last message sent in")
    });
    it("User can add message", async () => {
      const {
        chatGpt,
        oracle,
        owner,
        allSigners
      } = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      const promptId: number = 0
      const promptCallbackId: number = 0
      await startChat(chatGpt, allSigners, "Hello");
      await addOracleResponse(oracle, oracleAccount, "Hi", promptId, promptCallbackId);

      await addUserMessage(chatGpt, "message", promptId, allSigners);

      const messages = await getMessages(oracle, promptId, promptCallbackId)
      expect(messages.length).to.be.above(2)
      expect(messages[messages.length - 1].message).to.equal("message")
    });
    it("Can have a chat", async () => {
      const {
        chatGpt,
        oracle,
        allSigners
      } = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      let promptId = 0;
      const promptCallbackId: number = 0
      await startChat(chatGpt, allSigners, "Hello");
      const chatIterationsCount: number = 50
      for (let i = 0; i < chatIterationsCount; i++) {
        await addOracleResponse(oracle, oracleAccount, `Hi-${i}`, i, promptCallbackId);
        await addUserMessage(chatGpt, `message-${i}`, promptId, allSigners);
      }

      const messages = await getMessages(oracle, promptId, promptCallbackId)
      expect(messages.length).to.above(
        100,
        "Expecting history to have at least 100 messages after starting chat and then simulating 50 responses and new messages"
      )
      expect(messages[messages.length - 1].message).to.equal(`message-${chatIterationsCount - 1}`)
    });
  });
  describe("Error handling", function () {
    it("User cannot start chat and add another message", async () => {
      const {chatGpt, oracle, allSigners} = await loadFixture(deploy);

      await startChat(chatGpt, allSigners, "Hello")
      let error = null
      try {
        await addUserMessage(chatGpt, `message`, 0, allSigners)
      } catch (e) {
        error = e
      }
      expect(error).to.not.be.equal(null, "Expecting add message to fail if called multiple times in a row")
    });
    it("Oracle cannot add 2 responses", async () => {
      const {
        chatGpt,
        oracle,
        allSigners,
        owner
      } = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await oracle.updateWhitelist(oracleAccount, true);

      await startChat(chatGpt, allSigners, "Message1")
      await addOracleResponse(oracle, oracleAccount, "Hi", 0, 0)

      let isErrored = false
      try {
        await addOracleResponse(oracle, oracleAccount, "Hi", 0, 0)
      } catch (e) {
        isErrored = true
      }
      expect(isErrored).to.equal(true, "Oracle should not be able to send 2 responses in a row")
    });

  })
});