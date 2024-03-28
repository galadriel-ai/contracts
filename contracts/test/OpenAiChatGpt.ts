import {loadFixture,} from "@nomicfoundation/hardhat-toolbox/network-helpers";
import {expect} from "chai";
import {ethers} from "hardhat";

describe("OpenAiChatGpt", function () {
  // We define a fixture to reuse the same setup in every test.
  // We use loadFixture to run this setup once, snapshot that state,
  // and reset Hardhat Network to that snapshot in every test.
  async function deploy() {
    // Contracts are deployed using the first signer/account by default
    const allSigners = await ethers.getSigners();
    const owner = allSigners[0];

    const Oracle = await ethers.getContractFactory("ChatOracle");
    const oracle = await Oracle.deploy();

    const ChatGpt = await ethers.getContractFactory("OpenAiChatGpt");
    const chatGpt = await ChatGpt.deploy("0x0000000000000000000000000000000000000000");

    return {chatGpt, oracle, owner, allSigners};
  }

  describe("Deployment", function () {
    it("User can start chat", async () => {
      const {chatGpt, oracle, owner} = await loadFixture(deploy);
      await chatGpt.setOracleAddress(oracle.target);

      await chatGpt.startChat("Hello");
      // promptId: 0, callbackId: 0
      const messages = await oracle.getMessages(0, 0)
      expect(messages.length).to.equal(1)
      expect(messages[0]).to.equal("Hello")
    });
    it("Configuration gets sent to oracle", async () => {
      const {chatGpt, oracle, owner} = await loadFixture(deploy);
      await chatGpt.setOracleAddress(oracle.target);

      await chatGpt.startChat("Hello");
      // promptId: 0, callbackId: 0
      const openAiConf = await oracle.openAiConfigurations(0)
      const tools = [
        {
          "type": "function",
          "function": {
            "name": "web_search",
            "description": "Search the internet",
            "parameters": {
              "type": "object",
              "properties": {
                "query": {
                  "type": "string",
                  "description": "Search query"
                }
              },
              "required": [
                "query"
              ]
            }
          }
        },
        {
          "type": "function",
          "function": {
            "name": "code_interpreter",
            "description": "Evaluates python code in a sandbox environment. The environment resets on every execution. You must send the whole script every time and print your outputs. Script should be pure python code that can be evaluated. It should be in python format NOT markdown. The code should NOT be wrapped in backticks. All python packages including requests, matplotlib, scipy, numpy, pandas, etc are available. Output can only be read from stdout, and stdin. Do not use things like plot.show() as it will not work. print() any output and results so you can capture the output.",
            "parameters": {
              "type": "object",
              "properties": {
                "code": {
                  "type": "string",
                  "description": "The pure python script to be evaluated. The contents will be in main.py. It should not be in markdown format."
                }
              },
              "required": [
                "code"
              ]
            }
          }
        }
      ];
      expect(openAiConf.toString()).to.equal(`gpt-4-turbo-preview,21,,1000,21,{\"type\":\"text\"},0,,10,101,${JSON.stringify(tools)},auto,`);
    });
    it("Oracle can add response", async () => {
      const {chatGpt, oracle, allSigners} = await loadFixture(deploy);
      const oracleAccount = allSigners[6];
      await chatGpt.setOracleAddress(oracle.target);
      await oracle.updateWhitelist(oracleAccount, true);

      await chatGpt.startChat("Hello");

      const response = {
        id: "responseId",
        content: "Hi!",
        functionName: "functionNameHere",
        functionArguments: "functionArgumentsHere",
        created: 1618888901, // Example UNIX timestamp
        model: "gpt-4-turbo-preview",
        systemFingerprint: "systemFingerprintHere",
        object: "chat.completion",
        completionTokens: 10,
        promptTokens: 5,
        totalTokens: 15
      };
      await oracle.connect(oracleAccount).addOpenAiResponse(0, 0, response, "");

      const messages = await oracle.getMessages(0, 0)
      expect(messages.length).to.equal(2)
      expect(messages[1]).to.equal("Hi!")
    });
  });
});
